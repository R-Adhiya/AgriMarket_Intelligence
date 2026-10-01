"""
GET /api/dashboard/farmer  -- aggregated farmer dashboard data
GET /api/dashboard/buyer   -- aggregated buyer dashboard data

These endpoints collect data from multiple service layers into a single
response to minimise round-trips from the frontend dashboard page.
No business logic is duplicated here -- all calculations remain in their
respective service modules.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db
from app.models.buyer import Buyer
from app.models.buyer_requirement import BuyerRequirement, RequirementStatus
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.farmer_crop import FarmerCrop
from app.models.market import Market
from app.models.market_price import MarketPrice
from app.models.recommendation import Recommendation
from app.models.transaction_interest import InterestStatus, TransactionInterest
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ---------------------------------------------------------------------------
# Pydantic response schemas
# ---------------------------------------------------------------------------

class StatCards(BaseModel):
    total_crops: int = 0
    available_crops: int = 0
    total_available_quantity: float = 0.0
    buyer_opportunities: int = 0
    recommendation_count: int = 0
    pending_requests: int = 0
    accepted_requests: int = 0


class MarketSnapshotItem(BaseModel):
    crop_id: int
    crop_name: str
    market_id: int
    market_name: str
    modal_price: float
    unit: str
    price_date: str


class LatestRecommendation(BaseModel):
    id: int
    crop_name: str
    recommended_market: str
    net_revenue: float | None
    transport_cost: float | None
    price_used: float | None
    price_basis: str | None
    created_at: str


class BuyerOpportunity(BaseModel):
    requirement_id: int
    crop_name: str
    quantity_kg: float
    desired_price: float | None
    location: str | None
    buyer_name: str | None


class ActivityItem(BaseModel):
    kind: str          # "recommendation" | "interest_received" | "interest_sent"
    description: str
    created_at: str


class FarmerDashboardResponse(BaseModel):
    profile: dict[str, Any]
    stats: StatCards
    market_snapshot: list[MarketSnapshotItem]
    latest_recommendation: LatestRecommendation | None
    buyer_opportunities: list[BuyerOpportunity]
    recent_activity: list[ActivityItem]


# Buyer -----------------------------------------------------------------------

class BuyerStatCards(BaseModel):
    active_requirements: int = 0
    total_requirements: int = 0
    pending_requests: int = 0
    accepted_connections: int = 0
    rejected_requests: int = 0


class ActiveRequirement(BaseModel):
    id: int
    crop_name: str
    quantity_kg: float
    desired_price: float | None
    location: str | None
    status: str
    created_at: str


class MatchingFarmerItem(BaseModel):
    farmer_crop_id: int
    farmer_name: str
    crop_name: str
    available_quantity: float
    location: str | None
    district: str | None


class RequestActivityItem(BaseModel):
    id: int
    status: str
    crop_name: str | None
    other_party: str | None
    created_at: str


class BuyerDashboardResponse(BaseModel):
    profile: dict[str, Any]
    stats: BuyerStatCards
    active_requirements: list[ActiveRequirement]
    matching_farmers: list[MatchingFarmerItem]
    request_activity: list[RequestActivityItem]


# ---------------------------------------------------------------------------
# Farmer dashboard
# ---------------------------------------------------------------------------

@router.get("/farmer", response_model=FarmerDashboardResponse)
def get_farmer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.FARMER:
        raise HTTPException(status_code=403, detail="Farmer role required.")

    farmer: Farmer | None = db.query(Farmer).filter(
        Farmer.user_id == current_user.id
    ).first()

    if farmer is None:
        # Return empty dashboard rather than 404 so the page renders
        return FarmerDashboardResponse(
            profile={"full_name": current_user.full_name, "has_profile": False},
            stats=StatCards(),
            market_snapshot=[],
            latest_recommendation=None,
            buyer_opportunities=[],
            recent_activity=[],
        )

    # ---- Profile ----
    profile_data = {
        "has_profile": True,
        "full_name": current_user.full_name,
        "village": farmer.village,
        "district": farmer.district,
        "state": farmer.state,
        "phone": farmer.phone,
        "latitude": farmer.latitude,
        "longitude": farmer.longitude,
    }

    # ---- Crops ----
    crops = db.query(FarmerCrop).filter(
        FarmerCrop.farmer_id == farmer.id,
        FarmerCrop.is_active == True,
    ).options(joinedload(FarmerCrop.crop)).all()

    available_crops = [c for c in crops if c.is_available and (c.available_quantity or 0) > 0]
    total_available_qty = sum(
        float(c.available_quantity or 0) for c in available_crops
    )

    # ---- Buyer opportunities matching farmer's crops ----
    farmer_crop_ids = [c.crop_id for c in crops]
    opp_count = 0
    opportunities: list[BuyerOpportunity] = []
    if farmer_crop_ids:
        reqs = (
            db.query(BuyerRequirement)
            .filter(
                BuyerRequirement.crop_id.in_(farmer_crop_ids),
                BuyerRequirement.status == RequirementStatus.ACTIVE,
            )
            .options(joinedload(BuyerRequirement.crop), joinedload(BuyerRequirement.buyer))
            .order_by(BuyerRequirement.created_at.desc())
            .all()
        )
        opp_count = len(reqs)
        for r in reqs[:5]:
            buyer_name = None
            if r.buyer and r.buyer.user_id:
                u = db.query(User).filter(User.id == r.buyer.user_id).first()
                buyer_name = u.full_name if u else None
            opportunities.append(BuyerOpportunity(
                requirement_id=r.id,
                crop_name=r.crop.name if r.crop else "Unknown",
                quantity_kg=float(r.quantity_kg),
                desired_price=float(r.desired_price) if r.desired_price else None,
                location=r.location,
                buyer_name=buyer_name,
            ))

    # ---- Recommendations ----
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.farmer_id == farmer.id)
        .options(
            joinedload(Recommendation.crop),
            joinedload(Recommendation.recommended_market),
        )
        .order_by(Recommendation.created_at.desc())
        .all()
    )
    rec_count = len(recs)
    latest_rec: LatestRecommendation | None = None
    if recs:
        r = recs[0]
        latest_rec = LatestRecommendation(
            id=r.id,
            crop_name=r.crop.name if r.crop else "Unknown",
            recommended_market=r.recommended_market.name if r.recommended_market else "Unknown",
            net_revenue=float(r.expected_net_revenue) if r.expected_net_revenue else None,
            transport_cost=float(r.transport_cost) if r.transport_cost else None,
            price_used=float(r.current_price) if r.current_price else None,
            price_basis=r.price_basis,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )

    # ---- Pending interests received by this farmer ----
    pending_interests = db.query(TransactionInterest).filter(
        TransactionInterest.farmer_id == farmer.id,
        TransactionInterest.status == InterestStatus.PENDING,
    ).count()

    accepted_interests = db.query(TransactionInterest).filter(
        TransactionInterest.farmer_id == farmer.id,
        TransactionInterest.status == InterestStatus.ACCEPTED,
    ).count()

    stats = StatCards(
        total_crops=len(crops),
        available_crops=len(available_crops),
        total_available_quantity=round(total_available_qty, 2),
        buyer_opportunities=opp_count,
        recommendation_count=rec_count,
        pending_requests=pending_interests,
        accepted_requests=accepted_interests,
    )

    # ---- Market snapshot: latest price per (crop, market) for farmer's crops ----
    market_snapshot: list[MarketSnapshotItem] = []
    if farmer_crop_ids:
        # Latest price date per crop+market
        subq = (
            db.query(
                MarketPrice.crop_id,
                MarketPrice.market_id,
                func.max(MarketPrice.price_date).label("max_date"),
            )
            .filter(MarketPrice.crop_id.in_(farmer_crop_ids))
            .group_by(MarketPrice.crop_id, MarketPrice.market_id)
            .subquery()
        )
        latest_prices = (
            db.query(MarketPrice)
            .join(
                subq,
                (MarketPrice.crop_id == subq.c.crop_id)
                & (MarketPrice.market_id == subq.c.market_id)
                & (MarketPrice.price_date == subq.c.max_date),
            )
            .options(joinedload(MarketPrice.crop), joinedload(MarketPrice.market))
            .all()
        )
        for mp in latest_prices[:9]:  # limit to 9 cards
            market_snapshot.append(MarketSnapshotItem(
                crop_id=mp.crop_id,
                crop_name=mp.crop.name if mp.crop else "",
                market_id=mp.market_id,
                market_name=mp.market.name if mp.market else "",
                modal_price=float(mp.modal_price),
                unit=mp.crop.unit.value if mp.crop else "kg",
                price_date=mp.price_date.isoformat() if mp.price_date else "",
            ))

    # ---- Recent activity ----
    activity: list[ActivityItem] = []
    # recent recommendations
    for r in recs[:3]:
        activity.append(ActivityItem(
            kind="recommendation",
            description=f"Recommended {r.recommended_market.name if r.recommended_market else '?'} for {r.crop.name if r.crop else '?'}",
            created_at=r.created_at.isoformat() if r.created_at else "",
        ))
    # recent interests received
    recent_interests = (
        db.query(TransactionInterest)
        .filter(TransactionInterest.farmer_id == farmer.id)
        .options(
            joinedload(TransactionInterest.requirement).joinedload(BuyerRequirement.crop)
        )
        .order_by(TransactionInterest.created_at.desc())
        .limit(3)
        .all()
    )
    for i in recent_interests:
        req = i.requirement
        crop_name = req.crop.name if req and req.crop else "produce"
        activity.append(ActivityItem(
            kind="interest_received",
            description=f"Buyer interest received for {crop_name} ({i.status.value})",
            created_at=i.created_at.isoformat() if i.created_at else "",
        ))
    # sort by created_at desc, take top 5
    activity.sort(key=lambda x: x.created_at, reverse=True)
    activity = activity[:5]

    return FarmerDashboardResponse(
        profile=profile_data,
        stats=stats,
        market_snapshot=market_snapshot,
        latest_recommendation=latest_rec,
        buyer_opportunities=opportunities,
        recent_activity=activity,
    )


# ---------------------------------------------------------------------------
# Buyer dashboard
# ---------------------------------------------------------------------------

@router.get("/buyer", response_model=BuyerDashboardResponse)
def get_buyer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.BUYER:
        raise HTTPException(status_code=403, detail="Buyer role required.")

    buyer: Buyer | None = db.query(Buyer).filter(
        Buyer.user_id == current_user.id
    ).first()

    if buyer is None:
        return BuyerDashboardResponse(
            profile={"full_name": current_user.full_name, "has_profile": False},
            stats=BuyerStatCards(),
            active_requirements=[],
            matching_farmers=[],
            request_activity=[],
        )

    # ---- Profile ----
    profile_data = {
        "has_profile": True,
        "full_name": current_user.full_name,
        "business_name": buyer.business_name,
        "phone": buyer.phone,
        "location": buyer.location,
        "district": buyer.district,
        "state": buyer.state,
    }

    # ---- Requirements ----
    all_reqs = (
        db.query(BuyerRequirement)
        .filter(BuyerRequirement.buyer_id == buyer.id)
        .options(joinedload(BuyerRequirement.crop))
        .order_by(BuyerRequirement.created_at.desc())
        .all()
    )
    active_reqs = [r for r in all_reqs if r.status == RequirementStatus.ACTIVE]

    active_req_items: list[ActiveRequirement] = []
    for r in active_reqs[:10]:
        active_req_items.append(ActiveRequirement(
            id=r.id,
            crop_name=r.crop.name if r.crop else "Unknown",
            quantity_kg=float(r.quantity_kg),
            desired_price=float(r.desired_price) if r.desired_price else None,
            location=r.location,
            status=r.status.value,
            created_at=r.created_at.isoformat() if r.created_at else "",
        ))

    # ---- Matching farmers for active requirements ----
    matching: list[MatchingFarmerItem] = []
    seen_farmer_crops: set[int] = set()
    for req in active_reqs[:5]:
        farmer_crops = (
            db.query(FarmerCrop)
            .filter(
                FarmerCrop.crop_id == req.crop_id,
                FarmerCrop.is_available == True,
                FarmerCrop.available_quantity > 0,
                FarmerCrop.is_active == True,
            )
            .options(
                joinedload(FarmerCrop.crop),
                joinedload(FarmerCrop.farmer),
            )
            .all()
        )
        for fc in farmer_crops:
            if fc.id in seen_farmer_crops:
                continue
            seen_farmer_crops.add(fc.id)
            farmer_user = (
                db.query(User).filter(User.id == fc.farmer.user_id).first()
                if fc.farmer else None
            )
            matching.append(MatchingFarmerItem(
                farmer_crop_id=fc.id,
                farmer_name=farmer_user.full_name if farmer_user else "Farmer",
                crop_name=fc.crop.name if fc.crop else "Unknown",
                available_quantity=float(fc.available_quantity or 0),
                location=fc.farmer.district if fc.farmer else None,
                district=fc.farmer.district if fc.farmer else None,
            ))
            if len(matching) >= 10:
                break
        if len(matching) >= 10:
            break

    # ---- Sent interest requests ----
    interests = (
        db.query(TransactionInterest)
        .filter(TransactionInterest.buyer_id == buyer.id)
        .options(
            joinedload(TransactionInterest.requirement).joinedload(BuyerRequirement.crop)
        )
        .order_by(TransactionInterest.created_at.desc())
        .limit(20)
        .all()
    )

    pending_count = sum(1 for i in interests if i.status == InterestStatus.PENDING)
    accepted_count = sum(1 for i in interests if i.status == InterestStatus.ACCEPTED)
    rejected_count = sum(1 for i in interests if i.status == InterestStatus.REJECTED)

    req_activity: list[RequestActivityItem] = []
    for i in interests[:10]:
        req = i.requirement
        crop_name = req.crop.name if req and req.crop else None
        # Find farmer name
        farmer_user = None
        if i.farmer_id:
            farmer = db.query(Farmer).filter(Farmer.id == i.farmer_id).first()
            if farmer:
                farmer_user = db.query(User).filter(User.id == farmer.user_id).first()
        req_activity.append(RequestActivityItem(
            id=i.id,
            status=i.status.value,
            crop_name=crop_name,
            other_party=farmer_user.full_name if farmer_user else None,
            created_at=i.created_at.isoformat() if i.created_at else "",
        ))

    stats = BuyerStatCards(
        active_requirements=len(active_reqs),
        total_requirements=len(all_reqs),
        pending_requests=pending_count,
        accepted_connections=accepted_count,
        rejected_requests=rejected_count,
    )

    return BuyerDashboardResponse(
        profile=profile_data,
        stats=stats,
        active_requirements=active_req_items,
        matching_farmers=matching,
        request_activity=req_activity,
    )

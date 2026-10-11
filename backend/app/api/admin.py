"""
Admin Panel API — Phase 11

All endpoints require role=ADMIN.
FARMER/BUYER → 403, unauthenticated → 401.

Routes:
  GET /api/admin/dashboard
  GET /api/admin/users
  GET /api/admin/users/{user_id}
  PATCH /api/admin/users/{user_id}/status
  GET /api/admin/farmers
  GET /api/admin/buyers
  GET /api/admin/markets
  GET /api/admin/market-prices
  GET /api/admin/activity
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, get_db, require_role
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

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PlatformStats(BaseModel):
    # Users
    total_users: int
    total_farmers: int
    total_buyers: int
    total_admins: int
    # Farmer activity
    total_farmer_profiles: int
    total_crop_listings: int
    available_crop_listings: int
    total_available_quantity: float
    # Buyer activity
    total_requirements: int
    active_requirements: int
    fulfilled_requirements: int
    # Market activity
    total_markets: int
    total_crops: int
    total_price_records: int
    # Recommendations
    total_recommendations: int
    # Interests
    total_interests: int
    pending_interests: int
    accepted_interests: int
    rejected_interests: int


class AdminDashboardResponse(BaseModel):
    stats: PlatformStats


class UserRow(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    is_verified: bool
    completed_transaction_count: int
    created_at: str


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UserRow]


class UserDetail(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: str


class StatusUpdate(BaseModel):
    is_active: bool


class FarmerRow(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    district: Optional[str]
    state: Optional[str]
    farm_size_acres: Optional[float]
    crop_count: int
    available_crop_count: int


class FarmerListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[FarmerRow]


class BuyerRow(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    business_name: Optional[str]
    district: Optional[str]
    state: Optional[str]
    active_requirement_count: int


class BuyerListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[BuyerRow]


class MarketRow(BaseModel):
    id: int
    name: str
    market_code: Optional[str]
    location: Optional[str]
    district: Optional[str]
    state: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    market_type: Optional[str]
    is_active: bool


class MarketListResponse(BaseModel):
    total: int
    items: list[MarketRow]


class PriceRow(BaseModel):
    id: int
    crop_name: str
    market_name: str
    min_price: float
    modal_price: float
    max_price: float
    price_date: str
    source: Optional[str]


class PriceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PriceRow]


class ActivityItem(BaseModel):
    kind: str
    description: str
    timestamp: str


class ActivityResponse(BaseModel):
    items: list[ActivityItem]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(dt) -> str:
    return dt.isoformat() if dt else ""


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/dashboard", response_model=AdminDashboardResponse)
def admin_dashboard(db: Session = Depends(get_db)):
    # User counts
    role_counts = dict(
        db.query(User.role, func.count(User.id))
        .group_by(User.role)
        .all()
    )
    total_users   = db.query(func.count(User.id)).scalar() or 0
    total_farmers = role_counts.get(UserRole.FARMER, 0)
    total_buyers  = role_counts.get(UserRole.BUYER, 0)
    total_admins  = role_counts.get(UserRole.ADMIN, 0)

    # Farmer
    total_farmer_profiles = db.query(func.count(Farmer.id)).scalar() or 0
    total_listings        = db.query(func.count(FarmerCrop.id)).scalar() or 0
    avail_listings        = (
        db.query(func.count(FarmerCrop.id))
        .filter(FarmerCrop.is_available == True, FarmerCrop.quantity > 0)
        .scalar() or 0
    )
    total_avail_qty = float(
        db.query(func.sum(FarmerCrop.quantity))
        .filter(FarmerCrop.is_available == True)
        .scalar() or 0
    )

    # Buyer requirements
    req_counts = dict(
        db.query(BuyerRequirement.status, func.count(BuyerRequirement.id))
        .group_by(BuyerRequirement.status)
        .all()
    )
    total_reqs     = db.query(func.count(BuyerRequirement.id)).scalar() or 0
    active_reqs    = req_counts.get(RequirementStatus.ACTIVE, 0)
    fulfilled_reqs = req_counts.get(RequirementStatus.FULFILLED, 0)

    # Market
    total_markets = db.query(func.count(Market.id)).scalar() or 0
    total_crops   = db.query(func.count(Crop.id)).scalar() or 0
    total_prices  = db.query(func.count(MarketPrice.id)).scalar() or 0

    # Recommendations
    total_recs = db.query(func.count(Recommendation.id)).scalar() or 0

    # Interests
    interest_counts = dict(
        db.query(TransactionInterest.status, func.count(TransactionInterest.id))
        .group_by(TransactionInterest.status)
        .all()
    )
    total_interests    = db.query(func.count(TransactionInterest.id)).scalar() or 0
    pending_interests  = interest_counts.get(InterestStatus.PENDING, 0)
    accepted_interests = interest_counts.get(InterestStatus.ACCEPTED, 0)
    rejected_interests = interest_counts.get(InterestStatus.REJECTED, 0)

    stats = PlatformStats(
        total_users=total_users,
        total_farmers=total_farmers,
        total_buyers=total_buyers,
        total_admins=total_admins,
        total_farmer_profiles=total_farmer_profiles,
        total_crop_listings=total_listings,
        available_crop_listings=avail_listings,
        total_available_quantity=round(total_avail_qty, 2),
        total_requirements=total_reqs,
        active_requirements=active_reqs,
        fulfilled_requirements=fulfilled_reqs,
        total_markets=total_markets,
        total_crops=total_crops,
        total_price_records=total_prices,
        total_recommendations=total_recs,
        total_interests=total_interests,
        pending_interests=pending_interests,
        accepted_interests=accepted_interests,
        rejected_interests=rejected_interests,
    )
    return AdminDashboardResponse(stats=stats)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@router.get("/users", response_model=UserListResponse)
def list_users(
    role: Optional[str] = Query(None, description="Filter by role: FARMER, BUYER, ADMIN"),
    is_active: Optional[bool] = Query(None),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status (FARMER/BUYER only)"),
    search: Optional[str] = Query(None, description="Search by name or email (case-insensitive)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    from sqlalchemy import or_, case, literal, and_

    # Build a subquery that assigns is_verified to each user via OUTER JOINs to
    # farmers and buyers.  This lets us filter AND paginate in one DB round-trip
    # so that `total` and `items` are always consistent.

    # Left-join User → Farmer, User → Buyer; the actual is_verified value comes
    # from whichever profile row exists (at most one of them for a given user).
    farmer_alias = Farmer.__table__.alias("fa")
    buyer_alias  = Buyer.__table__.alias("ba")

    q = (
        db.query(
            User,
            case(
                (farmer_alias.c.is_verified.isnot(None), farmer_alias.c.is_verified),
                (buyer_alias.c.is_verified.isnot(None),  buyer_alias.c.is_verified),
                else_=literal(False),
            ).label("eff_verified"),
            case(
                (farmer_alias.c.completed_transaction_count.isnot(None),
                 farmer_alias.c.completed_transaction_count),
                (buyer_alias.c.completed_transaction_count.isnot(None),
                 buyer_alias.c.completed_transaction_count),
                else_=literal(0),
            ).label("eff_count"),
        )
        .outerjoin(farmer_alias, farmer_alias.c.user_id == User.id)
        .outerjoin(buyer_alias,  buyer_alias.c.user_id  == User.id)
    )

    if role:
        try:
            q = q.filter(User.role == UserRole(role.upper()))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid role: {role}")
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(User.full_name.ilike(like), User.email.ilike(like)))
    if is_verified is not None:
        # Filter on the effective verified flag computed in the query
        verified_expr = case(
            (farmer_alias.c.is_verified.isnot(None), farmer_alias.c.is_verified),
            (buyer_alias.c.is_verified.isnot(None),  buyer_alias.c.is_verified),
            else_=literal(False),
        )
        q = q.filter(verified_expr == is_verified)

    total = q.count()
    rows_raw = q.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        UserRow(
            id=u.id,
            full_name=u.full_name,
            email=u.email,
            role=u.role.value,
            is_active=u.is_active,
            is_verified=bool(eff_v),
            completed_transaction_count=int(eff_c or 0),
            created_at=_ts(u.created_at),
        )
        for u, eff_v, eff_c in rows_raw
    ]

    return UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/users/{user_id}", response_model=UserDetail)
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserDetail(
        id=u.id,
        full_name=u.full_name,
        email=u.email,
        phone=u.phone,
        role=u.role.value,
        is_active=u.is_active,
        created_at=_ts(u.created_at),
    )


@router.patch("/users/{user_id}/status", response_model=UserDetail)
def update_user_status(
    user_id: int,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
):
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Admin cannot change their own status.")
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found.")
    u.is_active = body.is_active
    db.commit()
    db.refresh(u)
    return UserDetail(
        id=u.id,
        full_name=u.full_name,
        email=u.email,
        phone=u.phone,
        role=u.role.value,
        is_active=u.is_active,
        created_at=_ts(u.created_at),
    )


# ---------------------------------------------------------------------------
# Farmers
# ---------------------------------------------------------------------------

@router.get("/farmers", response_model=FarmerListResponse)
def list_farmers(
    district: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Farmer).options(joinedload(Farmer.user))
    if district:
        q = q.filter(Farmer.district.ilike(f"%{district}%"))
    if state:
        q = q.filter(Farmer.state.ilike(f"%{state}%"))
    total = q.count()
    farmers = q.order_by(Farmer.id).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for f in farmers:
        crop_count  = db.query(func.count(FarmerCrop.id)).filter(FarmerCrop.farmer_id == f.id).scalar() or 0
        avail_count = (
            db.query(func.count(FarmerCrop.id))
            .filter(FarmerCrop.farmer_id == f.id, FarmerCrop.is_available == True)
            .scalar() or 0
        )
        items.append(FarmerRow(
            id=f.id,
            user_id=f.user_id,
            full_name=f.user.full_name if f.user else "",
            email=f.user.email if f.user else "",
            district=f.district,
            state=f.state,
            farm_size_acres=float(f.farm_size) if f.farm_size else None,
            crop_count=crop_count,
            available_crop_count=avail_count,
        ))

    return FarmerListResponse(total=total, page=page, page_size=page_size, items=items)


# ---------------------------------------------------------------------------
# Buyers
# ---------------------------------------------------------------------------

@router.get("/buyers", response_model=BuyerListResponse)
def list_buyers(
    district: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Buyer).options(joinedload(Buyer.user))
    if district:
        q = q.filter(Buyer.district.ilike(f"%{district}%"))
    if state:
        q = q.filter(Buyer.state.ilike(f"%{state}%"))
    total = q.count()
    buyers = q.order_by(Buyer.id).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for b in buyers:
        active_count = (
            db.query(func.count(BuyerRequirement.id))
            .filter(
                BuyerRequirement.buyer_id == b.id,
                BuyerRequirement.status == RequirementStatus.ACTIVE,
            )
            .scalar() or 0
        )
        items.append(BuyerRow(
            id=b.id,
            user_id=b.user_id,
            full_name=b.user.full_name if b.user else "",
            email=b.user.email if b.user else "",
            business_name=b.business_name,
            district=b.district,
            state=b.state,
            active_requirement_count=active_count,
        ))

    return BuyerListResponse(total=total, page=page, page_size=page_size, items=items)


# ---------------------------------------------------------------------------
# Markets
# ---------------------------------------------------------------------------

@router.get("/markets", response_model=MarketListResponse)
def list_markets(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Market)
    if state:
        q = q.filter(Market.state.ilike(f"%{state}%"))
    if district:
        q = q.filter(Market.district.ilike(f"%{district}%"))
    markets = q.order_by(Market.id).all()
    return MarketListResponse(
        total=len(markets),
        items=[
            MarketRow(
                id=m.id,
                name=m.name,
                market_code=m.market_code,
                location=m.location,
                district=m.district,
                state=m.state,
                latitude=float(m.latitude) if m.latitude else None,
                longitude=float(m.longitude) if m.longitude else None,
                market_type=m.market_type.value if m.market_type else None,
                is_active=m.is_active,
            )
            for m in markets
        ],
    )


# ---------------------------------------------------------------------------
# Market Prices
# ---------------------------------------------------------------------------

@router.get("/market-prices", response_model=PriceListResponse)
def list_market_prices(
    crop_id: Optional[int] = Query(None),
    market_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to:   Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = (
        db.query(MarketPrice)
        .options(joinedload(MarketPrice.crop), joinedload(MarketPrice.market))
    )
    if crop_id:
        q = q.filter(MarketPrice.crop_id == crop_id)
    if market_id:
        q = q.filter(MarketPrice.market_id == market_id)
    if date_from:
        q = q.filter(MarketPrice.price_date >= date_from)
    if date_to:
        q = q.filter(MarketPrice.price_date <= date_to)
    total = q.count()
    prices = q.order_by(MarketPrice.price_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PriceListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[
            PriceRow(
                id=mp.id,
                crop_name=mp.crop.name if mp.crop else "",
                market_name=mp.market.name if mp.market else "",
                min_price=float(mp.min_price),
                modal_price=float(mp.modal_price),
                max_price=float(mp.max_price),
                price_date=mp.price_date.isoformat() if mp.price_date else "",
                source=mp.source if hasattr(mp, "source") else None,
            )
            for mp in prices
        ],
    )


# ---------------------------------------------------------------------------
# Activity
# ---------------------------------------------------------------------------

@router.get("/activity", response_model=ActivityResponse)
def recent_activity(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items: list[ActivityItem] = []

    # Recent registrations
    users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    for u in users:
        items.append(ActivityItem(
            kind="registration",
            description=f"User registered: {u.full_name} ({u.role.value})",
            timestamp=_ts(u.created_at),
        ))

    # Recent recommendations
    recs = (
        db.query(Recommendation)
        .options(joinedload(Recommendation.crop), joinedload(Recommendation.recommended_market))
        .order_by(Recommendation.created_at.desc())
        .limit(5)
        .all()
    )
    for r in recs:
        items.append(ActivityItem(
            kind="recommendation",
            description=(
                f"Recommendation: {r.crop.name if r.crop else '?'} → "
                f"{r.recommended_market.name if r.recommended_market else '?'}"
            ),
            timestamp=_ts(r.created_at),
        ))

    # Recent buyer requirements
    reqs = (
        db.query(BuyerRequirement)
        .options(joinedload(BuyerRequirement.crop))
        .order_by(BuyerRequirement.created_at.desc())
        .limit(5)
        .all()
    )
    for r in reqs:
        items.append(ActivityItem(
            kind="requirement",
            description=f"Buyer requirement: {r.crop.name if r.crop else '?'} ({r.quantity} kg)",
            timestamp=_ts(r.created_at),
        ))

    # Recent interests
    interests = (
        db.query(TransactionInterest)
        .order_by(TransactionInterest.created_at.desc())
        .limit(5)
        .all()
    )
    for i in interests:
        items.append(ActivityItem(
            kind="interest",
            description=f"Interest request ({i.status.value})",
            timestamp=_ts(i.created_at),
        ))

    # Sort by timestamp desc and return top N
    items.sort(key=lambda x: x.timestamp, reverse=True)
    return ActivityResponse(items=items[:limit])




# ── Correction 5: Crop suggestion management (admin) ─────────────────────────

from app.models.crop_suggestion import CropSuggestion, SuggestionStatus
from app.models.crop import CropUnit


class CropSuggestionResponse(BaseModel):
    id: int
    suggested_name: str
    category: Optional[str] = None
    notes: Optional[str] = None
    status: str
    admin_notes: Optional[str] = None
    approved_crop_id: Optional[int] = None
    suggested_by_user_id: Optional[int] = None

    model_config = {"from_attributes": True}


class CropSuggestionAction(BaseModel):
    action: str          # "approve" | "reject"
    admin_notes: Optional[str] = None
    category: Optional[str] = None   # used when approving to set the crop category


@router.get(
    "/crop-suggestions",
    response_model=list[CropSuggestionResponse],
    summary="List crop suggestions (filterable by status)",
)
def list_crop_suggestions(
    status: Optional[str] = Query(None, description="PENDING | APPROVED | REJECTED"),
    db: Session = Depends(get_db),
):
    q = db.query(CropSuggestion)
    if status:
        q = q.filter(CropSuggestion.status == status.upper())
    return q.order_by(CropSuggestion.created_at.desc()).all()


@router.post(
    "/crop-suggestions/{suggestion_id}/review",
    response_model=CropSuggestionResponse,
    summary="Approve or reject a crop suggestion",
)
def review_crop_suggestion(
    suggestion_id: int,
    payload: CropSuggestionAction,
    db: Session = Depends(get_db),
):
    suggestion = db.query(CropSuggestion).filter_by(id=suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found.")
    if suggestion.status != SuggestionStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Suggestion is already {suggestion.status}.")

    if payload.action.lower() == "approve":
        # Case-insensitive duplicate check
        existing = (
            db.query(Crop)
            .filter(func.lower(Crop.name) == suggestion.suggested_name.strip().lower())
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"A crop named '{existing.name}' already exists (id={existing.id}).",
            )

        new_crop = Crop(
            name=suggestion.suggested_name.strip(),
            category=payload.category or suggestion.category,
            unit=CropUnit.KG,
            is_active=True,
        )
        db.add(new_crop)
        db.flush()   # get the id without committing

        suggestion.status = SuggestionStatus.APPROVED
        suggestion.approved_crop_id = new_crop.id
        suggestion.admin_notes = payload.admin_notes

    elif payload.action.lower() == "reject":
        suggestion.status = SuggestionStatus.REJECTED
        suggestion.admin_notes = payload.admin_notes

    else:
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'.")

    db.commit()
    db.refresh(suggestion)
    return suggestion

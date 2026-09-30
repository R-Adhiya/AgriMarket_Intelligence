"""
Recommendation API — Phase 8.

POST /api/recommendation/market   — run recommendation for authenticated farmer
GET  /api/recommendation/history  — farmer's own recommendation history
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.crop import Crop
from app.models.farmer import Farmer
from app.models.recommendation import Recommendation
from app.models.user import User, UserRole
from app.schemas.recommendation import (
    ExcludedMarketSchema,
    MarketOptionSchema,
    RecommendationHistoryEntry,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.location import LocationError
from app.services.recommendation import run_recommendation

router = APIRouter(
    prefix="/api/recommendation",
    tags=["Recommendation"],
    dependencies=[Depends(require_role(UserRole.FARMER))],
)


def _get_farmer(user: User, db: Session) -> Farmer:
    farmer = db.query(Farmer).filter_by(user_id=user.id).first()
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Farmer profile not found. Please create your profile first.",
        )
    return farmer


# ── POST /api/recommendation/market ──────────────────────────────────────────

@router.post(
    "/market",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Get market recommendation for the authenticated farmer",
)
def recommend_market(
    payload: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(current_user, db)

    crop = db.query(Crop).filter_by(id=payload.crop_id, is_active=True).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found.")

    if payload.price_basis not in ("current", "predicted"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="price_basis must be 'current' or 'predicted'.",
        )

    try:
        result = run_recommendation(
            farmer=farmer,
            crop=crop,
            quantity_kg=payload.quantity_kg,
            price_basis=payload.price_basis,
            db=db,
        )
    except LocationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # Save to history
    saved_id = None
    if result.recommended:
        rec = Recommendation(
            farmer_id=farmer.id,
            crop_id=crop.id,
            recommended_market_id=result.recommended.market_id,
            quantity=payload.quantity_kg,
            current_price=result.recommended.price_per_unit,
            transport_cost=result.recommended.transport_cost,
            expected_gross_revenue=result.recommended.gross_revenue,
            expected_net_revenue=result.recommended.net_revenue,
            distance_km=result.recommended.distance_km,
            price_basis=payload.price_basis,
            confidence=None,
            reason=result.explanation,
            explanation=result.explanation,
        )
        db.add(rec)
        db.commit()
        saved_id = rec.id

    return RecommendationResponse(
        recommended_market=(
            MarketOptionSchema(**result.recommended.as_dict()) if result.recommended else None
        ),
        crop_id=result.crop_id,
        crop_name=result.crop_name,
        crop_unit=result.crop_unit,
        quantity_kg=result.quantity_kg,
        price_basis=result.price_basis,
        recommendation_method=result.recommendation_method,
        confidence=None,
        explanation=result.explanation,
        comparison=[MarketOptionSchema(**o.as_dict()) for o in result.comparison],
        excluded_markets=[ExcludedMarketSchema(**e) for e in result.excluded_markets],
        saved_recommendation_id=saved_id,
    )


# ── GET /api/recommendation/history ──────────────────────────────────────────

@router.get(
    "/history",
    response_model=list[RecommendationHistoryEntry],
    summary="Retrieve the authenticated farmer's recommendation history",
)
def recommendation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer(current_user, db)

    recs = (
        db.query(Recommendation)
        .options(
            joinedload(Recommendation.crop),
            joinedload(Recommendation.recommended_market),
        )
        .filter_by(farmer_id=farmer.id)
        .order_by(Recommendation.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        RecommendationHistoryEntry(
            id=r.id,
            crop_name=r.crop.name if r.crop else None,
            market_name=r.recommended_market.name if r.recommended_market else None,
            quantity=float(r.quantity) if r.quantity is not None else None,
            current_price=float(r.current_price) if r.current_price is not None else None,
            transport_cost=float(r.transport_cost) if r.transport_cost is not None else None,
            expected_gross_revenue=float(r.expected_gross_revenue) if r.expected_gross_revenue is not None else None,
            expected_net_revenue=float(r.expected_net_revenue) if r.expected_net_revenue is not None else None,
            distance_km=float(r.distance_km) if r.distance_km is not None else None,
            price_basis=r.price_basis,
            explanation=r.explanation,
            created_at=r.created_at.isoformat(),
        )
        for r in recs
    ]

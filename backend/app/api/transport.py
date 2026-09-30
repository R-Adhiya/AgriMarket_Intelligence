"""
Location & Transport Cost API — Phase 6.

Routes:
  GET /api/transport/distance/{market_id}
      — distance from authenticated farmer to one market

  GET /api/transport/estimate/{market_id}
      — transport cost estimate for one market

  GET /api/transport/markets
      — distance + cost for ALL active markets (sorted by distance)

All endpoints require JWT (any authenticated role that has a farmer
profile).  FARMER role is recommended for meaningful responses;
other roles will receive a 422 if they have no farmer profile.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.database.session import get_db
from app.models.farmer import Farmer
from app.models.market import Market
from app.models.user import User
from app.schemas.transport import (
    DistanceResponse,
    MultiMarketTransportResponse,
    TransportEstimate,
)
from app.services.location import (
    LocationError,
    CoordinateError,
    estimate_transport_cost,
    haversine_km,
    resolve_farmer_coords,
    resolve_market_coords,
)

router = APIRouter(
    prefix="/api/transport",
    tags=["Location & Transport"],
    dependencies=[Depends(get_current_user)],
)

_DEFAULT_QUANTITY = 10.0  # quintals


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_farmer_or_422(user: User, db: Session) -> Farmer:
    farmer = db.query(Farmer).filter_by(user_id=user.id).first()
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Farmer profile not found. Please create your profile first.",
        )
    return farmer


def _resolve_farmer(farmer: Farmer) -> tuple[float, float, str]:
    """Returns (lat, lon, source_label). Raises 422 on failure."""
    try:
        lat, lon = resolve_farmer_coords(farmer.latitude, farmer.longitude, farmer.district)
        source = "stored_coordinates" if (farmer.latitude and farmer.longitude) else "district_lookup"
        return lat, lon, source
    except (LocationError, CoordinateError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


def _get_market_or_404(market_id: int, db: Session) -> Market:
    m = db.query(Market).filter_by(id=market_id, is_active=True).first()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found.")
    return m


def _resolve_market(market: Market) -> tuple[float, float]:
    try:
        return resolve_market_coords(market.latitude, market.longitude, market.name)
    except (LocationError, CoordinateError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


def _build_estimate(
    market: Market,
    farmer_lat: float, farmer_lon: float,
    quantity: float,
) -> TransportEstimate:
    m_lat, m_lon = _resolve_market(market)
    dist = round(haversine_km(farmer_lat, farmer_lon, m_lat, m_lon), 2)
    cost = estimate_transport_cost(
        dist, quantity,
        settings.TRANSPORT_BASE_COST,
        settings.TRANSPORT_RATE_PER_KM,
    )
    return TransportEstimate(
        market_id=market.id,
        market_name=market.name,
        district=market.district,
        state=market.state,
        distance_km=dist,
        quantity_quintals=quantity,
        estimated_transport_cost=cost,
        assumptions={
            "base_cost_inr": settings.TRANSPORT_BASE_COST,
            "rate_per_km_per_quintal": settings.TRANSPORT_RATE_PER_KM,
            "formula": "base_cost + (distance_km × rate_per_km × quantity_quintals)",
        },
    )


# ── Distance endpoint ─────────────────────────────────────────────────────────

@router.get(
    "/distance/{market_id}",
    response_model=DistanceResponse,
    summary="Distance from the authenticated farmer to a market",
)
def get_distance(
    market_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer_or_422(current_user, db)
    market = _get_market_or_404(market_id, db)
    f_lat, f_lon, source = _resolve_farmer(farmer)
    m_lat, m_lon = _resolve_market(market)
    dist = round(haversine_km(f_lat, f_lon, m_lat, m_lon), 2)
    return DistanceResponse(
        market_id=market.id,
        market_name=market.name,
        district=market.district,
        state=market.state,
        farmer_district=farmer.district,
        farmer_location_source=source,
        distance_km=dist,
    )


# ── Single-market transport estimate ─────────────────────────────────────────

@router.get(
    "/estimate/{market_id}",
    response_model=TransportEstimate,
    summary="Estimated transport cost from farmer to one market",
)
def estimate_to_market(
    market_id: int,
    quantity: float = Query(_DEFAULT_QUANTITY, gt=0, description="Quantity in quintals"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer_or_422(current_user, db)
    market = _get_market_or_404(market_id, db)
    f_lat, f_lon, _ = _resolve_farmer(farmer)
    return _build_estimate(market, f_lat, f_lon, quantity)


# ── Multi-market transport estimates ─────────────────────────────────────────

@router.get(
    "/markets",
    response_model=MultiMarketTransportResponse,
    summary="Distance and transport cost from farmer to ALL active markets",
)
def estimate_all_markets(
    quantity: float = Query(_DEFAULT_QUANTITY, gt=0, description="Quantity in quintals"),
    state: Optional[str] = Query(None, description="Filter markets by state"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    farmer = _get_farmer_or_422(current_user, db)
    f_lat, f_lon, source = _resolve_farmer(farmer)

    q = db.query(Market).filter(Market.is_active == True)  # noqa: E712
    if state:
        q = q.filter(Market.state.ilike(f"%{state}%"))
    markets = q.all()

    estimates = []
    for m in markets:
        try:
            estimates.append(_build_estimate(m, f_lat, f_lon, quantity))
        except HTTPException:
            # Skip markets with missing coordinates instead of failing the whole request
            continue

    estimates.sort(key=lambda e: e.distance_km)

    return MultiMarketTransportResponse(
        farmer_district=farmer.district,
        farmer_location_source=source,
        quantity_quintals=quantity,
        markets=estimates,
    )

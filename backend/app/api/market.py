"""
Market Intelligence API — Phase 5.

Endpoints:
  GET /api/market/markets            — list active markets
  GET /api/market/crops              — list crops that have price data
  GET /api/market/prices             — all recent prices (filterable)
  GET /api/market/prices/{crop_id}   — current price comparison across markets
  GET /api/market/prices/{crop_id}/history — historical prices for charting
"""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.crop import Crop
from app.models.market import Market
from app.models.market_price import MarketPrice
from app.models.user import User
from app.schemas.market import (
    CropSummary,
    MarketPriceComparison,
    MarketPriceResponse,
    MarketSummary,
    PriceComparisonResponse,
    PriceHistoryPoint,
    PriceHistoryResponse,
)

router = APIRouter(
    prefix="/api/market",
    tags=["Market Intelligence"],
    dependencies=[Depends(get_current_user)],  # JWT required; any authenticated role
)

_DATA_NOTICE = "Development sample data — not real-time government prices."


# ── Helper: latest price date per market+crop ─────────────────────────────────

def _latest_prices_subq(db: Session):
    """Return a subquery: (market_id, crop_id) → max(price_date)."""
    return (
        db.query(
            MarketPrice.market_id,
            MarketPrice.crop_id,
            func.max(MarketPrice.price_date).label("latest_date"),
        )
        .group_by(MarketPrice.market_id, MarketPrice.crop_id)
        .subquery()
    )


# ── Markets ───────────────────────────────────────────────────────────────────

@router.get(
    "/markets",
    response_model=list[MarketSummary],
    summary="List all active markets",
)
def list_markets(
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    db: Session = Depends(get_db),
):
    q = db.query(Market).filter(Market.is_active == True)  # noqa: E712
    if state:
        q = q.filter(Market.state.ilike(f"%{state}%"))
    if district:
        q = q.filter(Market.district.ilike(f"%{district}%"))
    return q.order_by(Market.name).all()


# ── Crops with price data ─────────────────────────────────────────────────────

@router.get(
    "/crops",
    response_model=list[CropSummary],
    summary="List crops that have market price data",
)
def list_crops_with_prices(db: Session = Depends(get_db)):
    from sqlalchemy import select
    crop_ids_sq = select(MarketPrice.crop_id).distinct()
    crops = (
        db.query(Crop)
        .filter(Crop.id.in_(crop_ids_sq), Crop.is_active == True)  # noqa: E712
        .order_by(Crop.name)
        .all()
    )
    return crops


# ── All recent prices ─────────────────────────────────────────────────────────

@router.get(
    "/prices",
    response_model=list[MarketPriceResponse],
    summary="List market prices (filterable by crop, market, date range)",
)
def list_prices(
    crop_id: Optional[int]  = Query(None),
    market_id: Optional[int] = Query(None),
    state: Optional[str]    = Query(None),
    district: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date]   = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = (
        db.query(MarketPrice)
        .options(joinedload(MarketPrice.market), joinedload(MarketPrice.crop))
    )
    if crop_id:
        q = q.filter(MarketPrice.crop_id == crop_id)
    if market_id:
        q = q.filter(MarketPrice.market_id == market_id)
    if from_date:
        q = q.filter(MarketPrice.price_date >= from_date)
    if to_date:
        q = q.filter(MarketPrice.price_date <= to_date)
    if state:
        q = q.join(Market, MarketPrice.market_id == Market.id).filter(
            Market.state.ilike(f"%{state}%")
        )
    if district:
        q = q.join(Market, MarketPrice.market_id == Market.id).filter(
            Market.district.ilike(f"%{district}%")
        )
    return q.order_by(MarketPrice.price_date.desc()).limit(limit).all()


# ── Current price comparison for one crop ────────────────────────────────────

@router.get(
    "/prices/{crop_id}",
    response_model=PriceComparisonResponse,
    summary="Compare current prices for one crop across markets",
)
def compare_prices(
    crop_id: int,
    state: Optional[str]    = Query(None, description="Filter markets by state"),
    district: Optional[str] = Query(None, description="Filter markets by district"),
    db: Session = Depends(get_db),
):
    crop = db.query(Crop).filter_by(id=crop_id, is_active=True).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found.")

    # Latest price per market for this crop
    latest_sq = (
        db.query(
            MarketPrice.market_id,
            func.max(MarketPrice.price_date).label("latest_date"),
        )
        .filter(MarketPrice.crop_id == crop_id)
        .group_by(MarketPrice.market_id)
        .subquery()
    )

    rows = (
        db.query(MarketPrice)
        .join(
            latest_sq,
            (MarketPrice.market_id == latest_sq.c.market_id)
            & (MarketPrice.price_date == latest_sq.c.latest_date),
        )
        .filter(MarketPrice.crop_id == crop_id)
        .options(joinedload(MarketPrice.market))
        .all()
    )

    comparisons = []
    for row in rows:
        mkt = row.market
        if not mkt or not mkt.is_active:
            continue
        if state and state.lower() not in (mkt.state or "").lower():
            continue
        if district and district.lower() not in (mkt.district or "").lower():
            continue
        comparisons.append(
            MarketPriceComparison(
                market_id=mkt.id,
                market_name=mkt.name,
                location=mkt.location,
                district=mkt.district,
                state=mkt.state,
                market_type=mkt.market_type.value,
                price_date=row.price_date,
                min_price=float(row.min_price),
                max_price=float(row.max_price),
                modal_price=float(row.modal_price),
                available_quantity=float(row.available_quantity) if row.available_quantity is not None else None,
                source=row.source,
            )
        )

    # Sort by modal price descending (best price first)
    comparisons.sort(key=lambda x: x.modal_price, reverse=True)

    return PriceComparisonResponse(
        crop=CropSummary(
            id=crop.id, name=crop.name, category=crop.category, unit=crop.unit.value
        ),
        prices=comparisons,
        data_notice=_DATA_NOTICE,
    )


# ── Historical prices for one crop (chart data) ───────────────────────────────

@router.get(
    "/prices/{crop_id}/history",
    response_model=PriceHistoryResponse,
    summary="Historical prices for one crop (suitable for line charts)",
)
def price_history(
    crop_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of past days to include"),
    market_id: Optional[int] = Query(None, description="Restrict to one market"),
    db: Session = Depends(get_db),
):
    crop = db.query(Crop).filter_by(id=crop_id, is_active=True).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found.")

    cutoff = date.today() - timedelta(days=days)

    q = (
        db.query(MarketPrice)
        .options(joinedload(MarketPrice.market))
        .filter(MarketPrice.crop_id == crop_id, MarketPrice.price_date >= cutoff)
    )
    if market_id:
        mkt = db.query(Market).filter_by(id=market_id, is_active=True).first()
        if not mkt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found.")
        q = q.filter(MarketPrice.market_id == market_id)

    records = q.order_by(MarketPrice.price_date.asc()).all()

    history = [
        PriceHistoryPoint(
            price_date=r.price_date,
            market_id=r.market_id,
            market_name=r.market.name if r.market else f"Market {r.market_id}",
            min_price=float(r.min_price),
            max_price=float(r.max_price),
            modal_price=float(r.modal_price),
            source=r.source,
        )
        for r in records
    ]

    return PriceHistoryResponse(
        crop=CropSummary(
            id=crop.id, name=crop.name, category=crop.category, unit=crop.unit.value
        ),
        days=days,
        history=history,
        data_notice=_DATA_NOTICE,
    )

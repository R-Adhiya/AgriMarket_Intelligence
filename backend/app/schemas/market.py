"""Pydantic schemas for the Market Intelligence module (Phase 5)."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


# ── Crop reference ────────────────────────────────────────────────────────────

class CropSummary(BaseModel):
    id: int
    name: str
    category: Optional[str]
    unit: str

    model_config = {"from_attributes": True}


# ── Market reference ──────────────────────────────────────────────────────────

class MarketSummary(BaseModel):
    id: int
    name: str
    market_code: str
    location: Optional[str]
    district: Optional[str]
    state: Optional[str]
    market_type: str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Market price ──────────────────────────────────────────────────────────────

class MarketPriceResponse(BaseModel):
    id: int
    market: MarketSummary
    crop: CropSummary
    price_date: date
    min_price: float
    max_price: float
    modal_price: float
    available_quantity: Optional[float]
    source: Optional[str]

    model_config = {"from_attributes": True}


# ── Price comparison (current prices across markets for one crop) ─────────────

class MarketPriceComparison(BaseModel):
    market_id: int
    market_name: str
    location: Optional[str]
    district: Optional[str]
    state: Optional[str]
    market_type: str
    price_date: date
    min_price: float
    max_price: float
    modal_price: float
    available_quantity: Optional[float]
    source: Optional[str]


class PriceComparisonResponse(BaseModel):
    crop: CropSummary
    prices: list[MarketPriceComparison]
    data_notice: str = "Development sample data — not live government prices."


# ── Historical price data point (for charting) ────────────────────────────────

class PriceHistoryPoint(BaseModel):
    price_date: date
    market_id: int
    market_name: str
    min_price: float
    max_price: float
    modal_price: float
    source: Optional[str]


class PriceHistoryResponse(BaseModel):
    crop: CropSummary
    days: int
    history: list[PriceHistoryPoint]
    data_notice: str = "Development sample data — not live government prices."

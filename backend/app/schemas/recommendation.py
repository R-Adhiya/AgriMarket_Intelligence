"""Pydantic schemas for the Recommendation API (Phase 8)."""

from typing import Optional
from pydantic import BaseModel, Field


# ── Request ───────────────────────────────────────────────────────────────────

class RecommendationRequest(BaseModel):
    crop_id:     int   = Field(..., gt=0)
    quantity_kg: float = Field(..., gt=0, description="Quantity to sell, in kilograms")
    price_basis: str   = Field("current", description="'current' or 'predicted'")


# ── Per-market entry in comparison table ─────────────────────────────────────

class MarketOptionSchema(BaseModel):
    market_id:      int
    market_name:    str
    district:       Optional[str]
    state:          Optional[str]
    price_per_unit: float
    price_unit:     str
    price_date:     str
    price_basis:    str
    distance_km:    float
    transport_cost: float
    gross_revenue:  float
    net_revenue:    float
    source:         Optional[str]
    is_recommended: bool


# ── Excluded market ───────────────────────────────────────────────────────────

class ExcludedMarketSchema(BaseModel):
    market_id:   int
    market_name: str
    reason:      str


# ── Full response ─────────────────────────────────────────────────────────────

class RecommendationResponse(BaseModel):
    # Recommended market (null if no eligible markets)
    recommended_market:    Optional[MarketOptionSchema]
    crop_id:               int
    crop_name:             str
    crop_unit:             str
    quantity_kg:           float
    price_basis:           str
    recommendation_method: str
    confidence:            None = None
    currency:              str = "INR"
    explanation:           str
    comparison:            list[MarketOptionSchema]
    excluded_markets:      list[ExcludedMarketSchema]
    saved_recommendation_id: Optional[int] = None
    disclaimer: str = (
        "Recommended based on available price and transport estimates. "
        "Not a guaranteed market price or commercial quote."
    )


# ── History entry ─────────────────────────────────────────────────────────────

class RecommendationHistoryEntry(BaseModel):
    id:                    int
    crop_name:             Optional[str]
    market_name:           Optional[str]
    quantity:              Optional[float]
    current_price:         Optional[float]
    transport_cost:        Optional[float]
    expected_gross_revenue: Optional[float]
    expected_net_revenue:  Optional[float]
    distance_km:           Optional[float]
    price_basis:           Optional[str]
    explanation:           Optional[str]
    created_at:            str

    model_config = {"from_attributes": True}

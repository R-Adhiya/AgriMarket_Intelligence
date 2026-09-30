"""Pydantic schemas for the Location / Transport module (Phase 6)."""

from typing import Optional
from pydantic import BaseModel, Field


class DistanceResponse(BaseModel):
    market_id: int
    market_name: str
    district: Optional[str]
    state: Optional[str]
    farmer_district: Optional[str]
    farmer_location_source: str   # "stored_coordinates" | "district_lookup"
    distance_km: float
    note: str = "Great-circle (Haversine) distance. Actual road distance will be longer."


class TransportEstimate(BaseModel):
    market_id: int
    market_name: str
    district: Optional[str]
    state: Optional[str]
    distance_km: float
    quantity_quintals: float
    estimated_transport_cost: float
    currency: str = "INR"
    assumptions: dict
    disclaimer: str = (
        "Estimated transport cost only — not a commercial quote. "
        "Formula: base_cost + (distance_km × rate_per_km × quantity_quintals)."
    )


class MultiMarketTransportResponse(BaseModel):
    farmer_district: Optional[str]
    farmer_location_source: str
    quantity_quintals: float
    markets: list[TransportEstimate]
    disclaimer: str = (
        "Estimated transport costs only — development sample data, not commercial quotes."
    )

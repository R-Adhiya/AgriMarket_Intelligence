"""Pydantic schemas for the Price Prediction API (Phase 7)."""

from typing import Optional
from pydantic import BaseModel, Field


class PredictionPoint(BaseModel):
    date: str
    predicted_price: float
    step: int


class PricePredictionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    crop: str
    market_id: int
    market_name: str
    unit: str
    horizon: int
    model_used: str
    latest_known_price: float
    latest_known_date: str
    predictions: list[PredictionPoint]
    data_source: str
    disclaimer: str


class PredictionUnavailableResponse(BaseModel):
    crop: str
    market_id: int
    reason: str
    suggestion: str

"""
Price Prediction API — Phase 7.

GET /api/prediction/price?crop_id=&market_id=&horizon=

Loads historical prices from the database, runs the trained ML model,
and returns predicted prices for the requested horizon.

NOTE: Models are trained on SYNTHETIC DEVELOPMENT DATA.
      Predictions are estimates only — not financial advice.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import pandas as pd

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.crop import Crop
from app.models.market import Market
from app.models.market_price import MarketPrice
from app.models.user import User
from app.schemas.prediction import PricePredictionResponse, PredictionPoint
from app.services.prediction import (
    predict_price,
    InsufficientDataError,
    ModelNotFoundError,
    SUPPORTED_HORIZONS,
)

router = APIRouter(
    prefix="/api/prediction",
    tags=["Price Prediction"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/price",
    response_model=PricePredictionResponse,
    summary="Predict future crop price using the trained ML model",
    description=(
        "Returns predicted modal prices for the selected crop/market combination. "
        "**Development data only** — not real-time government prices."
    ),
)
def predict(
    crop_id:   int = Query(..., description="Crop ID"),
    market_id: int = Query(..., description="Market ID"),
    horizon:   int = Query(1, description=f"Days ahead to predict: {SUPPORTED_HORIZONS}"),
    db: Session = Depends(get_db),
):
    # Validate crop
    crop = db.query(Crop).filter_by(id=crop_id, is_active=True).first()
    if not crop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crop not found.")

    # Validate market
    market = db.query(Market).filter_by(id=market_id, is_active=True).first()
    if not market:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found.")

    # Validate horizon
    if horizon not in SUPPORTED_HORIZONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported horizon {horizon}. Choose from {list(SUPPORTED_HORIZONS)}.",
        )

    # Load price history from DB
    records = (
        db.query(MarketPrice)
        .filter_by(crop_id=crop_id, market_id=market_id)
        .order_by(MarketPrice.price_date.asc())
        .all()
    )

    if len(records) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Not enough price history for {crop.name} @ {market.name}. "
                "At least 8 records needed for prediction."
            ),
        )

    history_df = pd.DataFrame([
        {"price_date": str(r.price_date), "modal_price": float(r.modal_price)}
        for r in records
    ])

    try:
        result = predict_price(
            crop=crop.name,
            market_id=market_id,
            history_df=history_df,
            horizon=horizon,
        )
    except ModelNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except InsufficientDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return PricePredictionResponse(
        crop=crop.name,
        market_id=market_id,
        market_name=market.name,
        unit=crop.unit.value,
        horizon=result["horizon"],
        model_used=result["model_used"],
        latest_known_price=result["latest_known_price"],
        latest_known_date=result["latest_known_date"],
        predictions=[PredictionPoint(**p) for p in result["predictions"]],
        data_source=result["data_source"],
        disclaimer=result["disclaimer"],
    )

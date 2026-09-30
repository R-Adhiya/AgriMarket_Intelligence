"""
Price prediction service — Phase 7.

Loads a trained model for a (crop, market) pair and generates
next-day, 3-day, and 7-day price estimates.

This service is intentionally stateless — it loads the model from
disk on every call, which is fine for development-scale usage.
"""

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# Make ml/ importable when called from backend context
_ML_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_ML_ROOT) not in sys.path:
    sys.path.insert(0, str(_ML_ROOT))

from ml.models.artifacts import load_model, model_exists
from ml.preprocessing.features import FEATURE_COLS, build_features

SUPPORTED_HORIZONS = (1, 3, 7)


class InsufficientDataError(ValueError):
    pass


class ModelNotFoundError(FileNotFoundError):
    pass


def predict_price(
    crop: str,
    market_id: int,
    history_df: pd.DataFrame,
    horizon: int = 1,
) -> dict:
    """
    Predict the modal price `horizon` days ahead.

    Args:
        crop:       Crop name (must match training data).
        market_id:  Market id (must match training data).
        history_df: DataFrame with columns [price_date, modal_price],
                    sorted ascending. At least 8 rows recommended.
        horizon:    Days ahead to predict (1, 3, or 7).

    Returns:
        dict with prediction details.

    Raises:
        ModelNotFoundError   — no trained model for this (crop, market).
        InsufficientDataError — not enough history for features.
        ValueError            — unsupported horizon.
    """
    if horizon not in SUPPORTED_HORIZONS:
        raise ValueError(f"Horizon {horizon} not supported. Choose from {SUPPORTED_HORIZONS}.")

    if not model_exists(crop, market_id):
        raise ModelNotFoundError(
            f"No trained model for crop='{crop}', market_id={market_id}. "
            "Run the ML pipeline first."
        )

    model = load_model(crop, market_id)
    if model is None:
        raise ModelNotFoundError(f"Model file missing for {crop}/{market_id}.")

    if len(history_df) < 8:
        raise InsufficientDataError(
            f"Only {len(history_df)} price records available. "
            "Need at least 8 to compute lag/rolling features."
        )

    # Build a rolling-horizon prediction: step forward one day at a time
    working = history_df.copy()
    last_date = pd.to_datetime(working["price_date"].max())
    predictions = []

    for step in range(1, horizon + 1):
        feat_df = build_features(working, drop_na=False)
        if len(feat_df) == 0 or feat_df[FEATURE_COLS].iloc[-1:].isnull().any(axis=1).all():
            raise InsufficientDataError("Could not compute features from available history.")

        X_pred = feat_df[FEATURE_COLS].iloc[-1:]
        # Replace remaining NaN with column means from the non-null rows
        col_means = feat_df[FEATURE_COLS].mean()
        X_pred = X_pred.fillna(col_means)

        pred_price = float(model.predict(X_pred)[0])
        pred_price = max(pred_price, 0.0)
        pred_date  = last_date + timedelta(days=step)

        predictions.append({
            "date":            pred_date.date().isoformat(),
            "predicted_price": round(pred_price, 2),
            "step":            step,
        })

        # Append prediction to working history for the next step
        new_row = pd.DataFrame([{
            "price_date":  pred_date.date().isoformat(),
            "modal_price": pred_price,
        }])
        working = pd.concat([working, new_row], ignore_index=True)

    # Determine model name from registry
    from ml.models.artifacts import load_registry, _key
    reg = load_registry()
    entry = reg.get(_key(crop, market_id), {})
    model_name = entry.get("best_model", type(model).__name__)

    return {
        "crop":             crop,
        "market_id":        market_id,
        "horizon":          horizon,
        "model_used":       model_name,
        "latest_known_price": round(float(history_df["modal_price"].iloc[-1]), 2),
        "latest_known_date":  history_df["price_date"].iloc[-1],
        "predictions":      predictions,
        "data_source":      "synthetic_development",
        "disclaimer": (
            "Predictions are estimates based on available historical data "
            "and should not be treated as guaranteed market prices."
        ),
    }

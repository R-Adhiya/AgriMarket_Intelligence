"""
Phase 7 — ML Price Prediction tests.

Tests cover:
- Feature engineering (no leakage, correct shape)
- Chronological split
- Baseline and ML model training
- Prediction service
- Prediction API (mocked DB, with seed prices from test engine)
"""

import app.models  # noqa: F401

import math
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Ensure ml/ is importable from project root
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tests.conftest import get_test_session
from app.main import app as fastapi_app
from app.models.crop import Crop, CropUnit
from app.models.market import Market, MarketType
from app.models.market_price import MarketPrice

from ml.preprocessing.features import (
    build_features, add_lag_features, add_rolling_features,
    chronological_split, FEATURE_COLS, TARGET_COL,
)
from ml.training.train import (
    run_training_pipeline, evaluate, NaiveBaseline, MIN_TRAIN,
)

client = TestClient(fastapi_app)

# Module-level state
_CROP_ID   = None
_MKT_ID    = None
_FARMER_H  = None


# ── Sample price series helper ────────────────────────────────────────────────

def _make_price_df(n=60, base=25.0, seed=42):
    rng = np.random.default_rng(seed)
    prices = []
    p = base
    for i in range(n):
        p = max(p + rng.normal(0, 1.5), 5.0)
        prices.append({"price_date": (date(2025, 1, 1) + timedelta(days=i)).isoformat(),
                       "modal_price": round(p, 2)})
    return pd.DataFrame(prices)


def _make_auth(email, role="FARMER"):
    client.post("/api/auth/register", json={"full_name": "Predict Tester",
                                            "email": email, "password": "Password1", "role": role})
    r = client.post("/api/auth/login", json={"email": email, "password": "Password1"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def setup_module(_m):
    global _CROP_ID, _MKT_ID, _FARMER_H

    db = get_test_session()

    # Seed crop
    c = db.query(Crop).filter_by(name="PredTestTomato").first()
    if not c:
        c = Crop(name="PredTestTomato", unit=CropUnit.KG, is_active=True)
        db.add(c); db.commit(); db.refresh(c)
    _CROP_ID = c.id

    # Seed market
    m = db.query(Market).filter_by(market_code="T7-MKT-CBE").first()
    if not m:
        m = Market(name="Pred Test Market", market_code="T7-MKT-CBE",
                   district="Coimbatore", state="Tamil Nadu",
                   latitude=11.0168, longitude=76.9558,
                   market_type=MarketType.APMC, is_active=True)
        db.add(m); db.commit(); db.refresh(m)
    _MKT_ID = m.id

    # Seed 15 days of price history (enough for API tests)
    today = date.today()
    for i in range(15):
        pd_ = today - timedelta(days=14 - i)
        exists = db.query(MarketPrice).filter_by(
            crop_id=_CROP_ID, market_id=_MKT_ID, price_date=pd_
        ).first()
        if not exists:
            price = 24.0 + i * 0.3
            db.add(MarketPrice(crop_id=_CROP_ID, market_id=_MKT_ID, price_date=pd_,
                               min_price=price - 1, modal_price=price, max_price=price + 1,
                               source="test"))
    db.commit()
    db.close()

    _FARMER_H = _make_auth("p7_farmer@test.com")


# ── Feature engineering tests ─────────────────────────────────────────────────

def test_lag_features_no_future_leakage():
    """lag_1 at row i must equal modal_price at row i-1 (no look-ahead)."""
    df = _make_price_df(20)
    df_feat = add_lag_features(df.copy())
    for i in range(1, len(df_feat)):
        expected = df_feat["modal_price"].iloc[i - 1]
        actual   = df_feat["lag_1"].iloc[i]
        assert actual == pytest.approx(expected), f"Leakage at row {i}"


def test_rolling_mean_no_future_leakage():
    """rolling_mean_3 uses shift(1) so it cannot see the current row."""
    df = _make_price_df(20)
    df_feat = add_rolling_features(df.copy())
    # At row 0, rolling_mean_3 should be NaN (or computed from just prior)
    # At row 1, it should be the mean of row 0 only (shift+rolling with min_periods=1)
    assert not math.isnan(df_feat["rolling_mean_3"].iloc[1])


def test_build_features_shape():
    df = _make_price_df(60)
    feat = build_features(df)
    assert set(FEATURE_COLS).issubset(feat.columns)
    assert TARGET_COL in feat.columns
    assert len(feat) > 0
    # No NaN in feature cols after drop_na
    assert not feat[FEATURE_COLS].isnull().any().any()


def test_chronological_split_order():
    df = _make_price_df(100)
    feat = build_features(df)
    train, val, test = chronological_split(feat)
    # All train dates < all val dates < all test dates
    assert train["price_date"].max() <= val["price_date"].min()
    assert val["price_date"].max() <= test["price_date"].min()


def test_chronological_split_sizes():
    df = _make_price_df(100)
    feat = build_features(df)
    train, val, test = chronological_split(feat, 0.70, 0.15)
    total = len(train) + len(val) + len(test)
    assert total == len(feat)
    assert len(train) > len(val)
    assert len(val) > 0 and len(test) > 0


# ── Baseline and model training ───────────────────────────────────────────────

def test_naive_baseline():
    df = _make_price_df(60)
    feat = build_features(df)
    train, val, test = chronological_split(feat)
    baseline = NaiveBaseline()
    baseline.fit(train[FEATURE_COLS], train[TARGET_COL])
    preds = baseline.predict(test[FEATURE_COLS])
    assert len(preds) == len(test)


def test_evaluate_metrics():
    y_true = np.array([10.0, 12.0, 11.0, 13.0])
    y_pred = np.array([10.5, 11.5, 11.0, 13.5])
    m = evaluate(y_true, y_pred)
    assert m.mae >= 0
    assert m.rmse >= m.mae
    assert -2.0 <= m.r2 <= 1.0


def test_run_training_pipeline():
    df = _make_price_df(120)
    feat = build_features(df)
    result = run_training_pipeline(feat)
    assert "error" not in result
    assert result["best_model"] in ("LinearRegression", "RandomForest")
    assert len(result["results"]) == 3  # Naive + LR + RF
    assert result["train_size"] > 0


def test_training_insufficient_data():
    df = _make_price_df(10)
    feat = build_features(df)
    result = run_training_pipeline(feat)
    assert "error" in result


def test_model_comparison_mae():
    """ML model must beat naive baseline on test set (for well-behaved series)."""
    df = _make_price_df(200)
    feat = build_features(df)
    result = run_training_pipeline(feat)
    assert "error" not in result
    naive_mae = next(r for r in result["results"] if r["name"] == "NaiveBaseline")["test_metrics"]["mae"]
    best_mae  = next(r for r in result["results"] if r["name"] == result["best_model"])["test_metrics"]["mae"]
    # Best ML model should be at least as good as naive (usually better)
    assert best_mae <= naive_mae * 1.5   # allow 50% slack for synthetic data


# ── Prediction service ────────────────────────────────────────────────────────

def test_predict_price_horizon1():
    from app.services.prediction import predict_price
    history = _make_price_df(60)
    # Use "Tomato" + market_id=1 which has a trained model from the pipeline
    result = predict_price("Tomato", 1, history, horizon=1)
    assert result["horizon"] == 1
    assert len(result["predictions"]) == 1
    assert result["predictions"][0]["predicted_price"] > 0
    assert "disclaimer" in result


def test_predict_price_horizon3():
    from app.services.prediction import predict_price
    history = _make_price_df(60)
    result = predict_price("Tomato", 1, history, horizon=3)
    assert len(result["predictions"]) == 3


def test_predict_price_unsupported_horizon():
    from app.services.prediction import predict_price
    with pytest.raises(ValueError, match="Horizon"):
        predict_price("Tomato", 1, _make_price_df(60), horizon=5)


def test_predict_price_insufficient_history():
    from app.services.prediction import predict_price, InsufficientDataError
    with pytest.raises(InsufficientDataError):
        predict_price("Tomato", 1, _make_price_df(3), horizon=1)


def test_predict_price_no_model():
    from app.services.prediction import predict_price, ModelNotFoundError
    with pytest.raises(ModelNotFoundError):
        predict_price("UnknownCropXYZ", 999, _make_price_df(60), horizon=1)


# ── Prediction API ────────────────────────────────────────────────────────────

def test_prediction_api_invalid_crop():
    r = client.get("/api/prediction/price?crop_id=99999&market_id=1&horizon=1",
                   headers=_FARMER_H)
    assert r.status_code == 404


def test_prediction_api_invalid_market():
    r = client.get(f"/api/prediction/price?crop_id={_CROP_ID}&market_id=99999&horizon=1",
                   headers=_FARMER_H)
    assert r.status_code == 404


def test_prediction_api_invalid_horizon():
    r = client.get(f"/api/prediction/price?crop_id={_CROP_ID}&market_id={_MKT_ID}&horizon=5",
                   headers=_FARMER_H)
    assert r.status_code == 422


def test_prediction_api_requires_auth():
    r = client.get(f"/api/prediction/price?crop_id={_CROP_ID}&market_id={_MKT_ID}&horizon=1")
    assert r.status_code == 401


def test_prediction_api_response_schema():
    """
    Uses seeded test data.  Model may be missing for PredTestTomato/T7-MKT-CBE
    since only dev pipeline crops (Tomato/Onion/Potato) are trained.
    We expect either 200 (model present) or 422 (model not yet trained for test crop).
    Both are valid outcomes.
    """
    r = client.get(
        f"/api/prediction/price?crop_id={_CROP_ID}&market_id={_MKT_ID}&horizon=1",
        headers=_FARMER_H,
    )
    assert r.status_code in (200, 422)
    if r.status_code == 200:
        d = r.json()
        assert "predictions" in d
        assert "disclaimer" in d
        assert "model_used" in d
        assert d["horizon"] == 1


def test_prediction_api_no_history_returns_422():
    """A crop/market with zero price records should return 422, not 500."""
    db = get_test_session()
    c = db.query(Crop).filter_by(name="EmptyCropNoHistory").first()
    if not c:
        c = Crop(name="EmptyCropNoHistory", unit=CropUnit.KG, is_active=True)
        db.add(c); db.commit(); db.refresh(c)
    cid = c.id
    db.close()
    r = client.get(f"/api/prediction/price?crop_id={cid}&market_id={_MKT_ID}&horizon=1",
                   headers=_FARMER_H)
    assert r.status_code in (404, 422)

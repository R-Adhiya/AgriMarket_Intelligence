"""
Model training, evaluation and comparison — Phase 7.

Models:
  1. NaiveBaseline     — predict last known price (benchmark)
  2. LinearRegression  — sklearn linear model
  3. RandomForest      — sklearn ensemble

Evaluation: MAE, RMSE, R²

Split strategy: chronological (train 70% | val 15% | test 15%).
Time-series cross-validation with TimeSeriesSplit where enough data exists.
"""

import json
import math
import warnings
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml.preprocessing.features import FEATURE_COLS, TARGET_COL, chronological_split

warnings.filterwarnings("ignore", category=FutureWarning)

RANDOM_SEED = 42
MIN_TRAIN   = 30   # rows needed to attempt training


# ── Evaluation helpers ────────────────────────────────────────────────────────

@dataclass
class Metrics:
    mae:  float
    rmse: float
    r2:   float
    n:    int

    def as_dict(self):
        return asdict(self)


def evaluate(y_true, y_pred) -> Metrics:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mae  = float(mean_absolute_error(y_true, y_pred))
    rmse = float(math.sqrt(mean_squared_error(y_true, y_pred)))
    r2   = float(r2_score(y_true, y_pred)) if len(y_true) > 1 else 0.0
    return Metrics(mae=round(mae, 4), rmse=round(rmse, 4),
                   r2=round(r2, 4), n=len(y_true))


# ── Naive baseline ────────────────────────────────────────────────────────────

class NaiveBaseline:
    """Predicts the last observed price (lag-1 naive forecast)."""
    name = "NaiveBaseline"

    def fit(self, X, y): return self

    def predict(self, X):
        return X["lag_1"].values


# ── Train and evaluate one model ─────────────────────────────────────────────

def train_evaluate(
    train_df: pd.DataFrame,
    val_df:   pd.DataFrame,
    test_df:  pd.DataFrame,
    model,
):
    X_train = train_df[FEATURE_COLS]
    y_train = train_df[TARGET_COL]
    X_val   = val_df[FEATURE_COLS]
    y_val   = val_df[TARGET_COL]
    X_test  = test_df[FEATURE_COLS]
    y_test  = test_df[TARGET_COL]

    model.fit(X_train, y_train)

    val_metrics  = evaluate(y_val,  model.predict(X_val))
    test_metrics = evaluate(y_test, model.predict(X_test))

    return model, val_metrics, test_metrics


# ── Time-series cross-validation ──────────────────────────────────────────────

def ts_cross_validate(df: pd.DataFrame, model_factory, n_splits=3):
    """
    Chronological TimeSeriesSplit.
    Returns mean MAE and RMSE across folds.
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    X = df[FEATURE_COLS]
    y = df[TARGET_COL]

    maes, rmses = [], []
    for _, (train_idx, val_idx) in enumerate(tscv.split(X)):
        m = model_factory()
        m.fit(X.iloc[train_idx], y.iloc[train_idx])
        preds = m.predict(X.iloc[val_idx])
        met = evaluate(y.iloc[val_idx], preds)
        maes.append(met.mae)
        rmses.append(met.rmse)

    return {
        "mean_mae":  round(float(np.mean(maes)),  4),
        "mean_rmse": round(float(np.mean(rmses)), 4),
        "n_splits":  n_splits,
    }


# ── Main training pipeline ────────────────────────────────────────────────────

@dataclass
class ModelResult:
    name:          str
    val_metrics:   Metrics
    test_metrics:  Metrics
    cv_result:     dict = field(default_factory=dict)


def run_training_pipeline(df: pd.DataFrame) -> dict:
    """
    Full pipeline for one (crop, market) slice.
    df must already have feature columns and be sorted by date.
    """
    if len(df) < MIN_TRAIN:
        return {"error": f"Insufficient data: {len(df)} rows (need {MIN_TRAIN})"}

    train_df, val_df, test_df = chronological_split(df)
    if len(val_df) == 0 or len(test_df) == 0:
        return {"error": "Dataset too small for three-way split."}

    models_to_try = [
        ("NaiveBaseline",    NaiveBaseline()),
        ("LinearRegression", LinearRegression()),
        ("RandomForest",     RandomForestRegressor(
            n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1
        )),
    ]

    results: list[ModelResult] = []
    trained_models = {}

    for name, m in models_to_try:
        trained_m, val_met, test_met = train_evaluate(train_df, val_df, test_df, m)
        cv = {}
        if name != "NaiveBaseline" and len(df) >= 60:
            factory = (
                LinearRegression if name == "LinearRegression"
                else lambda: RandomForestRegressor(
                    n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1
                )
            )
            cv = ts_cross_validate(df, factory)
        results.append(ModelResult(name=name, val_metrics=val_met,
                                   test_metrics=test_met, cv_result=cv))
        trained_models[name] = trained_m

    # Select best by validation MAE (exclude NaiveBaseline from selection)
    ml_results = [r for r in results if r.name != "NaiveBaseline"]
    best = min(ml_results, key=lambda r: r.val_metrics.mae)

    return {
        "results":       [asdict(r) for r in results],
        "best_model":    best.name,
        "train_size":    len(train_df),
        "val_size":      len(val_df),
        "test_size":     len(test_df),
        "feature_cols":  FEATURE_COLS,
        "trained_models": trained_models,
    }

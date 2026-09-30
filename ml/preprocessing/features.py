"""
Feature engineering for the price prediction pipeline — Phase 7.

Generates time-series features from a sorted price history.
Handles missing lags gracefully (NaN-fill with forward/backward fill
or row drop depending on context).

No future data is used in any feature — all lags and rolling windows
look strictly backward in time.
"""

import numpy as np
import pandas as pd


# Minimum records needed per (crop, market) to attempt training
MIN_TRAINING_ROWS = 30


def add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode calendar position from the price_date column."""
    df = df.copy()
    dt = pd.to_datetime(df["price_date"])
    df["day_of_week"]  = dt.dt.dayofweek          # 0=Mon … 6=Sun
    df["day_of_month"] = dt.dt.day
    df["month"]        = dt.dt.month
    df["year"]         = dt.dt.year
    df["day_of_year"]  = dt.dt.dayofyear
    return df


def add_lag_features(df: pd.DataFrame, lags=(1, 3, 7)) -> pd.DataFrame:
    """
    Add lagged modal_price columns.
    The series must be sorted ascending by date BEFORE calling this.
    """
    df = df.copy()
    for lag in lags:
        df[f"lag_{lag}"] = df["modal_price"].shift(lag)
    return df


def add_rolling_features(df: pd.DataFrame, windows=(3, 7)) -> pd.DataFrame:
    """
    Add rolling mean/std of modal_price.
    min_periods=1 so short series still produce a value.
    """
    df = df.copy()
    for w in windows:
        df[f"rolling_mean_{w}"] = (
            df["modal_price"].shift(1).rolling(w, min_periods=1).mean()
        )
        df[f"rolling_std_{w}"]  = (
            df["modal_price"].shift(1).rolling(w, min_periods=1).std().fillna(0)
        )
    return df


# The complete feature set used for model training
FEATURE_COLS = [
    "day_of_week", "day_of_month", "month", "day_of_year",
    "lag_1", "lag_3", "lag_7",
    "rolling_mean_3", "rolling_mean_7",
    "rolling_std_3",  "rolling_std_7",
]
TARGET_COL = "modal_price"


def build_features(df: pd.DataFrame, drop_na: bool = True) -> pd.DataFrame:
    """
    Full feature-engineering pipeline for one (crop, market) series.

    Args:
        df:      DataFrame with columns [price_date, modal_price], sorted asc by date.
        drop_na: drop rows where any feature is NaN (first few rows of lags).

    Returns:
        DataFrame with FEATURE_COLS + TARGET_COL + price_date retained.
    """
    df = df.sort_values("price_date").reset_index(drop=True)
    df = add_date_features(df)
    df = add_lag_features(df)
    df = add_rolling_features(df)
    if drop_na:
        df = df.dropna(subset=FEATURE_COLS).reset_index(drop=True)
    return df


def chronological_split(df: pd.DataFrame, train_frac=0.70, val_frac=0.15):
    """
    Time-ordered split: train | validation | test.
    NO shuffling — preserves temporal order to avoid data leakage.

    Returns:
        (train_df, val_df, test_df)
    """
    n = len(df)
    t1 = int(n * train_frac)
    t2 = int(n * (train_frac + val_frac))
    return df.iloc[:t1], df.iloc[t1:t2], df.iloc[t2:]

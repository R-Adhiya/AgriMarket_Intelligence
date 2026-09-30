"""
Synthetic development dataset generator — Phase 7.

Generates ~18 months of daily crop price records for 3 crops × 3 markets
using realistic Tamil Nadu agricultural price patterns.

WARNING: This is SYNTHETIC/DEVELOPMENT data only.
         It is NOT real government market data.
         It exists only to provide enough observations for ML training.
         Replace with real AgMarknet or government API data in production.

Output: ml/data/dev_prices.csv
"""

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# ── Dataset parameters ────────────────────────────────────────────────────────
RANDOM_SEED = 42
START_DATE  = date(2024, 1, 1)
END_DATE    = date(2025, 6, 30)   # ~18 months

CROP_BASE_PRICES = {
    "Tomato":  {"mean": 25.0,  "std": 6.0,  "unit": "kg"},
    "Onion":   {"mean": 950.0, "std": 120.0, "unit": "quintal"},
    "Potato":  {"mean": 1050.0,"std": 100.0, "unit": "quintal"},
}

MARKETS = [
    {"id": 1, "name": "Coimbatore APMC Market",     "district": "Coimbatore"},
    {"id": 2, "name": "Erode Wholesale Market",      "district": "Erode"},
    {"id": 3, "name": "Tiruppur Agricultural Market","district": "Tiruppur"},
]

# Market premium/discount (relative to base)
MARKET_FACTOR = {
    "Coimbatore APMC Market":     1.00,
    "Erode Wholesale Market":     0.96,
    "Tiruppur Agricultural Market": 0.98,
}


def generate_price_series(
    base: float, std: float, n_days: int, seed: int
) -> np.ndarray:
    """
    Random walk with seasonal component and mean-reversion.
    Mimics typical mandi price behavior (not real data).
    """
    rng = np.random.default_rng(seed)
    prices = np.empty(n_days)
    prices[0] = base
    for t in range(1, n_days):
        # Seasonal component: slightly higher in summer (months 3-5)
        day_idx = t % 365
        seasonal = 0.05 * base * np.sin(2 * np.pi * day_idx / 365)
        # Mean reversion
        reversion = 0.02 * (base - prices[t - 1])
        # Random shock
        shock = rng.normal(0, std * 0.08)
        prices[t] = max(prices[t - 1] + reversion + seasonal * 0.01 + shock, base * 0.3)
    return np.round(prices, 2)


def build_dataset(output_path: Path) -> pd.DataFrame:
    rng = random.Random(RANDOM_SEED)
    dates = [START_DATE + timedelta(days=i)
             for i in range((END_DATE - START_DATE).days + 1)]

    rows = []
    for crop_name, cp in CROP_BASE_PRICES.items():
        for mkt in MARKETS:
            factor = MARKET_FACTOR[mkt["name"]]
            seed = abs(hash((crop_name, mkt["name"]))) % (2**31)
            modal_series = generate_price_series(
                cp["mean"] * factor, cp["std"], len(dates), seed
            )
            for i, d in enumerate(dates):
                modal = modal_series[i]
                spread = abs(np.random.default_rng(seed + i).normal(0, cp["std"] * 0.15))
                rows.append({
                    "crop":        crop_name,
                    "market_id":   mkt["id"],
                    "market_name": mkt["name"],
                    "district":    mkt["district"],
                    "price_date":  d.isoformat(),
                    "min_price":   round(max(modal - spread, 1.0), 2),
                    "modal_price": round(modal, 2),
                    "max_price":   round(modal + spread, 2),
                    "unit":        cp["unit"],
                    "source":      "synthetic_development",
                })

    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[gen] Wrote {len(df):,} rows to {output_path}")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="ml/data/dev_prices.csv")
    args = parser.parse_args()
    build_dataset(Path(args.out))

"""
ML pipeline runner — Phase 7.

Generates synthetic dev data → trains models → saves artifacts → writes reports.

Run from the project root:
    python -m ml.training.pipeline

Or from the backend directory:
    .venv/Scripts/python.exe -m ml.training.pipeline
"""

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path when run as a script
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd

from ml.preprocessing.generate_dev_data import build_dataset, CROP_BASE_PRICES, MARKETS
from ml.preprocessing.features import build_features
from ml.training.train import run_training_pipeline
from ml.models.artifacts import save_model, MODELS_DIR

DATA_PATH    = _ROOT / "ml" / "data" / "dev_prices.csv"
REPORTS_DIR  = _ROOT / "ml" / "reports"


def run_pipeline(verbose: bool = True) -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (MODELS_DIR).mkdir(parents=True, exist_ok=True)

    # 1. Generate / load dev data
    if not DATA_PATH.exists():
        if verbose: print("[pipeline] Generating synthetic development data...")
        build_dataset(DATA_PATH)
    df = pd.read_csv(DATA_PATH)
    if verbose: print(f"[pipeline] Loaded {len(df):,} rows from {DATA_PATH.name}")

    # 2. Train per (crop, market) slice
    all_results = {}
    summary_rows = []

    for crop in df["crop"].unique():
        for market_id in df["market_id"].unique():
            slice_df = (
                df[(df["crop"] == crop) & (df["market_id"] == market_id)]
                .copy()
                .reset_index(drop=True)
            )
            mkt_name = slice_df["market_name"].iloc[0] if len(slice_df) else str(market_id)

            feat_df = build_features(slice_df[["price_date", "modal_price"]])
            result  = run_training_pipeline(feat_df)

            key = f"{crop}/{market_id}"
            all_results[key] = result

            if "error" in result:
                if verbose: print(f"  [skip] {crop} @ {mkt_name}: {result['error']}")
                continue

            # Save the best model
            best_name = result["best_model"]
            best_model = result["trained_models"][best_name]
            save_model(best_model, crop, market_id, {
                k: v for k, v in result.items()
                if k not in ("trained_models", "results")
            })

            # Collect summary
            for r in result["results"]:
                summary_rows.append({
                    "crop":       crop,
                    "market_id":  market_id,
                    "market_name":mkt_name,
                    "model":      r["name"],
                    "val_mae":    r["val_metrics"]["mae"],
                    "val_rmse":   r["val_metrics"]["rmse"],
                    "val_r2":     r["val_metrics"]["r2"],
                    "test_mae":   r["test_metrics"]["mae"],
                    "test_rmse":  r["test_metrics"]["rmse"],
                    "test_r2":    r["test_metrics"]["r2"],
                    "is_best":    r["name"] == best_name,
                })

            if verbose:
                tm = next(r for r in result["results"] if r["name"] == best_name)
                print(
                    f"  [ok] {crop:10s} @ {mkt_name:30s} "
                    f"best={best_name:20s} "
                    f"test_mae={tm['test_metrics']['mae']:.2f}"
                )

    # 3. Write reports
    report_json = REPORTS_DIR / "model_comparison.json"
    report_md   = REPORTS_DIR / "model_comparison.md"

    summary_df = pd.DataFrame(summary_rows)

    report_json.write_text(
        json.dumps({
            "data_source": "synthetic_development",
            "data_rows":   len(df),
            "crops":       list(df["crop"].unique()),
            "markets":     list(df["market_name"].unique()),
            "date_range":  [df["price_date"].min(), df["price_date"].max()],
            "split":       {"train": "70%", "val": "15%", "test": "15%"},
            "results":     all_results,
            "summary":     summary_rows,
        }, indent=2, default=str),
        encoding="utf-8",
    )

    # Markdown report
    md_lines = [
        "# AgriMarket Intelligence — Price Prediction Model Report",
        "",
        "> **Data**: Synthetic development data only — NOT real government market prices.",
        "",
        "## Dataset",
        f"- Rows: {len(df):,}",
        f"- Crops: {', '.join(df['crop'].unique())}",
        f"- Markets: {', '.join(df['market_name'].unique())}",
        f"- Date range: {df['price_date'].min()} → {df['price_date'].max()}",
        "",
        "## Split Strategy",
        "- 70% train | 15% validation | 15% test",
        "- Chronological (no shuffling) — prevents future data leakage",
        "",
        "## Model Comparison (Test Set)",
        "",
        "| Crop | Market | Model | MAE | RMSE | R² | Best? |",
        "|------|--------|-------|-----|------|----|-------|",
    ]
    for r in summary_rows:
        md_lines.append(
            f"| {r['crop']} | {r['market_name']} | {r['model']} "
            f"| {r['test_mae']:.2f} | {r['test_rmse']:.2f} | {r['test_r2']:.3f} "
            f"| {'✓' if r['is_best'] else ''} |"
        )

    md_lines += [
        "",
        "## Limitations",
        "- Trained on synthetic data; replace with real market data for production.",
        "- Lag/rolling features may not capture true market dynamics.",
        "- No external factors (weather, harvest, policy) are modelled.",
        "",
        "## Reproducibility",
        f"- Random seed: 42",
        "- Feature list: day_of_week, day_of_month, month, day_of_year, "
          "lag_1, lag_3, lag_7, rolling_mean_3, rolling_mean_7, rolling_std_3, rolling_std_7",
    ]
    report_md.write_text("\n".join(md_lines), encoding="utf-8")

    if verbose:
        print(f"\n[pipeline] Reports → {REPORTS_DIR}")
        print(f"[pipeline] Done. {len(summary_rows)} model records written.")

    return {"summary": summary_rows, "all_results": all_results}


if __name__ == "__main__":
    run_pipeline()

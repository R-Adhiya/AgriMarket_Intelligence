# AgriMarket Intelligence — Price Prediction Model Report

> **Data**: Synthetic development data only — NOT real government market prices.

## Dataset
- Rows: 4,923
- Crops: Tomato, Onion, Potato
- Markets: Coimbatore APMC Market, Erode Wholesale Market, Tiruppur Agricultural Market
- Date range: 2024-01-01 → 2025-06-30

## Split Strategy
- 70% train | 15% validation | 15% test
- Chronological (no shuffling) — prevents future data leakage

## Model Comparison (Test Set)

| Crop | Market | Model | MAE | RMSE | R² | Best? |
|------|--------|-------|-----|------|----|-------|
| Tomato | Coimbatore APMC Market | NaiveBaseline | 0.36 | 0.43 | 0.894 |  |
| Tomato | Coimbatore APMC Market | LinearRegression | 0.36 | 0.45 | 0.886 | ✓ |
| Tomato | Coimbatore APMC Market | RandomForest | 0.75 | 0.97 | 0.468 |  |
| Tomato | Erode Wholesale Market | NaiveBaseline | 0.42 | 0.53 | 0.920 |  |
| Tomato | Erode Wholesale Market | LinearRegression | 0.46 | 0.58 | 0.904 | ✓ |
| Tomato | Erode Wholesale Market | RandomForest | 0.59 | 0.76 | 0.837 |  |
| Tomato | Tiruppur Agricultural Market | NaiveBaseline | 0.40 | 0.48 | 0.830 |  |
| Tomato | Tiruppur Agricultural Market | LinearRegression | 0.41 | 0.51 | 0.804 | ✓ |
| Tomato | Tiruppur Agricultural Market | RandomForest | 0.41 | 0.53 | 0.785 |  |
| Onion | Coimbatore APMC Market | NaiveBaseline | 7.10 | 8.85 | 0.798 |  |
| Onion | Coimbatore APMC Market | LinearRegression | 6.96 | 8.82 | 0.800 | ✓ |
| Onion | Coimbatore APMC Market | RandomForest | 7.78 | 9.96 | 0.745 |  |
| Onion | Erode Wholesale Market | NaiveBaseline | 6.37 | 8.07 | 0.854 |  |
| Onion | Erode Wholesale Market | LinearRegression | 8.49 | 10.17 | 0.768 | ✓ |
| Onion | Erode Wholesale Market | RandomForest | 8.07 | 10.04 | 0.775 |  |
| Onion | Tiruppur Agricultural Market | NaiveBaseline | 7.92 | 9.71 | 0.803 |  |
| Onion | Tiruppur Agricultural Market | LinearRegression | 8.11 | 9.84 | 0.798 | ✓ |
| Onion | Tiruppur Agricultural Market | RandomForest | 8.44 | 10.74 | 0.759 |  |
| Potato | Coimbatore APMC Market | NaiveBaseline | 7.51 | 9.30 | 0.894 |  |
| Potato | Coimbatore APMC Market | LinearRegression | 7.31 | 9.20 | 0.897 | ✓ |
| Potato | Coimbatore APMC Market | RandomForest | 7.61 | 9.41 | 0.892 |  |
| Potato | Erode Wholesale Market | NaiveBaseline | 6.72 | 8.23 | 0.859 |  |
| Potato | Erode Wholesale Market | LinearRegression | 6.77 | 8.42 | 0.853 | ✓ |
| Potato | Erode Wholesale Market | RandomForest | 13.24 | 16.84 | 0.411 |  |
| Potato | Tiruppur Agricultural Market | NaiveBaseline | 5.91 | 7.70 | 0.776 |  |
| Potato | Tiruppur Agricultural Market | LinearRegression | 6.22 | 7.93 | 0.762 | ✓ |
| Potato | Tiruppur Agricultural Market | RandomForest | 6.02 | 7.82 | 0.769 |  |

## Limitations
- Trained on synthetic data; replace with real market data for production.
- Lag/rolling features may not capture true market dynamics.
- No external factors (weather, harvest, policy) are modelled.

## Reproducibility
- Random seed: 42
- Feature list: day_of_week, day_of_month, month, day_of_year, lag_1, lag_3, lag_7, rolling_mean_3, rolling_mean_7, rolling_std_3, rolling_std_7
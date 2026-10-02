# IML Academic Mapping — BizGuard

This document maps BizGuard's implementation to Introduction to Machine Learning (IML) course concepts.

| IML Concept | BizGuard Implementation | Files |
|---|---|---|
| Supervised Learning | Demand prediction from labeled data | `src/ml/train.py` |
| Feature Engineering | Temporal, lag, rolling, business features | `src/data/feature_engineering.py` |
| Train/Test Split | 80/20 random split with fixed seed | `src/ml/preprocessing.py` |
| Linear Regression | Baseline model for demand prediction | `src/ml/train.py` |
| Random Forest | Advanced ensemble model | `src/ml/train.py` |
| Model Comparison | Side-by-side metric comparison | `src/ml/evaluate.py` |
| Evaluation Metrics | MAE, RMSE, R² | `src/ml/evaluate.py` |
| Feature Importance | Random Forest feature ranking | `src/ml/train.py` |
| Prediction | Future demand forecasting | `src/ml/predict.py` |
| Model Persistence | Saving/loading trained models | `src/ml/model_utils.py` |

## ML Pipeline

```
Cleaned Data → Feature Engineering → Feature Selection →
Train/Test Split → Model Training → Evaluation →
Prediction → Decision Engine
```

## Features Used

### Temporal Features
- month, day, day_of_week, week_of_year, quarter
- is_weekend, is_month_start, is_month_end
- Cyclical encoding (month_sin, month_cos)

### Lag Features
- quantity_lag_1, quantity_lag_7, quantity_lag_14, quantity_lag_30

### Rolling Features
- quantity_rolling_mean_7/14/30
- quantity_rolling_std_7/14/30

### Business Features
- unit_price, discount, cost_per_unit
- marketing_spend, inventory_units
- price_to_cost_ratio, marketing_per_unit
- return_rate, inventory_to_sales

## Models

### Linear Regression (Baseline)
- Fits a linear relationship: y = β₀ + β₁x₁ + β₂x₂ + ...
- Simple, interpretable, provides performance floor
- Student can explain coefficients in viva

### Random Forest Regressor
- Ensemble of 100 decision trees
- Captures non-linear relationships
- Provides feature importance
- More accurate but less interpretable than linear

## Evaluation Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| MAE | mean(\|actual - predicted\|) | Average error in units |
| RMSE | sqrt(mean((actual - predicted)²)) | Error with large-error penalty |
| R² | 1 - SS_res/SS_tot | Proportion of variance explained |

## Limitations

- Uses synthetic data — real business data would improve predictions
- Limited historical period
- Correlation ≠ causation
- Model may not generalize to unseen market conditions

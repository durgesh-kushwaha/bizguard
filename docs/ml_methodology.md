# ML Methodology — BizGuard

## Objective

Predict future product demand (quantity) to support business decisions.

## Target Variable

- **quantity** — Units sold per order
- Aggregated predictions provide monthly/weekly demand forecasts

## Feature Engineering Pipeline

1. **Temporal Features**: Month, day of week, quarter, weekend flag
2. **Cyclical Encoding**: sin/cos transformation for month (Dec→Jan continuity)
3. **Lag Features**: Previous 1, 7, 14, 30-day quantities
4. **Rolling Statistics**: 7, 14, 30-day rolling mean and standard deviation
5. **Business Features**: Price ratios, marketing per unit, return rate

## Models

### Linear Regression (Baseline)
- Formula: ŷ = β₀ + Σ(βᵢxᵢ)
- Purpose: Establish performance baseline
- Advantage: Simple, interpretable coefficients

### Random Forest Regressor
- Ensemble of 100 decision trees
- Max depth: 15
- Purpose: Capture non-linear patterns
- Advantage: Feature importance, better accuracy

## Evaluation Protocol

- 80/20 train/test split (random, seed=42)
- Metrics: MAE, RMSE, R²
- Actual vs predicted visualization
- Residual analysis

## Forecasting

- Creates future feature rows from recent historical values
- Temporal features computed from future dates
- Lag/rolling features use recent historical averages
- Predictions clamped to non-negative values

## Limitations

- Synthetic data limits model realism
- No external features (weather, events, competitor actions)
- Correlation-based, not causal
- May not generalize to unseen market conditions
- Feature leakage is mitigated but lag features use simplifications

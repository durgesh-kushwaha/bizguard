# ML Methodology — BizGuard

## Prediction Targets

The training tab predicts quantity on a transaction row. The forecast tab has a separate, time-series target: the sum of units sold per calendar day. That daily target matches the historical chart and the inventory decision horizon.

## Transaction Model

The transaction pipeline includes calendar, product/business, and historical quantity features. Rolling averages and deviations are shifted so the current target is never part of its own feature. Quantity-derived ratios are excluded from predictors.

The latest 20% of observations are held out in date order, with all transactions from a date kept together. Linear Regression is a baseline; Random Forest, Extra Trees, and Histogram Gradient Boosting are compared on the same future slice using MAE, RMSE, and R². This is a single chronological holdout, not a claim of performance across every future period.

## Daily Demand Forecast

Transaction quantities are summed per date. Missing calendar dates are filled with zero so lag lengths mean days rather than transaction rows. The model uses:

- Recent demand at 1, 7, 14, and 28 days
- Trailing 7-, 14-, and 28-day averages and variability
- Weekly and annual calendar cycles
- A continuous trend index

Random Forest and HistGradientBoosting are compared with a weekly seasonal-naive forecast using three rolling-origin folds. Each fold trains only on dates before its validation window and forecasts forward recursively. The lowest-WAPE method is selected; the seasonal baseline remains eligible and wins when the ML models do not improve on it. Reported MAE and WAPE come from those held-out daily predictions.

## Limitations

The bundled dataset is synthetic. Forecast quality depends on the uploaded history and cannot be guaranteed. Promotions, stockouts, price changes, holidays, and market shifts are not included unless represented in the data. Backtests are evidence about historical periods, not certainty about future demand.

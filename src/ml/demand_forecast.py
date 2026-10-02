"""Daily demand forecasting with chronological model selection."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor


LAG_DAYS = (1, 7, 14, 28)
ROLLING_DAYS = (7, 14, 28)
MIN_HISTORY_DAYS = 70


def daily_demand_series(data: pd.DataFrame, product_id: str | None = None) -> pd.Series:
    """Aggregate transaction quantities into a continuous daily series."""
    if not {"date", "quantity"}.issubset(data.columns):
        raise ValueError("Forecasting requires date and quantity columns.")

    rows = data.copy()
    rows["date"] = pd.to_datetime(rows["date"], errors="coerce").dt.normalize()
    rows["quantity"] = pd.to_numeric(rows["quantity"], errors="coerce")
    rows = rows.dropna(subset=["date", "quantity"])
    if product_id is not None:
        if "product_id" not in rows:
            raise ValueError("Product-specific forecasting requires a product_id column.")
        rows = rows[rows["product_id"].astype(str) == str(product_id)]
    if rows.empty:
        raise ValueError("No dated demand is available for this selection.")

    observed = rows.groupby("date")["quantity"].sum().sort_index()
    index = pd.date_range(observed.index.min(), observed.index.max(), freq="D")
    return observed.reindex(index, fill_value=0.0).astype(float)


def _feature_row(history: np.ndarray, date: pd.Timestamp, first_date: pd.Timestamp) -> dict:
    features = {
        "day_of_week": date.dayofweek,
        "week_sin": np.sin(2 * np.pi * date.dayofweek / 7),
        "week_cos": np.cos(2 * np.pi * date.dayofweek / 7),
        "month_sin": np.sin(2 * np.pi * (date.dayofyear - 1) / 365.25),
        "month_cos": np.cos(2 * np.pi * (date.dayofyear - 1) / 365.25),
        "trend_days": (date - first_date).days,
    }
    for lag in LAG_DAYS:
        features[f"lag_{lag}"] = float(history[-lag]) if len(history) >= lag else 0.0
    for window in ROLLING_DAYS:
        recent = history[-window:]
        features[f"mean_{window}"] = float(np.mean(recent)) if len(recent) else 0.0
        features[f"std_{window}"] = float(np.std(recent)) if len(recent) else 0.0
    return features


def _training_frame(series: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    values = series.to_numpy(dtype=float)
    dates = series.index
    rows = [
        _feature_row(values[:position], dates[position], dates[0])
        for position in range(max(LAG_DAYS), len(values))
    ]
    features = pd.DataFrame(rows)
    target = pd.Series(values[max(LAG_DAYS):], index=dates[max(LAG_DAYS):], name="quantity")
    return features, target


def _new_models() -> dict[str, Callable[[], object]]:
    return {
        "Random Forest": lambda: RandomForestRegressor(
            n_estimators=220,
            max_depth=10,
            min_samples_leaf=3,
            max_features=0.9,
            random_state=42,
            n_jobs=1,
        ),
        "Gradient Boosting": lambda: HistGradientBoostingRegressor(
            max_iter=180,
            learning_rate=0.05,
            max_leaf_nodes=10,
            l2_regularization=2.0,
            random_state=42,
        ),
    }


def _recursive_forecast(series: pd.Series, model, periods: int) -> np.ndarray:
    history = series.to_numpy(dtype=float).tolist()
    first_date = series.index[0]
    predictions = []
    for step in range(1, periods + 1):
        date = series.index[-1] + pd.Timedelta(days=step)
        row = pd.DataFrame([_feature_row(np.asarray(history), date, first_date)])
        value = max(0.0, float(model.predict(row)[0]))
        predictions.append(value)
        history.append(value)
    return np.asarray(predictions)


def _seasonal_forecast(series: pd.Series, periods: int) -> np.ndarray:
    history = series.to_numpy(dtype=float).tolist()
    predictions = []
    for _ in range(periods):
        value = max(0.0, float(history[-7])) if len(history) >= 7 else float(np.mean(history))
        predictions.append(value)
        history.append(value)
    return np.asarray(predictions)


def _wape(actual: np.ndarray, predicted: np.ndarray) -> float:
    denominator = float(np.sum(np.abs(actual)))
    return float(np.sum(np.abs(actual - predicted)) / denominator) if denominator else float("inf")


def _backtest(series: pd.Series) -> tuple[dict[str, dict], int]:
    horizon = min(28, max(7, len(series) // 12))
    origins = [len(series) - 3 * horizon, len(series) - 2 * horizon, len(series) - horizon]
    model_names = list(_new_models()) + ["Seasonal Naive"]
    results = {name: {"actual": [], "predicted": []} for name in model_names}

    for origin in origins:
        history = series.iloc[:origin]
        actual = series.iloc[origin:origin + horizon].to_numpy(dtype=float)
        X_train, y_train = _training_frame(history)
        if len(X_train) < 7:
            continue
        for name, factory in _new_models().items():
            model = factory()
            model.fit(X_train, y_train)
            prediction = _recursive_forecast(history, model, len(actual))
            results[name]["actual"].extend(actual.tolist())
            results[name]["predicted"].extend(prediction.tolist())

        prediction = _seasonal_forecast(history, len(actual))
        results["Seasonal Naive"]["actual"].extend(actual.tolist())
        results["Seasonal Naive"]["predicted"].extend(prediction.tolist())

    metrics = {}
    for name, values in results.items():
        actual = np.asarray(values["actual"], dtype=float)
        predicted = np.asarray(values["predicted"], dtype=float)
        metrics[name] = {
            "mae": float(np.mean(np.abs(actual - predicted))) if len(actual) else float("inf"),
            "wape": _wape(actual, predicted) if len(actual) else float("inf"),
        }
    return metrics, horizon


def forecast_daily_demand(data: pd.DataFrame, periods: int = 30,
                          product_id: str | None = None) -> dict:
    """Backtest daily-demand models, then forecast from the best validated method."""
    series = daily_demand_series(data, product_id)
    if len(series) < MIN_HISTORY_DAYS:
        raise ValueError(
            f"At least {MIN_HISTORY_DAYS} days of dated history are required; found {len(series)}."
        )
    if periods < 1:
        raise ValueError("Forecast period must be at least one day.")

    backtest, validation_horizon = _backtest(series)
    best_name = min(backtest, key=lambda name: (backtest[name]["wape"], backtest[name]["mae"]))

    if best_name == "Seasonal Naive":
        predictions = _seasonal_forecast(series, periods)
    else:
        features, target = _training_frame(series)
        model = _new_models()[best_name]()
        model.fit(features, target)
        predictions = _recursive_forecast(series, model, periods)

    metrics = backtest[best_name]
    return {
        "dates": pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=periods, freq="D").tolist(),
        "predictions": predictions.tolist(),
        "total_predicted": round(float(predictions.sum()), 2),
        "avg_daily_predicted": round(float(predictions.mean()), 2),
        "periods": periods,
        "model_name": best_name,
        "product_id": product_id,
        "status": "success",
        "forecast_version": 3,
        "history": series,
        "backtest_mae": round(metrics["mae"], 2),
        "backtest_wape": round(metrics["wape"] * 100, 1),
        "baseline_wape": round(backtest["Seasonal Naive"]["wape"] * 100, 1),
        "beats_baseline": metrics["wape"] < backtest["Seasonal Naive"]["wape"],
        "validation_days": validation_horizon,
        "backtest_scores": backtest,
    }

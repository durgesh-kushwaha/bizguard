"""
Tests for ML pipeline: feature engineering, training, evaluation, prediction.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _create_ml_df():
    """Create a DataFrame suitable for ML testing."""
    np.random.seed(42)
    n = 500
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    
    return pd.DataFrame({
        "date": dates,
        "order_id": [f"ORD{i:04d}" for i in range(n)],
        "product_id": np.random.choice(["P001", "P002", "P003"], n),
        "product_name": np.random.choice(["Widget A", "Widget B", "Widget C"], n),
        "category": np.random.choice(["Electronics", "Office"], n),
        "quantity": np.random.poisson(5, n) + 1,
        "unit_price": np.random.uniform(100, 1000, n).round(2),
        "discount": np.random.choice([0, 5, 10, 15], n),
        "cost_per_unit": np.random.uniform(50, 500, n).round(2),
        "marketing_spend": np.random.uniform(0, 500, n).round(2),
        "returns": np.random.randint(0, 3, n),
        "customer_id": [f"C{i:04d}" for i in np.random.randint(1, 100, n)],
        "region": np.random.choice(["North", "South", "East", "West"], n),
        "inventory_units": np.random.randint(10, 200, n),
    })


class TestFeatureEngineering:
    """Tests for feature engineering module."""
    
    def test_temporal_features(self):
        """Test temporal feature creation."""
        from src.data.feature_engineering import create_temporal_features
        
        df = _create_ml_df()
        result = create_temporal_features(df)
        
        assert "month" in result.columns
        assert "day_of_week" in result.columns
        assert "is_weekend" in result.columns
        assert "month_sin" in result.columns
        assert "month_cos" in result.columns
    
    def test_lag_features(self):
        """Test lag feature creation."""
        from src.data.feature_engineering import create_lag_features
        
        df = _create_ml_df()
        result = create_lag_features(df, lags=[1, 7])
        
        assert "quantity_lag_1" in result.columns
        assert "quantity_lag_7" in result.columns
    
    def test_rolling_features(self):
        """Test rolling feature creation."""
        from src.data.feature_engineering import create_rolling_features
        
        df = _create_ml_df()
        result = create_rolling_features(df, windows=[7])
        
        assert "quantity_rolling_mean_7" in result.columns
        assert "quantity_rolling_std_7" in result.columns
    
    def test_full_pipeline(self):
        """Test the full feature engineering pipeline."""
        from src.data.feature_engineering import prepare_ml_features
        
        df = _create_ml_df()
        result = prepare_ml_features(df)
        
        assert len(result) > 0
        assert "month" in result.columns
        assert "quantity_lag_1" in result.columns


class TestMLTraining:
    """Tests for model training."""
    
    def test_train_linear_regression(self):
        """Test Linear Regression training."""
        from src.ml.train import train_linear_regression
        
        np.random.seed(42)
        X_train = pd.DataFrame({
            "feature1": np.random.randn(200),
            "feature2": np.random.randn(200),
        })
        y_train = pd.Series(X_train["feature1"] * 2 + np.random.randn(200) * 0.1)
        
        model, info = train_linear_regression(X_train, y_train)
        
        assert model is not None
        assert info["model_name"] == "Linear Regression"
        assert info["training_samples"] == 200
    
    def test_train_random_forest(self):
        """Test Random Forest training."""
        from src.ml.train import train_random_forest
        
        np.random.seed(42)
        X_train = pd.DataFrame({
            "feature1": np.random.randn(200),
            "feature2": np.random.randn(200),
        })
        y_train = pd.Series(np.random.poisson(5, 200))
        
        model, info = train_random_forest(X_train, y_train, n_estimators=10)
        
        assert model is not None
        assert info["model_name"] == "Random Forest Regressor"
        assert "feature_importance" in info

    def test_time_split_keeps_latest_rows_for_testing(self):
        from src.ml.preprocessing import split_data

        X = pd.DataFrame({"day": np.arange(10)})
        y = pd.Series(np.arange(10))
        X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)

        assert X_train["day"].max() < X_test["day"].min()
        assert y_train.max() < y_test.min()

    def test_time_split_keeps_same_day_rows_together(self):
        from src.ml.preprocessing import split_data

        X = pd.DataFrame({"value": range(6)})
        y = pd.Series(range(6))
        dates = pd.Series(pd.to_datetime([
            "2025-01-01", "2025-01-01", "2025-01-02",
            "2025-01-02", "2025-01-03", "2025-01-03",
        ]))
        X_train, X_test, _, _ = split_data(X, y, test_size=0.2, dates=dates)

        assert X_train.index.tolist() == [0, 1, 2, 3]
        assert X_test.index.tolist() == [4, 5]

    def test_rolling_features_only_use_prior_target_values(self):
        from src.data.feature_engineering import create_rolling_features

        frame = pd.DataFrame({
            "product_id": ["A"] * 4,
            "date": pd.date_range("2025-01-01", periods=4),
            "quantity": [1, 3, 5, 7],
        })
        result = create_rolling_features(frame, windows=[2])

        assert pd.isna(result["quantity_rolling_mean_2"].iloc[0])
        assert result["quantity_rolling_mean_2"].iloc[1:].tolist() == [1.0, 2.0, 4.0]


class TestDailyDemandForecast:
    def test_aggregates_rows_to_daily_totals_and_keeps_units_comparable(self):
        from src.ml.demand_forecast import forecast_daily_demand
        from src.data.loader import load_sample_data

        frame, _ = load_sample_data()
        result = forecast_daily_demand(frame, periods=14)

        recent_daily_average = result["history"].tail(90).mean()
        assert result["model_name"] in {"Random Forest", "Gradient Boosting", "Seasonal Naive"}
        assert result["avg_daily_predicted"] > recent_daily_average * 0.5
        assert result["avg_daily_predicted"] < recent_daily_average * 1.5
        assert result["backtest_wape"] >= 0
        assert result["baseline_wape"] >= 0
        assert len(result["predictions"]) == 14

    def test_product_forecast_uses_only_selected_product(self):
        from src.ml.demand_forecast import daily_demand_series

        dates = pd.date_range("2025-01-01", periods=40)
        frame = pd.DataFrame({
            "date": list(dates) + list(dates),
            "product_id": ["A"] * 40 + ["B"] * 40,
            "quantity": [2] * 40 + [20] * 40,
        })

        series = daily_demand_series(frame, "A")
        assert series.sum() == 80
        assert series.mean() == 2


class TestMLEvaluation:
    """Tests for model evaluation."""
    
    def test_evaluate_model(self):
        """Test model evaluation produces correct metrics."""
        from src.ml.train import train_linear_regression
        from src.ml.evaluate import evaluate_model
        
        np.random.seed(42)
        X = pd.DataFrame({"f1": np.random.randn(100), "f2": np.random.randn(100)})
        y = pd.Series(X["f1"] * 3 + np.random.randn(100) * 0.5)
        
        model, _ = train_linear_regression(X[:80], y[:80])
        metrics = evaluate_model(model, X[80:], y[80:])
        
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "r2" in metrics
        assert metrics["mae"] >= 0
        assert metrics["rmse"] >= 0
    
    def test_compare_models(self):
        """Test model comparison."""
        from src.ml.evaluate import compare_models
        
        evaluations = {
            "Model A": {"mae": 1.0, "rmse": 1.5, "r2": 0.8, "mean_error": 0.1, "std_error": 0.5},
            "Model B": {"mae": 0.8, "rmse": 1.2, "r2": 0.85, "mean_error": 0.05, "std_error": 0.4},
        }
        
        comparison = compare_models(evaluations)
        assert len(comparison) == 2
        assert "Model" in comparison.columns

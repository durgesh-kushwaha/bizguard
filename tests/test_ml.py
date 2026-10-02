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

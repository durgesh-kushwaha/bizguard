"""
Model training module for BizGuard.

Trains supervised ML models for demand/sales prediction.
Models:
1. Linear Regression (baseline)
2. Random Forest Regressor (advanced)

Each model is trained on the same data for fair comparison.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, Tuple, Any
import logging
import time

logger = logging.getLogger(__name__)


def train_linear_regression(X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[Any, Dict]:
    """
    Train a Linear Regression model (baseline).
    
    Linear Regression is used as a baseline because:
    - It's simple and interpretable
    - It shows the linear relationship between features and target
    - It provides a performance floor for comparison
    
    Args:
        X_train: Training features.
        y_train: Training target.
    
    Returns:
        Tuple of (trained model, training info dict).
    """
    start_time = time.time()
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    training_time = round(time.time() - start_time, 3)
    
    # Get feature coefficients
    coefficients = dict(zip(X_train.columns, model.coef_.round(4)))
    
    info = {
        "model_name": "Linear Regression",
        "model_type": "linear_regression",
        "training_time_seconds": training_time,
        "intercept": round(model.intercept_, 4),
        "coefficients": coefficients,
        "num_features": len(X_train.columns),
        "training_samples": len(X_train),
        "description": (
            "Linear Regression fits a straight-line relationship between features and the target. "
            "It minimizes the sum of squared errors between predicted and actual values. "
            "Used as the baseline model for comparison."
        ),
    }
    
    logger.info(f"Linear Regression trained in {training_time}s on {len(X_train)} samples")
    return model, info


def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series,
                        n_estimators: int = 100,
                        max_depth: int = 15,
                        random_state: int = 42) -> Tuple[Any, Dict]:
    """
    Train a Random Forest Regressor model.
    
    Random Forest is used because:
    - It captures non-linear relationships
    - It handles feature interactions automatically
    - It provides feature importance rankings
    - It's generally more accurate than linear models
    - It's still explainable (unlike deep learning)
    
    Args:
        X_train: Training features.
        y_train: Training target.
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of each tree.
        random_state: Random seed for reproducibility.
    
    Returns:
        Tuple of (trained model, training info dict).
    """
    start_time = time.time()
    
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,  # Use all CPU cores
    )
    model.fit(X_train, y_train)
    
    training_time = round(time.time() - start_time, 3)
    
    # Get feature importance
    importance = dict(zip(
        X_train.columns,
        model.feature_importances_.round(4)
    ))
    # Sort by importance
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
    
    info = {
        "model_name": "Random Forest Regressor",
        "model_type": "random_forest",
        "training_time_seconds": training_time,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "feature_importance": importance,
        "num_features": len(X_train.columns),
        "training_samples": len(X_train),
        "description": (
            "Random Forest combines multiple decision trees to make predictions. "
            "Each tree learns from a random subset of the data, and the final prediction "
            "is the average of all trees. This reduces overfitting and captures complex patterns. "
            "Feature importance shows which factors most influence predictions."
        ),
    }
    
    logger.info(f"Random Forest trained in {training_time}s on {len(X_train)} samples")
    return model, info


def train_all_models(X_train: pd.DataFrame, y_train: pd.Series) -> Dict[str, Tuple[Any, Dict]]:
    """
    Train all available models and return them with their info.
    
    Args:
        X_train: Training features.
        y_train: Training target.
    
    Returns:
        Dict mapping model_type -> (model, info).
    """
    models = {}
    
    # Train Linear Regression (baseline)
    lr_model, lr_info = train_linear_regression(X_train, y_train)
    models["linear_regression"] = (lr_model, lr_info)
    
    # Train Random Forest
    rf_model, rf_info = train_random_forest(X_train, y_train)
    models["random_forest"] = (rf_model, rf_info)
    
    return models

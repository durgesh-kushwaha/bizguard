"""
Prediction and forecasting module for BizGuard.

Generates future demand predictions using trained ML models.
These predictions feed into the decision simulator.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def predict(model: Any, X: pd.DataFrame) -> np.ndarray:
    """
    Generate predictions from a trained model.
    
    Args:
        model: Trained sklearn model.
        X: Feature DataFrame (same structure as training features).
    
    Returns:
        Array of predictions.
    """
    predictions = model.predict(X)
    # Ensure non-negative predictions for quantity
    predictions = np.maximum(predictions, 0)
    return predictions


def create_future_features(df: pd.DataFrame, feature_cols: List[str],
                           periods: int = 30,
                           product_id: Optional[str] = None) -> pd.DataFrame:
    """
    Create feature rows for future prediction periods.
    
    Strategy:
    - Temporal features: computed from future dates
    - Lag/rolling features: use recent historical values
    - Business features: use recent averages
    - Categorical encodings: carry forward
    
    Args:
        df: Historical data with all features.
        feature_cols: List of feature columns the model expects.
        periods: Number of future periods to forecast.
        product_id: Specific product to forecast (None = overall).
    
    Returns:
        DataFrame with future feature rows.
    """
    if product_id and "product_id" in df.columns:
        hist = df[df["product_id"] == product_id].copy()
    else:
        hist = df.copy()
    
    if len(hist) == 0:
        raise ValueError("No historical data available for prediction.")
    
    # Get the last date in the data
    if "date" in hist.columns:
        last_date = pd.to_datetime(hist["date"]).max()
    else:
        last_date = datetime.now()
    
    future_rows = []
    
    for i in range(1, periods + 1):
        future_date = last_date + timedelta(days=i)
        row = {}
        
        for col in feature_cols:
            if col == "month":
                row[col] = future_date.month
            elif col == "day":
                row[col] = future_date.day
            elif col == "day_of_week":
                row[col] = future_date.weekday()
            elif col == "week_of_year":
                row[col] = future_date.isocalendar()[1]
            elif col == "quarter":
                row[col] = (future_date.month - 1) // 3 + 1
            elif col == "year":
                row[col] = future_date.year
            elif col == "is_weekend":
                row[col] = 1 if future_date.weekday() >= 5 else 0
            elif col == "is_month_start":
                row[col] = 1 if future_date.day == 1 else 0
            elif col == "is_month_end":
                row[col] = 1 if (future_date + timedelta(days=1)).day == 1 else 0
            elif col == "month_sin":
                row[col] = round(np.sin(2 * np.pi * future_date.month / 12), 4)
            elif col == "month_cos":
                row[col] = round(np.cos(2 * np.pi * future_date.month / 12), 4)
            elif col in hist.columns:
                # Use recent average for other features
                recent = hist[col].tail(30)
                row[col] = recent.mean() if len(recent) > 0 else 0
            else:
                row[col] = 0
        
        row["_future_date"] = future_date
        future_rows.append(row)
    
    future_df = pd.DataFrame(future_rows)
    return future_df


def generate_forecast(model: Any, df: pd.DataFrame, feature_cols: List[str],
                      periods: int = 30,
                      product_id: Optional[str] = None,
                      model_name: str = "Model") -> Dict:
    """
    Generate a complete demand forecast.
    
    Args:
        model: Trained model.
        df: Historical data with features.
        feature_cols: Feature columns for the model.
        periods: Number of future days to forecast.
        product_id: Specific product (None = overall).
        model_name: Name of the model for display.
    
    Returns:
        Dict with forecast results including:
        - dates: list of future dates
        - predictions: list of predicted quantities
        - total_predicted: sum of all predictions
        - avg_daily_predicted: average daily prediction
        - model_name: name of model used
    """
    try:
        future_features = create_future_features(df, feature_cols, periods, product_id)
        
        # Extract dates before predicting
        future_dates = future_features["_future_date"].tolist()
        
        # Remove non-feature columns for prediction
        predict_features = future_features[feature_cols].copy()
        predict_features = predict_features.fillna(0)
        
        # Generate predictions
        predictions = predict(model, predict_features)
        
        return {
            "dates": future_dates,
            "predictions": predictions.tolist(),
            "total_predicted": round(float(np.sum(predictions)), 2),
            "avg_daily_predicted": round(float(np.mean(predictions)), 2),
            "max_daily_predicted": round(float(np.max(predictions)), 2),
            "min_daily_predicted": round(float(np.min(predictions)), 2),
            "periods": periods,
            "model_name": model_name,
            "product_id": product_id,
            "status": "success",
        }
    
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        return {
            "dates": [],
            "predictions": [],
            "total_predicted": 0,
            "avg_daily_predicted": 0,
            "periods": periods,
            "model_name": model_name,
            "product_id": product_id,
            "status": "error",
            "error": str(e),
        }

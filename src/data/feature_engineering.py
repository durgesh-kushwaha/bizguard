"""
Feature engineering module for BizGuard.

Creates features for ML models from cleaned business data.
Features are designed to capture temporal patterns, product characteristics,
and business context that help predict future demand.
"""

import pandas as pd
import numpy as np
from typing import List


def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract time-based features from the date column.
    
    Features created:
    - year, month, day, day_of_week, week_of_year
    - is_weekend (Saturday/Sunday)
    - is_month_start, is_month_end
    - quarter
    - month_sin, month_cos (cyclical encoding)
    
    Args:
        df: DataFrame with a 'date' column.
    
    Returns:
        DataFrame with temporal features added.
    """
    result = df.copy()
    
    if "date" not in result.columns:
        return result
    
    result["date"] = pd.to_datetime(result["date"])
    
    result["year"] = result["date"].dt.year
    result["month"] = result["date"].dt.month
    result["day"] = result["date"].dt.day
    result["day_of_week"] = result["date"].dt.dayofweek  # 0=Monday, 6=Sunday
    result["week_of_year"] = result["date"].dt.isocalendar().week.astype(int)
    result["quarter"] = result["date"].dt.quarter
    result["is_weekend"] = (result["day_of_week"] >= 5).astype(int)
    result["is_month_start"] = result["date"].dt.is_month_start.astype(int)
    result["is_month_end"] = result["date"].dt.is_month_end.astype(int)
    
    # Cyclical encoding for month (captures that Dec and Jan are close)
    result["month_sin"] = np.sin(2 * np.pi * result["month"] / 12).round(4)
    result["month_cos"] = np.cos(2 * np.pi * result["month"] / 12).round(4)
    
    return result


def create_lag_features(df: pd.DataFrame, group_col: str = "product_id",
                        target_col: str = "quantity",
                        lags: List[int] = None) -> pd.DataFrame:
    """
    Create lagged features for time-series prediction.
    
    Lag features capture how much was sold in previous periods,
    which is a strong predictor of future demand.
    
    Args:
        df: DataFrame sorted by date.
        group_col: Column to group by (usually product_id).
        target_col: Column to create lags for.
        lags: List of lag periods. Default is [1, 7, 14, 30] days.
    
    Returns:
        DataFrame with lag features added.
    """
    if lags is None:
        lags = [1, 7, 14, 30]
    
    result = df.copy()
    result = result.sort_values("date")
    
    if group_col in result.columns:
        for lag in lags:
            col_name = f"{target_col}_lag_{lag}"
            result[col_name] = result.groupby(group_col)[target_col].shift(lag)
    else:
        for lag in lags:
            col_name = f"{target_col}_lag_{lag}"
            result[col_name] = result[target_col].shift(lag)
    
    return result


def create_rolling_features(df: pd.DataFrame, group_col: str = "product_id",
                            target_col: str = "quantity",
                            windows: List[int] = None) -> pd.DataFrame:
    """
    Create rolling window statistics.
    
    Rolling means/stds capture recent trends and volatility.
    
    Args:
        df: DataFrame sorted by date.
        group_col: Column to group by.
        target_col: Column to compute rolling stats for.
        windows: List of window sizes. Default is [7, 14, 30].
    
    Returns:
        DataFrame with rolling features added.
    """
    if windows is None:
        windows = [7, 14, 30]
    
    result = df.copy()
    result = result.sort_values("date")
    
    for window in windows:
        mean_col = f"{target_col}_rolling_mean_{window}"
        std_col = f"{target_col}_rolling_std_{window}"
        
        if group_col in result.columns:
            result[mean_col] = result.groupby(group_col)[target_col].transform(
                lambda values: values.shift(1).rolling(window, min_periods=1).mean()
            ).round(2)
            result[std_col] = result.groupby(group_col)[target_col].transform(
                lambda values: values.shift(1).rolling(window, min_periods=1).std()
            ).fillna(0).round(2)
        else:
            history = result[target_col].shift(1)
            result[mean_col] = history.rolling(window, min_periods=1).mean().round(2)
            result[std_col] = history.rolling(window, min_periods=1).std().fillna(0).round(2)
    
    return result


def create_business_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create business-context features.
    
    Features:
    - price_to_cost_ratio: unit_price / cost_per_unit
    - effective_discount: actual discount percentage
    - marketing_per_unit: marketing spend per unit sold
    - return_rate: returns / quantity
    - inventory_to_sales: inventory / quantity (stock cover)
    
    Args:
        df: Cleaned DataFrame.
    
    Returns:
        DataFrame with business features added.
    """
    result = df.copy()
    
    if all(col in result.columns for col in ["unit_price", "cost_per_unit"]):
        result["price_to_cost_ratio"] = np.where(
            result["cost_per_unit"] > 0,
            (result["unit_price"] / result["cost_per_unit"]).round(2),
            0
        )
    
    if all(col in result.columns for col in ["marketing_spend", "quantity"]):
        result["marketing_per_unit"] = np.where(
            result["quantity"] > 0,
            (result["marketing_spend"] / result["quantity"]).round(2),
            0
        )
    
    if all(col in result.columns for col in ["returns", "quantity"]):
        result["return_rate"] = np.where(
            result["quantity"] > 0,
            (result["returns"] / result["quantity"]).round(4),
            0
        )
    
    if all(col in result.columns for col in ["inventory_units", "quantity"]):
        result["inventory_to_sales"] = np.where(
            result["quantity"] > 0,
            (result["inventory_units"] / result["quantity"]).round(2),
            0
        )
    
    return result


def prepare_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full feature engineering pipeline for ML.
    
    Pipeline:
    1. Temporal features (month, day_of_week, etc.)
    2. Lag features (past demand)
    3. Rolling statistics (trends)
    4. Business features (margins, ratios)
    5. Drop rows with NaN from lag/rolling (initial period)
    
    Args:
        df: Cleaned DataFrame.
    
    Returns:
        DataFrame ready for ML model training.
    """
    result = df.copy()
    
    # Step 1: Temporal features
    result = create_temporal_features(result)
    
    # Step 2: Lag features
    result = create_lag_features(result)
    
    # Step 3: Rolling features
    result = create_rolling_features(result)
    
    # Step 4: Business features
    result = create_business_features(result)
    
    # Step 5: Drop rows with NaN from lag/rolling computations
    # These are the initial rows that don't have enough history
    lag_cols = [col for col in result.columns if "lag_" in col or "rolling_" in col]
    result = result.dropna(subset=lag_cols).reset_index(drop=True)
    
    return result

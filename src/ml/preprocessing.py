"""
ML data preprocessing module for BizGuard.

Prepares data specifically for machine learning models.
Separate from general data cleaning — this module handles
feature selection, encoding, and train/test splitting.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Tuple, List, Dict, Optional
from config.settings import ML_TEST_SIZE, ML_RANDOM_STATE


def prepare_features(df: pd.DataFrame, target_col: str = "quantity") -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """
    Select and prepare features for ML model training.
    
    Feature selection logic:
    - Include numeric columns that are predictive
    - Exclude identifiers (order_id, customer_id, product_id)
    - Exclude the target itself
    - Exclude derived columns that leak the target (revenue, profit)
    - Encode categorical variables
    
    Args:
        df: Feature-engineered DataFrame.
        target_col: Name of the target column.
    
    Returns:
        Tuple of (feature DataFrame, target Series, feature names list).
    
    Raises:
        ValueError: If target column is missing or insufficient data.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
    
    if len(df) < 50:
        raise ValueError(f"Insufficient data for ML: {len(df)} rows (minimum 50 required).")
    
    # Columns to exclude (identifiers, target-leaking, and non-predictive)
    exclude_cols = {
        target_col,
        "date", "order_id", "customer_id", "product_id",
        # Target-leaking columns (computed from quantity)
        "revenue", "gross_profit", "profit_margin", "net_revenue",
        "cost", "net_price",
        # These ratios are calculated from the target quantity itself.
        "marketing_per_unit", "return_rate", "inventory_to_sales",
        # String identifiers
        "product_name",
    }
    
    # Select numeric features
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [col for col in numeric_cols if col not in exclude_cols]
    
    # Encode categorical columns that might be useful
    result_df = df.copy()
    categorical_encode = ["category", "region"]
    
    for col in categorical_encode:
        if col in result_df.columns:
            le = LabelEncoder()
            result_df[f"{col}_encoded"] = le.fit_transform(result_df[col].astype(str))
            feature_cols.append(f"{col}_encoded")
    
    # Filter to only existing columns
    feature_cols = [col for col in feature_cols if col in result_df.columns]
    
    X = result_df[feature_cols].copy()
    y = result_df[target_col].copy()
    
    # Handle any remaining NaN values
    X = X.fillna(0)
    
    return X, y, feature_cols


def split_data(X: pd.DataFrame, y: pd.Series,
               test_size: float = None,
               random_state: int = None,
               dates: Optional[pd.Series] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into training and testing sets.
    
    Keeps the latest observations for testing so evaluation reflects
    predictions on future data rather than a random mix of dates.
    
    Args:
        X: Feature DataFrame.
        y: Target Series.
        test_size: Fraction for test set (default from settings).
        random_state: Random seed (default from settings).
        dates: Optional observation dates used to keep each date in one split.
    
    Returns:
        Tuple of (X_train, X_test, y_train, y_test).
    """
    if test_size is None:
        test_size = ML_TEST_SIZE
    if random_state is None:
        random_state = ML_RANDOM_STATE
    
    if dates is not None:
        ordered_dates = pd.to_datetime(dates.reindex(X.index), errors="coerce")
        order = ordered_dates.sort_values(kind="stable").index
        X, y, ordered_dates = X.loc[order], y.loc[order], ordered_dates.loc[order]
        unique_dates = ordered_dates.dropna().drop_duplicates()
        test_date_count = max(1, int(np.ceil(len(unique_dates) * test_size)))
        first_test_date = unique_dates.iloc[-test_date_count]
        test_mask = ordered_dates >= first_test_date
        X_train, X_test = X.loc[~test_mask], X.loc[test_mask]
        y_train, y_test = y.loc[~test_mask], y.loc[test_mask]
    else:
        split_at = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_at], X.iloc[split_at:]
        y_train, y_test = y.iloc[:split_at], y.iloc[split_at:]
    
    return X_train, X_test, y_train, y_test


def scale_features(X_train: pd.DataFrame, X_test: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """
    Scale features using StandardScaler.
    
    Fit on training data only to prevent data leakage.
    
    Args:
        X_train: Training features.
        X_test: Testing features.
    
    Returns:
        Tuple of (scaled X_train, scaled X_test, fitted scaler).
    """
    scaler = StandardScaler()
    
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index,
    )
    
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=X_test.columns,
        index=X_test.index,
    )
    
    return X_train_scaled, X_test_scaled, scaler


def get_preprocessing_summary(X_train: pd.DataFrame, X_test: pd.DataFrame,
                               y_train: pd.Series, y_test: pd.Series,
                               feature_names: List[str]) -> Dict:
    """
    Generate a summary of the preprocessing step.
    
    Args:
        X_train, X_test: Feature DataFrames.
        y_train, y_test: Target Series.
        feature_names: List of feature names used.
    
    Returns:
        Summary dict for display.
    """
    return {
        "total_samples": len(X_train) + len(X_test),
        "training_samples": len(X_train),
        "testing_samples": len(X_test),
        "train_test_ratio": f"{len(X_train)}:{len(X_test)}",
        "num_features": len(feature_names),
        "feature_names": feature_names,
        "target_column": y_train.name if hasattr(y_train, 'name') else "quantity",
        "target_mean": round(y_train.mean(), 2),
        "target_std": round(y_train.std(), 2),
        "target_min": round(y_train.min(), 2),
        "target_max": round(y_train.max(), 2),
    }

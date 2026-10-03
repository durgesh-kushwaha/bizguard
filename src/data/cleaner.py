"""
Data cleaning module for BizGuard.

Cleans and preprocesses business data with documented rules.
Every cleaning operation is logged so the user knows what changed.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


def clean_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Clean the dataset and return the cleaned data with a cleaning report.
    
    Cleaning rules:
    1. Remove duplicate rows
    2. Handle missing values
    3. Fix data types
    4. Remove invalid records (negative prices, quantities)
    5. Compute derived columns if missing
    
    Args:
        df: Raw DataFrame.
    
    Returns:
        Tuple of (cleaned DataFrame, cleaning report dict).
    """
    report = {
        "original_rows": len(df),
        "original_columns": len(df.columns),
        "duplicates_removed": 0,
        "missing_values_handled": 0,
        "invalid_records_removed": 0,
        "columns_transformed": [],
        "cleaning_steps": [],
    }
    
    cleaned = df.copy()
    
    # Step 1: Remove duplicate rows
    dup_count = cleaned.duplicated().sum()
    if dup_count > 0:
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
        report["duplicates_removed"] = dup_count
        report["cleaning_steps"].append(f"Removed {dup_count} duplicate rows.")
    
    # Step 2: Parse date column
    if "date" in cleaned.columns:
        if not pd.api.types.is_datetime64_any_dtype(cleaned["date"]):
            cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
            report["columns_transformed"].append("date (converted to datetime)")
            report["cleaning_steps"].append("Converted 'date' column to datetime format.")
        
        # Remove rows with invalid dates
        invalid_dates = cleaned["date"].isna().sum()
        if invalid_dates > 0:
            cleaned = cleaned.dropna(subset=["date"])
            report["invalid_records_removed"] += invalid_dates
            report["cleaning_steps"].append(f"Removed {invalid_dates} rows with invalid dates.")
    
    # Step 3: Convert numeric columns
    numeric_cols = ["quantity", "unit_price", "revenue", "discount", "cost_per_unit",
                    "marketing_spend", "returns", "returned_revenue", "inventory_units"]
    
    for col in numeric_cols:
        if col in cleaned.columns:
            if not pd.api.types.is_numeric_dtype(cleaned[col]):
                cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")
                report["columns_transformed"].append(f"{col} (converted to numeric)")
    
    # Step 4: Handle missing values in numeric columns
    missing_handled = 0
    for col in numeric_cols:
        if col in cleaned.columns:
            missing = cleaned[col].isna().sum()
            if missing > 0:
                if col in ["discount", "returns", "returned_revenue", "marketing_spend"]:
                    # These can reasonably default to 0
                    cleaned[col] = cleaned[col].fillna(0)
                    report["cleaning_steps"].append(
                        f"Filled {missing} missing values in '{col}' with 0."
                    )
                else:
                    # For quantity, price, cost — use median
                    median_val = cleaned[col].median()
                    cleaned[col] = cleaned[col].fillna(median_val)
                    report["cleaning_steps"].append(
                        f"Filled {missing} missing values in '{col}' with median ({median_val:.2f})."
                    )
                missing_handled += missing
    
    report["missing_values_handled"] = missing_handled
    
    # Step 5: Remove invalid records
    initial_len = len(cleaned)
    
    # Remove negative quantities
    if "quantity" in cleaned.columns:
        cleaned = cleaned[cleaned["quantity"] >= 0]
    
    # Remove negative prices
    if "unit_price" in cleaned.columns:
        cleaned = cleaned[cleaned["unit_price"] > 0]
    
    # Remove negative costs
    if "cost_per_unit" in cleaned.columns:
        cleaned = cleaned[cleaned["cost_per_unit"] >= 0]
    
    removed = initial_len - len(cleaned)
    if removed > 0:
        report["invalid_records_removed"] += removed
        report["cleaning_steps"].append(
            f"Removed {removed} rows with invalid values (negative quantity/price/cost)."
        )
    
    cleaned = cleaned.reset_index(drop=True)
    
    # Step 6: Compute derived columns if missing
    cleaned = compute_derived_columns(cleaned)
    report["columns_transformed"].extend(
        [col for col in ["revenue", "gross_profit", "profit_margin", "net_revenue",
                         "discount_rate", "net_price"]
         if col in cleaned.columns]
    )
    
    report["final_rows"] = len(cleaned)
    report["final_columns"] = len(cleaned.columns)
    report["rows_removed"] = report["original_rows"] - report["final_rows"]
    
    if not report["cleaning_steps"]:
        report["cleaning_steps"].append("No cleaning was necessary. Data was already clean.")
    
    return cleaned, report


def compute_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute derived business columns from raw data.
    
    Formulas:
    - discount_rate = discount / 100
    - net_price = unit_price * (1 - discount_rate)
    - revenue = quantity * net_price
    - cost = quantity * cost_per_unit
    - gross_profit = revenue - cost
    - profit_margin = gross_profit / revenue (0 if revenue is 0)
    - net_revenue = revenue - (returns * net_price)
    
    Args:
        df: DataFrame with raw columns.
    
    Returns:
        DataFrame with derived columns added.
    """
    result = df.copy()
    
    if "discount" in result.columns:
        result["discount_rate"] = result["discount"] / 100.0
    else:
        result["discount_rate"] = 0.0
    
    if "unit_price" in result.columns:
        result["net_price"] = (result["unit_price"] * (1 - result["discount_rate"])).round(2)

    if "unit_price" not in result.columns and all(
        col in result.columns for col in ["quantity", "revenue"]
    ):
        result["unit_price"] = np.where(
            result["quantity"] > 0,
            result["revenue"] / result["quantity"],
            np.nan,
        ).round(2)
        result["net_price"] = result["unit_price"]

    if "revenue" not in result.columns and all(
        col in result.columns for col in ["quantity", "net_price"]
    ):
        result["revenue"] = (result["quantity"] * result["net_price"]).round(2)
    
    if all(col in result.columns for col in ["quantity", "cost_per_unit"]):
        result["cost"] = (result["quantity"] * result["cost_per_unit"]).round(2)
    
    if all(col in result.columns for col in ["revenue", "cost"]):
        result["gross_profit"] = (result["revenue"] - result["cost"]).round(2)
    
    if "revenue" in result.columns and "gross_profit" in result.columns:
        result["profit_margin"] = np.where(
            result["revenue"] != 0,
            (result["gross_profit"] / result["revenue"]).round(4),
            0.0
        )
    
    if all(col in result.columns for col in ["revenue", "returned_revenue"]):
        result["net_revenue"] = (
            result["revenue"] - result["returned_revenue"]
        ).round(2)
    elif all(col in result.columns for col in ["revenue", "returns", "net_price"]):
        result["net_revenue"] = (result["revenue"] - result["returns"] * result["net_price"]).round(2)
    
    return result

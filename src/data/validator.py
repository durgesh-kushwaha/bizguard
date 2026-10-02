"""
Data validation module for BizGuard.

Validates uploaded business data against expected schema and quality rules.
Every validation failure includes a clear explanation of:
- What the problem is
- Why it matters
- Expected format
- Suggested fix
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from config.settings import REQUIRED_COLUMNS, NUMERIC_COLUMNS, DATE_COLUMNS


def validate_schema(df: pd.DataFrame) -> List[Dict]:
    """
    Validate that the DataFrame has all required columns.
    
    Returns:
        List of validation issue dicts with keys:
        problem, why_it_matters, expected, suggested_fix, severity
    """
    issues = []
    df_columns = [col.strip().lower() for col in df.columns]
    
    for col in REQUIRED_COLUMNS:
        if col.lower() not in df_columns:
            issues.append({
                "problem": f"Missing required column: '{col}'",
                "why_it_matters": f"The column '{col}' is needed for analytics and decision simulations.",
                "expected": f"Column named '{col}' in the uploaded data.",
                "suggested_fix": f"Add a column named '{col}' to your dataset, or rename an existing similar column.",
                "severity": "error",
            })
    
    return issues


def validate_data_types(df: pd.DataFrame) -> List[Dict]:
    """
    Validate that numeric and date columns have correct types.
    
    Returns:
        List of validation issue dicts.
    """
    issues = []
    
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                converted = pd.to_numeric(df[col], errors="coerce")
                non_numeric_count = int((converted.isna() & df[col].notna()).sum())
                issues.append({
                    "problem": f"Column '{col}' contains non-numeric values ({non_numeric_count} rows).",
                    "why_it_matters": f"'{col}' must be numeric for calculations like revenue, profit, and ML predictions.",
                    "expected": f"Numeric values (integers or decimals) in column '{col}'.",
                    "suggested_fix": f"Check for text entries, special characters, or currency symbols in '{col}' and remove them.",
                    "severity": "error",
                })
            elif not np.isfinite(df[col].dropna()).all():
                issues.append({
                    "problem": f"Column '{col}' contains infinite values.",
                    "why_it_matters": f"Infinite '{col}' values cannot be used reliably in analytics or model training.",
                    "expected": f"Finite numeric values in column '{col}'.",
                    "suggested_fix": f"Replace infinite values in '{col}' with valid numbers or remove those records.",
                    "severity": "error",
                })
    
    for col in DATE_COLUMNS:
        if col in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                try:
                    pd.to_datetime(df[col], errors="raise")
                except (ValueError, TypeError):
                    issues.append({
                        "problem": f"Column '{col}' contains invalid date values.",
                        "why_it_matters": "Date column is required for time-series analytics and forecasting.",
                        "expected": "Dates in format YYYY-MM-DD or similar parseable format.",
                        "suggested_fix": f"Ensure all values in '{col}' are valid dates (e.g., 2024-01-15).",
                        "severity": "error",
                    })
    
    return issues


def validate_data_quality(df: pd.DataFrame) -> List[Dict]:
    """
    Validate data quality: missing values, negatives, impossibilities.
    
    Returns:
        List of validation issue dicts.
    """
    issues = []
    
    if df.empty:
        return [{
            "problem": "The dataset has no rows.",
            "why_it_matters": "Analytics, cleaning, and model training need at least one business record.",
            "expected": "A supported tabular file with column headers and business records.",
            "suggested_fix": "Upload a non-empty dataset or load the sample data.",
            "severity": "error",
        }]

    # Check for missing values
    missing = df.isnull().sum()
    cols_with_missing = missing[missing > 0]
    if len(cols_with_missing) > 0:
        for col, count in cols_with_missing.items():
            pct = round(count / len(df) * 100, 1)
            severity = "error" if pct > 50 else "warning"
            issues.append({
                "problem": f"Column '{col}' has {count} missing values ({pct}%).",
                "why_it_matters": "Missing values can distort analytics and cause ML model failures.",
                "expected": f"Complete data in column '{col}'.",
                "suggested_fix": f"Fill missing values or remove rows with missing '{col}'. The cleaner module will handle this automatically.",
                "severity": severity,
            })
    
    # Check for duplicate rows
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues.append({
            "problem": f"Found {dup_count} duplicate rows.",
            "why_it_matters": "Duplicate rows inflate metrics like total revenue and units sold.",
            "expected": "Unique transaction records.",
            "suggested_fix": "Remove duplicate rows. The cleaner module will handle this.",
            "severity": "warning",
        })
    
    # Check for negative values in columns that shouldn't be negative
    non_negative_cols = ["quantity", "unit_price", "cost_per_unit", "inventory_units"]
    for col in non_negative_cols:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                issues.append({
                    "problem": f"Column '{col}' has {neg_count} negative values.",
                    "why_it_matters": f"Negative {col} values are invalid and will produce incorrect calculations.",
                    "expected": f"Non-negative values in '{col}'.",
                    "suggested_fix": f"Review and correct negative values in '{col}'. They may be data entry errors.",
                    "severity": "error",
                })

    if "discount" in df.columns and pd.api.types.is_numeric_dtype(df["discount"]):
        invalid_discount = ((df["discount"] < 0) | (df["discount"] > 100)).sum()
        if invalid_discount:
            issues.append({
                "problem": f"Column 'discount' has {invalid_discount} values outside 0–100.",
                "why_it_matters": "Discounts are percentages and values outside this range create invalid prices.",
                "expected": "A percentage from 0 to 100 in each row.",
                "suggested_fix": "Check whether discounts use a different scale and convert them to percentages.",
                "severity": "error",
            })

    if {"returns", "quantity"}.issubset(df.columns) and all(
        pd.api.types.is_numeric_dtype(df[col]) for col in ("returns", "quantity")
    ):
        excessive_returns = (df["returns"] > df["quantity"]).sum()
        if excessive_returns:
            issues.append({
                "problem": f"Returns exceed quantity in {excessive_returns} rows.",
                "why_it_matters": "A transaction cannot return more units than it sold.",
                "expected": "Returns between 0 and the sold quantity for each row.",
                "suggested_fix": "Review the affected transaction records and correct the return counts.",
                "severity": "error",
            })
    
    # Check for zero prices
    if "unit_price" in df.columns and pd.api.types.is_numeric_dtype(df["unit_price"]):
        zero_price = (df["unit_price"] == 0).sum()
        if zero_price > 0:
            issues.append({
                "problem": f"{zero_price} rows have zero unit price.",
                "why_it_matters": "Zero-priced items distort revenue and margin calculations.",
                "expected": "Positive unit prices for all products.",
                "suggested_fix": "Check if zero prices are intentional (free samples) or errors.",
                "severity": "warning",
            })
    
    # Check minimum row count
    if len(df) < 50:
        issues.append({
            "problem": f"Dataset has only {len(df)} rows.",
            "why_it_matters": "Too few rows for reliable analytics and ML model training.",
            "expected": "At least 100 rows for basic analytics, 500+ for ML.",
            "suggested_fix": "Use a larger dataset or the built-in sample data.",
            "severity": "warning",
        })
    
    return issues


def validate_dataset(df: pd.DataFrame) -> Dict:
    """
    Run all validations and return a comprehensive report.
    
    Args:
        df: DataFrame to validate.
    
    Returns:
        Dict with keys:
        - is_valid: bool (True if no errors)
        - errors: list of error issues
        - warnings: list of warning issues  
        - summary: text summary
    """
    schema_issues = validate_schema(df)
    type_issues = validate_data_types(df)
    quality_issues = validate_data_quality(df)
    
    all_issues = schema_issues + type_issues + quality_issues
    
    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]
    
    is_valid = len(errors) == 0
    
    if is_valid and len(warnings) == 0:
        summary = "\u2705 Data validation passed. No issues found."
    elif is_valid:
        summary = f"\u26a0\ufe0f Data validation passed with {len(warnings)} warning(s). Data can be processed."
    else:
        summary = f"\u274c Data validation failed with {len(errors)} error(s) and {len(warnings)} warning(s)."
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
        "total_issues": len(all_issues),
    }

"""
Data loading module for BizGuard.

Loads common business-table formats and normalizes their columns.
"""

import pandas as pd
from pathlib import Path
import re
from typing import Tuple
from src.data.column_mapping import map_business_columns

SUPPORTED_FILE_TYPES = ["csv", "tsv", "xlsx", "xls", "json", "jsonl", "ndjson", "parquet"]


def _file_suffix(file_path) -> str:
    if isinstance(file_path, (str, Path)):
        return Path(file_path).suffix.lower()
    return Path(getattr(file_path, "name", "")).suffix.lower()


def _metadata(df: pd.DataFrame, file_type: str,
              column_mappings=None, uncertain_columns=None) -> dict:
    return {
        "rows_loaded": len(df),
        "columns_loaded": len(df.columns),
        "column_names": list(df.columns),
        "file_type": file_type,
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "column_mappings": column_mappings or [],
        "uncertain_columns": uncertain_columns or [],
    }


def _prepare_loaded_data(df: pd.DataFrame, file_type: str) -> Tuple[pd.DataFrame, dict]:
    df = _normalize_columns(df)
    df, mappings, uncertain = map_business_columns(df)
    df = _parse_date_column(df)
    return df, _metadata(df, file_type, mappings, uncertain)


def _parse_date_column(df: pd.DataFrame) -> pd.DataFrame:
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim column names and make their casing consistent."""
    result = df.copy()
    result.columns = [str(column).strip().lower() for column in result.columns]
    duplicates = result.columns[result.columns.duplicated()].tolist()
    if duplicates:
        names = ", ".join(sorted(set(duplicates)))
        raise ValueError(f"Column names are duplicated after trimming and lowercasing: {names}.")
    return result


def load_csv(file_path) -> Tuple[pd.DataFrame, dict]:
    """
    Load a CSV file and return the DataFrame with loading metadata.
    
    Args:
        file_path: Path to CSV file or file-like object (from Streamlit uploader).
    
    Returns:
        Tuple of (DataFrame, metadata dict with loading stats).
    
    Raises:
        ValueError: If the file cannot be read as CSV.
    """
    try:
        df = pd.read_csv(file_path)
        return _prepare_loaded_data(df, "CSV")
    except Exception as e:
        raise ValueError(f"Failed to load CSV file: {str(e)}")


def load_tsv(file_path) -> Tuple[pd.DataFrame, dict]:
    try:
        return _prepare_loaded_data(pd.read_csv(file_path, sep="\t"), "TSV")
    except Exception as e:
        raise ValueError(f"Failed to load TSV file: {str(e)}")


def load_excel(file_path) -> Tuple[pd.DataFrame, dict]:
    """
    Load an Excel file and return the DataFrame with loading metadata.
    
    Args:
        file_path: Path to Excel file or file-like object.
    
    Returns:
        Tuple of (DataFrame, metadata dict).
    
    Raises:
        ValueError: If the file cannot be read as Excel.
    """
    try:
        engine = "xlrd" if _file_suffix(file_path) == ".xls" else "openpyxl"
        return _prepare_loaded_data(pd.read_excel(file_path, engine=engine), "Excel")
    except Exception as e:
        raise ValueError(f"Failed to load Excel file: {str(e)}")


def load_json(file_path) -> Tuple[pd.DataFrame, dict]:
    try:
        df = pd.read_json(file_path, lines=_file_suffix(file_path) in (".jsonl", ".ndjson"))
        return _prepare_loaded_data(df, "JSON")
    except Exception as e:
        raise ValueError(f"Failed to load JSON file: {str(e)}")


def load_parquet(file_path) -> Tuple[pd.DataFrame, dict]:
    try:
        return _prepare_loaded_data(pd.read_parquet(file_path), "Parquet")
    except Exception as e:
        raise ValueError(f"Failed to load Parquet file: {str(e)}")


def load_sample_data() -> Tuple[pd.DataFrame, dict]:
    """
    Load the built-in sample dataset.
    
    Returns:
        Tuple of (DataFrame, metadata dict).
    
    Raises:
        FileNotFoundError: If sample data file doesn't exist.
    """
    sample_path = Path(__file__).parent.parent.parent / "data" / "sample" / "business_data.csv"
    
    if not sample_path.exists():
        # Generate it on the fly
        from src.data.generator import save_sample_dataset
        save_sample_dataset()
    
    return load_csv(sample_path)


def load_file(file_path, file_type: str = "auto") -> Tuple[pd.DataFrame, dict]:
    """
    Load a data file, auto-detecting format if needed.
    
    Args:
        file_path: Path or file-like object.
    file_type: A supported format name or 'auto' (detect from extension).
    
    Returns:
        Tuple of (DataFrame, metadata dict).
    """
    suffix = _file_suffix(file_path)
    if file_type == "auto":
        file_type = suffix.lstrip(".").lower()

    if file_type == "excel":
        return load_excel(file_path)
    if file_type == "csv":
        return load_csv(file_path)
    if file_type == "tsv":
        return load_tsv(file_path)
    if file_type in ("xls", "xlsx"):
        return load_excel(file_path)
    if file_type in ("json", "jsonl", "ndjson"):
        return load_json(file_path)
    if file_type == "parquet":
        return load_parquet(file_path)

    supported = ", ".join(f".{suffix}" for suffix in SUPPORTED_FILE_TYPES)
    raise ValueError(f"Unsupported file type. Choose one of: {supported}.")


def load_business_files(file_paths) -> Tuple[pd.DataFrame, dict]:
    """Load sales reports together and attach matching return rows by order ID."""
    file_paths = list(file_paths)
    if not file_paths:
        raise ValueError("Choose at least one business data file.")

    loaded = []
    for file_path in file_paths:
        df, metadata = load_file(file_path)
        name = getattr(file_path, "name", None) or Path(file_path).name
        is_return = (
            "cancel_return_date" in df.columns
            or re.search(r"return|refund", name, flags=re.IGNORECASE) is not None
        )
        loaded.append({"name": name, "df": df, "metadata": metadata, "is_return": is_return})

    sales_files = [item for item in loaded if not item["is_return"]]
    return_files = [item for item in loaded if item["is_return"]]
    if not sales_files:
        raise ValueError("Select at least one sales report with its return report.")

    from config.settings import OPTIONAL_COLUMNS, REQUIRED_COLUMNS

    expected = set(REQUIRED_COLUMNS) | (set(OPTIONAL_COLUMNS) & set(sales_files[0]["df"].columns))
    for item in sales_files[1:]:
        fields = set(REQUIRED_COLUMNS) | (set(OPTIONAL_COLUMNS) & set(item["df"].columns))
        if fields != expected:
            raise ValueError(
                "The selected sales reports have different business columns. "
                "Upload matching sales exports together, or load them separately."
            )

    sales_df = pd.concat([item["df"] for item in sales_files], ignore_index=True, sort=False)
    mappings = []
    uncertain = []
    for item in loaded:
        mappings.extend(
            {**mapping, "source_file": item["name"]}
            for mapping in item["metadata"].get("column_mappings", [])
        )
        uncertain.extend(
            {**column, "source_file": item["name"]}
            for column in item["metadata"].get("uncertain_columns", [])
        )

    return_summary = None
    if return_files:
        returns_df = pd.concat([item["df"] for item in return_files], ignore_index=True, sort=False)
        return_summary = _attach_returns(sales_df, returns_df, return_files)

    metadata = {
        "rows_loaded": len(sales_df),
        "columns_loaded": len(sales_df.columns),
        "column_names": list(sales_df.columns),
        "file_type": "Multiple files" if len(loaded) > 1 else loaded[0]["metadata"]["file_type"],
        "memory_usage_mb": round(sales_df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "column_mappings": mappings,
        "uncertain_columns": uncertain,
        "source_files": [item["name"] for item in loaded],
        "return_summary": return_summary,
    }
    return sales_df, metadata


def _attach_returns(sales_df: pd.DataFrame, returns_df: pd.DataFrame, return_files: list) -> dict:
    """Link reported returns to one unambiguous sales row; leave other returns unmatched."""
    summary = {
        "files": [item["name"] for item in return_files],
        "rows": len(returns_df),
        "matched_rows": 0,
        "unmatched_rows": len(returns_df),
        "matched_orders": 0,
        "return_value": 0.0,
        "matched_value": 0.0,
        "unmatched_value": 0.0,
        "match_note": "",
    }

    if "revenue" in returns_df.columns:
        return_values = pd.to_numeric(returns_df["revenue"], errors="coerce")
        if "unit_price" in returns_df.columns:
            fallback_quantity = returns_df.get("returns", returns_df.get("quantity", 0))
            fallback = (
                pd.to_numeric(returns_df["unit_price"], errors="coerce")
                * pd.to_numeric(fallback_quantity, errors="coerce")
            )
            return_values = return_values.fillna(fallback)
        return_values = return_values.fillna(0)
        summary["return_value"] = round(float(return_values.sum()), 2)
    elif "unit_price" in returns_df.columns and "quantity" in returns_df.columns:
        return_values = (
            pd.to_numeric(returns_df["unit_price"], errors="coerce").fillna(0)
            * pd.to_numeric(returns_df["quantity"], errors="coerce").fillna(0)
        )
        summary["return_value"] = round(float(return_values.sum()), 2)
    else:
        return_values = pd.Series(0.0, index=returns_df.index)

    quantity_column = "returns" if "returns" in returns_df.columns else "quantity"
    if "order_id" not in sales_df.columns or "order_id" not in returns_df.columns:
        summary["match_note"] = "Order IDs are missing, so no return rows were linked to sales."
        summary["unmatched_value"] = summary["return_value"]
        return summary
    if quantity_column not in returns_df.columns:
        summary["match_note"] = "Return quantities are missing, so no return rows were linked to sales."
        summary["unmatched_value"] = summary["return_value"]
        return summary
    if "returns" in sales_df and pd.to_numeric(sales_df["returns"], errors="coerce").fillna(0).gt(0).any():
        summary["match_note"] = (
            "The sales file already contains return quantities, so the separate return report "
            "was not applied to avoid counting them twice."
        )
        summary["unmatched_value"] = summary["return_value"]
        return summary

    sales_keys = sales_df["order_id"].astype("string").str.strip()
    key_counts = sales_keys.dropna().value_counts()
    unique_sales_keys = set(key_counts[key_counts == 1].index)
    return_keys = returns_df["order_id"].astype("string").str.strip()
    matched = return_keys.isin(unique_sales_keys)
    summary["matched_rows"] = int(matched.sum())
    summary["unmatched_rows"] = int((~matched).sum())
    summary["matched_orders"] = int(return_keys[matched].nunique())
    summary["matched_value"] = round(float(return_values[matched].sum()), 2)
    summary["unmatched_value"] = round(float(return_values[~matched].sum()), 2)

    return_quantities = pd.to_numeric(returns_df[quantity_column], errors="coerce").fillna(0)
    adjustments = pd.DataFrame({
        "order_id": return_keys[matched],
        "returns": return_quantities[matched],
        "returned_revenue": return_values[matched],
    })
    adjustments = adjustments.groupby("order_id", dropna=True).sum()

    if "returns" in sales_df.columns:
        sales_df["returns"] = (
            pd.to_numeric(sales_df["returns"], errors="coerce").fillna(0)
        )
    else:
        sales_df["returns"] = 0.0
    if "returned_revenue" in sales_df.columns:
        sales_df["returned_revenue"] = (
            pd.to_numeric(sales_df["returned_revenue"], errors="coerce").fillna(0)
        )
    else:
        sales_df["returned_revenue"] = 0.0
    for index, key in sales_keys.items():
        if key in adjustments.index:
            sales_df.at[index, "returns"] += adjustments.at[key, "returns"]
            sales_df.at[index, "returned_revenue"] += adjustments.at[key, "returned_revenue"]

    if summary["unmatched_rows"]:
        summary["match_note"] = (
            f"{summary['unmatched_rows']} return row(s) did not match a unique order in the sales files. "
            "Their value is excluded from net revenue."
        )
    else:
        summary["match_note"] = "All return rows matched to a unique sales order."
    return summary

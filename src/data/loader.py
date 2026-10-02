"""
Data loading module for BizGuard.

Handles CSV and Excel file loading with basic validation.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple


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
        
        df = _normalize_columns(df)

        # Try to parse date column if it exists
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        metadata = {
            "rows_loaded": len(df),
            "columns_loaded": len(df.columns),
            "column_names": list(df.columns),
            "file_type": "CSV",
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        }
        
        return df, metadata
    
    except Exception as e:
        raise ValueError(f"Failed to load CSV file: {str(e)}")


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
        df = pd.read_excel(file_path, engine="openpyxl")
        df = _normalize_columns(df)
        
        # Try to parse date column if it exists
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        metadata = {
            "rows_loaded": len(df),
            "columns_loaded": len(df.columns),
            "column_names": list(df.columns),
            "file_type": "Excel",
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        }
        
        return df, metadata
    
    except Exception as e:
        raise ValueError(f"Failed to load Excel file: {str(e)}")


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
        file_type: 'csv', 'excel', or 'auto' (detect from extension).
    
    Returns:
        Tuple of (DataFrame, metadata dict).
    """
    if file_type == "auto":
        if isinstance(file_path, (str, Path)):
            ext = Path(file_path).suffix.lower()
            if ext in (".xlsx", ".xls"):
                file_type = "excel"
            else:
                file_type = "csv"
        else:
            # File-like object — try to get name
            name = getattr(file_path, "name", "")
            if name.endswith((".xlsx", ".xls")):
                file_type = "excel"
            else:
                file_type = "csv"
    
    if file_type == "excel":
        return load_excel(file_path)
    else:
        return load_csv(file_path)

"""
Data loading module for BizGuard.

Loads common business-table formats and normalizes their columns.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple

SUPPORTED_FILE_TYPES = ["csv", "tsv", "xlsx", "xls", "json", "jsonl", "ndjson", "parquet"]


def _file_suffix(file_path) -> str:
    if isinstance(file_path, (str, Path)):
        return Path(file_path).suffix.lower()
    return Path(getattr(file_path, "name", "")).suffix.lower()


def _metadata(df: pd.DataFrame, file_type: str) -> dict:
    return {
        "rows_loaded": len(df),
        "columns_loaded": len(df.columns),
        "column_names": list(df.columns),
        "file_type": file_type,
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
    }


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
        df = _normalize_columns(df)
        return _parse_date_column(df), _metadata(df, "CSV")
    except Exception as e:
        raise ValueError(f"Failed to load CSV file: {str(e)}")


def load_tsv(file_path) -> Tuple[pd.DataFrame, dict]:
    try:
        df = _normalize_columns(pd.read_csv(file_path, sep="\t"))
        return _parse_date_column(df), _metadata(df, "TSV")
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
        df = _normalize_columns(pd.read_excel(file_path, engine=engine))
        return _parse_date_column(df), _metadata(df, "Excel")
    except Exception as e:
        raise ValueError(f"Failed to load Excel file: {str(e)}")


def load_json(file_path) -> Tuple[pd.DataFrame, dict]:
    try:
        df = pd.read_json(file_path, lines=_file_suffix(file_path) in (".jsonl", ".ndjson"))
        df = _normalize_columns(df)
        return _parse_date_column(df), _metadata(df, "JSON")
    except Exception as e:
        raise ValueError(f"Failed to load JSON file: {str(e)}")


def load_parquet(file_path) -> Tuple[pd.DataFrame, dict]:
    try:
        df = _normalize_columns(pd.read_parquet(file_path))
        return _parse_date_column(df), _metadata(df, "Parquet")
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

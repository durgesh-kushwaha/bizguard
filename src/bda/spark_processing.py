"""
PySpark data processing pipeline for BizGuard.

Demonstrates big data processing concepts:
- DataFrame creation from Pandas
- Schema definition
- Data transformations
- Cleaning operations
- Derived column computation

This is the core BDA component that shows distributed processing capability.
"""

import pandas as pd
import logging
from typing import Optional, Tuple
from src.bda.spark_session import get_spark_error, get_spark_session, is_spark_available

logger = logging.getLogger(__name__)


def pandas_to_spark(df: pd.DataFrame):
    """
    Convert a Pandas DataFrame to a Spark DataFrame.
    
    Args:
        df: Pandas DataFrame.
    
    Returns:
        Spark DataFrame, or None if Spark is not available.
    """
    spark = get_spark_session()
    if spark is None:
        return None
    
    try:
        # Ensure date column is string for Spark compatibility
        df_copy = df.copy()
        if "date" in df_copy.columns:
            df_copy["date"] = df_copy["date"].astype(str)
        
        spark_df = spark.createDataFrame(df_copy)
        logger.info(f"Created Spark DataFrame: {spark_df.count()} rows, {len(spark_df.columns)} columns")
        return spark_df
    except Exception as e:
        raise RuntimeError(f"Could not convert the uploaded data to a Spark DataFrame: {e}") from e


def spark_to_pandas(spark_df) -> pd.DataFrame:
    """
    Convert a Spark DataFrame back to Pandas.
    
    Args:
        spark_df: Spark DataFrame.
    
    Returns:
        Pandas DataFrame.
    """
    pdf = spark_df.toPandas()
    
    # Convert date back to datetime
    if "date" in pdf.columns:
        pdf["date"] = pd.to_datetime(pdf["date"], errors="coerce")
    
    return pdf


def spark_clean_data(spark_df):
    """
    Perform data cleaning using Spark operations.
    
    Demonstrates:
    - Filtering (removing invalid records)
    - Column casting
    - Null handling
    - Derived column computation
    
    Args:
        spark_df: Input Spark DataFrame.
    
    Returns:
        Cleaned Spark DataFrame.
    """
    from pyspark.sql import functions as F
    from pyspark.sql.types import DoubleType, IntegerType
    
    result = spark_df
    
    # Remove rows with null in critical columns
    result = result.dropna(subset=["product_id", "quantity", "unit_price"])
    
    # Filter out invalid values
    result = result.filter(
        (F.col("quantity") >= 0) &
        (F.col("unit_price") > 0) &
        (F.col("cost_per_unit") >= 0)
    )
    
    # Fill nulls in non-critical columns
    result = result.fillna({
        "discount": 0,
        "returns": 0,
        "marketing_spend": 0,
    })
    
    # Compute derived columns using Spark
    result = result.withColumn(
        "discount_rate", F.col("discount") / 100.0
    ).withColumn(
        "net_price", F.round(F.col("unit_price") * (1 - F.col("discount_rate")), 2)
    ).withColumn(
        "revenue", F.round(F.col("quantity") * F.col("net_price"), 2)
    ).withColumn(
        "cost", F.round(F.col("quantity") * F.col("cost_per_unit"), 2)
    ).withColumn(
        "gross_profit", F.round(F.col("revenue") - F.col("cost"), 2)
    ).withColumn(
        "profit_margin",
        F.when(F.col("revenue") != 0,
               F.round(F.col("gross_profit") / F.col("revenue"), 4))
        .otherwise(0.0)
    ).withColumn(
        "net_revenue",
        F.round(F.col("revenue") - F.col("returns") * F.col("net_price"), 2)
    )
    
    return result


def run_spark_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Run the complete Spark processing pipeline.
    
    Pipeline:
    1. Convert Pandas -> Spark DataFrame
    2. Clean data using Spark operations
    3. Convert back to Pandas
    4. Collect processing metadata
    
    Args:
        df: Input Pandas DataFrame.
    
    Returns:
        Tuple of (processed Pandas DataFrame, processing metadata dict).
        If Spark is not available, returns (original df, metadata with fallback info).
    """
    if not is_spark_available():
        return df, {
            "engine": "Pandas (Spark not available)",
            "status": "Fallback",
            "error": get_spark_error() or "PySpark is not installed.",
            "input_rows": len(df),
            "output_rows": len(df),
            "spark_available": False,
        }
    
    try:
        # Step 1: Convert to Spark
        spark_df = pandas_to_spark(df)
        if spark_df is None:
            return df, {
                "engine": "Pandas (Spark conversion failed)",
                "status": "Fallback",
                "error": get_spark_error() or "Could not start the Spark session. Check Java 17+ and JAVA_HOME.",
                "input_rows": len(df),
                "output_rows": len(df),
                "spark_available": False,
            }
        
        input_count = spark_df.count()
        num_partitions = spark_df.rdd.getNumPartitions()
        
        # Step 2: Clean with Spark
        cleaned_spark = spark_clean_data(spark_df)
        output_count = cleaned_spark.count()
        
        # Step 3: Convert back
        result_df = spark_to_pandas(cleaned_spark)
        
        # Step 4: Metadata
        from src.bda.spark_session import get_spark_info
        spark_info = get_spark_info()
        
        metadata = {
            "engine": "PySpark",
            "status": "Completed",
            "spark_version": spark_info.get("spark_version", "Unknown"),
            "master": spark_info.get("master", "Unknown"),
            "input_rows": input_count,
            "output_rows": output_count,
            "rows_removed": input_count - output_count,
            "partitions": num_partitions,
            "columns_processed": len(result_df.columns),
            "spark_available": True,
            "transformations": [
                "Null removal in critical columns",
                "Invalid value filtering (negative qty/price)",
                "Null filling for optional columns",
                "Discount rate computation",
                "Net price computation",
                "Revenue computation",
                "Cost computation",
                "Gross profit computation",
                "Profit margin computation",
                "Net revenue computation",
            ],
        }
        
        return result_df, metadata
    
    except Exception as e:
        logger.exception("Spark pipeline failed")
        return df, {
            "engine": "Pandas (Spark pipeline failed)",
            "status": "Fallback",
            "error": str(e),
            "input_rows": len(df),
            "output_rows": len(df),
            "spark_available": False,
        }

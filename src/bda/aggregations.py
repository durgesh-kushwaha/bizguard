"""
Business aggregations using PySpark for BizGuard.

Demonstrates big data aggregation concepts:
- groupBy operations
- Multiple aggregation functions
- Window functions
- Date-based transformations
- Cross-dimensional analysis

Each function has a Pandas fallback for environments without Spark.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional
from src.bda.spark_session import get_spark_session, is_spark_available

logger = logging.getLogger(__name__)


def _ensure_spark_df(df):
    """
    Ensure we have a Spark DataFrame. Convert from Pandas if needed.
    Returns None if Spark is not available.
    """
    if not is_spark_available():
        return None
    
    spark = get_spark_session()
    if spark is None:
        return None
    
    # Check if already a Spark DataFrame
    try:
        from pyspark.sql import DataFrame as SparkDataFrame
        if isinstance(df, SparkDataFrame):
            return df
    except ImportError:
        return None
    
    # Convert from Pandas
    try:
        from src.bda.spark_processing import pandas_to_spark
        return pandas_to_spark(df)
    except Exception:
        return None


def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate monthly revenue aggregation.
    
    Uses PySpark if available, falls back to Pandas.
    
    Args:
        df: Business data DataFrame.
    
    Returns:
        DataFrame with columns: year_month, total_revenue, total_profit,
        total_orders, total_units, avg_order_value, profit_margin
    """
    spark_df = _ensure_spark_df(df)
    
    if spark_df is not None:
        try:
            from pyspark.sql import functions as F
            
            result = (
                spark_df
                .withColumn("year_month", F.date_format(F.col("date"), "yyyy-MM"))
                .groupBy("year_month")
                .agg(
                    F.round(F.sum("revenue"), 2).alias("total_revenue"),
                    F.round(F.sum("gross_profit"), 2).alias("total_profit"),
                    F.countDistinct("order_id").alias("total_orders"),
                    F.sum("quantity").alias("total_units"),
                    F.round(F.avg("revenue"), 2).alias("avg_order_value"),
                    F.round(F.avg("profit_margin"), 4).alias("avg_profit_margin"),
                )
                .orderBy("year_month")
            )
            
            return result.toPandas()
        except Exception as e:
            logger.warning(f"Spark monthly_revenue failed, using Pandas: {e}")
    
    # Pandas fallback
    df = df.copy()
    df["year_month"] = pd.to_datetime(df["date"]).dt.to_period("M").astype(str)
    
    result = df.groupby("year_month").agg(
        total_revenue=("revenue", "sum"),
        total_profit=("gross_profit", "sum"),
        total_orders=("order_id", "nunique"),
        total_units=("quantity", "sum"),
        avg_order_value=("revenue", "mean"),
        avg_profit_margin=("profit_margin", "mean"),
    ).round(2).reset_index()
    
    return result.sort_values("year_month")


def product_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate product-level performance metrics.
    
    Args:
        df: Business data DataFrame.
    
    Returns:
        DataFrame with product performance metrics.
    """
    spark_df = _ensure_spark_df(df)
    
    if spark_df is not None:
        try:
            from pyspark.sql import functions as F
            
            result = (
                spark_df
                .groupBy("product_id", "product_name", "category")
                .agg(
                    F.round(F.sum("revenue"), 2).alias("total_revenue"),
                    F.round(F.sum("gross_profit"), 2).alias("total_profit"),
                    F.sum("quantity").alias("total_units"),
                    F.round(F.avg("unit_price"), 2).alias("avg_price"),
                    F.round(F.avg("profit_margin"), 4).alias("avg_margin"),
                    F.round(F.avg("discount"), 2).alias("avg_discount"),
                    F.sum("returns").alias("total_returns"),
                    F.round(F.sum("marketing_spend"), 2).alias("total_marketing"),
                )
                .orderBy(F.desc("total_revenue"))
            )
            
            return result.toPandas()
        except Exception as e:
            logger.warning(f"Spark product_performance failed, using Pandas: {e}")
    
    # Pandas fallback
    result = df.groupby(["product_id", "product_name", "category"]).agg(
        total_revenue=("revenue", "sum"),
        total_profit=("gross_profit", "sum"),
        total_units=("quantity", "sum"),
        avg_price=("unit_price", "mean"),
        avg_margin=("profit_margin", "mean"),
        avg_discount=("discount", "mean"),
        total_returns=("returns", "sum"),
        total_marketing=("marketing_spend", "sum"),
    ).round(2).reset_index()
    
    return result.sort_values("total_revenue", ascending=False)


def category_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate category-level analysis.
    
    Args:
        df: Business data DataFrame.
    
    Returns:
        DataFrame with category metrics.
    """
    spark_df = _ensure_spark_df(df)
    
    if spark_df is not None:
        try:
            from pyspark.sql import functions as F
            
            result = (
                spark_df
                .groupBy("category")
                .agg(
                    F.round(F.sum("revenue"), 2).alias("total_revenue"),
                    F.round(F.sum("gross_profit"), 2).alias("total_profit"),
                    F.sum("quantity").alias("total_units"),
                    F.countDistinct("product_id").alias("num_products"),
                    F.round(F.avg("profit_margin"), 4).alias("avg_margin"),
                    F.round(F.sum("marketing_spend"), 2).alias("total_marketing"),
                    F.sum("returns").alias("total_returns"),
                )
                .orderBy(F.desc("total_revenue"))
            )
            
            return result.toPandas()
        except Exception as e:
            logger.warning(f"Spark category_analysis failed, using Pandas: {e}")
    
    # Pandas fallback
    result = df.groupby("category").agg(
        total_revenue=("revenue", "sum"),
        total_profit=("gross_profit", "sum"),
        total_units=("quantity", "sum"),
        num_products=("product_id", "nunique"),
        avg_margin=("profit_margin", "mean"),
        total_marketing=("marketing_spend", "sum"),
        total_returns=("returns", "sum"),
    ).round(2).reset_index()
    
    return result.sort_values("total_revenue", ascending=False)


def regional_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate region-level analysis.
    
    Args:
        df: Business data DataFrame.
    
    Returns:
        DataFrame with regional metrics.
    """
    spark_df = _ensure_spark_df(df)
    
    if spark_df is not None:
        try:
            from pyspark.sql import functions as F
            
            result = (
                spark_df
                .groupBy("region")
                .agg(
                    F.round(F.sum("revenue"), 2).alias("total_revenue"),
                    F.round(F.sum("gross_profit"), 2).alias("total_profit"),
                    F.sum("quantity").alias("total_units"),
                    F.countDistinct("order_id").alias("total_orders"),
                    F.round(F.avg("profit_margin"), 4).alias("avg_margin"),
                )
                .orderBy(F.desc("total_revenue"))
            )
            
            return result.toPandas()
        except Exception as e:
            logger.warning(f"Spark regional_analysis failed, using Pandas: {e}")
    
    # Pandas fallback
    result = df.groupby("region").agg(
        total_revenue=("revenue", "sum"),
        total_profit=("gross_profit", "sum"),
        total_units=("quantity", "sum"),
        total_orders=("order_id", "nunique"),
        avg_margin=("profit_margin", "mean"),
    ).round(2).reset_index()
    
    return result.sort_values("total_revenue", ascending=False)


def marketing_effectiveness(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate marketing effectiveness metrics.
    
    ROAS = Revenue / Marketing Spend
    
    Note: This shows correlation, not causation.
    Historical ROAS is an association metric.
    
    Args:
        df: Business data DataFrame.
    
    Returns:
        DataFrame with marketing metrics per category.
    """
    spark_df = _ensure_spark_df(df)
    
    if spark_df is not None:
        try:
            from pyspark.sql import functions as F
            
            result = (
                spark_df
                .filter(F.col("marketing_spend") > 0)
                .groupBy("category")
                .agg(
                    F.round(F.sum("revenue"), 2).alias("total_revenue"),
                    F.round(F.sum("marketing_spend"), 2).alias("total_marketing"),
                    F.round(F.sum("gross_profit"), 2).alias("total_profit"),
                )
                .withColumn(
                    "roas",
                    F.when(F.col("total_marketing") > 0,
                           F.round(F.col("total_revenue") / F.col("total_marketing"), 2))
                    .otherwise(0)
                )
                .withColumn(
                    "profit_per_marketing_dollar",
                    F.when(F.col("total_marketing") > 0,
                           F.round(F.col("total_profit") / F.col("total_marketing"), 2))
                    .otherwise(0)
                )
                .orderBy(F.desc("roas"))
            )
            
            return result.toPandas()
        except Exception as e:
            logger.warning(f"Spark marketing_effectiveness failed, using Pandas: {e}")
    
    # Pandas fallback
    mkt_df = df[df["marketing_spend"] > 0].copy()
    result = mkt_df.groupby("category").agg(
        total_revenue=("revenue", "sum"),
        total_marketing=("marketing_spend", "sum"),
        total_profit=("gross_profit", "sum"),
    ).round(2).reset_index()
    
    result["roas"] = np.where(
        result["total_marketing"] > 0,
        (result["total_revenue"] / result["total_marketing"]).round(2),
        0
    )
    result["profit_per_marketing_dollar"] = np.where(
        result["total_marketing"] > 0,
        (result["total_profit"] / result["total_marketing"]).round(2),
        0
    )
    
    return result.sort_values("roas", ascending=False)


def inventory_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze inventory levels vs sales velocity.
    
    Calculates:
    - Average inventory
    - Average daily sales
    - Stock cover (days of inventory remaining at current sales rate)
    - Inventory concentration
    
    Args:
        df: Business data DataFrame.
    
    Returns:
        DataFrame with inventory metrics per product.
    """
    # Pandas implementation (Spark adds limited value for this computation)
    result = df.groupby(["product_id", "product_name", "category"]).agg(
        avg_inventory=("inventory_units", "mean"),
        avg_daily_sales=("quantity", "mean"),
        total_units_sold=("quantity", "sum"),
        total_revenue=("revenue", "sum"),
        avg_cost=("cost_per_unit", "mean"),
    ).round(2).reset_index()
    
    # Stock cover in days
    result["stock_cover_days"] = np.where(
        result["avg_daily_sales"] > 0,
        (result["avg_inventory"] / result["avg_daily_sales"]).round(1),
        np.inf
    )
    
    # Capital locked in inventory
    result["inventory_capital"] = (result["avg_inventory"] * result["avg_cost"]).round(2)
    
    # Sales velocity classification
    median_velocity = result["avg_daily_sales"].median()
    result["velocity_class"] = np.where(
        result["avg_daily_sales"] >= median_velocity * 1.5, "High",
        np.where(result["avg_daily_sales"] >= median_velocity * 0.5, "Medium", "Low")
    )
    
    return result.sort_values("total_units_sold", ascending=False)

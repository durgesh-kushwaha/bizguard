"""Checks for business KPIs and the Spark processing path."""

import pandas as pd
import pytest

from src.bda.analytics import compute_kpis


def test_compute_kpis_handles_empty_data():
    empty = pd.DataFrame(columns=["revenue", "gross_profit", "order_id", "quantity"])

    assert compute_kpis(empty) == {
        "total_revenue": 0,
        "total_profit": 0,
        "num_orders": 0,
        "units_sold": 0,
        "avg_order_value": None,
        "profit_margin": None,
    }


def test_compute_kpis_uses_order_count_for_average_order_value():
    sales = pd.DataFrame({
        "revenue": [100.0, 50.0, 25.0],
        "gross_profit": [20.0, 10.0, 5.0],
        "order_id": ["A", "A", "B"],
        "quantity": [2, 1, 1],
    })

    result = compute_kpis(sales)
    assert result["num_orders"] == 2
    assert result["avg_order_value"] == 87.5
    assert result["profit_margin"] == 0.2


def test_partial_marketplace_data_keeps_unavailable_metrics_blank():
    from src.bda.aggregations import (
        category_analysis,
        inventory_analysis,
        marketing_effectiveness,
        monthly_revenue,
        product_performance,
        regional_analysis,
    )

    sales = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-31", "2026-02-01"]),
        "order_id": ["A1", "A2"],
        "quantity": [1, 2],
        "revenue": [100.0, 250.0],
        "category": ["610910", "610910"],
        "region": ["Delhi", "Delhi"],
    })

    kpis = compute_kpis(sales)
    monthly = monthly_revenue(sales)
    by_category = category_analysis(sales)
    by_region = regional_analysis(sales)

    assert kpis["total_revenue"] == 350.0
    assert kpis["total_profit"] is None
    assert monthly["total_revenue"].tolist() == [100.0, 250.0]
    assert "total_profit" not in monthly.columns
    assert by_category.loc[0, "total_units"] == 3
    assert by_region.loc[0, "total_revenue"] == 350.0
    assert product_performance(sales).empty
    assert marketing_effectiveness(sales).empty
    assert inventory_analysis(sales).empty


def test_monthly_revenue_shows_sales_after_matched_returns():
    from src.bda.aggregations import monthly_revenue

    sales = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-10", "2026-01-11"]),
        "revenue": [100.0, 50.0],
        "net_revenue": [75.0, 50.0],
        "quantity": [1, 1],
    })

    monthly = monthly_revenue(sales)

    assert monthly.loc[0, "total_revenue"] == 150
    assert monthly.loc[0, "total_net_revenue"] == 125


def test_spark_pipeline_computes_business_columns():
    pytest.importorskip("pyspark")
    from src.bda.spark_processing import run_spark_pipeline
    from src.bda.spark_session import get_spark_session, stop_spark_session

    spark = get_spark_session()
    if spark is None:
        pytest.skip("A working local Spark runtime is not available")

    data = pd.DataFrame({
        "date": ["2024-01-01"],
        "product_id": ["P1"],
        "quantity": [2],
        "unit_price": [10.0],
        "cost_per_unit": [4.0],
        "discount": [0.0],
        "returns": [0],
        "marketing_spend": [1.0],
    })

    try:
        processed, metadata = run_spark_pipeline(data)
        assert metadata["engine"] == "PySpark"
        assert metadata["input_rows"] == 1
        assert metadata["output_rows"] == 1
        assert processed.loc[0, "revenue"] == 20.0
        assert processed.loc[0, "gross_profit"] == 12.0
    finally:
        stop_spark_session()


def test_spark_unavailable_reports_fallback_reason(monkeypatch):
    from src.bda import spark_processing

    monkeypatch.setattr(spark_processing, "is_spark_available", lambda: False)
    monkeypatch.setattr(spark_processing, "get_spark_error", lambda: "Java was not found")
    data = pd.DataFrame({"quantity": [1]})

    unchanged, metadata = spark_processing.run_spark_pipeline(data)
    assert unchanged.equals(data)
    assert metadata["status"] == "Fallback"
    assert metadata["error"] == "Java was not found"


def test_spark_conversion_failure_is_reported(monkeypatch):
    from src.bda import spark_processing

    class BrokenSpark:
        def createDataFrame(self, _):
            raise ValueError("unsupported column type")

    monkeypatch.setattr(spark_processing, "get_spark_session", lambda: BrokenSpark())
    data = pd.DataFrame({"quantity": [1]})

    unchanged, metadata = spark_processing.run_spark_pipeline(data)
    assert unchanged.equals(data)
    assert metadata["status"] == "Fallback"
    assert "unsupported column type" in metadata["error"]

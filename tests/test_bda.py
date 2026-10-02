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
        "avg_order_value": 0,
        "profit_margin": 0,
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

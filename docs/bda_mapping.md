# BDA Academic Mapping — BizGuard

This document maps BizGuard's implementation to Big Data Analytics (BDA) course concepts.

| BDA Concept | BizGuard Implementation | Files |
|---|---|---|
| Data Ingestion | CSV/Excel file loading with validation | `src/data/loader.py` |
| Data Preprocessing | Schema validation, cleaning, missing value handling | `src/data/validator.py`, `src/data/cleaner.py` |
| Distributed Processing | PySpark DataFrame operations | `src/bda/spark_processing.py` |
| Data Transformation | Derived column computation, type casting | `src/bda/spark_processing.py` |
| Aggregation | GroupBy operations, multi-level aggregations | `src/bda/aggregations.py` |
| Window Functions | Rolling calculations for time-series | `src/data/feature_engineering.py` |
| Analytics | Business KPI computation, trend analysis | `src/bda/analytics.py` |
| Visualization | Interactive Plotly charts | `ui/analytics.py`, `ui/overview.py` |
| Scalable Architecture | Spark processing layer designed for scale | `src/bda/spark_session.py` |

## PySpark Operations Demonstrated

1. **DataFrame Creation** — Converting Pandas to Spark DataFrames
2. **Filtering** — Removing invalid records
3. **Column Operations** — Derived column computation using `withColumn`
4. **GroupBy Aggregations** — Revenue, profit, and quantity aggregations
5. **Multiple Aggregation Functions** — `sum`, `avg`, `count`, `countDistinct`
6. **Ordering** — `orderBy` for sorted results
7. **Null Handling** — `dropna`, `fillna`
8. **Type Casting** — Column type conversions
9. **Conditional Columns** — `when/otherwise` expressions
10. **Date Operations** — `date_format` for temporal grouping

## Processing Pipeline

```
Raw CSV/Excel → Pandas DataFrame → Spark DataFrame → 
Cleaning → Transformation → Aggregation → 
Analytical Output → Visualization
```

## Honest Statement

The prototype uses PySpark to demonstrate distributed-data-processing concepts.
The architecture is designed to scale to larger datasets.
The sample dataset (~15,000 rows) is relatively small for true big data processing,
but the processing pipeline demonstrates the same concepts that would apply
to datasets of millions of rows.

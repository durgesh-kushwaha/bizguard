# AGENT HANDOFF — BizGuard

**Last Updated:** 2026-10-02

## CURRENT PHASE
Phases 0-9 are complete. Optional screenshots are deferred.

## CURRENT TASK
No required project task remains. The app is available at `http://localhost:8517`.

## LAST COMPLETED TASK
- Completed UI and data hardening, BDA test coverage, and documentation review
- 52/52 tests passing, including file-format and local PySpark coverage
- App responds at `http://localhost:8517`

## CURRENT FILES BEING MODIFIED
None — clean state.

## WHAT WORKS
- Data loading (CSV, TSV, XLS/XLSX, JSON/JSON Lines, Parquet, sample data)
- Direct desktop/mobile upload from Overview and Data Explorer, with validation and cleaning in Data Explorer
- Data validation with detailed error reporting
- Data cleaning with documented rules
- Feature engineering (temporal, lag, rolling, business features)
- PySpark processing pipeline with Pandas fallback
- Business aggregations (monthly, product, category, regional, marketing)
- KPI computation and business signal detection
- ML training (Linear Regression + Random Forest)
- ML evaluation (MAE, RMSE, R²)
- Demand forecasting
- Decision simulation (pricing, inventory, marketing)
- Multi-scenario analysis (Conservative/Expected/Optimistic)
- Decision contracts with assumptions, risks, monitoring
- SQLite decision persistence
- Streamlit UI with 7 pages
- 52 tests passing
- Streamlit Community Cloud uses Pandas by default; install `requirements-spark.txt` and Java 17 only for local Spark demonstrations
- Phone-width upload picker verified; supports CSV, TSV, XLS/XLSX, JSON/JSONL/NDJSON, and Parquet
- Upload headers are normalized; ambiguous duplicate columns are rejected
- Empty data and invalid numeric/business values receive validation errors
- Replacing a dataset clears dependent cleaning, Spark, forecast, and model results

## WHAT DOES NOT WORK
- Nothing known to be broken
- PySpark requires Java to be installed (falls back to Pandas if unavailable)

## LAST SUCCESSFUL TEST
`python -m pytest tests/ -q` — 52 passed (2026-10-02)

## CURRENT ERROR
None.

## NEXT EXACT ACTION
No required action. Capture screenshots of the main workflows if presentation materials are needed.

## BLOCKERS
None.

## IMPORTANT DECISIONS
- Using Streamlit (not React) for UI
- Using PySpark for BDA demonstration (Pandas fallback)
- Using scikit-learn (Linear Regression + Random Forest) for ML
- Using SQLite for decision persistence
- Synthetic dataset (13,077 rows) for demo purposes
- Target variable: quantity (sales/demand prediction)
- Sample data has 16 products, 4 categories, 4 regions, 21 months
- The existing layout is the user's preferred baseline; preserve it in follow-up work

## DO NOT REPEAT
- Do not add React, Angular, or complex frontend frameworks
- Do not add authentication/payment systems
- Do not over-engineer with microservices
- Do not redesign the Streamlit navigation
- Do not replace the working architecture
- Do not re-generate sample data (it's already created)

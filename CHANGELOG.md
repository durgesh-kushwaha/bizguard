# CHANGELOG — BizGuard

## [Unreleased]

### 2026-10-02 — UI Polish and Hardening
- **fix:** Make CSV/Excel upload available from the Overview screen, including after data is loaded
- **fix:** Normalize uploaded column names and reject duplicate normalized headers
- **fix:** Validate empty datasets, infinite numeric values, discount bounds, and return counts
- **fix:** Clear stale analysis results when the source dataset changes
- **fix:** Avoid reloading an unchanged Streamlit upload during page interactions
- **test:** Add BDA KPI and PySpark pipeline coverage; full suite passes (44 tests)
- **docs:** Update setup and project status to reflect the verified build

### 2026-10-02 — Initial Build
- **feat:** Initialized project repository structure
- **feat:** Created configuration and settings module
- **feat:** Created synthetic business dataset generator (13,077 rows)
- **feat:** Built data loading module (CSV, Excel, sample data)
- **feat:** Built data validation module (schema, types, quality checks)
- **feat:** Built data cleaning module (duplicates, missing values, derived columns)
- **feat:** Built feature engineering module (temporal, lag, rolling, business features)
- **feat:** Built PySpark session management with graceful fallback
- **feat:** Built PySpark processing pipeline (clean, transform, derive)
- **feat:** Built business aggregations (monthly, product, category, regional, marketing)
- **feat:** Built business analytics with KPIs and signal detection
- **feat:** Built ML preprocessing (feature selection, train/test split)
- **feat:** Built Linear Regression baseline model
- **feat:** Built Random Forest Regressor model
- **feat:** Built model evaluation module (MAE, RMSE, R², comparison)
- **feat:** Built demand forecasting with future feature construction
- **feat:** Built pricing decision simulator with elasticity estimation
- **feat:** Built inventory decision simulator
- **feat:** Built marketing decision simulator with ROAS
- **feat:** Built scenario analysis (Conservative/Expected/Optimistic)
- **feat:** Built decision contract system
- **feat:** Built SQLite persistence layer for decisions
- **feat:** Built Streamlit app with 7-page navigation
- **feat:** Built Overview page (KPIs, trends, business signals)
- **feat:** Built Data Explorer page (upload, validate, clean, Spark)
- **feat:** Built Analytics page (revenue, products, marketing, inventory, regional)
- **feat:** Built Forecasting page (train, evaluate, forecast)
- **feat:** Built Decision Simulator page (pricing, inventory, marketing)
- **feat:** Built Decision History page (view, compare, delete)
- **feat:** Built About page
- **docs:** Created README, BDA mapping, IML mapping, data dictionary
- **docs:** Created ML methodology, decision engine, demo flow, future scope
- **docs:** Created project state management files (9 files)
- **test:** Created 36 tests (data, ML, decisions, utils) — all passing

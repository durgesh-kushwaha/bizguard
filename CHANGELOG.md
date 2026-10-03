# CHANGELOG — BizGuard

## [Unreleased]

### 2026-10-03 — Multi-File Sales and Returns
- **fix:** Prepare valid uploads on load so Overview shows analytics immediately
- **feat:** Accept multiple reports from Overview and Data Explorer
- **fix:** Link return quantities and value only to unique sales order IDs; disclose unmatched returns and exclude them from net revenue
- **feat:** Show net revenue after matched returns in overview and monthly analytics
- **fix:** Explain when there is too little history for model training or a demand forecast
- **test:** Cover paired reports, multi-file controls, and invalid-upload navigation; full suite passes (72 tests)

### 2026-10-03 — Marketplace Column Recognition
- **fix:** Map common marketplace headers, including order dates, sub-order IDs, taxable sales, and delivery states
- **fix:** Keep unknown columns, reject ambiguous matches, and allow sales data without optional cost or product fields
- **fix:** Leave unavailable profit and product metrics blank instead of reporting misleading zeroes
- **docs:** Explain automatic header matching in the upload instructions
- **test:** Cover marketplace aliases, near-typos, optional fields, and partial analytics; full suite passes (66 tests)

### 2026-10-03 — Decision History Workflow
- **fix:** Keep successful pricing, inventory, and marketing simulations available after Streamlit reruns so the save form can submit
- **fix:** Verify saved decisions by reading them back; report storage failures separately from an empty history
- **feat:** Persist historical evidence and display expected-versus-actual metric comparisons
- **fix:** Validate update/delete targets and report missing records instead of silently succeeding
- **test:** Cover the full simulation, save, retrieve, update, compare, and delete workflow using a temporary SQLite database
- **docs:** Clarify that Streamlit Community Cloud does not guarantee local SQLite persistence across restarts or redeployments

### 2026-10-03 — Daily Forecast Accuracy
- **fix:** Forecast daily totals rather than per-transaction quantities so forecast and history share units
- **feat:** Select Random Forest, Gradient Boosting, or weekly seasonal-naive forecasts using rolling-origin WAPE
- **feat:** Compare Extra Trees and Histogram Gradient Boosting alongside existing transaction-model candidates
- **fix:** Invalidate saved forecasts and trained models from older session revisions
- **fix:** Use chronological holdouts, date-grouped boundaries, shifted rolling features, and remove target-derived predictors
- **test:** Add forecast-scale, product-scope, and time-split regression coverage

### 2026-10-02 — Stable Cloud Dependencies
- **fix:** Remove PySpark and Java from the Streamlit Cloud install so the app starts on the working Pandas path
- **docs:** Keep PySpark available as an optional local dependency via `requirements-spark.txt`

### 2026-10-02 — Streamlit Cloud Spark Runtime
- **fix:** Install Java 17 in Streamlit Community Cloud for PySpark startup
- **fix:** Show a warning and the recorded failure reason when Spark falls back to Pandas
- **fix:** Detect Java from `PATH` when `JAVA_HOME` is unset and lower Spark driver memory to 1 GB
- **test:** Cover unavailable Spark and DataFrame conversion failures

### 2026-10-02 — Mobile and Tabular Upload Formats
- **feat:** Accept CSV, TSV, XLS/XLSX, JSON, JSON Lines, and Parquet business data files
- **fix:** Read legacy `.xls` workbooks with the correct engine
- **test:** Verify file-format loaders and the upload picker at a phone-sized viewport; full suite passes (50 tests)

### 2026-10-02 — UI Polish and Hardening
- **fix:** Make CSV/Excel upload available from the Overview screen, including after data is loaded
- **fix:** Normalize uploaded column names and reject duplicate normalized headers
- **fix:** Validate empty datasets, infinite numeric values, discount bounds, and return counts
- **fix:** Clear stale analysis results when the source dataset changes
- **fix:** Avoid reloading an unchanged Streamlit upload during page interactions
- **test:** Add BDA KPI and PySpark pipeline coverage; full suite passes (44 tests at that checkpoint)
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

# ARCHITECTURE — BizGuard

## System Overview

BizGuard is a Business Decision Intelligence System that follows this pipeline:

```
Business Data → Data Ingestion → Data Cleaning → Big Data Processing →
Descriptive/Diagnostic Analytics → ML Prediction → Decision Simulation →
Business Recommendation → Decision Tracking
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.9+ |
| UI Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Big Data | PySpark |
| Machine Learning | scikit-learn |
| Visualization | Plotly |
| Database | SQLite |
| Version Control | Git |

## Architecture Layers

### 1. Data Layer (`src/data/`)
- **loader.py** — CSV/Excel file loading
- **validator.py** — Schema and data quality validation
- **cleaner.py** — Data cleaning and preprocessing
- **feature_engineering.py** — Derived feature computation

### 2. BDA Layer (`src/bda/`)
- **spark_session.py** — PySpark session management
- **spark_processing.py** — Spark DataFrame transformations
- **aggregations.py** — Business aggregations (groupBy, window functions)
- **analytics.py** — KPI computation and trend analysis

### 3. ML Layer (`src/ml/`)
- **preprocessing.py** — ML-specific feature preparation
- **train.py** — Model training (Linear Regression, Random Forest)
- **predict.py** — Prediction and forecasting
- **evaluate.py** — Model evaluation (MAE, RMSE, R²)
- **model_utils.py** — Model persistence and utilities

### 4. Decision Layer (`src/decisions/`)
- **pricing.py** — Pricing scenario simulation
- **inventory.py** — Inventory decision simulation
- **marketing.py** — Marketing spend simulation
- **scenarios.py** — Multi-scenario generation
- **decision_engine.py** — Orchestration and decision contracts

### 5. Storage Layer (`src/storage/`)
- **database.py** — SQLite operations for decision persistence

### 6. UI Layer (`ui/`)
- **overview.py** — Business performance overview
- **data_explorer.py** — Data upload and exploration
- **analytics.py** — Business analytics and charts
- **forecasting.py** — ML forecast visualization
- **decisions.py** — Decision simulator interface
- **history.py** — Decision history and tracking

### 7. Application Entry Point
- **app.py** — Streamlit main app with sidebar navigation

## Data Flow

```
CSV/Excel Upload
    ↓
Validation & Cleaning (Pandas)
    ↓
Spark Processing (PySpark)
    ↓
Analytics & KPIs
    ↓
ML Feature Engineering
    ↓
Model Training & Prediction
    ↓
Decision Simulation
    ↓
SQLite Persistence
```

## Key Design Principles
1. **Separation of Concerns** — Business logic separate from UI
2. **Readability** — Code understandable by B.Tech students
3. **Testability** — Modular functions with clear inputs/outputs
4. **Explainability** — Every calculation has documented formulas
5. **Persistence** — Project state survives session interruptions

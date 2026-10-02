# 🛡️ BizGuard — Business Decision Intelligence System

> **"Test the decision before you make it."**

BizGuard is a Big Data Analytics + Machine Learning based Business Decision Intelligence System that helps businesses make data-driven decisions with confidence.

## 🎯 What Does BizGuard Do?

BizGuard answers four critical business questions:

| # | Question | How |
|---|----------|-----|
| 1 | **What happened?** | BDA analytics & KPIs |
| 2 | **What is likely to happen?** | ML demand prediction |
| 3 | **What if I change something?** | Decision simulation |
| 4 | **What should I watch?** | Monitoring triggers |

## ✨ Key Features

### 📊 Business Analytics
- Revenue, profit, and margin analytics
- Product performance analysis
- Marketing effectiveness (ROAS)
- Inventory analysis with stock cover
- Regional performance breakdown
- Automated business signal detection

### ⚡ Big Data Processing
- PySpark-powered data pipeline
- Distributed processing demonstration
- Aggregations, transformations, and KPIs
- Scalable architecture for larger datasets

### 🧠 Machine Learning
- Demand/sales prediction
- Linear Regression (baseline) + Random Forest
- Model comparison with MAE, RMSE, R²
- Feature importance visualization
- Future demand forecasting

### 🧪 Decision Simulator
- **Pricing:** What happens if I change product price?
- **Inventory:** Should I purchase additional stock?
- **Marketing:** What’s the ROI of changing ad spend?
- Multi-scenario analysis (Conservative / Expected / Optimistic)
- Transparent assumptions and risk assessment
- Decision contracts with monitoring triggers

### 📋 Decision History
- Save and track past decisions
- Compare expected vs actual outcomes
- Build organizational decision memory

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| UI Framework | Streamlit |
| Data Processing | Pandas, NumPy |
| Big Data | PySpark 4.x (Java 17+) |
| Machine Learning | scikit-learn |
| Visualization | Plotly |
| Database | SQLite |
| Version Control | Git |

## 📁 Project Structure

```
bizguard/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── config/settings.py        # Configuration
├── data/sample/              # Sample dataset
├── src/
│   ├── data/                 # Data loading, validation, cleaning
│   ├── bda/                  # PySpark processing & analytics
│   ├── ml/                   # ML models & prediction
│   ├── decisions/            # Decision simulators
│   ├── storage/              # SQLite persistence
│   └── utils/                # Utilities
├── ui/                       # Streamlit UI pages
├── tests/                    # Test suite
├── docs/                     # Documentation
└── database/                 # SQLite database
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Java 17 or newer (required for PySpark 4.x)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd BizGuard

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The application opens at `http://localhost:8501`.

## 📖 How to Use

### 1. Load Data
- Go to **Data Explorer** → Click "Load Sample Dataset"
- Or upload your own CSV, TSV, Excel, JSON, JSON Lines, or Parquet business data file from desktop or mobile

Supported uploads are structured business tables (`.csv`, `.tsv`, `.xls`, `.xlsx`, `.json`, `.jsonl`, `.ndjson`, `.parquet`). PDFs, images, and other document formats are not accepted.

### 2. Clean & Process
- Review data quality report
- Click "Clean & Preprocess Data"
- Run Spark Processing (demonstrates BDA)

### 3. View Analytics
- **Overview** → KPIs and business signals
- **Analytics** → Revenue, products, marketing, inventory

### 4. Train ML Models
- Go to **Forecast** → Click "Train ML Models"
- Review evaluation metrics
- Generate demand forecast

### 5. Test a Decision
- Go to **Test a Decision**
- Choose: Pricing / Inventory / Marketing
- Enter parameters → Analyze Impact
- Review scenarios, assumptions, and risks
- Save the decision

### 6. Track Decisions
- Go to **Decision History**
- Review past decisions
- Record actual outcomes for comparison

## 🏫 Academic Context

This project demonstrates concepts from:

### Big Data Analytics (BDA)
- Structured data ingestion and validation
- PySpark distributed processing pipeline
- GroupBy aggregations and transformations
- Business KPI computation
- Interactive visualizations

See [`docs/bda_mapping.md`](docs/bda_mapping.md) for detailed mapping.

### Introduction to Machine Learning (IML)
- Feature engineering (temporal, lag, rolling features)
- Supervised learning (regression)
- Train/test split and model validation
- Model comparison (Linear Regression vs Random Forest)
- Evaluation metrics (MAE, RMSE, R²)
- Feature importance analysis

See [`docs/iml_mapping.md`](docs/iml_mapping.md) for detailed mapping.

## 📊 Dataset

The sample dataset contains **~13,000 synthetic business transactions** with:
- 16 products across 4 categories
- 4 regions (North, South, East, West)
- 21 months of data (Jan 2024 – Sep 2025)
- Seasonal patterns, price variation, and marketing effects

⚠️ **This is synthetic demo data**, NOT real business data.

## ⚠️ Limitations

- **Prototype application** — not production-ready
- **Synthetic data** — real data would improve ML predictions
- **Price elasticity** — estimated via correlation, not causal analysis
- **ROAS** — shows association, does not prove marketing caused revenue
- **ML models** — simplified feature sets, may not generalize
- **Small dataset** — PySpark demonstrates concepts but dataset is small for true big data

## 🔮 Future Scope

- Shopify/Amazon API integration
- Real-time data pipelines
- Advanced ML (time series, causal inference)
- Cloud deployment
- Multi-user authentication
- Automated decision monitoring

See [`docs/future_scope.md`](docs/future_scope.md) for details.

## 🧑💻 Development

### Running Tests
```bash
python -m pytest tests/ -v
```

### Project State
See `PROJECT_STATE.md`, `TASKS.md`, and `AGENT_HANDOFF.md` for current development status.

---

*Built as an academic project demonstrating Big Data Analytics and Machine Learning concepts for business decision intelligence.*

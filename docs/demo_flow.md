# Demo Flow — BizGuard

Step-by-step guide for demonstrating BizGuard.

## 1. Start the Application
```bash
streamlit run app.py
```

## 2. Load Data (Data Explorer)
- Click "Load Sample Dataset"
- Show the data quality report
- Click "Clean & Preprocess Data"
- Run Spark Processing (shows BDA component)

## 3. View Overview
- Show KPI cards (revenue, profit, orders)
- Show trend charts
- Show business signals

## 4. Explore Analytics
- Revenue analytics tab
- Product performance
- Marketing effectiveness (mention ROAS is correlation)
- Inventory analysis
- Regional breakdown

## 5. Train ML Models (Forecast)
- Click "Train ML Models"
- Show training progress
- Review model evaluation metrics
- Compare Linear Regression vs Random Forest
- Show feature importance
- Generate a forecast

## 6. Test a Decision
- Select "Pricing" → Pick a product → Change price
- Show scenario comparison
- Show assumptions and risks
- Save the decision

## 7. Decision History
- Show saved decision
- Explain Decision Contract concept

## Key Talking Points
- BDA: PySpark processing, aggregations, analytics
- IML: Feature engineering, model training, evaluation
- Product: Decision simulation with transparency
- All numbers are computed, never hardcoded

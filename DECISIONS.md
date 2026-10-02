# DECISIONS — BizGuard

## Decision 1: UI Framework
- **Decision:** Use Streamlit instead of React/Angular
- **Context:** Limited development timeline (25 days), developer has beginner web knowledge
- **Options Considered:** React, Angular, Flask+HTML, Streamlit
- **Chosen Option:** Streamlit
- **Reason:** Python-first, rapid prototyping, built-in data visualization support
- **Trade-offs:** Less flexible frontend, limited customization

## Decision 2: Big Data Framework
- **Decision:** Use PySpark for BDA component
- **Context:** Project requires demonstrating big data processing concepts
- **Options Considered:** PySpark, Dask, Vaex
- **Chosen Option:** PySpark
- **Reason:** Industry standard, academic relevance, maps directly to BDA curriculum
- **Trade-offs:** Overhead for small datasets, but demonstrates scalable architecture

## Decision 3: ML Framework
- **Decision:** Use scikit-learn with Linear Regression + Random Forest
- **Context:** Need academically defensible ML that student can explain in viva
- **Options Considered:** scikit-learn, TensorFlow, XGBoost
- **Chosen Option:** scikit-learn (Linear Regression + Random Forest Regressor)
- **Reason:** Explainable, well-documented, maps to IML curriculum
- **Trade-offs:** May not achieve highest accuracy, but prioritizes explainability

## Decision 4: Database
- **Decision:** Use SQLite for decision persistence
- **Context:** Need lightweight local persistence for decision history
- **Options Considered:** SQLite, PostgreSQL, JSON files
- **Chosen Option:** SQLite
- **Reason:** Zero configuration, file-based, Python stdlib support
- **Trade-offs:** Not suitable for multi-user production, but appropriate for prototype

## Decision 5: ML Target Variable
- **Decision:** Predict quantity (sales/demand) as primary target
- **Context:** Need meaningful prediction target for business decisions
- **Options Considered:** quantity, revenue, profit
- **Chosen Option:** quantity (aggregated as monthly/weekly sales)
- **Reason:** Directly actionable for inventory/pricing/marketing decisions
- **Trade-offs:** Revenue prediction might seem more intuitive, but quantity drives the decision simulators

## Decision 6: Sample Data
- **Decision:** Use synthetic generated dataset (~10,000+ rows)
- **Context:** Need realistic data with discoverable patterns
- **Options Considered:** Public datasets, synthetic generation
- **Chosen Option:** Synthetic generation with embedded patterns
- **Reason:** Can control seasonality, trends, and correlations needed for demo
- **Trade-offs:** Not real business data — documented as synthetic

## Decision 7: Decision History Storage
- **Decision:** Keep SQLite as the app's local decision-history store
- **Context:** The save workflow bug was caused by Streamlit reruns clearing the simulator result, not by SQLite failing to commit records.
- **Options Considered:** Retain SQLite, introduce a hosted database
- **Chosen Option:** Retain SQLite and make the save flow survive reruns and verify writes by reading them back
- **Reason:** This fixes the confirmed workflow defect without adding credentials or infrastructure the project does not have.
- **Trade-offs:** Streamlit Community Cloud does not guarantee local-file persistence across restarts or redeployments. Durable cloud history requires a separately configured remote database.

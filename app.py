"""
BizGuard — Business Decision Intelligence System

Main Streamlit application entry point.
Provides sidebar navigation and page routing.

Run with: streamlit run app.py
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import APP_NAME, APP_VERSION, PAGE_ICON, LAYOUT

# Page configuration — must be the first Streamlit command
st.set_page_config(
    page_title=APP_NAME,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded",
)


def main():
    """Main application with sidebar navigation."""
    
    # Custom CSS for consistent styling
    st.markdown("""
    <style>
    /* Clean card-like metric containers */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 12px 16px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebarContent"] { padding-top: 1rem; }
    
    /* Section headers */
    .section-header {
        color: #1f2937;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    /* Signal cards */
    .signal-card {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"## {PAGE_ICON} {APP_NAME}")
        st.caption(f"Business Decision Intelligence • v{APP_VERSION}")
        st.markdown("---")
        
        page = st.radio(
            "Navigate",
            [
                "📊 Overview",
                "📁 Data Explorer",
                "📈 Analytics",
                "🔮 Forecast",
                "🧪 Test a Decision",
                "📋 Decision History",
                "ℹ️ About",
            ],
            label_visibility="collapsed",
        )
        
        st.markdown("---")
        
        # Data status indicator
        if "df" in st.session_state and st.session_state.df is not None:
            st.success(f"✅ Data loaded: {len(st.session_state.df):,} rows")
        else:
            st.info("📁 No data loaded. Go to Data Explorer.")
    
    # Initialize session state
    if "df" not in st.session_state:
        st.session_state.df = None
    if "cleaned_df" not in st.session_state:
        st.session_state.cleaned_df = None
    if "spark_metadata" not in st.session_state:
        st.session_state.spark_metadata = None
    if "models" not in st.session_state:
        st.session_state.models = None
    if "model_evaluations" not in st.session_state:
        st.session_state.model_evaluations = None
    if "feature_cols" not in st.session_state:
        st.session_state.feature_cols = None
    if "ml_df" not in st.session_state:
        st.session_state.ml_df = None
    
    # Page routing
    if page == "📊 Overview":
        from ui.overview import render
        render()
    elif page == "📁 Data Explorer":
        from ui.data_explorer import render
        render()
    elif page == "📈 Analytics":
        from ui.analytics import render
        render()
    elif page == "🔮 Forecast":
        from ui.forecasting import render
        render()
    elif page == "🧪 Test a Decision":
        from ui.decisions import render
        render()
    elif page == "📋 Decision History":
        from ui.history import render
        render()
    elif page == "ℹ️ About":
        render_about()


def render_about():
    """Render the About page."""
    st.title("ℹ️ About BizGuard")
    
    st.markdown("""
    ## What is BizGuard?
    
    BizGuard is a **Business Decision Intelligence System** that helps you:
    
    1. **Understand** your business performance through analytics
    2. **Predict** future demand using machine learning
    3. **Test** business decisions before making them
    4. **Track** decisions and compare expected vs actual outcomes
    
    ### Core Idea
    > *"Test the decision before you make it."*
    
    ### Technology Stack
    
    | Component | Technology |
    |-----------|------------|
    | Language | Python 3.9+ |
    | UI | Streamlit |
    | Data Processing | Pandas, PySpark |
    | Machine Learning | scikit-learn |
    | Visualization | Plotly |
    | Database | SQLite |
    
    ### Academic Context
    
    This project was developed for:
    - **BDA** (Big Data Analytics) — Demonstrates PySpark processing, aggregations, and analytics
    - **IML** (Introduction to Machine Learning) — Demonstrates supervised learning, model training, and evaluation
    
    ### Dataset
    
    The sample dataset is **synthetic demo data** generated for demonstration purposes.
    It does NOT represent real business data.
    
    ### Limitations
    
    - Prototype-level application, not production-ready
    - Uses synthetic data — real business data would improve predictions
    - ML models use simplified feature sets
    - Price elasticity estimation uses correlation, not causal analysis
    - ROAS is an association metric, not a causal measure
    
    ---
    
    *Built as an academic project demonstrating Big Data Analytics and Machine Learning concepts.*
    """)


if __name__ == "__main__":
    main()

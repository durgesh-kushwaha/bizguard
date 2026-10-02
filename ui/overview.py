"""
Overview page for BizGuard.

Displays top-level business KPIs, trends, and business signals.
Every metric is computed from actual data — nothing is fabricated.
"""

import logging

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.data.loader import SUPPORTED_FILE_TYPES, load_file
from src.utils.formatting import format_currency, format_number, format_percentage, severity_emoji

logger = logging.getLogger(__name__)


def render():
    """Render the Overview page."""
    st.title("📊 Business Overview")
    st.caption("Real-time view of your business performance based on uploaded data.")

    if st.session_state.get("cleaned_df") is None:
        st.markdown("### Upload your business data")
        st.caption("Choose a business data file from your device or a connected file provider.")
        uploaded_file = st.file_uploader(
            "Choose a business data file",
            type=SUPPORTED_FILE_TYPES,
            key="overview_data_upload",
        )
        _load_uploaded_file(uploaded_file)
    else:
        with st.expander("Upload or replace dataset"):
            uploaded_file = st.file_uploader(
                "Choose a business data file",
                type=SUPPORTED_FILE_TYPES,
                key="overview_data_upload",
            )
            _load_uploaded_file(uploaded_file)
    
    # Check if data is loaded
    if st.session_state.get("cleaned_df") is None:
        st.markdown("Or try the built-in synthetic dataset:")
        
        # Offer to load sample data
        if st.button("🚀 Load Sample Data to Get Started"):
            _load_sample_data()
            st.rerun()
        return
    
    df = st.session_state.cleaned_df
    
    # Compute KPIs
    from src.bda.analytics import compute_kpis, detect_business_signals
    kpis = compute_kpis(df)
    
    # KPI Cards Row
    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Revenue", format_currency(kpis["total_revenue"]))
    with col2:
        st.metric("Total Profit", format_currency(kpis["total_profit"]))
    with col3:
        st.metric("Orders", format_number(kpis["num_orders"]))
    with col4:
        st.metric("Units Sold", format_number(kpis["units_sold"]))
    with col5:
        st.metric("Avg Order Value", format_currency(kpis["avg_order_value"]))
    with col6:
        st.metric("Profit Margin", format_percentage(kpis["profit_margin"]))
    
    st.markdown("---")
    
    # Trends
    from src.bda.aggregations import monthly_revenue, product_performance, category_analysis
    
    monthly = monthly_revenue(df)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### Revenue & Profit Trend")
        if len(monthly) > 0:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly["year_month"], y=monthly["total_revenue"],
                mode="lines+markers", name="Revenue",
                line=dict(color="#2563eb", width=2),
            ))
            fig.add_trace(go.Scatter(
                x=monthly["year_month"], y=monthly["total_profit"],
                mode="lines+markers", name="Profit",
                line=dict(color="#16a34a", width=2),
            ))
            fig.update_layout(
                height=350, margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="Month", yaxis_title="Amount (₹)",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Not enough data for trend analysis.")
    
    with col_right:
        st.markdown("### Monthly Sales Volume")
        if len(monthly) > 0 and "total_units" in monthly.columns:
            fig = px.bar(
                monthly, x="year_month", y="total_units",
                color_discrete_sequence=["#7c3aed"],
            )
            fig.update_layout(
                height=350, margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="Month", yaxis_title="Units Sold",
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Top Products and Categories
    col_left2, col_right2 = st.columns(2)
    
    with col_left2:
        st.markdown("### Top Products by Revenue")
        products = product_performance(df)
        if len(products) > 0:
            top_products = products.head(8)
            fig = px.bar(
                top_products, x="total_revenue", y="product_name",
                orientation="h", color="category",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(
                height=350, margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="Revenue (₹)", yaxis_title="",
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col_right2:
        st.markdown("### Revenue by Category")
        categories = category_analysis(df)
        if len(categories) > 0:
            fig = px.pie(
                categories, values="total_revenue", names="category",
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.4,
            )
            fig.update_layout(
                height=350, margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Business Signals
    st.markdown("### 🔔 Business Signals")
    st.caption("Automatically detected patterns and trends from your data. Every signal is based on actual calculations.")
    
    signals = detect_business_signals(df)
    
    if signals:
        for signal in signals:
            emoji = severity_emoji(signal["severity"])
            with st.expander(f"{emoji} {signal['title']}", expanded=signal["severity"] == "warning"):
                st.markdown(f"**What:** {signal['what']}")
                st.markdown(f"**Evidence:** {signal['why']}")
                st.markdown(f"**So what:** {signal['so_what']}")
    else:
        st.info("No significant business signals detected. This may be due to insufficient data or stable business conditions.")


def _load_sample_data():
    """Load the sample dataset into session state."""
    try:
        from src.data.loader import load_sample_data
        from src.data.cleaner import clean_dataset
        from ui.session_state import clear_analysis_results
        
        df, metadata = load_sample_data()
        clear_analysis_results(st.session_state)
        st.session_state.df = df
        
        cleaned_df, cleaning_report = clean_dataset(df)
        st.session_state.cleaned_df = cleaned_df
        st.session_state.loading_metadata = metadata
        st.session_state.cleaning_report = cleaning_report
        st.session_state.uploaded_file_signature = None
        
    except Exception as e:
        st.error(f"Failed to load sample data: {e}")


def _load_uploaded_file(uploaded_file):
    """Load a selected file once and clear results from the previous dataset."""
    if uploaded_file is None:
        return

    signature = (
        uploaded_file.name,
        uploaded_file.size,
        getattr(uploaded_file, "file_id", None),
    )
    if signature == st.session_state.get("overview_upload_signature"):
        return

    try:
        df, metadata = load_file(uploaded_file)
        from ui.session_state import clear_analysis_results

        clear_analysis_results(st.session_state)
        st.session_state.df = df
        st.session_state.loading_metadata = metadata
        st.session_state.overview_upload_signature = signature
        st.success(f"Loaded {metadata['rows_loaded']:,} rows. Open Data Explorer to validate and clean the file.")
        st.rerun()
    except ValueError as error:
        st.error(f"Could not load this file: {error}")
    except Exception:
        logger.exception("Could not load business data from the Overview page")
        st.error("Could not load this file. Check that it is a supported, readable business data file.")

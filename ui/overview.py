"""
Overview page for BizGuard.

Displays top-level business KPIs, trends, and business signals.
Every metric is computed from actual data — nothing is fabricated.
"""

import logging

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from src.data.loader import SUPPORTED_FILE_TYPES
from src.utils.formatting import format_currency, format_number, format_percentage, severity_emoji
from ui.session_state import prepare_uploaded_files

logger = logging.getLogger(__name__)


def render():
    """Render the Overview page."""
    st.title("📊 Business Overview")
    st.caption("Real-time view of your business performance based on uploaded data.")

    if st.session_state.get("cleaned_df") is None:
        st.markdown("### Upload your business data")
        st.caption("Choose one or more business reports from your device.")
        uploaded_files = st.file_uploader(
            "Choose business data files",
            type=SUPPORTED_FILE_TYPES,
            accept_multiple_files=True,
            help="Select one or more related reports. Choose sales and returns together to match them by order ID.",
            key="overview_data_upload",
        )
        _load_uploaded_files(uploaded_files, "overview_upload_signature")
    else:
        with st.expander("Upload or replace dataset"):
            uploaded_files = st.file_uploader(
                "Choose business data files",
                type=SUPPORTED_FILE_TYPES,
                accept_multiple_files=True,
                help="Select one or more related reports. Choose sales and returns together to match them by order ID.",
                key="overview_data_upload",
            )
            _load_uploaded_files(uploaded_files, "overview_upload_signature")
    
    # Check if data is loaded
    if st.session_state.get("cleaned_df") is None:
        if st.session_state.get("df") is not None:
            st.warning("The upload needs a quick review before BizGuard can analyze it.")
            if st.button("Review upload in Data Explorer"):
                st.session_state["_requested_page"] = "📁 Data Explorer"
                st.rerun()
            return

        st.markdown("Or try the built-in synthetic dataset:")
        
        # Offer to load sample data
        if st.button("🚀 Load Sample Data to Get Started"):
            _load_sample_data()
            st.rerun()
        return
    
    df = st.session_state.cleaned_df
    return_summary = st.session_state.get("loading_metadata", {}).get("return_summary")
    if return_summary:
        matched_value = format_currency(return_summary["matched_value"])
        st.info(
            f"Return report: {return_summary['rows']:,} rows, "
            f"{return_summary['matched_rows']:,} linked to sales. "
            f"Matched return value: {matched_value}; "
            f"reported return value: {format_currency(return_summary['return_value'])}."
        )
        if return_summary["unmatched_rows"]:
            st.warning(return_summary["match_note"])
    
    # Compute KPIs
    from src.bda.analytics import compute_kpis, detect_business_signals
    kpis = compute_kpis(df)
    
    # KPI Cards Row
    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    def show_metric(value, formatter):
        return "Not available" if value is None else formatter(value)
    
    with col1:
        revenue_label = "Gross Revenue" if "net_revenue" in df.columns else "Total Revenue"
        st.metric(revenue_label, format_currency(kpis["total_revenue"]))
    with col2:
        st.metric("Total Profit", show_metric(kpis["total_profit"], format_currency))
    with col3:
        st.metric("Orders", show_metric(kpis["num_orders"], format_number))
    with col4:
        st.metric("Units Sold", format_number(kpis["units_sold"]))
    with col5:
        st.metric("Avg Order Value", show_metric(kpis["avg_order_value"], format_currency))
    with col6:
        st.metric("Profit Margin", show_metric(kpis["profit_margin"], format_percentage))

    if "net_revenue" in df.columns:
        st.metric("Net Revenue After Matched Returns", format_currency(df["net_revenue"].sum()))
    
    st.markdown("---")
    
    # Trends
    from src.bda.aggregations import monthly_revenue, product_performance, category_analysis
    
    monthly = monthly_revenue(df)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        has_profit = "total_profit" in monthly.columns
        if "total_net_revenue" in monthly.columns:
            trend_title = "Gross & Net Revenue Trend"
        else:
            trend_title = "Revenue & Profit Trend" if has_profit else "Revenue Trend"
        st.markdown(f"### {trend_title}")
        if len(monthly) > 0:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly["year_month"], y=monthly["total_revenue"],
                mode="lines+markers", name="Revenue",
                line=dict(color="#2563eb", width=2),
            ))
            if has_profit:
                fig.add_trace(go.Scatter(
                    x=monthly["year_month"], y=monthly["total_profit"],
                    mode="lines+markers", name="Profit",
                    line=dict(color="#16a34a", width=2),
                ))
            if "total_net_revenue" in monthly.columns:
                fig.add_trace(go.Scatter(
                    x=monthly["year_month"], y=monthly["total_net_revenue"],
                    mode="lines+markers", name="Net Revenue",
                    line=dict(color="#dc2626", width=2),
                ))
            fig.update_layout(
                height=350, margin=dict(l=0, r=0, t=30, b=0),
                xaxis_title="Month", yaxis_title="Amount (₹)",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)
            if not has_profit:
                st.caption("Profit is unavailable because this upload has no unit-cost field.")
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
        else:
            st.info("Product charts need product IDs, names, categories, sales, and unit counts.")
    
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
        
    except Exception as e:
        st.error(f"Failed to load sample data: {e}")


def _load_uploaded_files(uploaded_files, signature_key):
    """Load a selected report set once and prepare it for the dashboard."""
    if not uploaded_files:
        return

    try:
        validation = prepare_uploaded_files(uploaded_files, st.session_state, signature_key)
        if validation is None:
            return
        if validation["is_valid"]:
            summary = st.session_state.loading_metadata.get("return_summary")
            files = len(st.session_state.loading_metadata.get("source_files", []))
            st.success(
                f"Loaded {st.session_state.loading_metadata['rows_loaded']:,} sales rows "
                f"from {files} file(s) and prepared the data."
            )
            if summary and summary["unmatched_rows"]:
                st.warning(summary["match_note"])
        else:
            st.error("The file loaded, but validation found issues. Open Data Explorer to review them.")
    except ValueError as error:
        st.error(f"Could not load this file: {error}")
    except Exception:
        logger.exception("Could not load business data from the Overview page")
        st.error("Could not load this file. Check that it is a supported, readable business data file.")

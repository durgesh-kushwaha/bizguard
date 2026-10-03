"""
Analytics page for BizGuard.

Displays detailed business analytics with interactive charts.
All metrics are computed from actual data.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.utils.formatting import format_currency, format_number, format_percentage


def render():
    """Render the Analytics page."""
    st.title("📈 Business Analytics")
    st.caption("Deep dive into your business data with interactive visualizations.")
    
    if st.session_state.get("cleaned_df") is None:
        st.info("👈 Load and clean your data in the **Data Explorer** page first.")
        return
    
    df = st.session_state.cleaned_df
    
    # Analytics tabs
    tab_revenue, tab_product, tab_marketing, tab_inventory, tab_regional = st.tabs([
        "💰 Revenue", "📦 Products", "📢 Marketing", "🏭 Inventory", "🗺️ Regional"
    ])
    
    with tab_revenue:
        _render_revenue_analytics(df)
    
    with tab_product:
        _render_product_analytics(df)
    
    with tab_marketing:
        _render_marketing_analytics(df)
    
    with tab_inventory:
        _render_inventory_analytics(df)
    
    with tab_regional:
        _render_regional_analytics(df)


def _render_revenue_analytics(df: pd.DataFrame):
    """Render revenue analytics."""
    st.markdown("### Revenue Analytics")
    st.caption("How is revenue trending over time?")
    
    from src.bda.aggregations import monthly_revenue
    monthly = monthly_revenue(df)
    
    if len(monthly) == 0:
        st.warning("Not enough data for revenue analytics.")
        return
    
    # Revenue trend with profit margin overlay
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=monthly["year_month"], y=monthly["total_revenue"],
        name="Revenue", marker_color="#2563eb", opacity=0.7,
    ))
    if "total_profit" in monthly.columns:
        fig.add_trace(go.Bar(
            x=monthly["year_month"], y=monthly["total_profit"],
            name="Profit", marker_color="#16a34a", opacity=0.7,
        ))
    else:
        st.caption("Profit is unavailable because this upload has no unit-cost field.")

    if "total_net_revenue" in monthly.columns:
        fig.add_trace(go.Scatter(
            x=monthly["year_month"], y=monthly["total_net_revenue"],
            name="Net Revenue After Returns", mode="lines+markers",
            line=dict(color="#dc2626", width=2),
        ))
    
    if "avg_profit_margin" in monthly.columns:
        fig.add_trace(go.Scatter(
            x=monthly["year_month"],
            y=monthly["avg_profit_margin"] * monthly["total_revenue"].max(),
            name="Margin Trend (scaled)",
            mode="lines+markers",
            line=dict(color="#dc2626", width=2, dash="dot"),
            yaxis="y2",
        ))
    
    fig.update_layout(
        height=400,
        barmode="group",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Monthly summary table
    with st.expander("📊 Monthly Summary Table"):
        display_monthly = monthly.copy()
        if "total_revenue" in display_monthly.columns:
            display_monthly["total_revenue"] = display_monthly["total_revenue"].apply(lambda x: format_currency(x))
        if "total_profit" in display_monthly.columns:
            display_monthly["total_profit"] = display_monthly["total_profit"].apply(lambda x: format_currency(x))
        if "total_net_revenue" in display_monthly.columns:
            display_monthly["total_net_revenue"] = display_monthly["total_net_revenue"].apply(format_currency)
        st.dataframe(display_monthly, use_container_width=True, hide_index=True)


def _render_product_analytics(df: pd.DataFrame):
    """Render product performance analytics."""
    st.markdown("### Product Performance")
    st.caption("Which products drive the most value?")
    
    from src.bda.aggregations import product_performance
    products = product_performance(df)
    
    if len(products) == 0:
        st.warning("No product data available.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Revenue by Product")
        fig = px.bar(
            products.head(10), x="total_revenue", y="product_name",
            orientation="h", color="category",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(
            height=400, yaxis=dict(autorange="reversed"),
            xaxis_title="Total Revenue (₹)", yaxis_title="",
        )
        st.plotly_chart(fig, use_container_width=True)

    if "avg_margin" in products.columns:
        with col2:
            st.markdown("#### Profit Margin by Product")
            fig = px.bar(
                products.head(10), x="avg_margin", y="product_name",
                orientation="h", color="category",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(
                height=400, yaxis=dict(autorange="reversed"),
                xaxis_title="Average Margin", yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)
    
    if "avg_margin" in products.columns:
        st.markdown("#### Revenue vs Margin (Product Portfolio)")
        st.caption("Ideally, products should be in the top-right quadrant (high revenue + high margin).")

        fig = px.scatter(
            products, x="total_revenue", y="avg_margin",
            size="total_units", color="category",
            hover_name="product_name",
            color_discrete_sequence=px.colors.qualitative.Set2,
            size_max=40,
        )
        fig.update_layout(
            height=400,
            xaxis_title="Total Revenue (₹)",
            yaxis_title="Average Profit Margin",
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Product table
    with st.expander("📊 Product Details Table"):
        st.dataframe(products, use_container_width=True, hide_index=True)


def _render_marketing_analytics(df: pd.DataFrame):
    """Render marketing effectiveness analytics."""
    st.markdown("### Marketing Effectiveness")
    st.caption("How efficiently is marketing spend generating revenue?")
    
    st.info(
        "⚠️ **Note:** ROAS (Return on Ad Spend) shows the historical *association* between "
        "marketing spend and revenue. It does not prove that marketing *caused* the revenue. "
        "Many other factors influence sales."
    )
    
    from src.bda.aggregations import marketing_effectiveness
    mkt = marketing_effectiveness(df)
    
    if len(mkt) == 0:
        st.warning("No marketing spend data available.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ROAS by Category")
        fig = px.bar(
            mkt, x="category", y="roas",
            color="category",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(
            height=350, xaxis_title="Category", yaxis_title="ROAS (x)",
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Marketing Spend vs Revenue")
        fig = px.scatter(
            mkt, x="total_marketing", y="total_revenue",
            size="roas", color="category",
            hover_name="category",
            color_discrete_sequence=px.colors.qualitative.Set2,
            size_max=40,
        )
        fig.update_layout(
            height=350,
            xaxis_title="Total Marketing Spend (₹)",
            yaxis_title="Total Revenue (₹)",
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 Marketing Details"):
        st.dataframe(mkt, use_container_width=True, hide_index=True)


def _render_inventory_analytics(df: pd.DataFrame):
    """Render inventory analytics."""
    st.markdown("### Inventory Analysis")
    st.caption("How are inventory levels compared to sales velocity?")
    
    from src.bda.aggregations import inventory_analysis
    inv = inventory_analysis(df)
    
    if len(inv) == 0:
        st.warning("No inventory data available.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Stock Cover (Days)")
        # Filter out infinite values
        inv_display = inv[inv["stock_cover_days"] != float('inf')].copy()
        if len(inv_display) > 0:
            fig = px.bar(
                inv_display.sort_values("stock_cover_days", ascending=False).head(10),
                x="stock_cover_days", y="product_name",
                orientation="h", color="velocity_class",
                color_discrete_map={"High": "#16a34a", "Medium": "#eab308", "Low": "#dc2626"},
            )
            fig.update_layout(
                height=400, yaxis=dict(autorange="reversed"),
                xaxis_title="Days of Stock Cover", yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Sales Velocity Classification")
        velocity_counts = inv["velocity_class"].value_counts().reset_index()
        velocity_counts.columns = ["Velocity", "Count"]
        fig = px.pie(
            velocity_counts, values="Count", names="Velocity",
            color="Velocity",
            color_discrete_map={"High": "#16a34a", "Medium": "#eab308", "Low": "#dc2626"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("📊 Inventory Details"):
        st.dataframe(inv, use_container_width=True, hide_index=True)


def _render_regional_analytics(df: pd.DataFrame):
    """Render regional analytics."""
    st.markdown("### Regional Analysis")
    st.caption("How does performance vary across regions?")
    
    from src.bda.aggregations import regional_analysis
    regions = regional_analysis(df)
    
    if len(regions) == 0:
        st.warning("No regional data available.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Revenue by Region")
        fig = px.bar(
            regions, x="region", y="total_revenue",
            color="region",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(
            height=350, xaxis_title="Region", yaxis_title="Total Revenue (₹)",
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if "avg_margin" in regions.columns:
        with col2:
            st.markdown("#### Profit Margin by Region")
            fig = px.bar(
                regions, x="region", y="avg_margin",
                color="region",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(
                height=350, xaxis_title="Region", yaxis_title="Average Margin",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        with col2:
            st.info("Profit margin needs a unit-cost field.")
    
    with st.expander("📊 Regional Details"):
        st.dataframe(regions, use_container_width=True, hide_index=True)

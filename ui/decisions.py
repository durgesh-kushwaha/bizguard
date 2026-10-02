"""
Decision simulator page for BizGuard.

The central product feature — "Test Your Decision."
Allows users to simulate pricing, inventory, and marketing decisions.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.utils.formatting import format_currency, format_number, format_percentage, format_change_pct


def render():
    """Render the Decision Simulator page."""
    st.title("🧪 Test a Business Decision")
    st.caption('"Test the decision before you make it." — Simulate pricing, inventory, and marketing changes.')
    
    if st.session_state.get("cleaned_df") is None:
        st.info("👈 Load and clean your data in the **Data Explorer** page first.")
        return
    
    df = st.session_state.cleaned_df
    
    # Decision type selector
    decision_type = st.radio(
        "What type of decision do you want to test?",
        ["💰 Pricing", "📦 Inventory", "📢 Marketing"],
        horizontal=True,
    )
    
    st.markdown("---")
    
    if decision_type == "💰 Pricing":
        _render_pricing_simulator(df)
    elif decision_type == "📦 Inventory":
        _render_inventory_simulator(df)
    elif decision_type == "📢 Marketing":
        _render_marketing_simulator(df)


def _render_pricing_simulator(df: pd.DataFrame):
    """Render the pricing decision simulator."""
    st.markdown("### 💰 Pricing Simulator")
    st.caption("What happens if you change a product's price?")
    
    # Product selection
    if "product_id" not in df.columns:
        st.error("Product ID column not found in data.")
        return
    
    products = df.groupby(["product_id", "product_name"]).agg(
        current_price=("unit_price", "mean"),
        avg_daily_qty=("quantity", "mean"),
    ).reset_index()
    
    product_options = {f"{row['product_name']} ({row['product_id']})": row["product_id"] 
                       for _, row in products.iterrows()}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_product_label = st.selectbox("Select Product", list(product_options.keys()))
        product_id = product_options[selected_product_label]
        product_row = products[products["product_id"] == product_id].iloc[0]
    
    with col2:
        current_price = st.number_input(
            "Current Price (₹)",
            value=float(round(product_row["current_price"], 2)),
            min_value=0.01,
            step=10.0,
        )
    
    with col3:
        proposed_price = st.number_input(
            "Proposed Price (₹)",
            value=float(round(product_row["current_price"] * 1.1, 2)),
            min_value=0.01,
            step=10.0,
        )
    
    if st.button("🔍 Analyze Pricing Impact", type="primary"):
        with st.spinner("Simulating pricing scenarios..."):
            from src.decisions.pricing import simulate_pricing
            
            # Get ML forecast if available
            forecast_demand = _get_forecast_demand(df, product_id)
            
            result = simulate_pricing(df, product_id, current_price, proposed_price, forecast_demand)
            
            if "error" in result:
                st.error(result["error"])
            else:
                _display_decision_result(result, "Pricing")


def _render_inventory_simulator(df: pd.DataFrame):
    """Render the inventory decision simulator."""
    st.markdown("### 📦 Inventory Simulator")
    st.caption("Should you purchase additional inventory?")
    
    if "product_id" not in df.columns:
        st.error("Product ID column not found in data.")
        return
    
    products = df.groupby(["product_id", "product_name"]).agg(
        avg_inventory=("inventory_units", "mean"),
        avg_cost=("cost_per_unit", "mean"),
    ).reset_index()
    
    product_options = {f"{row['product_name']} ({row['product_id']})": row["product_id"]
                       for _, row in products.iterrows()}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_product_label = st.selectbox("Select Product", list(product_options.keys()), key="inv_product")
        product_id = product_options[selected_product_label]
        product_row = products[products["product_id"] == product_id].iloc[0]
    
    with col2:
        current_inventory = st.number_input(
            "Current Inventory (units)",
            value=int(product_row["avg_inventory"]),
            min_value=0,
            step=10,
        )
    
    with col3:
        proposed_purchase = st.number_input(
            "Proposed Purchase (units)",
            value=100,
            min_value=0,
            step=10,
        )
    
    if st.button("🔍 Analyze Inventory Impact", type="primary"):
        with st.spinner("Simulating inventory scenarios..."):
            from src.decisions.inventory import simulate_inventory
            
            forecast_demand = _get_forecast_demand(df, product_id)
            
            result = simulate_inventory(df, product_id, current_inventory, proposed_purchase, forecast_demand)
            
            if "error" in result:
                st.error(result["error"])
            else:
                _display_decision_result(result, "Inventory")


def _render_marketing_simulator(df: pd.DataFrame):
    """Render the marketing spend simulator."""
    st.markdown("### 📢 Marketing Simulator")
    st.caption("What's the impact of changing marketing spend?")
    
    # Category selection
    categories = ["All Categories"] + sorted(df["category"].unique().tolist()) if "category" in df.columns else ["All Categories"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_category = st.selectbox("Category", categories)
        category = None if selected_category == "All Categories" else selected_category
    
    # Calculate current spend
    if category:
        current_data = df[df["category"] == category]
    else:
        current_data = df
    
    avg_monthly_spend = current_data["marketing_spend"].sum() / max(1, current_data["date"].nunique()) * 30 if "marketing_spend" in df.columns else 10000
    
    with col2:
        current_spend = st.number_input(
            "Current Monthly Spend (₹)",
            value=float(round(avg_monthly_spend, 2)),
            min_value=0.0,
            step=1000.0,
        )
    
    with col3:
        proposed_spend = st.number_input(
            "Proposed Monthly Spend (₹)",
            value=float(round(avg_monthly_spend * 1.2, 2)),
            min_value=0.0,
            step=1000.0,
        )
    
    if st.button("🔍 Analyze Marketing Impact", type="primary"):
        with st.spinner("Simulating marketing scenarios..."):
            from src.decisions.marketing import simulate_marketing
            
            result = simulate_marketing(df, current_spend, proposed_spend, category)
            
            if "error" in result:
                st.error(result["error"])
            else:
                _display_decision_result(result, "Marketing")


def _get_forecast_demand(df, product_id):
    """Return a validated daily-demand forecast for inventory decisions."""
    try:
        from src.ml.demand_forecast import forecast_daily_demand

        forecast = forecast_daily_demand(df, periods=30, product_id=product_id)
        return forecast["total_predicted"]
    except Exception:
        pass
    return None


def _display_decision_result(result: dict, decision_type: str):
    """Display decision simulation results."""
    st.markdown("---")
    st.markdown("## 📋 Decision Analysis")
    
    # Current state
    st.markdown("### Current State")
    if decision_type == "Pricing":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Price", format_currency(result.get("current_price", 0)))
        with col2:
            st.metric("Proposed Price", format_currency(result.get("proposed_price", 0)))
        with col3:
            st.metric("Price Change", format_change_pct(result.get("price_change_pct", 0)))
        with col4:
            st.metric("Margin Change", f"{result.get('margin_change', 0):+.2f}%")
    
    elif decision_type == "Inventory":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Stock", format_number(result.get("current_inventory", 0)))
        with col2:
            st.metric("Proposed Purchase", format_number(result.get("proposed_purchase", 0)))
        with col3:
            st.metric("Total After", format_number(result.get("total_after_purchase", 0)))
        with col4:
            st.metric("Capital Required", format_currency(result.get("capital_required", 0)))
    
    elif decision_type == "Marketing":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Spend", format_currency(result.get("current_spend", 0)))
        with col2:
            st.metric("Proposed Spend", format_currency(result.get("proposed_spend", 0)))
        with col3:
            st.metric("Change", format_change_pct(result.get("spend_change_pct", 0)))
        with col4:
            st.metric("Historical ROAS", f"{result.get('historical_roas', 0):.1f}x")
    
    # Scenario comparison
    st.markdown("### Scenario Analysis")
    scenarios = result.get("scenarios", {})
    
    if scenarios:
        cols = st.columns(len(scenarios))
        colors = {"Conservative": "🟡", "Expected": "🟢", "Optimistic": "🔵"}
        
        for i, (name, data) in enumerate(scenarios.items()):
            with cols[i]:
                st.markdown(f"#### {colors.get(name, '⚪')} {name}")
                for key, value in data.items():
                    if isinstance(value, bool):
                        display_val = "Yes" if value else "No"
                    elif isinstance(value, float):
                        if "revenue" in key or "profit" in key or "cost" in key or "impact" in key:
                            display_val = format_currency(value)
                        elif "pct" in key:
                            display_val = f"{value:+.1f}%"
                        else:
                            display_val = f"{value:,.1f}"
                    else:
                        display_val = str(value)
                    
                    label = key.replace("_", " ").title()
                    st.markdown(f"**{label}:** {display_val}")
        
        # Scenario comparison chart
        _render_scenario_chart(scenarios, decision_type)
    
    # Assumptions
    st.markdown("### ⚠️ Key Assumptions")
    for assumption in result.get("assumptions", []):
        st.markdown(f"• {assumption}")
    
    # Risks
    st.markdown("### 🚨 Risks")
    for risk in result.get("risks", []):
        st.markdown(f"• {risk}")
    
    # Monitoring
    st.markdown("### 📡 Monitoring Triggers")
    st.caption("What to watch after implementing this decision.")
    for trigger in result.get("monitoring", []):
        st.markdown(f"• {trigger}")
    
    # Save decision
    st.markdown("---")
    _render_save_decision(result, decision_type)


def _render_scenario_chart(scenarios: dict, decision_type: str):
    """Render a comparison chart for scenarios."""
    # Find a common metric to chart
    metric_key = None
    for key in ["projected_revenue", "expected_revenue_change", "potential_revenue", "projected_profit"]:
        first_scenario = list(scenarios.values())[0]
        if key in first_scenario:
            metric_key = key
            break
    
    if metric_key is None:
        return
    
    chart_data = pd.DataFrame([
        {"Scenario": name, "Value": data.get(metric_key, 0)}
        for name, data in scenarios.items()
    ])
    
    fig = px.bar(
        chart_data, x="Scenario", y="Value",
        color="Scenario",
        color_discrete_map={"Conservative": "#eab308", "Expected": "#16a34a", "Optimistic": "#2563eb"},
    )
    fig.update_layout(
        height=300,
        yaxis_title=metric_key.replace("_", " ").title() + " (₹)",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_save_decision(result: dict, decision_type: str):
    """Render the save decision section."""
    st.markdown("### 💾 Save This Decision")
    
    user_notes = st.text_area(
        "Add notes about this decision (optional)",
        placeholder="e.g., 'Planning to implement this after festival season'",
    )
    
    if st.button("💾 Save Decision Contract", type="primary"):
        try:
            from src.decisions.decision_engine import create_decision_contract
            from src.storage.database import save_decision
            
            contract = create_decision_contract(decision_type, result, user_notes)
            save_decision(contract)
            
            st.success(f"✅ Decision saved! ID: **{contract['decision_id']}**")
            st.balloons()
        except Exception as e:
            st.error(f"Failed to save decision: {e}")

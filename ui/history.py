"""
Decision History page for BizGuard.

Displays saved decisions and allows comparison with actual outcomes.
"""

import streamlit as st
import pandas as pd
from src.storage.database import get_all_decisions, delete_decision, update_actual_outcome
from src.utils.formatting import format_currency


def render():
    """Render the Decision History page."""
    st.title("📋 Decision History")
    st.caption("Review past decisions, compare expected vs actual outcomes, and learn from results.")
    
    decisions = get_all_decisions()
    
    if not decisions:
        st.info(
            "No decisions saved yet. Go to **Test a Decision** to simulate "
            "and save your first business decision."
        )
        return
    
    st.markdown(f"**{len(decisions)} decision(s) recorded.**")
    
    # Summary table
    summary_data = []
    for d in decisions:
        input_data = d.get("input", {})
        recommendation = d.get("recommendation", {})
        
        summary_data.append({
            "ID": d["decision_id"],
            "Date": d["date"][:10] if d.get("date") else "—",
            "Type": d["decision_type"],
            "Description": _get_decision_description(d),
            "Recommendation": recommendation.get("recommendation", "—"),
            "Status": d.get("status", "—"),
        })
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Detailed view
    st.markdown("### Decision Details")
    
    decision_ids = [d["decision_id"] for d in decisions]
    selected_id = st.selectbox("Select a decision to view details", decision_ids)
    
    selected = next((d for d in decisions if d["decision_id"] == selected_id), None)
    
    if selected:
        _render_decision_detail(selected)


def _get_decision_description(decision: dict) -> str:
    """Generate a human-readable description of a decision."""
    input_data = decision.get("input", {})
    decision_type = decision.get("decision_type", "")
    
    if decision_type == "Pricing":
        product = input_data.get("product", "Unknown")
        change = input_data.get("price_change", "")
        return f"{product}: Price {change}"
    elif decision_type == "Inventory":
        product = input_data.get("product", "Unknown")
        qty = input_data.get("proposed_purchase", 0)
        return f"{product}: Purchase {qty} units"
    elif decision_type == "Marketing":
        category = input_data.get("category", "All")
        change = input_data.get("spend_change", "")
        return f"{category}: Spend {change}"
    return "—"


def _render_decision_detail(decision: dict):
    """Render detailed view of a single decision."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**Decision ID:** {decision['decision_id']}")
    with col2:
        st.markdown(f"**Type:** {decision['decision_type']}")
    with col3:
        st.markdown(f"**Date:** {decision.get('date', '—')[:10]}")
    
    # Input
    st.markdown("#### Input")
    input_data = decision.get("input", {})
    for key, value in input_data.items():
        label = key.replace("_", " ").title()
        if isinstance(value, (int, float)) and "price" in key.lower() or "spend" in key.lower() or "capital" in key.lower():
            st.markdown(f"**{label}:** {format_currency(value)}")
        else:
            st.markdown(f"**{label}:** {value}")
    
    # Expected outcome
    st.markdown("#### Expected Outcome")
    expected = decision.get("expected_outcome", {})
    if expected:
        for key, value in expected.items():
            label = key.replace("_", " ").title()
            if isinstance(value, float):
                st.markdown(f"**{label}:** {value:,.2f}")
            else:
                st.markdown(f"**{label}:** {value}")
    else:
        st.info("No expected outcome data.")
    
    # Recommendation
    recommendation = decision.get("recommendation", {})
    if recommendation:
        rec = recommendation.get("recommendation", "")
        confidence = recommendation.get("confidence", "")
        explanation = recommendation.get("explanation", "")
        
        color_map = {
            "Favorable": "success",
            "Proceed with Caution": "warning",
            "Reconsider": "error",
        }
        msg_type = color_map.get(rec, "info")
        
        getattr(st, msg_type)(f"**{rec}** (Confidence: {confidence})\n\n{explanation}")
    
    # Assumptions
    assumptions = decision.get("key_assumptions", [])
    if assumptions:
        with st.expander("⚠️ Key Assumptions"):
            for a in assumptions:
                st.markdown(f"• {a}")
    
    # Risks
    risks = decision.get("risk_indicators", [])
    if risks:
        with st.expander("🚨 Risks"):
            for r in risks:
                st.markdown(f"• {r}")
    
    # Monitoring
    monitoring = decision.get("monitoring_triggers", [])
    if monitoring:
        with st.expander("📡 Monitoring Triggers"):
            for m in monitoring:
                st.markdown(f"• {m}")
    
    # User notes
    notes = decision.get("user_notes", "")
    if notes:
        st.markdown(f"**Notes:** {notes}")
    
    # Actual outcome entry
    st.markdown("---")
    st.markdown("#### 📝 Record Actual Outcome")
    st.caption("After implementing the decision, record the actual results for comparison.")
    
    actual_result = st.text_input(
        "Actual outcome description",
        value="",
        key=f"actual_{decision['decision_id']}",
    )
    actual_value = st.number_input(
        "Actual value (₹ or units)",
        value=0.0,
        key=f"actual_val_{decision['decision_id']}",
    )
    
    col_save, col_delete = st.columns(2)
    
    with col_save:
        if st.button("💾 Save Actual Outcome", key=f"save_{decision['decision_id']}"):
            if actual_result or actual_value > 0:
                actual_outcome = {
                    "description": actual_result,
                    "value": actual_value,
                }
                update_actual_outcome(decision["decision_id"], actual_outcome)
                st.success("Actual outcome saved!")
                st.rerun()
            else:
                st.warning("Please enter the actual outcome.")
    
    with col_delete:
        if st.button("🗑️ Delete Decision", key=f"del_{decision['decision_id']}", type="secondary"):
            delete_decision(decision["decision_id"])
            st.success("Decision deleted.")
            st.rerun()

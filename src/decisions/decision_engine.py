"""
Decision engine orchestrator for BizGuard.

Coordinates decision simulations and creates Decision Contracts.
A Decision Contract captures everything about a simulated decision
so it can be saved, reviewed, and later compared with actual outcomes.
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime
import uuid

from src.decisions.pricing import simulate_pricing
from src.decisions.inventory import simulate_inventory
from src.decisions.marketing import simulate_marketing
from src.decisions.scenarios import get_scenario_recommendation


def create_decision_contract(decision_type: str, simulation_result: Dict,
                             user_notes: str = "") -> Dict:
    """
    Create a Decision Contract from simulation results.
    
    A Decision Contract captures:
    - Decision ID and timestamp
    - What was decided
    - Expected outcome
    - Historical evidence used
    - ML prediction (if applicable)
    - Scenario results
    - Key assumptions
    - Risk indicators
    - Monitoring triggers
    
    This enables the learning loop:
    Decision -> Prediction -> Action -> Actual Result -> Compare -> Learning
    
    Args:
        decision_type: Type of decision (Pricing/Inventory/Marketing).
        simulation_result: Results from the simulator.
        user_notes: Optional user notes about the decision.
    
    Returns:
        Decision Contract dict.
    """
    # Get recommendation
    scenarios = simulation_result.get("scenarios", {})
    recommendation = get_scenario_recommendation(scenarios)
    
    contract = {
        "decision_id": str(uuid.uuid4())[:8].upper(),
        "date": datetime.now().isoformat(),
        "decision_type": decision_type,
        "input": _extract_input(decision_type, simulation_result),
        "expected_outcome": _extract_expected_outcome(scenarios),
        "historical_evidence": _extract_evidence(simulation_result),
        "scenario_results": scenarios,
        "key_assumptions": simulation_result.get("assumptions", []),
        "risk_indicators": simulation_result.get("risks", []),
        "monitoring_triggers": simulation_result.get("monitoring", []),
        "recommendation": recommendation,
        "user_notes": user_notes,
        "actual_outcome": None,  # To be filled later
        "status": "Simulated",
    }
    
    return contract


def _extract_input(decision_type: str, result: Dict) -> Dict:
    """Extract the decision input parameters."""
    if decision_type == "Pricing":
        return {
            "product": result.get("product_name", ""),
            "current_price": result.get("current_price", 0),
            "proposed_price": result.get("proposed_price", 0),
            "price_change": f"{result.get('price_change_pct', 0)}%",
        }
    elif decision_type == "Inventory":
        return {
            "product": result.get("product_name", ""),
            "current_inventory": result.get("current_inventory", 0),
            "proposed_purchase": result.get("proposed_purchase", 0),
            "capital_required": result.get("capital_required", 0),
        }
    elif decision_type == "Marketing":
        return {
            "category": result.get("category", "All"),
            "current_spend": result.get("current_spend", 0),
            "proposed_spend": result.get("proposed_spend", 0),
            "spend_change": f"{result.get('spend_change_pct', 0)}%",
        }
    return {}


def _extract_expected_outcome(scenarios: Dict) -> Dict:
    """Extract the expected outcome from scenarios."""
    expected = scenarios.get("Expected", {})
    return {
        key: value for key, value in expected.items()
        if isinstance(value, (int, float, str, bool))
    }


def _extract_evidence(result: Dict) -> Dict:
    """Extract historical evidence from simulation."""
    evidence = {}
    evidence_keys = [
        "historical_roas", "estimated_elasticity",
        "historical_daily_velocity", "current_avg_daily_demand",
        "avg_cost_per_unit", "avg_selling_price",
        "avg_profit_margin",
    ]
    for key in evidence_keys:
        if key in result:
            evidence[key] = result[key]
    return evidence


def run_decision(df: pd.DataFrame, decision_type: str,
                 params: Dict, forecast_demand: Optional[float] = None,
                 user_notes: str = "") -> Dict:
    """
    Run a complete decision simulation and create a contract.
    
    This is the main entry point for the decision engine.
    
    Args:
        df: Historical business data.
        decision_type: 'Pricing', 'Inventory', or 'Marketing'.
        params: Decision-specific parameters.
        forecast_demand: ML demand forecast (optional).
        user_notes: User notes about the decision.
    
    Returns:
        Decision Contract dict.
    """
    if decision_type == "Pricing":
        result = simulate_pricing(
            df,
            product_id=params["product_id"],
            current_price=params["current_price"],
            proposed_price=params["proposed_price"],
            forecast_demand=forecast_demand,
        )
    elif decision_type == "Inventory":
        result = simulate_inventory(
            df,
            product_id=params["product_id"],
            current_inventory=params["current_inventory"],
            proposed_purchase=params["proposed_purchase"],
            forecast_demand=forecast_demand,
        )
    elif decision_type == "Marketing":
        result = simulate_marketing(
            df,
            current_spend=params["current_spend"],
            proposed_spend=params["proposed_spend"],
            category=params.get("category"),
        )
    else:
        return {"error": f"Unknown decision type: {decision_type}"}
    
    if "error" in result:
        return result
    
    contract = create_decision_contract(decision_type, result, user_notes)
    contract["simulation_details"] = result
    
    return contract

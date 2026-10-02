"""
Scenario analysis module for BizGuard.

Generates and formats multi-scenario analysis for decision simulation.
"""

from typing import Dict, List


def format_scenario_comparison(scenarios: Dict) -> List[Dict]:
    """
    Format scenarios for display in the UI.
    
    Args:
        scenarios: Dict of scenario_name -> scenario_results.
    
    Returns:
        List of formatted scenario dicts.
    """
    formatted = []
    for name, data in scenarios.items():
        scenario = {"Scenario": name}
        scenario.update(data)
        formatted.append(scenario)
    return formatted


def get_scenario_recommendation(scenarios: Dict) -> Dict:
    """
    Generate a recommendation based on scenario analysis.
    
    The recommendation considers the Expected scenario primarily,
    with Conservative as the risk check.
    
    Args:
        scenarios: Dict of scenario results.
    
    Returns:
        Dict with recommendation, confidence, and explanation.
    """
    if not scenarios:
        return {
            "recommendation": "Insufficient data",
            "confidence": "Low",
            "explanation": "Not enough scenario data to generate a recommendation.",
        }
    
    expected = scenarios.get("Expected", {})
    conservative = scenarios.get("Conservative", {})
    
    # Check if the decision is profitable in expected case
    profit_key = None
    for key in ["projected_profit", "net_impact", "profit_change", "expected_profit_change"]:
        if key in expected:
            profit_key = key
            break
    
    if profit_key is None:
        return {
            "recommendation": "Review required",
            "confidence": "Low",
            "explanation": "Unable to determine profitability from scenarios.",
        }
    
    expected_profit = expected.get(profit_key, 0)
    conservative_profit = conservative.get(profit_key, 0)
    
    if expected_profit > 0 and conservative_profit > 0:
        return {
            "recommendation": "Favorable",
            "confidence": "Moderate-High",
            "explanation": (
                f"The decision appears favorable. Even in the conservative scenario, "
                f"the projected outcome is positive. "
                f"Expected scenario projects a positive result of \u20b9{expected_profit:,.0f}."
            ),
        }
    elif expected_profit > 0:
        return {
            "recommendation": "Proceed with Caution",
            "confidence": "Moderate",
            "explanation": (
                f"The expected scenario shows a positive outcome (\u20b9{expected_profit:,.0f}), "
                f"but the conservative scenario suggests potential downside "
                f"(\u20b9{conservative_profit:,.0f}). Consider the risk tolerance."
            ),
        }
    else:
        return {
            "recommendation": "Reconsider",
            "confidence": "Moderate",
            "explanation": (
                f"The expected scenario projects a negative outcome (\u20b9{expected_profit:,.0f}). "
                f"This decision may not be favorable under current conditions."
            ),
        }

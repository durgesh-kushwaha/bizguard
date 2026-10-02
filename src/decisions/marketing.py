"""
Marketing spend decision simulator for BizGuard.

Simulates the impact of changing marketing/advertising budget.
Uses historical ROAS (Return on Ad Spend) as the basis.

IMPORTANT: ROAS is a correlation metric, NOT a causal measure.
Historical ROAS shows the association between spend and revenue.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def calculate_historical_roas(df: pd.DataFrame, category: Optional[str] = None) -> Dict:
    """
    Calculate historical Return on Ad Spend.
    
    ROAS = Revenue / Marketing Spend
    
    A ROAS of 5.0 means: for every \u20b91 spent on marketing,
    \u20b95 of revenue was generated (correlation, not causation).
    
    Args:
        df: Historical data.
        category: Specific category (None = overall).
    
    Returns:
        Dict with ROAS metrics.
    """
    if category:
        data = df[df["category"] == category].copy()
    else:
        data = df.copy()
    
    data = data[data["marketing_spend"] > 0]
    
    if len(data) == 0:
        return {
            "roas": 0,
            "total_revenue": 0,
            "total_marketing": 0,
            "profit_per_marketing_dollar": 0,
        }
    
    total_revenue = data["revenue"].sum()
    total_marketing = data["marketing_spend"].sum()
    total_profit = data["gross_profit"].sum() if "gross_profit" in data.columns else 0
    
    roas = total_revenue / total_marketing if total_marketing > 0 else 0
    profit_per_dollar = total_profit / total_marketing if total_marketing > 0 else 0
    
    return {
        "roas": round(roas, 2),
        "total_revenue": round(total_revenue, 2),
        "total_marketing": round(total_marketing, 2),
        "profit_per_marketing_dollar": round(profit_per_dollar, 2),
        "avg_daily_spend": round(data["marketing_spend"].mean(), 2),
        "data_points": len(data),
    }


def simulate_marketing(df: pd.DataFrame,
                       current_spend: float, proposed_spend: float,
                       category: Optional[str] = None) -> Dict:
    """
    Simulate the impact of changing marketing spend.
    
    Formulas:
    - Spend change = proposed - current
    - Expected revenue change = spend_change * historical_ROAS * efficiency_factor
    - Break-even ROAS = cost / revenue_contribution
    
    The efficiency factor accounts for diminishing returns:
    - Increasing spend has diminishing marginal returns
    - Decreasing spend may have proportionally larger impact
    
    Args:
        df: Historical data.
        current_spend: Current monthly marketing spend.
        proposed_spend: Proposed monthly marketing spend.
        category: Specific category (None = overall).
    
    Returns:
        Dict with simulation results.
    """
    historical = calculate_historical_roas(df, category)
    historical_roas = historical["roas"]
    
    if historical_roas == 0:
        return {"error": "No historical marketing data available for estimation."}
    
    spend_change = proposed_spend - current_spend
    spend_change_pct = (spend_change / current_spend * 100) if current_spend > 0 else 0
    
    # Calculate average profit margin from data
    if category:
        data = df[df["category"] == category]
    else:
        data = df
    
    avg_margin = data["profit_margin"].mean() if "profit_margin" in data.columns else 0.3
    
    # Break-even ROAS: at what ROAS does the marketing spend just cover its cost
    break_even_roas = 1 / avg_margin if avg_margin > 0 else float('inf')
    
    # Scenarios with diminishing returns factor
    scenarios = {}
    efficiency_factors = {
        "Conservative": 0.6,   # Significant diminishing returns
        "Expected": 0.8,       # Moderate diminishing returns
        "Optimistic": 1.0,     # Linear returns (best case)
    }
    
    for scenario_name, efficiency in efficiency_factors.items():
        expected_revenue_change = spend_change * historical_roas * efficiency
        expected_profit_change = expected_revenue_change * avg_margin
        net_impact = expected_profit_change - spend_change  # Profit minus additional spend
        
        effective_roas = (historical_roas * efficiency)
        is_profitable = net_impact > 0
        
        scenarios[scenario_name] = {
            "expected_revenue_change": round(expected_revenue_change, 2),
            "expected_profit_change": round(expected_profit_change, 2),
            "additional_cost": round(spend_change, 2),
            "net_impact": round(net_impact, 2),
            "effective_roas": round(effective_roas, 2),
            "is_profitable": is_profitable,
        }
    
    return {
        "decision_type": "Marketing",
        "category": category or "All Categories",
        "current_spend": current_spend,
        "proposed_spend": proposed_spend,
        "spend_change": round(spend_change, 2),
        "spend_change_pct": round(spend_change_pct, 1),
        "historical_roas": historical_roas,
        "break_even_roas": round(break_even_roas, 2),
        "avg_profit_margin": round(avg_margin, 4),
        "scenarios": scenarios,
        "assumptions": [
            f"Historical ROAS: {historical_roas:.1f}x (based on {historical['data_points']} data points).",
            "ROAS is a correlation metric, not a causal measure.",
            "Diminishing returns are modeled with efficiency factors.",
            f"Average profit margin: {avg_margin:.1%}.",
            "Competitor marketing activity is assumed unchanged.",
            "Market conditions are assumed to be similar to the historical period.",
        ],
        "risks": [
            "ROAS may differ significantly from historical values.",
            "Competitor marketing changes can affect results.",
            "Seasonal effects may amplify or reduce impact.",
            "Channel saturation may reduce returns at higher spend levels.",
        ],
        "monitoring": [
            "Track ROAS weekly after spend change.",
            "Monitor customer acquisition cost.",
            "Compare actual revenue lift vs projected.",
            "Watch for changes in competitor marketing.",
        ],
    }

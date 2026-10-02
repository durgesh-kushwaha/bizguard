"""
Pricing decision simulator for BizGuard.

Simulates the impact of changing a product's price.
Uses historical data and price elasticity estimation
to project revenue and profit under different scenarios.

All calculations use documented formulas — no black-box magic.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def estimate_price_elasticity(df: pd.DataFrame, product_id: str) -> float:
    """
    Estimate price elasticity of demand from historical data.
    
    Price elasticity = % change in quantity / % change in price
    
    A value of -1.5 means: for every 1% price increase,
    demand decreases by approximately 1.5%.
    
    Note: This is a simplified estimation using historical variation.
    It captures correlation, not proven causation.
    
    Args:
        df: Historical data.
        product_id: Product to analyze.
    
    Returns:
        Estimated elasticity (typically negative).
    """
    product_data = df[df["product_id"] == product_id].copy()
    
    if len(product_data) < 10:
        # Not enough data — use default assumption
        return -1.2  # Moderate elasticity
    
    # Group by date and aggregate
    daily = product_data.groupby("date").agg(
        avg_price=("unit_price", "mean"),
        total_qty=("quantity", "sum"),
    ).reset_index()
    
    if daily["avg_price"].std() == 0 or daily["total_qty"].std() == 0:
        return -1.2  # No price variation to estimate from
    
    # Calculate percentage changes
    daily["price_pct_change"] = daily["avg_price"].pct_change()
    daily["qty_pct_change"] = daily["total_qty"].pct_change()
    
    # Remove infinite and NaN values
    daily = daily.replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(daily) < 5:
        return -1.2
    
    # Estimate elasticity using correlation
    if daily["price_pct_change"].std() > 0:
        correlation = daily["qty_pct_change"].corr(daily["price_pct_change"])
        elasticity = correlation * (daily["qty_pct_change"].std() / daily["price_pct_change"].std())
        
        # Clamp to reasonable range
        elasticity = max(min(elasticity, -0.3), -3.0)
        return round(elasticity, 2)
    
    return -1.2


def simulate_pricing(df: pd.DataFrame, product_id: str,
                     current_price: float, proposed_price: float,
                     forecast_demand: Optional[float] = None) -> Dict:
    """
    Simulate the impact of a pricing change.
    
    Formulas:
    - Price change % = (proposed - current) / current
    - Expected demand change = price_change% * elasticity
    - New quantity = current_quantity * (1 + demand_change)
    - New revenue = new_quantity * proposed_price
    - Break-even volume = current_revenue / proposed_price
    
    Args:
        df: Historical data.
        product_id: Product to simulate.
        current_price: Current selling price.
        proposed_price: Proposed new price.
        forecast_demand: ML forecast demand (optional, enhances accuracy).
    
    Returns:
        Dict with simulation results including scenarios.
    """
    product_data = df[df["product_id"] == product_id]
    
    if len(product_data) == 0:
        return {"error": f"No data found for product {product_id}"}
    
    # Current metrics
    avg_daily_qty = product_data["quantity"].mean()
    avg_cost = product_data["cost_per_unit"].mean()
    total_revenue = product_data["revenue"].sum()
    total_quantity = product_data["quantity"].sum()
    current_margin = (current_price - avg_cost) / current_price if current_price > 0 else 0
    proposed_margin = (proposed_price - avg_cost) / proposed_price if proposed_price > 0 else 0
    
    # Price change
    price_change_pct = (proposed_price - current_price) / current_price if current_price > 0 else 0
    
    # Estimate elasticity
    elasticity = estimate_price_elasticity(df, product_id)
    
    # Use forecast demand if available
    base_demand = forecast_demand if forecast_demand else avg_daily_qty * 30
    
    # Generate scenarios
    scenarios = {}
    
    # Scenario multipliers for demand response
    scenario_configs = {
        "Conservative": 1.3,   # Demand responds more than expected
        "Expected": 1.0,      # Demand follows estimated elasticity
        "Optimistic": 0.7,    # Demand is less sensitive than expected
    }
    
    for scenario_name, sensitivity in scenario_configs.items():
        demand_change_pct = price_change_pct * elasticity * sensitivity
        projected_demand = base_demand * (1 + demand_change_pct)
        projected_demand = max(0, projected_demand)
        
        projected_revenue = projected_demand * proposed_price
        projected_cost = projected_demand * avg_cost
        projected_profit = projected_revenue - projected_cost
        
        current_revenue_30d = base_demand * current_price
        current_profit_30d = base_demand * (current_price - avg_cost)
        
        revenue_change = projected_revenue - current_revenue_30d
        profit_change = projected_profit - current_profit_30d
        
        scenarios[scenario_name] = {
            "projected_demand": round(projected_demand, 0),
            "demand_change_pct": round(demand_change_pct * 100, 1),
            "projected_revenue": round(projected_revenue, 2),
            "projected_profit": round(projected_profit, 2),
            "revenue_change": round(revenue_change, 2),
            "profit_change": round(profit_change, 2),
        }
    
    # Break-even volume
    break_even_volume = total_revenue / proposed_price if proposed_price > 0 else 0
    break_even_change_pct = ((break_even_volume / total_quantity) - 1) * 100 if total_quantity > 0 else 0
    
    return {
        "product_id": product_id,
        "product_name": product_data["product_name"].iloc[0] if "product_name" in product_data.columns else product_id,
        "decision_type": "Pricing",
        "current_price": current_price,
        "proposed_price": proposed_price,
        "price_change_pct": round(price_change_pct * 100, 1),
        "current_margin": round(current_margin, 4),
        "proposed_margin": round(proposed_margin, 4),
        "margin_change": round((proposed_margin - current_margin) * 100, 2),
        "estimated_elasticity": elasticity,
        "avg_cost_per_unit": round(avg_cost, 2),
        "current_avg_daily_demand": round(avg_daily_qty, 1),
        "base_demand_30d": round(base_demand, 0),
        "break_even_volume": round(break_even_volume, 0),
        "break_even_change_pct": round(break_even_change_pct, 1),
        "scenarios": scenarios,
        "assumptions": [
            f"Price elasticity estimated at {elasticity} from historical data.",
            "Elasticity captures historical correlation, not proven causation.",
            "Competitor pricing is assumed to remain unchanged.",
            "No supply chain disruptions assumed.",
            f"Base demand: {'ML forecast' if forecast_demand else 'historical average'} ({base_demand:.0f} units/month).",
        ],
        "risks": [
            "Competitor may respond with matching price changes.",
            "Customer behavior may differ from historical patterns.",
            "Seasonal factors may amplify or dampen the effect.",
        ],
        "monitoring": [
            "Track daily sales volume for 2 weeks after price change.",
            "Monitor customer acquisition/churn.",
            "Compare actual demand vs projected demand.",
            "Watch competitor pricing.",
        ],
    }

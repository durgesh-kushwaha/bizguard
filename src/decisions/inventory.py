"""
Inventory decision simulator for BizGuard.

Simulates the impact of purchasing additional inventory.
Uses historical sales velocity and ML demand forecasts.

All calculations use documented formulas.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


def simulate_inventory(df: pd.DataFrame, product_id: str,
                       current_inventory: int, proposed_purchase: int,
                       forecast_demand: Optional[float] = None) -> Dict:
    """
    Simulate an inventory purchase decision.
    
    Formulas:
    - Total inventory after purchase = current + proposed
    - Expected demand = ML forecast or historical avg * 30
    - Projected remaining = total inventory - expected demand
    - Capital required = proposed_purchase * cost_per_unit
    - Stock cover = total inventory / daily_sales_velocity
    
    Args:
        df: Historical data.
        product_id: Product to simulate.
        current_inventory: Current inventory units.
        proposed_purchase: Additional units to purchase.
        forecast_demand: ML demand forecast (optional).
    
    Returns:
        Dict with simulation results.
    """
    product_data = df[df["product_id"] == product_id]
    
    if len(product_data) == 0:
        return {"error": f"No data found for product {product_id}"}
    
    # Historical metrics
    avg_daily_sales = product_data["quantity"].mean()
    avg_cost = product_data["cost_per_unit"].mean()
    avg_price = product_data["unit_price"].mean()
    total_days = (pd.to_datetime(product_data["date"]).max() - 
                  pd.to_datetime(product_data["date"]).min()).days or 1
    
    # Demand estimation
    if forecast_demand:
        expected_demand_30d = forecast_demand
    else:
        expected_demand_30d = avg_daily_sales * 30
    
    daily_velocity = expected_demand_30d / 30
    
    # Inventory calculations
    total_after_purchase = current_inventory + proposed_purchase
    capital_required = proposed_purchase * avg_cost
    
    # Scenarios
    scenarios = {}
    demand_multipliers = {
        "Conservative": 0.75,    # Demand is 25% lower than expected
        "Expected": 1.0,
        "Optimistic": 1.30,      # Demand is 30% higher than expected
    }
    
    for scenario_name, multiplier in demand_multipliers.items():
        scenario_demand = expected_demand_30d * multiplier
        remaining = total_after_purchase - scenario_demand
        stock_cover = total_after_purchase / (scenario_demand / 30) if scenario_demand > 0 else float('inf')
        potential_revenue = min(scenario_demand, total_after_purchase) * avg_price
        potential_profit = min(scenario_demand, total_after_purchase) * (avg_price - avg_cost)
        surplus_units = max(0, remaining)
        stockout_risk = remaining < 0
        
        scenarios[scenario_name] = {
            "scenario_demand": round(scenario_demand, 0),
            "remaining_inventory": round(remaining, 0),
            "stock_cover_days": round(stock_cover, 1) if stock_cover != float('inf') else "N/A",
            "potential_revenue": round(potential_revenue, 2),
            "potential_profit": round(potential_profit, 2),
            "surplus_units": round(surplus_units, 0),
            "stockout_risk": stockout_risk,
        }
    
    return {
        "product_id": product_id,
        "product_name": product_data["product_name"].iloc[0] if "product_name" in product_data.columns else product_id,
        "decision_type": "Inventory",
        "current_inventory": current_inventory,
        "proposed_purchase": proposed_purchase,
        "total_after_purchase": total_after_purchase,
        "capital_required": round(capital_required, 2),
        "avg_cost_per_unit": round(avg_cost, 2),
        "avg_selling_price": round(avg_price, 2),
        "historical_daily_velocity": round(avg_daily_sales, 1),
        "expected_demand_30d": round(expected_demand_30d, 0),
        "demand_source": "ML Forecast" if forecast_demand else "Historical Average",
        "scenarios": scenarios,
        "assumptions": [
            f"Cost per unit: \u20b9{avg_cost:.2f} (historical average).",
            f"Demand estimate: {expected_demand_30d:.0f} units/month ({'ML forecast' if forecast_demand else 'historical average'}).",
            "No lead time for delivery is included.",
            "Holding costs are not included in this prototype.",
            "Seasonal demand variation may affect actual outcomes.",
        ],
        "risks": [
            "Demand may be lower than forecast, leading to surplus inventory.",
            "Perishability or obsolescence may affect unsold stock.",
            f"Capital of \u20b9{capital_required:,.0f} will be locked in inventory.",
            "Storage costs may reduce net profit.",
        ],
        "monitoring": [
            "Track daily sales after restocking.",
            "Monitor inventory turnover ratio weekly.",
            "Compare actual demand vs forecast demand.",
            "Watch for slow-moving inventory alerts.",
        ],
    }

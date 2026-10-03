"""
Business analytics module for BizGuard.

Computes high-level KPIs and generates business insights.
Every insight is derived from actual calculations, never fabricated.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from src.bda.aggregations import (
    monthly_revenue,
    product_performance,
    category_analysis,
    marketing_effectiveness,
    inventory_analysis,
)


def compute_kpis(df: pd.DataFrame) -> Dict:
    """
    Compute top-level business KPIs from the dataset.
    
    KPIs:
    - Total Revenue
    - Total Profit
    - Number of Orders
    - Units Sold
    - Average Order Value
    - Overall Profit Margin
    
    Args:
        df: Cleaned business data.
    
    Returns:
        Dict of KPI name -> value.
    """
    total_revenue = df["revenue"].sum() if "revenue" in df.columns else 0
    total_profit = df["gross_profit"].sum() if "gross_profit" in df.columns else None
    num_orders = df["order_id"].nunique() if "order_id" in df.columns else None
    units_sold = df["quantity"].sum() if "quantity" in df.columns else 0
    
    avg_order_value = (
        total_revenue / num_orders
        if num_orders and num_orders > 0 and "revenue" in df.columns else None
    )
    profit_margin = (
        total_profit / total_revenue
        if total_profit is not None and total_revenue > 0 else None
    )
    
    return {
        "total_revenue": round(total_revenue, 2),
        "total_profit": round(total_profit, 2) if total_profit is not None else None,
        "num_orders": num_orders,
        "units_sold": int(units_sold),
        "avg_order_value": round(avg_order_value, 2) if avg_order_value is not None else None,
        "profit_margin": round(profit_margin, 4) if profit_margin is not None else None,
    }


def detect_business_signals(df: pd.DataFrame) -> List[Dict]:
    """
    Detect business signals from the data.
    
    Each signal answers:
    - WHAT changed?
    - WHY might it have changed? (evidence)
    - SO WHAT? (why it matters)
    
    Signals are generated from actual calculations, never fabricated.
    
    Args:
        df: Cleaned business data.
    
    Returns:
        List of signal dicts with keys: type, title, what, why, so_what, severity
    """
    signals = []
    
    if "date" not in df.columns or len(df) < 100:
        return signals
    
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    
    # Get monthly data
    monthly = monthly_revenue(df)
    
    if len(monthly) < 2:
        return signals
    
    # Signal 1: Declining profit margin
    if "avg_profit_margin" in monthly.columns and len(monthly) >= 3:
        recent_margins = monthly["avg_profit_margin"].tail(3).values
        earlier_margins = monthly["avg_profit_margin"].head(3).values
        
        recent_avg = np.mean(recent_margins)
        earlier_avg = np.mean(earlier_margins)
        
        if earlier_avg > 0 and recent_avg < earlier_avg * 0.9:
            decline_pct = round((1 - recent_avg / earlier_avg) * 100, 1)
            signals.append({
                "type": "margin",
                "title": "Declining Profit Margin",
                "what": f"Profit margin declined by {decline_pct}% comparing recent months to earlier months.",
                "why": f"Recent average margin: {recent_avg:.2%}, Earlier average: {earlier_avg:.2%}.",
                "so_what": "Revenue growth may not translate into proportional profit growth. Review discount levels and cost changes.",
                "severity": "warning",
            })
    
    # Signal 2: Revenue trend
    if "total_revenue" in monthly.columns and len(monthly) >= 4:
        recent_rev = monthly["total_revenue"].tail(3).mean()
        earlier_rev = monthly["total_revenue"].head(3).mean()
        
        if earlier_rev > 0:
            change_pct = round((recent_rev / earlier_rev - 1) * 100, 1)
            if change_pct > 15:
                signals.append({
                    "type": "revenue",
                    "title": "Revenue Growth Detected",
                    "what": f"Revenue increased by {change_pct}% (recent vs earlier months).",
                    "why": f"Recent avg: \u20b9{recent_rev:,.0f}, Earlier avg: \u20b9{earlier_rev:,.0f}.",
                    "so_what": "Positive trend. Verify whether growth is sustainable or seasonal.",
                    "severity": "info",
                })
            elif change_pct < -15:
                signals.append({
                    "type": "revenue",
                    "title": "Revenue Decline Detected",
                    "what": f"Revenue declined by {abs(change_pct)}% (recent vs earlier months).",
                    "why": f"Recent avg: \u20b9{recent_rev:,.0f}, Earlier avg: \u20b9{earlier_rev:,.0f}.",
                    "so_what": "Investigate whether decline is seasonal, competitive, or structural.",
                    "severity": "warning",
                })
    
    # Signal 3: High returns in any category
    if all(col in df.columns for col in ("returns", "quantity", "category")):
        cat_returns = df.groupby("category").agg(
            total_returns=("returns", "sum"),
            total_quantity=("quantity", "sum"),
        ).reset_index()
        cat_returns["return_rate"] = np.where(
            cat_returns["total_quantity"] > 0,
            cat_returns["total_returns"] / cat_returns["total_quantity"],
            0,
        )
        
        high_returns = cat_returns[cat_returns["return_rate"] > 0.05]
        for _, row in high_returns.iterrows():
            signals.append({
                "type": "returns",
                "title": f"High Return Rate: {row['category']}",
                "what": f"{row['category']} has a {row['return_rate']:.1%} return rate.",
                "why": f"{int(row['total_returns'])} returns out of {int(row['total_quantity'])} units sold.",
                "so_what": "High returns reduce net revenue and may indicate quality or sizing issues.",
                "severity": "warning",
            })
    
    # Signal 4: Marketing effectiveness variation
    mkt = marketing_effectiveness(df)
    if len(mkt) > 0 and "roas" in mkt.columns:
        low_roas = mkt[mkt["roas"] < mkt["roas"].median() * 0.5]
        for _, row in low_roas.iterrows():
            signals.append({
                "type": "marketing",
                "title": f"Low Marketing ROAS: {row['category']}",
                "what": f"{row['category']} has ROAS of {row['roas']:.1f}x.",
                "why": f"\u20b9{row['total_marketing']:,.0f} marketing spend generated \u20b9{row['total_revenue']:,.0f} revenue.",
                "so_what": "Marketing spend may not be generating proportional returns. Consider reallocation.",
                "severity": "info",
            })
    
    # Signal 5: Inventory concentration
    inv = inventory_analysis(df)
    if len(inv) > 0 and "stock_cover_days" in inv.columns:
        high_stock = inv[inv["stock_cover_days"] > 90]
        for _, row in high_stock.iterrows():
            if row["stock_cover_days"] != np.inf:
                signals.append({
                    "type": "inventory",
                    "title": f"High Inventory: {row['product_name']}",
                    "what": f"{row['product_name']} has {row['stock_cover_days']:.0f} days of stock cover.",
                    "why": f"Average inventory: {row['avg_inventory']:.0f} units, Average daily sales: {row['avg_daily_sales']:.1f} units.",
                    "so_what": "Excess inventory ties up capital. Consider promotional pricing or reducing reorders.",
                    "severity": "info",
                })
    
    return signals

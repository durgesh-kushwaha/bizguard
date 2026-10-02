"""
Tests for decision engine: pricing, inventory, marketing simulators.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _create_decision_df():
    """Create a DataFrame for decision testing."""
    np.random.seed(42)
    n = 200
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "order_id": [f"ORD{i:04d}" for i in range(n)],
        "product_id": ["P001"] * 100 + ["P002"] * 100,
        "product_name": ["Widget A"] * 100 + ["Widget B"] * 100,
        "category": ["Electronics"] * 100 + ["Office"] * 100,
        "quantity": np.random.randint(1, 20, n),
        "unit_price": [500.0] * 100 + [200.0] * 100,
        "discount": np.random.choice([0, 5, 10], n),
        "cost_per_unit": [250.0] * 100 + [100.0] * 100,
        "marketing_spend": np.random.uniform(50, 300, n).round(2),
        "returns": np.random.randint(0, 2, n),
        "customer_id": [f"C{i:04d}" for i in np.random.randint(1, 50, n)],
        "region": np.random.choice(["North", "South"], n),
        "inventory_units": np.random.randint(50, 200, n),
        "revenue": np.random.uniform(500, 5000, n).round(2),
        "gross_profit": np.random.uniform(100, 2000, n).round(2),
        "profit_margin": np.random.uniform(0.1, 0.5, n).round(4),
        "net_price": np.random.uniform(400, 500, n).round(2),
    })


class TestPricingSimulator:
    """Tests for pricing decision simulator."""
    
    def test_simulate_pricing(self):
        """Test basic pricing simulation."""
        from src.decisions.pricing import simulate_pricing
        
        df = _create_decision_df()
        result = simulate_pricing(df, "P001", 500.0, 550.0)
        
        assert "error" not in result
        assert result["decision_type"] == "Pricing"
        assert "scenarios" in result
        assert "Conservative" in result["scenarios"]
        assert "Expected" in result["scenarios"]
        assert "Optimistic" in result["scenarios"]
        assert len(result["assumptions"]) > 0
        assert len(result["risks"]) > 0
    
    def test_pricing_price_decrease(self):
        """Test pricing with a price decrease."""
        from src.decisions.pricing import simulate_pricing
        
        df = _create_decision_df()
        result = simulate_pricing(df, "P001", 500.0, 400.0)
        
        assert result["price_change_pct"] < 0
        assert "scenarios" in result
    
    def test_pricing_unknown_product(self):
        """Test pricing with unknown product returns error."""
        from src.decisions.pricing import simulate_pricing
        
        df = _create_decision_df()
        result = simulate_pricing(df, "UNKNOWN", 500.0, 550.0)
        
        assert "error" in result
    
    def test_price_elasticity_estimation(self):
        """Test elasticity is within reasonable range."""
        from src.decisions.pricing import estimate_price_elasticity
        
        df = _create_decision_df()
        elasticity = estimate_price_elasticity(df, "P001")
        
        assert -3.0 <= elasticity <= -0.3


class TestInventorySimulator:
    """Tests for inventory decision simulator."""
    
    def test_simulate_inventory(self):
        """Test basic inventory simulation."""
        from src.decisions.inventory import simulate_inventory
        
        df = _create_decision_df()
        result = simulate_inventory(df, "P001", 120, 500)
        
        assert "error" not in result
        assert result["decision_type"] == "Inventory"
        assert result["total_after_purchase"] == 620
        assert result["capital_required"] > 0
        assert "scenarios" in result
    
    def test_inventory_zero_purchase(self):
        """Test inventory with zero purchase."""
        from src.decisions.inventory import simulate_inventory
        
        df = _create_decision_df()
        result = simulate_inventory(df, "P001", 100, 0)
        
        assert result["total_after_purchase"] == 100


class TestMarketingSimulator:
    """Tests for marketing decision simulator."""
    
    def test_simulate_marketing(self):
        """Test basic marketing simulation."""
        from src.decisions.marketing import simulate_marketing
        
        df = _create_decision_df()
        result = simulate_marketing(df, 10000.0, 15000.0)
        
        assert "error" not in result
        assert result["decision_type"] == "Marketing"
        assert result["spend_change"] == 5000.0
        assert "scenarios" in result
        assert result["historical_roas"] > 0
    
    def test_marketing_by_category(self):
        """Test marketing simulation for specific category."""
        from src.decisions.marketing import simulate_marketing
        
        df = _create_decision_df()
        result = simulate_marketing(df, 5000.0, 8000.0, category="Electronics")
        
        assert "error" not in result
        assert result["category"] == "Electronics"
    
    def test_historical_roas(self):
        """Test ROAS calculation."""
        from src.decisions.marketing import calculate_historical_roas
        
        df = _create_decision_df()
        roas = calculate_historical_roas(df)
        
        assert roas["roas"] > 0
        assert roas["total_revenue"] > 0
        assert roas["total_marketing"] > 0


class TestDecisionEngine:
    """Tests for the decision engine orchestrator."""
    
    def test_run_pricing_decision(self):
        """Test running a complete pricing decision."""
        from src.decisions.decision_engine import run_decision
        
        df = _create_decision_df()
        contract = run_decision(
            df, "Pricing",
            {"product_id": "P001", "current_price": 500.0, "proposed_price": 550.0}
        )
        
        assert "decision_id" in contract
        assert contract["decision_type"] == "Pricing"
        assert "scenario_results" in contract
        assert "key_assumptions" in contract
    
    def test_decision_contract_fields(self):
        """Test that decision contract has all required fields."""
        from src.decisions.decision_engine import run_decision
        
        df = _create_decision_df()
        contract = run_decision(
            df, "Inventory",
            {"product_id": "P001", "current_inventory": 100, "proposed_purchase": 200}
        )
        
        required_fields = [
            "decision_id", "date", "decision_type", "input",
            "expected_outcome", "scenario_results", "key_assumptions",
            "risk_indicators", "monitoring_triggers", "recommendation",
        ]
        for field in required_fields:
            assert field in contract, f"Missing field: {field}"

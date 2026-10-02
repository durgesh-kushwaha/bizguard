"""
Tests for utility modules.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestFormatting:
    """Tests for formatting utilities."""
    
    def test_format_currency(self):
        from src.utils.formatting import format_currency
        
        assert "\u20b9" in format_currency(1000)
        assert format_currency(0) == "\u20b90.00"
    
    def test_format_number(self):
        from src.utils.formatting import format_number
        
        assert format_number(1000) == "1,000"
        assert format_number(0) == "0"
    
    def test_format_percentage(self):
        from src.utils.formatting import format_percentage
        
        assert format_percentage(0.5) == "50.0%"
        assert format_percentage(0) == "0.0%"
    
    def test_format_currency_large(self):
        from src.utils.formatting import format_currency
        
        result = format_currency(15000000)
        assert "Cr" in result
        
        result = format_currency(500000)
        assert "L" in result


class TestDatabase:
    """Tests for database operations."""

    def test_init_database_adds_history_evidence_to_legacy_schema(self, tmp_path):
        import sqlite3
        from src.storage.database import init_database

        db_path = tmp_path / "legacy.db"
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE decisions (
                    id TEXT PRIMARY KEY,
                    date TEXT,
                    decision_type TEXT,
                    input_json TEXT,
                    expected_outcome_json TEXT,
                    scenario_results_json TEXT,
                    assumptions_json TEXT,
                    risks_json TEXT,
                    monitoring_json TEXT,
                    recommendation_json TEXT,
                    user_notes TEXT,
                    actual_outcome_json TEXT,
                    status TEXT DEFAULT 'Simulated',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

        init_database(db_path)
        with sqlite3.connect(db_path) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(decisions)")}

        assert "historical_evidence_json" in columns
    
    def test_init_database(self, tmp_path):
        from src.storage.database import init_database
        
        db_path = tmp_path / "test.db"
        init_database(db_path)
        assert db_path.exists()
    
    def test_save_and_retrieve_decision(self, tmp_path):
        from src.storage.database import save_decision, get_all_decisions
        
        db_path = tmp_path / "test.db"
        
        contract = {
            "decision_id": "TEST001",
            "date": "2024-01-01",
            "decision_type": "Pricing",
            "input": {"product": "Widget", "price": 100},
            "expected_outcome": {"revenue": 5000},
            "scenario_results": {},
            "key_assumptions": ["Stable market"],
            "risk_indicators": ["Competition"],
            "monitoring_triggers": ["Track sales"],
            "recommendation": {"recommendation": "Favorable"},
            "user_notes": "Test note",
            "status": "Simulated",
        }
        
        save_decision(contract, db_path)
        decisions = get_all_decisions(db_path)
        
        assert len(decisions) == 1
        assert decisions[0]["decision_id"] == "TEST001"
        assert decisions[0]["decision_type"] == "Pricing"
    
    def test_delete_decision(self, tmp_path):
        from src.storage.database import save_decision, delete_decision, get_all_decisions
        
        db_path = tmp_path / "test.db"
        
        contract = {
            "decision_id": "DEL001",
            "date": "2024-01-01",
            "decision_type": "Test",
            "status": "Simulated",
        }
        
        save_decision(contract, db_path)
        assert len(get_all_decisions(db_path)) == 1
        
        delete_decision("DEL001", db_path)
        assert len(get_all_decisions(db_path)) == 0

    def test_full_decision_contract_history_workflow(self, tmp_path):
        import numpy as np
        import pandas as pd
        from src.decisions.decision_engine import compare_expected_actual, run_decision
        from src.storage.database import (
            delete_decision,
            get_all_decisions,
            get_decision_by_id,
            init_database,
            save_decision,
            update_actual_outcome,
        )

        db_path = tmp_path / "workflow.db"
        init_database(db_path)
        history = pd.DataFrame({
            "date": pd.date_range("2025-01-01", periods=20, freq="D"),
            "product_id": ["P001"] * 20,
            "product_name": ["Widget"] * 20,
            "quantity": np.arange(5, 25),
            "unit_price": [100.0] * 20,
            "cost_per_unit": [40.0] * 20,
            "revenue": np.arange(5, 25) * 100.0,
        })

        contract = run_decision(
            history,
            "Pricing",
            {"product_id": "P001", "current_price": 100.0, "proposed_price": 110.0},
            user_notes="Review after the next sales cycle.",
        )
        assert contract["scenario_results"]["Expected"]["projected_revenue"] > 0
        decision_id = save_decision(contract, db_path)
        assert len(decision_id) == 8

        saved = get_decision_by_id(decision_id, db_path)
        assert saved is not None
        assert saved["decision_type"] == "Pricing"
        assert saved["input"]["product"] == "Widget"
        assert saved["scenario_results"] == contract["scenario_results"]
        assert saved["historical_evidence"] == contract["historical_evidence"]
        assert saved["user_notes"] == "Review after the next sales cycle."

        expected = saved["expected_outcome"]["projected_revenue"]
        actual = {
            "description": "Revenue recorded for the test period.",
            "metric": "projected_revenue",
            "value": expected * 0.9,
        }
        update_actual_outcome(decision_id, actual, db_path)
        updated = get_decision_by_id(decision_id, db_path)
        assert updated["status"] == "Completed"
        assert updated["actual_outcome"] == actual
        comparison = compare_expected_actual(updated["expected_outcome"], updated["actual_outcome"])
        assert comparison["difference"] == pytest.approx(actual["value"] - expected)
        assert comparison["difference_pct"] == pytest.approx(-10.0)

        delete_decision(decision_id, db_path)
        assert get_decision_by_id(decision_id, db_path) is None
        assert get_all_decisions(db_path) == []

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

"""
Tests for data loading, validation, and cleaning modules.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def _create_sample_df():
    """Create a minimal valid DataFrame for testing."""
    quantity = np.random.randint(1, 20, 100)
    returns = np.minimum(np.random.randint(0, 3, 100), quantity)
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=100, freq="D"),
        "order_id": [f"ORD{i:04d}" for i in range(100)],
        "product_id": ["P001"] * 50 + ["P002"] * 50,
        "product_name": ["Widget A"] * 50 + ["Widget B"] * 50,
        "category": ["Electronics"] * 50 + ["Office"] * 50,
        "quantity": quantity,
        "unit_price": np.random.uniform(100, 1000, 100).round(2),
        "discount": np.random.choice([0, 5, 10, 15], 100),
        "cost_per_unit": np.random.uniform(50, 500, 100).round(2),
        "marketing_spend": np.random.uniform(0, 500, 100).round(2),
        "returns": returns,
        "customer_id": [f"C{i:04d}" for i in np.random.randint(1, 50, 100)],
        "region": np.random.choice(["North", "South", "East", "West"], 100),
        "inventory_units": np.random.randint(10, 200, 100),
    })


class TestDataLoader:
    """Tests for data loading module."""
    
    def test_load_sample_data(self):
        """Test loading the built-in sample dataset."""
        from src.data.loader import load_sample_data
        df, metadata = load_sample_data()
        
        assert df is not None
        assert len(df) > 0
        assert metadata["rows_loaded"] > 0
        assert metadata["columns_loaded"] > 0
    
    def test_load_csv_from_path(self, tmp_path):
        """Test loading a CSV file from a path."""
        from src.data.loader import load_csv
        
        # Create a test CSV
        test_df = _create_sample_df()
        csv_path = tmp_path / "test.csv"
        test_df.to_csv(csv_path, index=False)
        
        loaded_df, metadata = load_csv(str(csv_path))
        assert len(loaded_df) == 100
        assert metadata["file_type"] == "CSV"
    
    def test_load_invalid_file(self):
        """Test that loading an invalid file raises ValueError."""
        from src.data.loader import load_csv
        
        with pytest.raises(ValueError):
            load_csv("/nonexistent/path.csv")

    def test_load_normalizes_column_names(self, tmp_path):
        from src.data.loader import load_csv

        csv_path = tmp_path / "mixed_case.csv"
        csv_path.write_text(" Date ,ORDER_ID\n2024-01-01,ORD1\n")

        loaded, _ = load_csv(csv_path)
        assert list(loaded.columns) == ["date", "order_id"]

    def test_load_rejects_duplicate_normalized_columns(self, tmp_path):
        from src.data.loader import load_csv

        csv_path = tmp_path / "duplicate_columns.csv"
        csv_path.write_text("date, Date \n2024-01-01,2024-01-02\n")

        with pytest.raises(ValueError, match="duplicated"):
            load_csv(csv_path)


class TestDataValidator:
    """Tests for data validation module."""
    
    def test_validate_valid_data(self):
        """Test that valid data passes validation."""
        from src.data.validator import validate_dataset
        
        df = _create_sample_df()
        result = validate_dataset(df)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_missing_columns(self):
        """Test that missing required columns are detected."""
        from src.data.validator import validate_dataset
        
        df = pd.DataFrame({"date": ["2024-01-01"], "order_id": ["ORD001"]})
        result = validate_dataset(df)
        
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
    
    def test_validate_negative_values(self):
        """Test that negative values in quantity/price are detected."""
        from src.data.validator import validate_dataset
        
        df = _create_sample_df()
        df.loc[0, "quantity"] = -5
        df.loc[1, "unit_price"] = -100
        
        result = validate_dataset(df)
        # Should have warnings or errors about negatives
        all_issues = result["errors"] + result["warnings"]
        negative_issues = [i for i in all_issues if "negative" in i["problem"].lower()]
        assert len(negative_issues) > 0
    
    def test_validate_duplicates(self):
        """Test that duplicate rows are detected."""
        from src.data.validator import validate_dataset
        
        df = _create_sample_df()
        df = pd.concat([df, df.head(5)], ignore_index=True)  # Add duplicates
        
        result = validate_dataset(df)
        dup_issues = [i for i in result["warnings"] if "duplicate" in i["problem"].lower()]
        assert len(dup_issues) > 0

    def test_validate_empty_dataset(self):
        from src.data.validator import validate_dataset

        result = validate_dataset(pd.DataFrame(columns=["date"]))
        assert not result["is_valid"]
        assert any("no rows" in issue["problem"].lower() for issue in result["errors"])

    def test_validate_impossible_discount_and_returns(self):
        from src.data.validator import validate_dataset

        df = _create_sample_df()
        df.loc[0, "discount"] = 125
        df.loc[1, "returns"] = df.loc[1, "quantity"] + 1

        result = validate_dataset(df)
        problems = [issue["problem"] for issue in result["errors"]]
        assert any("outside 0" in problem for problem in problems)
        assert any("Returns exceed quantity" in problem for problem in problems)

    def test_validate_infinite_numeric_value(self):
        from src.data.validator import validate_dataset

        df = _create_sample_df()
        df.loc[0, "unit_price"] = np.inf

        result = validate_dataset(df)
        assert any("infinite" in issue["problem"].lower() for issue in result["errors"])


class TestDataCleaner:
    """Tests for data cleaning module."""
    
    def test_clean_valid_data(self):
        """Test cleaning valid data returns valid output."""
        from src.data.cleaner import clean_dataset
        
        df = _create_sample_df()
        cleaned, report = clean_dataset(df)
        
        assert len(cleaned) > 0
        assert report["original_rows"] == 100
        assert "revenue" in cleaned.columns
        assert "gross_profit" in cleaned.columns
    
    def test_clean_removes_duplicates(self):
        """Test that duplicates are removed."""
        from src.data.cleaner import clean_dataset
        
        df = _create_sample_df()
        df = pd.concat([df, df.head(5)], ignore_index=True)
        
        cleaned, report = clean_dataset(df)
        assert report["duplicates_removed"] == 5
    
    def test_derived_columns_computed(self):
        """Test that derived columns are correctly computed."""
        from src.data.cleaner import compute_derived_columns
        
        df = pd.DataFrame({
            "quantity": [10],
            "unit_price": [100.0],
            "discount": [10.0],
            "cost_per_unit": [50.0],
            "returns": [1],
        })
        
        result = compute_derived_columns(df)
        
        assert result["discount_rate"].iloc[0] == 0.1
        assert result["net_price"].iloc[0] == 90.0
        assert result["revenue"].iloc[0] == 900.0
        assert result["cost"].iloc[0] == 500.0
        assert result["gross_profit"].iloc[0] == 400.0

"""
Tests for data loading, validation, and cleaning modules.
"""

import pytest
from io import BytesIO
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

    def test_load_maps_marketplace_headers(self, tmp_path):
        from src.data.loader import load_file

        path = tmp_path / "marketplace.csv"
        path.write_text(
            "Order_Date,Sub_Order_Num,Quanity,Total_Taxable_Sale_Value,"
            "End_Customer_State_New,HSN_Code,Platform_Note\n"
            "2026-01-31,SUB-1,2,240.00,MAHARASHTRA,610910,keep me\n"
        )

        loaded, metadata = load_file(path)

        assert loaded.loc[0, "date"] == pd.Timestamp("2026-01-31")
        assert loaded.loc[0, "order_id"] == "SUB-1"
        assert loaded.loc[0, "quantity"] == 2
        assert loaded.loc[0, "revenue"] == 240.0
        assert loaded.loc[0, "region"] == "MAHARASHTRA"
        assert loaded.loc[0, "category"] == 610910
        assert loaded.loc[0, "platform_note"] == "keep me"
        assert any(item["match"] == "similar name" for item in metadata["column_mappings"])

    def test_load_reports_colliding_header_matches(self, tmp_path):
        from src.data.loader import load_csv

        path = tmp_path / "ambiguous.csv"
        path.write_text("order_id,order number\nA1,A-001\n")

        with pytest.raises(ValueError, match="same business field"):
            load_csv(path)

    def test_sales_and_returns_are_linked_without_counting_refunds_as_sales(self, tmp_path):
        from src.data.loader import load_business_files

        sales = tmp_path / "sales.csv"
        sales.write_text(
            "order_id,date,quantity,revenue\n"
            "A,2026-01-01,1,100\n"
            "B,2026-01-02,1,50\n"
        )
        returns = tmp_path / "sales_return.csv"
        returns.write_text(
            "order_id,date,quantity,revenue,cancel_return_date\n"
            "A,2026-01-01,1,25,2026-01-10\n"
            "OLD,2025-12-20,1,5,2026-01-05\n"
        )

        loaded, metadata = load_business_files([sales, returns])

        assert len(loaded) == 2
        assert loaded["revenue"].sum() == 150
        assert loaded.loc[loaded["order_id"] == "A", "returns"].item() == 1
        assert loaded.loc[loaded["order_id"] == "A", "returned_revenue"].item() == 25
        assert metadata["return_summary"]["matched_rows"] == 1
        assert metadata["return_summary"]["unmatched_rows"] == 1
        assert metadata["return_summary"]["unmatched_value"] == 5

    def test_return_report_needs_sales_file(self, tmp_path):
        from src.data.loader import load_business_files

        returns = tmp_path / "returns.csv"
        returns.write_text(
            "order_id,date,quantity,revenue,cancel_return_date\n"
            "A,2026-01-01,1,25,2026-01-10\n"
        )

        with pytest.raises(ValueError, match="at least one sales report"):
            load_business_files([returns])

    def test_upload_workflow_cleans_valid_sales_and_return_reports(self):
        from ui.session_state import prepare_uploaded_files

        class Upload(BytesIO):
            def __init__(self, name, content):
                super().__init__(content.encode())
                self.name = name
                self.size = len(content)
                self.file_id = name

        sales = Upload(
            "sales.csv",
            "order_id,date,quantity,revenue\nA,2026-01-01,1,100\nB,2026-01-02,1,50\n",
        )
        returns = Upload(
            "sales_return.csv",
            "order_id,date,quantity,revenue,cancel_return_date\n"
            "A,2026-01-01,1,25,2026-01-10\nOLD,2025-12-20,1,5,2026-01-05\n",
        )
        state = {"models": {"old": True}}

        validation = prepare_uploaded_files([sales, returns], state, "upload_signature")

        assert validation["is_valid"]
        assert state["cleaned_df"] is not None
        assert state["cleaned_df"]["revenue"].sum() == 150
        assert state["cleaned_df"]["net_revenue"].sum() == 125
        assert state["models"] is None
        assert prepare_uploaded_files([sales, returns], state, "upload_signature") is None

    def test_load_rejects_duplicate_normalized_columns(self, tmp_path):
        from src.data.loader import load_csv

        csv_path = tmp_path / "duplicate_columns.csv"
        csv_path.write_text("date, Date \n2024-01-01,2024-01-02\n")

        with pytest.raises(ValueError, match="duplicated"):
            load_csv(csv_path)

    def test_load_tsv(self, tmp_path):
        from src.data.loader import load_file

        path = tmp_path / "sales.tsv"
        path.write_text("order_id\tquantity\nA1\t3\n")

        loaded, metadata = load_file(path)
        assert loaded.loc[0, "quantity"] == 3
        assert metadata["file_type"] == "TSV"

    def test_load_json_and_json_lines(self, tmp_path):
        from src.data.loader import load_file

        records = [{"Order_ID": "A1", "quantity": 3}]
        json_path = tmp_path / "sales.json"
        json_path.write_text('[{"Order_ID":"A1","quantity":3}]')
        lines_path = tmp_path / "sales.jsonl"
        lines_path.write_text('{"Order_ID":"A1","quantity":3}\n')

        for path in (json_path, lines_path):
            loaded, metadata = load_file(path)
            assert loaded.loc[0, "order_id"] == records[0]["Order_ID"]
            assert metadata["rows_loaded"] == 1

    def test_load_xlsx(self, tmp_path):
        from src.data.loader import load_file

        path = tmp_path / "sales.xlsx"
        pd.DataFrame({"Order_ID": ["A1"], "quantity": [3]}).to_excel(path, index=False)

        loaded, metadata = load_file(path)
        assert loaded.loc[0, "quantity"] == 3
        assert metadata["file_type"] == "Excel"

    def test_xls_uses_legacy_excel_reader(self, tmp_path, monkeypatch):
        from src.data import loader

        path = tmp_path / "sales.xls"
        path.touch()
        calls = []

        def fake_read_excel(file_path, engine):
            calls.append(engine)
            return pd.DataFrame({"Order_ID": ["A1"]})

        monkeypatch.setattr(loader.pd, "read_excel", fake_read_excel)
        loaded, _ = loader.load_file(path)
        assert calls == ["xlrd"]
        assert loaded.loc[0, "order_id"] == "A1"

    def test_load_parquet(self, tmp_path):
        from src.data.loader import load_file

        path = tmp_path / "sales.parquet"
        pd.DataFrame({"Order_ID": ["A1"], "quantity": [3]}).to_parquet(path)

        loaded, metadata = load_file(path)
        assert loaded.loc[0, "quantity"] == 3
        assert metadata["file_type"] == "Parquet"

    def test_unsupported_file_type_has_helpful_message(self, tmp_path):
        from src.data.loader import load_file

        path = tmp_path / "sales.pdf"
        path.touch()
        with pytest.raises(ValueError, match="Unsupported file type"):
            load_file(path)


class TestDataValidator:
    """Tests for data validation module."""
    
    def test_validate_valid_data(self):
        """Test that valid data passes validation."""
        from src.data.validator import validate_dataset
        
        df = _create_sample_df()
        result = validate_dataset(df)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_sales_data_without_optional_fields(self):
        from src.data.validator import validate_dataset

        df = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=3),
            "quantity": [1, 2, 1],
            "revenue": [100.0, 200.0, 100.0],
        })

        result = validate_dataset(df)

        assert result["is_valid"]
        assert not result["errors"]
        assert any("optional business fields" in issue["problem"] for issue in result["warnings"])

    def test_empty_unrecognized_column_does_not_block_sales_data(self):
        from src.data.validator import validate_dataset

        df = pd.DataFrame({
            "date": pd.to_datetime(["2026-01-31"]),
            "quantity": [1],
            "revenue": [100.0],
            "enrollment_no": [None],
        })

        result = validate_dataset(df)

        assert result["is_valid"]
        assert any("enrollment_no" in issue["problem"] for issue in result["warnings"])
    
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

    def test_cleaner_keeps_reported_revenue_and_derives_unit_price(self):
        from src.data.cleaner import clean_dataset

        df = pd.DataFrame({
            "date": pd.date_range("2026-01-01", periods=3),
            "quantity": [1, 2, 1],
            "revenue": [125.0, 400.0, 80.0],
        })

        cleaned, _ = clean_dataset(df)

        assert cleaned["revenue"].tolist() == [125.0, 400.0, 80.0]
        assert cleaned["unit_price"].tolist() == [125.0, 200.0, 80.0]
        assert "gross_profit" not in cleaned.columns

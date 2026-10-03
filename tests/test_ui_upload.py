"""Streamlit checks for the upload-to-analysis handoff."""

from pathlib import Path
import sys

import pandas as pd
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_upload_pages_accept_multiple_reports_and_render_prepared_data():
    app = AppTest.from_file(Path(__file__).parent.parent / "app.py").run()
    assert app.get("file_uploader")[0].proto.multiple_files

    sales = pd.DataFrame({
        "date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "order_id": ["A", "B"],
        "quantity": [1, 1],
        "revenue": [100.0, 50.0],
        "returns": [1, 0],
        "returned_revenue": [25.0, 0.0],
        "net_revenue": [75.0, 50.0],
    })
    app.session_state["df"] = sales
    app.session_state["cleaned_df"] = sales
    app.session_state["loading_metadata"] = {
        "source_files": ["sales.csv", "sales_return.csv"],
        "return_summary": {
            "rows": 1,
            "matched_rows": 1,
            "unmatched_rows": 0,
            "matched_value": 25.0,
            "return_value": 25.0,
            "match_note": "All return rows matched to a unique sales order.",
        },
    }
    app.run()

    assert not app.exception
    assert any(metric.label == "Net Revenue After Matched Returns" for metric in app.metric)

    app.radio[0].set_value("📁 Data Explorer").run()
    assert not app.exception
    assert app.get("file_uploader")[0].proto.multiple_files


def test_invalid_overview_upload_has_a_data_explorer_path():
    app = AppTest.from_file(Path(__file__).parent.parent / "app.py").run()
    app.session_state["df"] = pd.DataFrame({"unexpected": [1]})
    app.session_state["cleaned_df"] = None
    app.run()

    assert any(button.label == "Review upload in Data Explorer" for button in app.button)
    app.button[0].click().run()
    assert not app.exception
    assert app.radio[0].value == "📁 Data Explorer"

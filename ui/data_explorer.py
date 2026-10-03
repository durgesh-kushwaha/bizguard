"""
Data Explorer page for BizGuard.

Allows users to:
- Upload CSV/Excel files
- Select sample dataset
- View data quality report
- Preview cleaned data
"""

import streamlit as st
import pandas as pd
import logging
from src.data.loader import SUPPORTED_FILE_TYPES, load_sample_data
from src.data.validator import validate_dataset
from src.data.cleaner import clean_dataset
from src.utils.formatting import format_number, severity_emoji
from ui.session_state import clear_analysis_results, prepare_uploaded_files

logger = logging.getLogger(__name__)


def render():
    """Render the Data Explorer page."""
    st.title("📁 Data Explorer")
    st.caption("Upload your business data or use the sample dataset to get started.")
    
    # Data source selection
    tab_upload, tab_sample = st.tabs(["📤 Upload Data", "📊 Sample Dataset"])
    
    with tab_upload:
        _render_upload_section()
    
    with tab_sample:
        _render_sample_section()
    
    st.markdown("---")
    
    # Show data if loaded
    if st.session_state.get("df") is not None:
        _render_data_info()
        _render_validation_report()
        _render_cleaning_section()
        _render_data_preview()
        _render_spark_processing()


def _render_upload_section():
    """Render file upload section."""
    st.markdown("### Upload Your Data")
    st.markdown("""
    Upload one or more related business reports from your device.
    
    **Required:** a transaction date, quantity, and either a unit price or sales amount.
    Product, customer, cost, marketing, return, region, and stock fields are optional.
    BizGuard recognizes common marketplace header names automatically.
    """)
    
    uploaded_file = st.file_uploader(
        "Choose business data files",
        type=SUPPORTED_FILE_TYPES,
        accept_multiple_files=True,
        help="Choose matching sales exports and a returns report together. CSV, TSV, Excel, JSON, JSON Lines, or Parquet files are supported.",
        key="data_explorer_upload",
    )

    if uploaded_file:
        try:
            with st.spinner("Loading and preparing reports..."):
                validation = prepare_uploaded_files(
                    uploaded_file,
                    st.session_state,
                    "data_explorer_upload_signature",
                )
            if validation is not None and validation["is_valid"]:
                st.success("Reports loaded, validated, and prepared for analysis.")
            elif validation is not None:
                st.warning("The reports loaded, but validation found issues. Review them below.")
        except ValueError as e:
            st.error(f"❌ Failed to load file: {e}")
        except Exception as e:
            logger.exception("Could not load uploaded business data")
            st.error("The file could not be loaded. Check that it is a supported, readable business data file.")


def _render_sample_section():
    """Render sample dataset section."""
    st.markdown("### Sample Dataset")
    st.markdown("""
    Use the built-in synthetic business dataset for demonstration.
    
    ⚠️ **Note:** This is synthetic demo data generated for testing purposes.
    It does NOT represent real business data.
    """)
    
    if st.button("🚀 Load Sample Dataset", type="primary"):
        try:
            with st.spinner("Generating and loading sample data..."):
                df, metadata = load_sample_data()
                clear_analysis_results(st.session_state)
                st.session_state.df = df
                st.session_state.loading_metadata = metadata
            
            st.success(f"✅ Sample data loaded: {metadata['rows_loaded']:,} rows.")
            st.rerun()
        except Exception as e:
            logger.exception("Could not load the sample dataset")
            st.error("The sample dataset could not be loaded. Check that the sample CSV is present and readable.")


def _render_data_info():
    """Render dataset information."""
    df = st.session_state.df
    metadata = st.session_state.get("loading_metadata", {})
    
    st.markdown("### 📋 Dataset Information")
    source_files = metadata.get("source_files", [])
    if source_files:
        st.caption("Source files: " + ", ".join(source_files))
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rows", format_number(len(df)))
    with col2:
        st.metric("Columns", format_number(len(df.columns)))
    with col3:
        missing = df.isnull().sum().sum()
        st.metric("Missing Values", format_number(missing))
    with col4:
        duplicates = df.duplicated().sum()
        st.metric("Duplicate Rows", format_number(duplicates))

    mappings = metadata.get("column_mappings", [])
    if mappings:
        with st.expander("Recognized upload headers"):
            mapping_table = pd.DataFrame(mappings).rename(columns={
                "source": "Uploaded column",
                "field": "BizGuard field",
                "match": "Recognition",
                "source_file": "File",
            })
            st.dataframe(mapping_table, use_container_width=True, hide_index=True)
    uncertain = metadata.get("uncertain_columns", [])
    if uncertain:
        headers = ", ".join(item["source"] for item in uncertain)
        st.warning(f"Some headers were left unchanged because their meaning was unclear: {headers}.")

    return_summary = metadata.get("return_summary")
    if return_summary:
        st.info(
            f"Returns: {return_summary['rows']:,} rows, "
            f"{return_summary['matched_rows']:,} linked to unique sales orders; "
            f"matched taxable return value {return_summary['matched_value']:,.2f} "
            f"out of {return_summary['return_value']:,.2f} reported."
        )
        if return_summary["unmatched_rows"]:
            st.warning(return_summary["match_note"])
    
    # Column information
    with st.expander("📊 Column Details"):
        col_info = pd.DataFrame({
            "Column": df.columns,
            "Type": df.dtypes.astype(str).values,
            "Non-Null": df.count().values,
            "Missing": df.isnull().sum().values,
            "Unique": df.nunique().values,
        })
        st.dataframe(col_info, use_container_width=True, hide_index=True)


def _render_validation_report():
    """Render data validation report."""
    df = st.session_state.df
    
    st.markdown("### ✅ Data Validation")
    
    validation = validate_dataset(df)
    
    st.markdown(validation["summary"])
    
    if validation["errors"]:
        st.markdown("#### Errors")
        for issue in validation["errors"]:
            with st.expander(f"{severity_emoji('error')} {issue['problem']}"):
                st.markdown(f"**Why it matters:** {issue['why_it_matters']}")
                st.markdown(f"**Expected:** {issue['expected']}")
                st.markdown(f"**Suggested fix:** {issue['suggested_fix']}")
                if issue.get("columns"):
                    st.markdown(f"**Fields not found:** {', '.join(issue['columns'])}")
    
    if validation["warnings"]:
        st.markdown("#### Warnings")
        for issue in validation["warnings"]:
            with st.expander(f"{severity_emoji('warning')} {issue['problem']}"):
                st.markdown(f"**Why it matters:** {issue['why_it_matters']}")
                st.markdown(f"**Expected:** {issue['expected']}")
                st.markdown(f"**Suggested fix:** {issue['suggested_fix']}")
                if issue.get("columns"):
                    st.markdown(f"**Fields not found:** {', '.join(issue['columns'])}")


def _render_cleaning_section():
    """Render data cleaning controls and report."""
    df = st.session_state.df
    
    st.markdown("### 🧹 Data Cleaning")
    
    if st.session_state.get("cleaned_df") is None:
        if st.button("🔄 Clean & Preprocess Data", type="primary"):
            with st.spinner("Cleaning data..."):
                validation = validate_dataset(df)
                if not validation["is_valid"]:
                    st.error("Fix the validation errors above before cleaning this dataset.")
                    return
                try:
                    cleaned_df, report = clean_dataset(df)
                except (ValueError, TypeError) as e:
                    st.error(f"This dataset could not be cleaned: {e}")
                    return
                st.session_state.cleaned_df = cleaned_df
                st.session_state.cleaning_report = report
            st.rerun()
    else:
        report = st.session_state.get("cleaning_report", {})
        
        st.success("✅ Data has been cleaned and preprocessed.")
        
        # Cleaning summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Original Rows", format_number(report.get("original_rows", 0)))
        with col2:
            st.metric("Final Rows", format_number(report.get("final_rows", 0)))
        with col3:
            st.metric("Rows Removed", format_number(report.get("rows_removed", 0)))
        with col4:
            st.metric("Missing Handled", format_number(report.get("missing_values_handled", 0)))
        
        # Detailed cleaning steps
        with st.expander("📝 Cleaning Details"):
            for step in report.get("cleaning_steps", []):
                st.markdown(f"• {step}")
            
            if report.get("columns_transformed"):
                st.markdown("**Columns transformed:**")
                for col in report["columns_transformed"]:
                    st.markdown(f"• {col}")


def _render_data_preview():
    """Render a preview of the data."""
    st.markdown("### 👁️ Data Preview")
    
    show_cleaned = st.session_state.get("cleaned_df") is not None
    
    if show_cleaned:
        tab_raw, tab_clean = st.tabs(["Raw Data", "Cleaned Data"])
        with tab_raw:
            st.dataframe(_preview_rows(st.session_state.df), use_container_width=True)
        with tab_clean:
            st.dataframe(_preview_rows(st.session_state.cleaned_df), use_container_width=True)
    else:
        st.dataframe(_preview_rows(st.session_state.df), use_container_width=True)
    
    # Basic statistics
    with st.expander("📊 Descriptive Statistics"):
        display_df = st.session_state.cleaned_df if show_cleaned else st.session_state.df
        numeric_columns = display_df.select_dtypes(include="number")
        st.dataframe(numeric_columns.describe().round(2), use_container_width=True)


def _preview_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep date values readable in the tabular preview."""
    preview = df.head(100).copy()
    if "date" in preview.columns:
        preview["date"] = pd.to_datetime(preview["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    return preview


def _render_spark_processing():
    """Render PySpark processing section."""
    if st.session_state.get("cleaned_df") is None:
        return

    spark_fields = {
        "product_id", "unit_price", "cost_per_unit", "discount", "returns"
    }
    missing_fields = sorted(spark_fields - set(st.session_state.cleaned_df.columns))
    if missing_fields:
        st.info(
            "The Spark demonstration needs these source fields: "
            f"{', '.join(missing_fields)}. Pandas analysis and forecasting are still available."
        )
        return
    
    st.markdown("### ⚡ Big Data Processing (PySpark)")
    st.caption("Process the cleaned data through the PySpark pipeline to demonstrate big data processing concepts.")
    
    if st.session_state.get("spark_metadata") is None:
        if st.button("🔥 Run Spark Processing"):
            with st.spinner("Running PySpark pipeline..."):
                try:
                    from src.bda.spark_processing import run_spark_pipeline
                    processed_df, metadata = run_spark_pipeline(st.session_state.cleaned_df)
                    st.session_state.cleaned_df = processed_df
                    st.session_state.spark_metadata = metadata
                    st.rerun()
                except Exception as e:
                    st.error(f"Spark processing failed: {e}")
                    st.info("The analytics will work using Pandas as a fallback.")
    else:
        metadata = st.session_state.spark_metadata
        
        if metadata.get("spark_available") and metadata.get("status") == "Completed":
            st.success(f"Spark processing completed using **{metadata.get('engine', 'Unknown')}**.")
        else:
            reason = metadata.get("error", "Check that Java 17+ and PySpark are installed.")
            st.warning(f"PySpark did not run; the app kept your data and used the Pandas fallback. {reason}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Engine", metadata.get("engine", "N/A"))
        with col2:
            st.metric("Input Rows", format_number(metadata.get("input_rows", 0)))
        with col3:
            st.metric("Output Rows", format_number(metadata.get("output_rows", 0)))
        with col4:
            partitions = metadata.get("partitions", "N/A")
            st.metric("Partitions", partitions)
        
        if metadata.get("spark_available"):
            with st.expander("🔧 Spark Processing Details"):
                st.markdown(f"**Spark Version:** {metadata.get('spark_version', 'N/A')}")
                st.markdown(f"**Master:** {metadata.get('master', 'N/A')}")
                st.markdown(f"**Status:** {metadata.get('status', 'N/A')}")
                
                if metadata.get("transformations"):
                    st.markdown("**Transformations Applied:**")
                    for t in metadata["transformations"]:
                        st.markdown(f"• {t}")
                
                st.info(
                    "The prototype uses PySpark to demonstrate distributed-data-processing concepts. "
                    "The architecture is designed to scale to larger datasets."
                )

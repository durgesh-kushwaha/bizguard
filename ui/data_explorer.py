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
from src.data.loader import load_file, load_sample_data
from src.data.validator import validate_dataset
from src.data.cleaner import clean_dataset
from src.utils.formatting import format_number, severity_emoji


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
    Upload a CSV or Excel file with your business transaction data.
    
    **Required columns:** `date`, `order_id`, `product_id`, `product_name`, `category`,
    `quantity`, `unit_price`, `discount`, `cost_per_unit`, `marketing_spend`, `returns`,
    `customer_id`, `region`, `inventory_units`
    """)
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls"],
        help="Supported formats: CSV, Excel (.xlsx, .xls)",
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Loading data..."):
                df, metadata = load_file(uploaded_file)
                st.session_state.df = df
                st.session_state.loading_metadata = metadata
                st.session_state.cleaned_df = None  # Reset cleaned data
                st.session_state.models = None  # Reset models
            
            st.success(f"✅ Loaded {metadata['rows_loaded']:,} rows and {metadata['columns_loaded']} columns.")
        except ValueError as e:
            st.error(f"❌ Failed to load file: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")


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
                st.session_state.df = df
                st.session_state.loading_metadata = metadata
                st.session_state.cleaned_df = None
                st.session_state.models = None
            
            st.success(f"✅ Sample data loaded: {metadata['rows_loaded']:,} rows.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to load sample data: {e}")


def _render_data_info():
    """Render dataset information."""
    df = st.session_state.df
    metadata = st.session_state.get("loading_metadata", {})
    
    st.markdown("### 📋 Dataset Information")
    
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
    
    if validation["warnings"]:
        st.markdown("#### Warnings")
        for issue in validation["warnings"]:
            with st.expander(f"{severity_emoji('warning')} {issue['problem']}"):
                st.markdown(f"**Why it matters:** {issue['why_it_matters']}")
                st.markdown(f"**Expected:** {issue['expected']}")
                st.markdown(f"**Suggested fix:** {issue['suggested_fix']}")


def _render_cleaning_section():
    """Render data cleaning controls and report."""
    df = st.session_state.df
    
    st.markdown("### 🧹 Data Cleaning")
    
    if st.session_state.get("cleaned_df") is None:
        if st.button("🔄 Clean & Preprocess Data", type="primary"):
            with st.spinner("Cleaning data..."):
                cleaned_df, report = clean_dataset(df)
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
            st.dataframe(st.session_state.df.head(100), use_container_width=True)
        with tab_clean:
            st.dataframe(st.session_state.cleaned_df.head(100), use_container_width=True)
    else:
        st.dataframe(st.session_state.df.head(100), use_container_width=True)
    
    # Basic statistics
    with st.expander("📊 Descriptive Statistics"):
        display_df = st.session_state.cleaned_df if show_cleaned else st.session_state.df
        st.dataframe(display_df.describe().round(2), use_container_width=True)


def _render_spark_processing():
    """Render PySpark processing section."""
    if st.session_state.get("cleaned_df") is None:
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
        
        st.success(f"✅ Spark processing completed using **{metadata.get('engine', 'Unknown')}**.")
        
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
        elif not metadata.get("spark_available"):
            st.warning(
                "PySpark was not available. Data was processed using Pandas as a fallback. "
                "Install PySpark (`pip install pyspark`) and ensure Java is available for full BDA demonstration."
            )

"""Helpers for state shared across BizGuard pages."""


def clear_analysis_results(session_state):
    """Clear results that belong to a dataset being replaced."""
    for key in (
        "cleaned_df", "cleaning_report", "spark_metadata", "models",
        "model_evaluations", "feature_cols", "ml_df", "current_forecast",
        "X_test", "y_test", "preprocessing_summary",
    ):
        session_state[key] = None


def prepare_uploaded_files(uploaded_files, session_state, signature_key):
    """Load, validate, and clean a new upload before analysis uses it."""
    signature = tuple(sorted(
        (
            getattr(item, "name", str(item)),
            getattr(item, "size", 0),
            str(getattr(item, "file_id", "")),
        )
        for item in uploaded_files
    ))
    if signature == session_state.get(signature_key):
        return None

    from src.data.cleaner import clean_dataset
    from src.data.loader import load_business_files
    from src.data.validator import validate_dataset

    df, metadata = load_business_files(uploaded_files)
    validation = validate_dataset(df)
    cleaned = clean_dataset(df) if validation["is_valid"] else (None, None)

    clear_analysis_results(session_state)
    session_state["df"] = df
    session_state["loading_metadata"] = metadata
    session_state["validation_report"] = validation
    session_state[signature_key] = signature
    if cleaned[0] is not None:
        session_state["cleaned_df"], session_state["cleaning_report"] = cleaned
    return validation

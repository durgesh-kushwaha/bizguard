"""Helpers for state shared across BizGuard pages."""


def clear_analysis_results(session_state):
    """Clear results that belong to a dataset being replaced."""
    for key in (
        "cleaned_df", "cleaning_report", "spark_metadata", "models",
        "model_evaluations", "feature_cols", "ml_df", "current_forecast",
        "X_test", "y_test", "preprocessing_summary",
    ):
        session_state[key] = None

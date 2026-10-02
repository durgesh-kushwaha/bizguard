"""
Model evaluation module for BizGuard.

Evaluates ML models using standard regression metrics.
All metrics are computed from actual model predictions — never hardcoded.

Metrics:
- MAE (Mean Absolute Error): Average prediction error in original units
- RMSE (Root Mean Squared Error): Penalizes large errors more
- R² (Coefficient of Determination): Proportion of variance explained
"""

import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict, Any, List


def evaluate_model(model: Any, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
    """
    Evaluate a trained model on test data.
    
    Metrics explanation:
    - MAE: On average, predictions are off by this many units.
      Lower is better.
    - RMSE: Like MAE but penalizes large errors more heavily.
      Lower is better.
    - R²: 1.0 = perfect prediction, 0.0 = predicts the mean,
      negative = worse than predicting the mean.
    
    Args:
        model: Trained sklearn model.
        X_test: Test features.
        y_test: True test values.
    
    Returns:
        Dict with evaluation metrics.
    """
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    # Additional analysis
    errors = y_test.values - y_pred
    
    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "mean_error": round(np.mean(errors), 4),
        "std_error": round(np.std(errors), 4),
        "max_overestimate": round(np.min(errors), 4),
        "max_underestimate": round(np.max(errors), 4),
        "predictions": y_pred,
        "actuals": y_test.values,
    }


def compare_models(evaluations: Dict[str, Dict]) -> pd.DataFrame:
    """
    Compare multiple models side by side.
    
    Args:
        evaluations: Dict mapping model_name -> evaluation results.
    
    Returns:
        DataFrame with model comparison.
    """
    rows = []
    for model_name, eval_result in evaluations.items():
        rows.append({
            "Model": model_name,
            "MAE": eval_result["mae"],
            "RMSE": eval_result["rmse"],
            "R²": eval_result["r2"],
            "Mean Error": eval_result["mean_error"],
            "Std Error": eval_result["std_error"],
        })
    
    comparison = pd.DataFrame(rows)
    return comparison


def get_prediction_analysis(y_test: pd.Series, y_pred: np.ndarray) -> pd.DataFrame:
    """
    Create a detailed prediction vs actual analysis.
    
    Args:
        y_test: Actual values.
        y_pred: Predicted values.
    
    Returns:
        DataFrame with actual, predicted, error, and percentage error.
    """
    analysis = pd.DataFrame({
        "Actual": y_test.values,
        "Predicted": np.round(y_pred, 2),
        "Error": np.round(y_test.values - y_pred, 2),
        "Abs_Error": np.round(np.abs(y_test.values - y_pred), 2),
        "Pct_Error": np.where(
            y_test.values != 0,
            np.round(np.abs(y_test.values - y_pred) / np.abs(y_test.values) * 100, 2),
            0
        ),
    })
    
    return analysis


def get_evaluation_explanation(metrics: Dict) -> str:
    """
    Generate a human-readable explanation of model evaluation.
    
    Args:
        metrics: Evaluation metrics dict.
    
    Returns:
        Multi-line string explanation.
    """
    r2 = metrics["r2"]
    mae = metrics["mae"]
    rmse = metrics["rmse"]
    
    # Interpret R²
    if r2 >= 0.8:
        r2_interpretation = "strong predictive power"
    elif r2 >= 0.5:
        r2_interpretation = "moderate predictive power"
    elif r2 >= 0.2:
        r2_interpretation = "weak predictive power"
    else:
        r2_interpretation = "very limited predictive power"
    
    explanation = (
        f"The model explains {r2:.1%} of the variance in the target variable, "
        f"indicating {r2_interpretation}.\n\n"
        f"On average, predictions differ from actual values by {mae:.2f} units (MAE).\n"
        f"The RMSE of {rmse:.2f} suggests that larger prediction errors are "
        f"{'relatively rare' if rmse < mae * 1.5 else 'somewhat common'}.\n\n"
    )
    
    if r2 < 0.5:
        explanation += (
            "Note: The model has limited accuracy. This is expected with synthetic data "
            "and a relatively simple feature set. In production, additional features "
            "(customer behavior, external factors) would improve predictions."
        )
    
    return explanation

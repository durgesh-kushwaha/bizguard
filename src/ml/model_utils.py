"""
ML model utilities for BizGuard.

Handles model persistence (save/load) and helper functions.
"""

import joblib
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent.parent / "models"


def save_model(model: Any, model_name: str, metadata: dict = None) -> Path:
    """
    Save a trained model to disk.
    
    Args:
        model: Trained sklearn model.
        model_name: Name for the saved model file.
        metadata: Optional metadata to save alongside.
    
    Returns:
        Path to the saved model file.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    model_path = MODELS_DIR / f"{model_name}.joblib"
    joblib.dump({"model": model, "metadata": metadata}, model_path)
    
    logger.info(f"Model saved: {model_path}")
    return model_path


def load_model(model_name: str) -> Optional[dict]:
    """
    Load a trained model from disk.
    
    Args:
        model_name: Name of the model file (without extension).
    
    Returns:
        Dict with 'model' and 'metadata' keys, or None if not found.
    """
    model_path = MODELS_DIR / f"{model_name}.joblib"
    
    if not model_path.exists():
        logger.warning(f"Model not found: {model_path}")
        return None
    
    try:
        data = joblib.load(model_path)
        logger.info(f"Model loaded: {model_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None


def list_saved_models() -> list:
    """
    List all saved models.
    
    Returns:
        List of model file names.
    """
    if not MODELS_DIR.exists():
        return []
    
    return [f.stem for f in MODELS_DIR.glob("*.joblib")]

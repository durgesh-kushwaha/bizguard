"""
PySpark session management for BizGuard.

Provides a managed Spark session for big data processing.
Designed to gracefully handle environments where Spark is not available.
"""

import logging
import os
import shutil
import sys
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Global Spark session reference
_spark_session = None
_spark_available = None
_spark_error = None


def is_spark_available() -> bool:
    """
    Check if PySpark is available in the current environment.
    
    Returns:
        True if PySpark can be imported and a session can be created.
    """
    global _spark_available
    global _spark_error
    
    if _spark_available is not None:
        return _spark_available
    
    try:
        from pyspark.sql import SparkSession
        _spark_available = True
    except ImportError as e:
        logger.warning("PySpark is not installed. Big data features will use Pandas fallback.")
        _spark_available = False
        _spark_error = str(e)
    
    return _spark_available


def get_spark_session(app_name: str = "BizGuard-BDA") -> Optional[object]:
    """
    Get or create a PySpark SparkSession.
    
    Uses local mode for the prototype. The architecture supports
    switching to a cluster by changing the master URL.
    
    Args:
        app_name: Name for the Spark application.
    
    Returns:
        SparkSession if available, None otherwise.
    """
    global _spark_session
    global _spark_error
    
    if not is_spark_available():
        return None
    
    if _spark_session is not None:
        try:
            # Verify session is still alive
            _spark_session.sparkContext.getConf().get("spark.app.name")
            return _spark_session
        except Exception:
            _spark_session = None
    
    try:
        if sys.platform.startswith("linux") and not os.environ.get("JAVA_HOME"):
            java_path = shutil.which("java")
            if java_path:
                os.environ["JAVA_HOME"] = str(Path(java_path).resolve().parent.parent)

        from pyspark.sql import SparkSession
        
        _spark_session = (
            SparkSession.builder
            .appName(app_name)
            .master("local[*]")
            .config("spark.driver.memory", "1g")
            .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
            .config("spark.ui.showConsoleProgress", "false")
            .config("spark.log.level", "ERROR")
            .getOrCreate()
        )
        
        # Set log level to reduce noise
        _spark_session.sparkContext.setLogLevel("ERROR")
        
        logger.info(f"Spark session created: {app_name}")
        return _spark_session
    
    except Exception as e:
        _spark_error = str(e)
        logger.exception("Failed to create Spark session")
        _spark_available = False
        return None


def stop_spark_session():
    """Stop the current Spark session if it exists."""
    global _spark_session
    
    if _spark_session is not None:
        try:
            _spark_session.stop()
        except Exception:
            pass
        _spark_session = None


def get_spark_error() -> Optional[str]:
    """Return the last reason Spark could not start, if any."""
    return _spark_error


def get_spark_info() -> dict:
    """
    Get information about the current Spark session.
    Used for the BDA demonstration mode.
    
    Returns:
        Dict with Spark session details.
    """
    session = get_spark_session()
    
    if session is None:
        return {
            "available": False,
            "status": "Not Available",
            "message": _spark_error or "PySpark is not available. Using Pandas for data processing.",
        }
    
    try:
        sc = session.sparkContext
        return {
            "available": True,
            "status": "Active",
            "app_name": sc.appName,
            "master": sc.master,
            "spark_version": sc.version,
            "default_parallelism": sc.defaultParallelism,
            "driver_memory": sc.getConf().get("spark.driver.memory", "Unknown"),
        }
    except Exception as e:
        return {
            "available": False,
            "status": "Error",
            "message": str(e),
        }

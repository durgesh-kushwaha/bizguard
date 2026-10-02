"""BizGuard configuration settings."""
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "bizguard.db"

# Application settings
APP_NAME = "BizGuard"
APP_DESCRIPTION = "Business Decision Intelligence System"
APP_VERSION = "1.0.0"

# Data settings
REQUIRED_COLUMNS = [
    "date", "order_id", "product_id", "product_name", "category",
    "quantity", "unit_price", "discount", "cost_per_unit",
    "marketing_spend", "returns", "customer_id", "region",
    "inventory_units"
]

NUMERIC_COLUMNS = [
    "quantity", "unit_price", "discount", "cost_per_unit",
    "marketing_spend", "returns", "inventory_units"
]

DATE_COLUMNS = ["date"]

# Derived columns
DERIVED_COLUMNS = [
    "revenue", "gross_profit", "profit_margin", "net_revenue",
    "discount_rate", "sales_velocity"
]

# ML settings
ML_TARGET = "quantity"
ML_TEST_SIZE = 0.2
ML_RANDOM_STATE = 42

# Spark settings
SPARK_APP_NAME = "BizGuard-BDA"
SPARK_MASTER = "local[*]"

# Decision settings
SCENARIO_TYPES = ["Conservative", "Expected", "Optimistic"]
DECISION_TYPES = ["Pricing", "Inventory", "Marketing"]

# UI settings
PAGE_ICON = "🛡️"
LAYOUT = "wide"

"""
Synthetic Business Dataset Generator for BizGuard.

Generates realistic-looking business data with:
- Multiple products across categories
- Seasonal demand patterns
- Price sensitivity
- Marketing spend effects
- Regional variation
- Returns and discounts
- Inventory tracking

IMPORTANT: This is synthetic demo data, NOT real business data.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


# Product catalog with realistic pricing
PRODUCTS = {
    "Electronics": [
        {"id": "E001", "name": "Wireless Earbuds", "base_price": 1499, "cost": 750, "base_demand": 45},
        {"id": "E002", "name": "Bluetooth Speaker", "base_price": 2499, "cost": 1200, "base_demand": 30},
        {"id": "E003", "name": "Phone Case", "base_price": 399, "cost": 120, "base_demand": 80},
        {"id": "E004", "name": "USB-C Cable", "base_price": 299, "cost": 80, "base_demand": 100},
        {"id": "E005", "name": "Power Bank", "base_price": 999, "cost": 450, "base_demand": 40},
    ],
    "Home & Kitchen": [
        {"id": "H001", "name": "Water Bottle", "base_price": 499, "cost": 180, "base_demand": 60},
        {"id": "H002", "name": "Coffee Mug Set", "base_price": 799, "cost": 300, "base_demand": 35},
        {"id": "H003", "name": "Storage Container", "base_price": 349, "cost": 130, "base_demand": 50},
        {"id": "H004", "name": "Kitchen Towel Set", "base_price": 249, "cost": 90, "base_demand": 55},
    ],
    "Fashion": [
        {"id": "F001", "name": "Cotton T-Shirt", "base_price": 599, "cost": 200, "base_demand": 70},
        {"id": "F002", "name": "Sports Shoes", "base_price": 1999, "cost": 900, "base_demand": 25},
        {"id": "F003", "name": "Backpack", "base_price": 1299, "cost": 550, "base_demand": 30},
        {"id": "F004", "name": "Sunglasses", "base_price": 899, "cost": 300, "base_demand": 35},
    ],
    "Office": [
        {"id": "O001", "name": "Notebook Pack", "base_price": 199, "cost": 70, "base_demand": 90},
        {"id": "O002", "name": "Pen Set", "base_price": 149, "cost": 45, "base_demand": 85},
        {"id": "O003", "name": "Desk Organizer", "base_price": 699, "cost": 280, "base_demand": 25},
    ],
}

REGIONS = ["North", "South", "East", "West"]


def _seasonal_factor(month: int) -> float:
    """
    Return a seasonal demand multiplier based on month.

    Pattern:
    - Jan-Feb: Post-holiday dip (0.8)
    - Mar-May: Spring growth (1.0-1.1)
    - Jun-Aug: Summer steady (0.95-1.05)
    - Sep-Oct: Festival season surge (1.2-1.4)
    - Nov-Dec: Holiday peak (1.3-1.5)
    """
    seasonal_map = {
        1: 0.80, 2: 0.85,
        3: 1.00, 4: 1.05, 5: 1.10,
        6: 0.95, 7: 1.00, 8: 1.05,
        9: 1.20, 10: 1.35, 11: 1.45, 12: 1.50,
    }
    return seasonal_map.get(month, 1.0)


def _regional_factor(region: str) -> float:
    """Return a demand multiplier based on region."""
    regional_map = {
        "North": 1.15,
        "South": 1.10,
        "East": 0.90,
        "West": 1.00,
    }
    return regional_map.get(region, 1.0)


def generate_dataset(
    start_date: str = "2024-01-01",
    end_date: str = "2025-09-30",
    random_seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a synthetic business dataset.

    Args:
        start_date: Start date for the dataset (YYYY-MM-DD).
        end_date: End date for the dataset (YYYY-MM-DD).
        random_seed: Random seed for reproducibility.

    Returns:
        DataFrame with synthetic business transaction data.
    """
    np.random.seed(random_seed)

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    date_range = pd.date_range(start, end, freq="D")

    records = []
    order_counter = 1000

    for current_date in date_range:
        month = current_date.month
        day_of_week = current_date.dayofweek  # 0=Mon, 6=Sun
        seasonal = _seasonal_factor(month)

        # Weekend boost
        weekend_factor = 1.15 if day_of_week >= 5 else 1.0

        for category, products in PRODUCTS.items():
            for product in products:
                for region in REGIONS:
                    # Determine if this product sells today in this region
                    # Not every product sells every day in every region
                    daily_probability = min(
                        product["base_demand"] / 100 * 0.6, 0.95
                    )
                    if np.random.random() > daily_probability:
                        continue

                    order_counter += 1
                    regional = _regional_factor(region)

                    # Calculate demand with noise
                    base_qty = product["base_demand"] / 30  # daily demand
                    demand = base_qty * seasonal * regional * weekend_factor
                    quantity = max(1, int(np.random.poisson(max(1, demand))))

                    # Price variation (+/- 5% from base)
                    price_variation = np.random.uniform(0.95, 1.05)
                    unit_price = round(product["base_price"] * price_variation, 2)

                    # Discount: higher during festivals, some random promotions
                    if month in [9, 10, 11, 12]:
                        discount = np.random.choice(
                            [0, 0, 5, 10, 15, 20],
                            p=[0.2, 0.2, 0.2, 0.2, 0.1, 0.1],
                        )
                    else:
                        discount = np.random.choice(
                            [0, 0, 0, 5, 10],
                            p=[0.4, 0.2, 0.2, 0.1, 0.1],
                        )

                    # Marketing spend: category-level daily spend allocated per order
                    base_marketing = {
                        "Electronics": 500,
                        "Home & Kitchen": 300,
                        "Fashion": 400,
                        "Office": 200,
                    }
                    marketing_spend = round(
                        base_marketing[category]
                        * seasonal
                        * np.random.uniform(0.5, 1.5)
                        / len(products),
                        2,
                    )

                    # Returns: small percentage, higher for fashion
                    return_rate = {
                        "Electronics": 0.03,
                        "Home & Kitchen": 0.02,
                        "Fashion": 0.06,
                        "Office": 0.01,
                    }
                    returns = int(
                        quantity * return_rate[category] * np.random.uniform(0, 2)
                    )

                    # Inventory: base stock with seasonal ordering
                    base_inventory = product["base_demand"] * 3
                    inventory_units = max(
                        0,
                        int(
                            base_inventory
                            * np.random.uniform(0.5, 1.5)
                            * (1.2 if month in [8, 9, 10] else 1.0)
                        ),
                    )

                    # Customer IDs (some repeat customers)
                    customer_id = f"C{np.random.choice(range(1, 2001)):04d}"

                    record = {
                        "date": current_date.strftime("%Y-%m-%d"),
                        "order_id": f"ORD{order_counter:06d}",
                        "product_id": product["id"],
                        "product_name": product["name"],
                        "category": category,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "discount": discount,
                        "cost_per_unit": product["cost"],
                        "marketing_spend": marketing_spend,
                        "returns": returns,
                        "customer_id": customer_id,
                        "region": region,
                        "inventory_units": inventory_units,
                    }
                    records.append(record)

    df = pd.DataFrame(records)

    # Compute derived columns
    df["date"] = pd.to_datetime(df["date"])
    df["discount_rate"] = df["discount"] / 100.0
    df["net_price"] = df["unit_price"] * (1 - df["discount_rate"])
    df["revenue"] = (df["quantity"] * df["net_price"]).round(2)
    df["cost"] = (df["quantity"] * df["cost_per_unit"]).round(2)
    df["gross_profit"] = (df["revenue"] - df["cost"]).round(2)
    df["profit_margin"] = (
        (df["gross_profit"] / df["revenue"]).replace([np.inf, -np.inf], 0).round(4)
    )
    df["net_revenue"] = (df["revenue"] - df["returns"] * df["net_price"]).round(2)

    # Sort by date
    df = df.sort_values("date").reset_index(drop=True)

    return df


def save_sample_dataset(output_dir: Path = None) -> Path:
    """
    Generate and save the sample dataset to CSV.

    Args:
        output_dir: Directory to save the CSV. Defaults to data/sample/.

    Returns:
        Path to the saved CSV file.
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "data" / "sample"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "business_data.csv"

    df = generate_dataset()
    df.to_csv(output_path, index=False)

    print(f"Generated dataset: {len(df)} rows, {len(df.columns)} columns")
    print(f"Saved to: {output_path}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Products: {df['product_name'].nunique()}")
    print(f"Categories: {df['category'].nunique()}")
    print(f"Regions: {df['region'].nunique()}")

    return output_path


if __name__ == "__main__":
    save_sample_dataset()

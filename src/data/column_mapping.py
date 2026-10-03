"""Recognize common names used for business data columns."""

import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

import pandas as pd


ALIASES = {
    "date": (
        "order date", "date of order", "sale date", "sales date",
        "transaction date", "invoice date", "purchase date",
    ),
    "order_id": (
        "order number", "order no", "order ref", "sub order number",
        "sub order num", "sub order no", "suborder number", "transaction id",
        "invoice number", "invoice no", "order item id",
    ),
    "product_id": (
        "sku", "seller sku", "supplier sku", "product sku", "item sku", "item id",
        "variant id", "product code", "style code", "listing id",
    ),
    "product_name": (
        "item name", "product title", "item title", "listing name",
        "style name", "item description",
    ),
    "category": (
        "product category", "item category", "category name", "hsn",
        "hsn code", "commodity code",
    ),
    "quantity": (
        "qty", "units", "quantity sold", "units sold", "sold quantity",
        "sold qty", "sale quantity", "item quantity", "number of units",
    ),
    "unit_price": (
        "price", "selling price", "sale price", "item price", "price per unit",
        "unit selling price", "supplier discounted price", "discounted price",
    ),
    "revenue": (
        "total sales", "sales value", "sale value", "sale amount",
        "sales amount", "total sales amount", "total sale value",
        "taxable sale value", "total taxable sale value", "net sales",
        "net sales amount", "line total",
    ),
    "discount": (
        "discount percent", "discount percentage", "discount pct",
        "discount rate",
    ),
    "cost_per_unit": (
        "unit cost", "cost price", "purchase price", "cost per item",
        "product cost",
    ),
    "marketing_spend": (
        "ad spend", "advertising spend", "advertising cost", "marketing cost",
        "campaign spend",
    ),
    "returns": (
        "return quantity", "returned quantity", "return qty", "returned units",
        "units returned",
    ),
    "customer_id": (
        "buyer id", "customer number", "customer no", "buyer user id",
        "customer code",
    ),
    "region": (
        "state", "customer state", "shipping state", "delivery state",
        "destination state", "end customer state new", "customer location",
    ),
    "inventory_units": (
        "stock on hand", "available stock", "inventory quantity", "closing stock",
        "current stock", "stock quantity",
    ),
}

INTERNAL_COLUMNS = {
    "discount_rate", "net_price", "net_revenue", "gross_profit", "profit_margin",
    "cost", "sales_velocity", "year", "month", "day", "day_of_week",
    "week_of_year", "quarter", "is_weekend", "is_month_start", "is_month_end",
    "month_sin", "month_cos", "price_to_cost_ratio", "effective_discount",
    "marketing_per_unit", "return_rate", "inventory_to_sales",
    "returned_revenue",
}

FUZZY_THRESHOLD = 0.90
FUZZY_MARGIN = 0.07


def _key(value: str) -> str:
    """Reduce a header to words so spaces and punctuation do not matter."""
    return " ".join(re.findall(r"[a-z0-9]+", str(value).casefold()))


def _candidate_scores(header: str) -> List[Tuple[str, float]]:
    normalized = _key(header)
    scores = []
    for field, aliases in ALIASES.items():
        names = (field.replace("_", " "),) + aliases
        score = max(
            SequenceMatcher(None, normalized, _key(name)).ratio()
            for name in names
        )
        scores.append((field, score))
    return sorted(scores, key=lambda item: item[1], reverse=True)


def map_business_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict], List[Dict]]:
    """Rename recognized headers and return mappings and uncertain suggestions."""
    canonical = {
        _key(field): field for field in set(ALIASES).union(INTERNAL_COLUMNS)
    }
    aliases = {
        _key(alias): field
        for field, names in ALIASES.items()
        for alias in names
    }
    proposals = []
    uncertain = []

    for source in df.columns:
        normalized = _key(source)
        if normalized in canonical:
            proposals.append((source, canonical[normalized], "canonical field"))
            continue
        if normalized in aliases:
            proposals.append((source, aliases[normalized], "recognized name"))
            continue

        scores = _candidate_scores(source)
        best_field, best_score = scores[0]
        next_score = scores[1][1]
        if best_score >= FUZZY_THRESHOLD and best_score - next_score >= FUZZY_MARGIN:
            proposals.append((source, best_field, "similar name"))
        elif best_score >= FUZZY_THRESHOLD:
            uncertain.append({
                "source": source,
                "candidates": [field for field, score in scores[:3] if score >= FUZZY_THRESHOLD],
            })

    targets: Dict[str, List[str]] = {}
    for source, field, _ in proposals:
        targets.setdefault(field, []).append(str(source))
    collisions = {field: sources for field, sources in targets.items() if len(sources) > 1}
    if collisions:
        details = "; ".join(
            f"{field}: {', '.join(sources)}" for field, sources in collisions.items()
        )
        raise ValueError(
            "More than one uploaded column matches the same business field ("
            f"{details}). Keep the intended column and upload again."
        )

    mappings = [
        {"source": str(source), "field": field, "match": match}
        for source, field, match in proposals
        if str(source) != field
    ]
    rename = {source: field for source, field, _ in proposals if str(source) != field}
    return df.rename(columns=rename), mappings, uncertain

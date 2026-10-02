# Data Dictionary — BizGuard

## Raw Columns (Required Input)

| Column | Type | Description | Example |
|--------|------|-------------|--------|
| date | Date | Transaction date | 2024-06-15 |
| order_id | String | Unique order identifier | ORD001234 |
| product_id | String | Product identifier | E001 |
| product_name | String | Product display name | Wireless Earbuds |
| category | String | Product category | Electronics |
| quantity | Integer | Units sold in order | 3 |
| unit_price | Float | Selling price per unit (₹) | 1499.00 |
| discount | Float | Discount percentage (0-100) | 10 |
| cost_per_unit | Float | Cost per unit (₹) | 750.00 |
| marketing_spend | Float | Marketing spend allocated (₹) | 250.00 |
| returns | Integer | Units returned | 0 |
| customer_id | String | Customer identifier | C0042 |
| region | String | Sales region | North |
| inventory_units | Integer | Current inventory level | 120 |

## Derived Columns (Computed)

| Column | Formula | Description |
|--------|---------|-------------|
| discount_rate | discount / 100 | Decimal discount rate |
| net_price | unit_price × (1 - discount_rate) | Price after discount |
| revenue | quantity × net_price | Total order revenue |
| cost | quantity × cost_per_unit | Total order cost |
| gross_profit | revenue - cost | Gross profit |
| profit_margin | gross_profit / revenue | Profit margin ratio |
| net_revenue | revenue - (returns × net_price) | Revenue after returns |

## Data Quality Rules

- `quantity` must be ≥ 0
- `unit_price` must be > 0
- `cost_per_unit` must be ≥ 0
- `discount` must be between 0 and 100
- `date` must be a valid date
- All required columns must be present

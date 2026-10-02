# Decision Engine — BizGuard

## Overview

The Decision Engine is BizGuard's core feature. It allows users to simulate
business decisions and understand potential outcomes before committing.

## Decision Types

### 1. Pricing Decision
**Question:** What happens if I change a product's price?

**Inputs:** Product, current price, proposed price

**Method:**
- Estimates price elasticity from historical data
- Projects demand change under three scenarios
- Calculates revenue and profit impact
- Computes break-even volume

**Key Formula:**
- Elasticity = % change in quantity / % change in price
- New demand = current × (1 + price_change% × elasticity × sensitivity)

### 2. Inventory Decision
**Question:** Should I purchase additional inventory?

**Inputs:** Product, current inventory, proposed purchase

**Method:**
- Uses historical sales velocity
- Incorporates ML demand forecast (if available)
- Projects stock cover under three scenarios
- Calculates capital requirements

### 3. Marketing Decision
**Question:** What's the impact of changing marketing spend?

**Inputs:** Category, current spend, proposed spend

**Method:**
- Calculates historical ROAS
- Models diminishing returns
- Projects revenue/profit impact
- Computes break-even ROAS

## Scenario Framework

Each decision generates three scenarios:
- **Conservative** — Assumes worse-than-expected response
- **Expected** — Assumes response follows historical patterns
- **Optimistic** — Assumes better-than-expected response

## Decision Contract

Every saved decision creates a Decision Contract containing:
- Decision ID and timestamp
- Input parameters
- Expected outcome
- Historical evidence
- Scenario results
- Key assumptions
- Risk indicators
- Monitoring triggers
- Space for actual outcome (for later comparison)

## Transparency

- All calculations use documented formulas
- Assumptions are explicitly listed
- ROAS is labeled as correlation, not causation
- Elasticity is estimated, not proven
- Risks are clearly stated

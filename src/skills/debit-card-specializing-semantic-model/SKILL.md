---
name: debit-card-specializing-semantic-model
description: Semantic model for the debit_card_specializing database (Czech fuel card transactions — gas stations, customers, products, monthly aggregates). Load this skill when the user is querying the debit_card_specializing database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-25T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 4
---

# Debit Card Specializing — Semantic Model

## Available Resources

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | YYYYMM date format, Czech product names, country codes, segment values | `read_skill_resource("debit-card-specializing-semantic-model", "references/gotchas.md")` |
| Metric definitions | Spend per customer, monthly consumption, station-level aggregates | `read_skill_resource("debit-card-specializing-semantic-model", "references/metrics.md")` |
| Query patterns | Canonical SQL for customer spend, station queries, product filtering | `read_skill_resource("debit-card-specializing-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If filtering by date or month → load `references/gotchas.md` (date is an integer, not a DATE column)
- If filtering by product type or country → load `references/gotchas.md` (Czech text and abbreviations)
- If aggregating spend or consumption → load `references/metrics.md`
- For simple transaction lookups → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "monthly data" / "monthly consumption" | `yearmonth` table — `Date` column is an integer in YYYYMM format (e.g. `201207`) | verified |
| "transaction" | `transactions_1k` table — a sample of 1000 transactions | verified |
| "customer segment" | `customers.Segment` — values: `'SME'`, `'LAM'`, `'KAM'` (company size tiers) | verified |
| "gas station country" | `gasstations.Country` — values: `'CZE'`, `'SVK'`, `'HUN'` (not full names) | verified |
| "diesel" | `products.Description = 'Nafta'` (Czech for diesel) | verified |
| "station segment" | `gasstations.Segment` — values like `'Premium'`, `'Value'` | verified |

## Gotchas

1. **`yearmonth.Date` is an integer in YYYYMM format** — e.g. `201207` means
   July 2012. It is not a SQL DATE. To filter by year or month, use integer
   arithmetic: `Date / 100 = 2012` for year, `Date % 100 = 7` for month.

2. **Product descriptions are in Czech** — `'Nafta'` = diesel,
   `'Rucní zadání'` = manual entry. Filtering on English product names returns
   zero rows.

3. **Country codes are 3-letter abbreviations** — `'CZE'` (Czech Republic),
   `'SVK'` (Slovakia), `'HUN'` (Hungary). There are no full country names.

4. **`transactions_1k` is a 1000-row sample** — not the full transaction history.
   The `yearmonth` table has complete monthly aggregates per customer and is
   more reliable for total-spend queries.

5. **`customers.Segment` values are business size categories** — `'SME'` (small
   and medium enterprise), `'LAM'` (large account management), `'KAM'` (key
   account management). Not geographic segments.

For extended gotchas and SQL examples, call:
```python
read_skill_resource(
	skill_name="debit-card-specializing-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
customers.CustomerID     ──→  transactions_1k.CustomerID   (customer ↔ transactions)
customers.CustomerID     ──→  yearmonth.CustomerID          (customer ↔ monthly aggregates)
gasstations.GasStationID ──→  transactions_1k.GasStationID (station ↔ transactions)
products.ProductID       ──→  transactions_1k.ProductID     (product ↔ transactions)
```

`yearmonth` has no direct join to `gasstations` or `products` — it aggregates
consumption at the customer level only.

## Frequently Asked Queries

For canonical query patterns (spend by segment, monthly trends, station country
breakdowns), call:
```python
read_skill_resource(
	skill_name="debit-card-specializing-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas (total spend, monthly consumption, station-level
aggregates), call:
```python
read_skill_resource(
	skill_name="debit-card-specializing-semantic-model",
	resource_name="references/metrics.md"
)
```

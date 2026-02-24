---
name: debit-card-semantic-model
description: Semantic model for the debit_card_specializing database.
metadata:
  author: manual
  version: "1.0"
---

# Debit Card Specializing — Semantic Model
| Resource | How to load |
|---|---|
| Extended gotchas | `read_skill_resource("debit-card-semantic-model", "references/gotchas.md")` |
| Metric definitions | `read_skill_resource("debit-card-semantic-model", "references/metrics.md")` |
| Query patterns | `read_skill_resource("debit-card-semantic-model", "references/query_patterns.md")` |


## ENRICHMENT: recommended improvements
- Normalize currencies at ingestion: store `amount_base_currency` and `fx_rate` used; mark `currency` on transactions.
- Add `txn_local_date` as a DATE cast from timestamp with timezone for consistent day bucketing.
- Suggested metrics: spend by merchant category, customer 90-day rolling spend.

### Extra Query Patterns
-- Daily spend per currency
SELECT txn_local_date, currency, SUM(amount) as total_by_currency FROM transactions GROUP BY txn_local_date, currency ORDER BY txn_local_date DESC;

---
name: financial-semantic-model
description: Semantic model for the financial database (Czech banking dataset). Contains business definitions for banking (loans, accounts, transactions), and critical join logic across districts, accounts, and clients.
metadata:
  author: manual
  version: "1.0"
  last_updated: "2026-02-23T00:00:00Z"
---

# Financial — Semantic Model
| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | Date formats, NULL handling for loans, join pitfalls | `read_skill_resource("financial-semantic-model", "references/gotchas.md")` |
| Metric definitions | Formulas for balances, avg loan amounts, default rates | `read_skill_resource("financial-semantic-model", "references/metrics.md")` |
| Query patterns | Canonical SQL for regional stats, client demographics | `read_skill_resource("financial-semantic-model", "references/query_patterns.md")` |

| Term | Actual meaning |
|---|---|
| "loan status" | `loan.status` ('A'=Finished/OK, 'B'=Finished/Unpaid, 'C'=Running/OK, 'D'=Running/Debt) |
| "district" | `district.A2` (Name) or `district.A3` (Region) |
| "owner" | `disp.type = 'OWNER'` (vs 'DISPONENT') |

**Core Join Path:** `client.client_id` ──→ `disp.client_id` ──→ `account.account_id`


## ENRICHMENT: recommended improvements
- Normalize and document all date fields to ISO 8601 at ingestion; add explicit `date_source_format` metadata for YYMMDD integer columns.
- Add derived columns: `account_open_date::date`, `loan_start_date::date`, `loan_end_date::date`, `is_default` (boolean).
- Add PII & privacy notes: mark `client.*` fields with `sensitivity: pii` and suggest masking/role-based access.
- Suggested metrics: rolling 30/90-day delinquency, cohort survival curves for loan vintage analysis.

### Extra Query Patterns
-- Delinquency by cohort (loan origination month)
SELECT date_trunc('month', loan_origination::date) as cohort_month,
 SUM(CASE WHEN is_default THEN 1 ELSE 0 END)::float / COUNT(*) as default_rate
 FROM loan GROUP BY cohort_month ORDER BY cohort_month;

-- Owner counts per account (detect joint accounts)
SELECT a.account_id, SUM(CASE WHEN d.type='OWNER' THEN 1 ELSE 0 END) as owner_count
FROM account a JOIN disp d ON a.account_id = d.account_id GROUP BY a.account_id HAVING SUM(CASE WHEN d.type='OWNER' THEN 1 ELSE 0 END) > 1;

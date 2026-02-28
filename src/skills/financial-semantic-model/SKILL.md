---
name: financial-semantic-model
description: Semantic model for the financial database (Czech banking PKDD 1999 dataset). Contains business definitions for banking — loans, accounts, transactions, clients, districts. Load this skill when the user is querying the financial database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-25T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 5
---

# Financial — Semantic Model

## Available Resources

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | Date format (YYMMDD integer), Czech text codes, district column names | `read_skill_resource("financial-semantic-model", "references/gotchas.md")` |
| Metric definitions | Loan default rates, avg balances, transaction flows | `read_skill_resource("financial-semantic-model", "references/metrics.md")` |
| Query patterns | Canonical SQL for regional stats, client loans, account owners | `read_skill_resource("financial-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If the query involves dates or date arithmetic → load `references/gotchas.md` (YYMMDD format is critical)
- If the query involves loan status or default analysis → load `references/gotchas.md` + `references/metrics.md`
- If the query spans client → account → loan → district → load `references/query_patterns.md`
- For simple account or transaction lookups → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "loan status" | `loan.status` — single letter: 'A'=Finished/OK, 'B'=Finished/Unpaid, 'C'=Running/OK, 'D'=Running/Debt | verified |
| "account owner" | `disp.type = 'OWNER'` — the primary account holder | verified |
| "disponent" | `disp.type = 'DISPONENT'` — secondary card holder, not owner | verified |
| "district name" | `district.a2` (lowercase) — e.g. 'Hl.m. Praha' | verified |
| "region" | `district.a3` (lowercase) — e.g. 'Prague', 'central Bohemia' | verified |
| "incoming transaction" | `trans.type = 'PRIJEM'` (Czech for credit/incoming) | verified |
| "outgoing transaction" | `trans.type = 'VYDAJ'` (Czech for debit/outgoing) | verified |
| "gold card" / "classic card" | `card.type` — values: 'gold', 'classic', 'electron' | verified |

## Gotchas

1. **Date columns are integers in YYMMDD format** — `account.date`, `loan.date`,
   and `trans.date` store dates as integers like `930101` (= 1993-01-01). Never
   compare them directly to ISO strings. Cast with `TO_DATE(date::text, 'YYMMDD')`.

2. **`district` columns use cryptic codes `a1`–`a16` (all lowercase)** — there
   are no human-readable column names. Key ones: `a1`=district_id, `a2`=name,
   `a3`=region, `a4`=population, `a11`=avg salary.

3. **Always join client→account through `disp`** — there is no direct FK from
   `client` to `account`. The path is always:
   `client.client_id → disp.client_id → disp.account_id → account.account_id`.

4. **`trans.type` and `trans.operation` are Czech text** — `'PRIJEM'` means
   credit, `'VYDAJ'` means debit. Operation values include `'VKLAD'` (cash
   deposit), `'PREVOD Z UCTU'` (transfer from another account).

5. **`disp.type` must be filtered when finding the account owner** — an account
   can have both an OWNER and one or more DISPONENTs. Always add
   `WHERE disp.type = 'OWNER'` when you want the primary client for an account.

For extended gotchas and SQL examples, call:
```python
read_skill_resource(
	skill_name="financial-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
client.client_id    ──→  disp.client_id    ──→  account.account_id
account.district_id ──→  district.district_id    (account's home district)
client.district_id  ──→  district.district_id    (client's home district)
account.account_id  ──→  loan.account_id          (account ↔ loans)
account.account_id  ──→  trans.account_id         (account ↔ transactions)
account.account_id  ──→  order.account_id         (account ↔ standing orders)
disp.disp_id        ──→  card.disp_id             (disposition ↔ issued card)
```

Note: `client` has its own `district_id` (where the client lives); `account`
has a separate `district_id` (where the account was opened). These can differ.

## Frequently Asked Queries

For canonical query patterns (loan defaults by region, client demographics,
account ownership), call:
```python
read_skill_resource(
	skill_name="financial-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas (default rates, average loan amounts, transaction
balances), call:
```python
read_skill_resource(
	skill_name="financial-semantic-model",
	resource_name="references/metrics.md"
)
```

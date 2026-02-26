---
name: student-club-semantic-model
description: Semantic model for the student_club database (college student club events, members, budgets, expenses, income). Load this skill when the user is querying the student_club database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-25T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 4
---

# Student Club — Semantic Model

## Available Resources

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | Airtable-style IDs, FK column naming, boolean-as-string, budget vs expense columns | `read_skill_resource("student-club-semantic-model", "references/gotchas.md")` |
| Metric definitions | Attendance counts, budget utilisation, expense totals | `read_skill_resource("student-club-semantic-model", "references/metrics.md")` |
| Query patterns | Canonical SQL for event attendance, expense approvals, member roles | `read_skill_resource("student-club-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If joining `attendance`, `expense`, or `budget` tables → load `references/gotchas.md` (non-standard FK naming)
- If filtering by `expense.approved` → load `references/gotchas.md` (stored as string, not boolean)
- If computing budget utilisation → load `references/metrics.md`
- For simple member or event lookups → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "event attendance" | `attendance` table — `link_to_event` + `link_to_member` (composite PK) | verified |
| "event type" | `event.type` — values: `'Meeting'`, `'Election'`, `'Social'`, `'Speaker'`, etc. | verified |
| "event status" | `event.status` — `'Open'` or `'Closed'` | verified |
| "approved expense" | `expense.approved = 'true'` (string, not SQL boolean) | verified |
| "budget amount" | `budget.amount` — the budgeted allocation | verified |
| "actual spend" | `budget.spent` — amount actually spent (separate from `budget.amount`) | verified |
| "remaining budget" | `budget.remaining` = `budget.amount - budget.spent` (pre-computed) | verified |
| "member role" | `member.role` — e.g. `'Member'`, `'Officer'` | verified |

## Gotchas

1. **All primary keys are Airtable-style base64 strings** — IDs start with `rec`
   followed by alphanumeric characters. Never cast to integer.

2. **FK columns use `link_to_*` naming, not `_id` suffix** — the FK from
   `attendance` to `event` is `link_to_event`, not `event_id`. Likewise for
   `link_to_member`, `link_to_budget`.

3. **`expense.approved` is a string `'true'` or `'false'`**, not a SQL boolean.
   Filter with `WHERE approved = 'true'`, not `WHERE approved = TRUE`.

4. **`budget.amount` and `budget.spent` are different columns** — `amount`
   is the allocated budget; `spent` is what was actually spent. Do not treat
   them as the same metric.

5. **`member.zip` joins to `zip_code.zip_code`** — for city/state lookups,
   join on this column (not a typical `_id` FK).

For extended gotchas and SQL examples, call:
```python
read_skill_resource(
	skill_name="student-club-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
attendance.link_to_event   ──→  event.event_id
attendance.link_to_member  ──→  member.member_id
budget.link_to_event       ──→  event.event_id
expense.link_to_member     ──→  member.member_id
expense.link_to_budget     ──→  budget.budget_id
member.zip                 ──→  zip_code.zip_code
member.major               ──→  major.major_name  (if FK exists)
```

There is no direct join between `expense` and `event` — go through
`expense → budget → event`.

## Frequently Asked Queries

For canonical query patterns (event attendance, expense approvals, budget
utilisation), call:
```python
read_skill_resource(
	skill_name="student-club-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas (total spend, attendance per event, budget utilisation),
call:
```python
read_skill_resource(
	skill_name="student-club-semantic-model",
	resource_name="references/metrics.md"
)
```

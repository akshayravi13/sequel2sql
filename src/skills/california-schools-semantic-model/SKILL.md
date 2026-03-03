---
name: california-schools-semantic-model
description: Semantic model for the california_schools database. Contains business term definitions, metric formulas, known query patterns, and critical gotchas for the California Schools dataset (FRPM eligibility, SAT scores, district/school hierarchy). Load this skill when the user is querying the california_schools database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-23T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 4
---

# California Schools — Semantic Model

## Available Resources

This skill includes reference files with extended documentation. Load them
when you need deeper detail beyond what is in this file.

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | Edge cases, NULL handling details, type pitfalls | `read_skill_resource("california-schools-semantic-model", "references/gotchas.md")` |
| Metric definitions | Full formulas for FRPM rate, SAT composite, etc. | `read_skill_resource("california-schools-semantic-model", "references/metrics.md")` |
| Query patterns | Canonical SQL for common questions (top schools, county stats, etc.) | `read_skill_resource("california-schools-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If you are unsure about a metric formula → load `references/metrics.md`
- If the query is complex or involves edge cases → load `references/gotchas.md`
- If the query matches a common pattern (top-N, aggregation by county, etc.) → load `references/query_patterns.md`
- For simple, straightforward queries → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "free meal eligible" / "FRPM eligible" | `frpm."FRPM Count (K-12)"` — students eligible for Free or Reduced Price Meals | verified |
| "free meal rate" / "FRPM rate" | `frpm."FRPM Count (K-12)" / frpm."Enrollment (K-12)"` | verified |
| "free lunch" (strict) | `frpm."Free Meal Count (K-12)"` (excludes reduced-price) | verified |
| "SAT score" | Usually `satscores.AvgScrMath + satscores.AvgScrRead + satscores.AvgScrWrite` (total). Clarify if user wants a single subject. | verified |
| "test takers" | `satscores.NumTstTakr` | verified |
| "school type" | `schools.StatusType` — values include `Active`, `Closed`, `Merged` | verified |
| "charter school" | `frpm."Charter School (Y/N)" = 1` | verified |

## Gotchas

1. **`satscores` uses `cds`, not `CDSCode`** — to join with `schools`, use
   `schools.CDSCode = satscores.cds`. Using `satscores.CDSCode` will fail
   (column does not exist).

2. **Column names with spaces in `frpm`** — columns like `Free Meal Count (K-12)`
   must be double-quoted in PostgreSQL:
   `frpm."Free Meal Count (K-12)"`. Never use backticks.

3. **NULL SAT scores** — schools that did not administer the SAT have NULL in
   `AvgScrMath`, `AvgScrRead`, `AvgScrWrite`, and `NumTstTakr`. Always
   filter `WHERE satscores.NumTstTakr IS NOT NULL` (or use `COALESCE`)
   unless the user explicitly wants all schools including non-participants.

4. **CDSCode is a string** — `schools.CDSCode` and `satscores.cds` are both
   `VARCHAR`/`TEXT`. Do NOT cast to integer or numeric.

5. **`frpm` contains both district-level and school-level rows** — school-level
   rows have a non-null `School Name`. Filter `WHERE frpm."School Name" IS NOT NULL`
   when you need school-level data only.

For extended gotchas and edge cases, call:
```python
read_skill_resource(
	skill_name="california-schools-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
schools.CDSCode  ──→  frpm.CDSCode          (school ↔ FRPM data)
schools.CDSCode  ──→  satscores.cds         (school ↔ SAT scores — note different col name)
```

There is no direct join between `frpm` and `satscores`; always go through `schools`.

## Frequently Asked Queries

For canonical query patterns (top schools by SAT score, FRPM rate by county, etc.), call:
```python
read_skill_resource(
	skill_name="california-schools-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas and calculation details, call:
```python
read_skill_resource(
	skill_name="california-schools-semantic-model",
	resource_name="references/metrics.md"
)
```

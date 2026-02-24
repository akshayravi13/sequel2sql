# Gotchas — california_schools_template

## 1. `satscores` join column is `cds`, not `CDSCode`

**Problem**: The `schools` table uses `CDSCode` as its primary key. But
`satscores` uses the column name `cds` for the same identifier. A common
mistake is writing `satscores.CDSCode` which fails immediately.

**Correct join**:
```sql
-- CORRECT
JOIN satscores sat ON s.CDSCode = sat.cds

-- WRONG — column does not exist
JOIN satscores sat ON s.CDSCode = sat.CDSCode
```

---

## 2. Column names with spaces must be double-quoted

**Problem**: The `frpm` table has columns like `Free Meal Count (K-12)`,
`Enrollment (K-12)`, `FRPM Count (K-12)`, `Percent (%) Eligible Free (K-12)`.
PostgreSQL requires double quotes around identifiers with spaces or special chars.

**Correct usage**:
```sql
-- CORRECT
frpm."Free Meal Count (K-12)"
frpm."Enrollment (K-12)"
frpm."FRPM Count (K-12)"
frpm."Percent (%) Eligible Free (K-12)"

-- WRONG — syntax error
frpm.Free Meal Count (K-12)
frpm.`Free Meal Count (K-12)`   -- backticks are MySQL syntax, not PostgreSQL
```

---

## 3. NULL SAT scores for non-participating schools

**Problem**: Many schools have no SAT data. Their rows in `satscores` have
`NULL` for `AvgScrMath`, `AvgScrRead`, `AvgScrWrite`, and `NumTstTakr`.
Including them in averages or rankings silently skews results.

**Fix**: Always filter when ranking or aggregating SAT scores:
```sql
WHERE sat.NumTstTakr IS NOT NULL
```

Or when computing averages across schools, use `AVG()` which naturally ignores
NULLs but be aware the denominator excludes non-participants.

---

## 4. `frpm` contains both school-level and district-level rows

**Problem**: The `frpm` table includes aggregate rows for entire districts, not
just individual schools. If you aggregate without filtering, district rows
double-count students.

**Fix**: Filter to school-level rows only:
```sql
WHERE frpm."School Name" IS NOT NULL
```
District-only rows have `NULL` in `School Name`.

---

## 5. CDSCode is a string, not a number

**Problem**: `CDSCode` looks numeric (14 digits) but is stored as `VARCHAR`/`TEXT`.
Casting to integer will fail for codes with leading zeros.

**Fix**: Always treat as string — no CAST, no arithmetic operations on it.
```sql
-- CORRECT
WHERE s.CDSCode = '01100170109835'

-- WRONG — CAST fails or loses leading zeros
WHERE CAST(s.CDSCode AS BIGINT) = 1100170109835
```

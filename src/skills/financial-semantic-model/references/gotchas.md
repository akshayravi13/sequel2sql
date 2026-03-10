# Gotchas — financial

## 1. Date columns are integers in YYMMDD format, not DATE types

**Problem**: `account.date`, `loan.date`, `trans.date`, and `card.issued` store
dates as integers like `930101` (meaning 1993-01-01). Standard date comparisons
and `DATE_TRUNC` fail unless you cast first.

**Correct usage**:
```sql
-- CORRECT: convert to DATE for comparison
SELECT *
FROM loan
WHERE TO_DATE(date::text, 'YYMMDD') BETWEEN '1997-01-01' AND '1997-12-31';

-- CORRECT: extract year
SELECT EXTRACT(year FROM TO_DATE(date::text, 'YYMMDD')) AS loan_year
FROM loan;

-- WRONG — integer comparison gives wrong or nonsensical results
WHERE date > 970101   -- syntactically OK but semantically wrong
WHERE date::date ...  -- CAST fails because 930101 is not a valid DATE literal
```

---

## 2. `district` columns have cryptic names `a1` through `a16` (all lowercase)

**Problem**: The `district` table has no human-readable column names. All
demographic columns are named `a1`, `a2`, ..., `a16` in lowercase. Using
uppercase (e.g. `A2`) may work on case-insensitive systems but will fail on
case-sensitive PostgreSQL if quoted.

| Column | Meaning |
|---|---|
| `a1` | district_id (PK) |
| `a2` | district name |
| `a3` | region name |
| `a4` | population |
| `a11` | average salary |

**Correct usage**:
```sql
-- CORRECT
SELECT a2 AS district_name, a11 AS avg_salary
FROM district
WHERE a3 = 'south Bohemia';

-- WRONG — columns don't exist by these names
SELECT name, avg_salary FROM district;
SELECT "Name", "AvgSalary" FROM district;
```

---

## 3. No direct link from `client` to `account` — always go through `disp`

**Problem**: There is no FK column `client.account_id` or `account.client_id`.
The `disp` (disposition) table is the required bridge. Skipping it leads to
a query that fails or returns wrong results.

**Correct join path**:
```sql
-- CORRECT
SELECT c.client_id, a.account_id
FROM client c
JOIN disp d ON c.client_id = d.client_id
JOIN account a ON d.account_id = a.account_id;

-- WRONG — no such column exists
JOIN account ON client.account_id = account.account_id
```

---

## 4. Filter `disp.type = 'OWNER'` to find the primary account holder

**Problem**: One account can have multiple rows in `disp` — one OWNER plus
one or more DISPONENTs (authorised secondary card holders). Joining without
the type filter returns duplicate rows and non-owner clients.

**Correct usage**:
```sql
-- CORRECT: primary holder only
SELECT c.client_id, a.account_id
FROM client c
JOIN disp d ON c.client_id = d.client_id AND d.type = 'OWNER'
JOIN account a ON d.account_id = a.account_id;

-- WRONG — returns both owner and disponents, causing row duplication
JOIN disp d ON c.client_id = d.client_id   -- missing type filter
```

---

## 5. `trans.type` and `trans.operation` are Czech-language strings

**Problem**: Transaction direction uses Czech vocabulary, not English.
Filtering on English terms returns zero rows.

| Column | Czech value | English meaning |
|---|---|---|
| `trans.type` | `'PRIJEM'` | credit / incoming |
| `trans.type` | `'VYDAJ'` | debit / outgoing |
| `trans.operation` | `'VKLAD'` | cash deposit |
| `trans.operation` | `'PREVOD Z UCTU'` | transfer from another account |
| `trans.operation` | `'PREVOD NA UCET'` | transfer to another account |

```sql
-- CORRECT
SELECT SUM(amount) FROM trans WHERE type = 'PRIJEM';   -- total credits
SELECT SUM(amount) FROM trans WHERE type = 'VYDAJ';    -- total debits

-- WRONG
WHERE type = 'CREDIT' OR type = 'INCOMING'   -- returns zero rows
```

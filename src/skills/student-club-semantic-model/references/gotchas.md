# Gotchas — student_club

## 1. All IDs are Airtable-style base64 strings — never cast to integer

**Problem**: Primary keys look like `recABC123XYZ` — they are base64-encoded
Airtable record IDs. Casting to integer fails; using them in numeric comparisons
gives wrong results.

**Correct usage**:
```sql
-- CORRECT
SELECT * FROM event WHERE event_id = 'recChpCTUhNMc3BsS';

-- WRONG — fails or returns zero rows
WHERE event_id = 1
WHERE event_id::integer = 1
```

---

## 2. FK columns use `link_to_*` naming, not `_id` suffix

**Problem**: The `attendance` table has `link_to_event` and `link_to_member`
as FK columns — not `event_id` or `member_id`. Trying to join on conventional
`_id` column names fails.

**Correct join**:
```sql
-- CORRECT
SELECT e.event_name, m.name AS member_name
FROM attendance a
JOIN event e ON a.link_to_event = e.event_id
JOIN member m ON a.link_to_member = m.member_id;

-- WRONG — column does not exist
JOIN event e ON a.event_id = e.event_id
```

---

## 3. `expense.approved` is a string `'true'`/`'false'`, not a SQL boolean

**Problem**: The approved column stores string literals, not SQL boolean TRUE/FALSE.
Using `WHERE approved = TRUE` may coerce or return wrong results.

**Correct usage**:
```sql
-- CORRECT
SELECT * FROM expense WHERE approved = 'true';
SELECT * FROM expense WHERE approved = 'false';

-- WRONG — type mismatch, may silently fail
WHERE approved = TRUE
WHERE approved IS TRUE
```

---

## 4. `budget.amount` ≠ `budget.spent` — they measure different things

**Problem**: `budget.amount` is the allocated budget for a category;
`budget.spent` is what was actually disbursed. `budget.remaining` is a
pre-computed column (`amount - spent`). Conflating these gives wrong financials.

**Correct usage**:
```sql
-- CORRECT: budget utilisation rate
SELECT
	category,
	amount AS budgeted,
	spent AS actual_spend,
	remaining,
	ROUND(spent::numeric / NULLIF(amount, 0), 4) AS utilisation_rate
FROM budget;

-- WRONG — treating amount as spend
SELECT category, SUM(amount) AS total_spend FROM budget GROUP BY category;
-- (This returns the budgeted total, not the actual spend)
```

---

## 5. To link `expense` to `event`, go through `budget`

**Problem**: There is no direct FK from `expense` to `event`. The path is
`expense → budget → event` via `link_to_budget` then `link_to_event`.

**Correct join chain**:
```sql
-- CORRECT
SELECT e.event_name, ex.expense_description, ex.cost
FROM expense ex
JOIN budget b ON ex.link_to_budget = b.budget_id
JOIN event e ON b.link_to_event = e.event_id;

-- WRONG — no such column
JOIN event e ON ex.link_to_event = e.event_id
```

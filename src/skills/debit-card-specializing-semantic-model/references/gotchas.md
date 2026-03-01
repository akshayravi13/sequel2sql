# Gotchas — debit_card_specializing

## 1. `yearmonth.Date` is an integer in YYYYMM format, not a DATE

**Problem**: The `yearmonth` table's `Date` column stores months as integers
like `201207` (= July 2012). It cannot be compared to ISO date strings or used
with `DATE_TRUNC`. Filter using integer arithmetic.

**Correct usage**:
```sql
-- CORRECT: get all records for the year 2012
SELECT * FROM yearmonth WHERE Date / 100 = 2012;

-- CORRECT: get July of any year
SELECT * FROM yearmonth WHERE Date % 100 = 7;

-- CORRECT: get a specific month
SELECT * FROM yearmonth WHERE Date = 201207;

-- WRONG — type mismatch or silent wrong results
WHERE Date = '2012-07-01'
WHERE Date BETWEEN '2012-01-01' AND '2012-12-31'
```

---

## 2. Product descriptions are Czech text

**Problem**: The `products.Description` column uses Czech vocabulary.
Searching for English product names (e.g. 'Diesel') returns zero rows.

**Known Czech product description values**:
| Czech | English meaning |
|---|---|
| `'Nafta'` | Diesel |
| `'Rucní zadání'` | Manual/cash entry |
| `'Special'` | Special fuel type |

```sql
-- CORRECT
SELECT * FROM transactions_1k t
JOIN products p ON t.ProductID = p.ProductID
WHERE p.Description = 'Nafta';   -- diesel transactions

-- WRONG
WHERE p.Description = 'Diesel'   -- returns zero rows
```

---

## 3. Gas station country codes are 3-letter abbreviations

**Problem**: `gasstations.Country` uses ISO-like 3-letter codes, not full
country names. `'Czech Republic'` or `'CZ'` will not match.

**Country code values**:
| Code | Country |
|---|---|
| `'CZE'` | Czech Republic |
| `'SVK'` | Slovakia |
| `'HUN'` | Hungary |

```sql
-- CORRECT
SELECT COUNT(*) FROM gasstations WHERE Country = 'CZE';

-- WRONG
WHERE Country = 'Czech Republic'  -- zero rows
WHERE Country = 'CZ'              -- zero rows
```

---

## 4. `transactions_1k` is a sample — use `yearmonth` for totals

**Problem**: `transactions_1k` contains only 1000 rows (a sample). Any
customer-level total spend computed from this table will be incomplete.
For monthly totals, use the `yearmonth` table which has full aggregates.

```sql
-- CORRECT: monthly total consumption per customer
SELECT CustomerID, Date, Consumption
FROM yearmonth
WHERE Date / 100 = 2012
ORDER BY Consumption DESC;

-- MISLEADING: partial spend from the sample only
SELECT CustomerID, SUM(Amount) FROM transactions_1k GROUP BY CustomerID;
-- (This underestimates true spend since only 1000 transactions are present)
```

---

## 5. `customers.Segment` and `gasstations.Segment` use different value sets

**Problem**: Both `customers` and `gasstations` have a `Segment` column but
they contain different categories — customer segments classify company size
while station segments classify service tier. Do not conflate them.

```sql
-- Customer segments (company size)
SELECT DISTINCT Segment FROM customers;
-- Returns: 'SME', 'LAM', 'KAM'

-- Gas station segments (service tier)
SELECT DISTINCT Segment FROM gasstations;
-- Returns: 'Premium', 'Value', etc. (varies by data version)
```

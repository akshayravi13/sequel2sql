# Query Patterns — debit_card_specializing

## "Which customers spent the most on diesel in 2012?"

```sql
-- yearmonth for totals; transactions_1k for product-level detail
SELECT
	t.CustomerID,
	c.Segment,
	SUM(t.Amount) AS diesel_spend
FROM transactions_1k t
JOIN customers c ON t.CustomerID = c.CustomerID
JOIN products p ON t.ProductID = p.ProductID
WHERE p.Description = 'Nafta'          -- Czech for diesel
  AND t.Date LIKE '2012%'              -- transactions_1k.Date is text 'YYYY-MM-DD'
GROUP BY t.CustomerID, c.Segment
ORDER BY diesel_spend DESC
LIMIT 10;
```

---

## "How many gas stations are in each country?"

```sql
-- Country codes: 'CZE', 'SVK', 'HUN'
SELECT
	Country,
	COUNT(*) AS station_count
FROM gasstations
GROUP BY Country
ORDER BY station_count DESC;
```

---

## "What is the monthly consumption trend for SME customers?"

```sql
-- yearmonth has full monthly aggregates (not sampled)
SELECT
	ym.Date AS year_month,
	SUM(ym.Consumption) AS total_consumption,
	COUNT(DISTINCT ym.CustomerID) AS sme_customers
FROM yearmonth ym
JOIN customers c ON ym.CustomerID = c.CustomerID
WHERE c.Segment = 'SME'
GROUP BY ym.Date
ORDER BY ym.Date;
```

---

## "Show transactions at Premium gas stations in Slovakia"

```sql
SELECT
	t.Date,
	t.CustomerID,
	t.Amount,
	g.GasStationID,
	g.Segment AS station_segment
FROM transactions_1k t
JOIN gasstations g ON t.GasStationID = g.GasStationID
WHERE g.Country = 'SVK'
  AND g.Segment = 'Premium'
ORDER BY t.Date DESC;
```

---

## "What is the average transaction amount per product type?"

```sql
SELECT
	p.ProductID,
	p.Description AS product_name,
	COUNT(*) AS txn_count,
	ROUND(AVG(t.Amount), 2) AS avg_amount,
	SUM(t.Amount) AS total_amount
FROM transactions_1k t
JOIN products p ON t.ProductID = p.ProductID
GROUP BY p.ProductID, p.Description
ORDER BY avg_amount DESC;
```

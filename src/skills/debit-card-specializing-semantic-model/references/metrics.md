# Metric Definitions — debit_card_specializing

## Total Annual Consumption per Customer

```sql
-- Use yearmonth for complete data (transactions_1k is a sample only)
SELECT
	CustomerID,
	Date / 100 AS year,
	SUM(Consumption) AS total_consumption
FROM yearmonth
GROUP BY CustomerID, Date / 100
ORDER BY total_consumption DESC;
```

---

## Total Spend per Customer Segment (from transactions_1k)

```sql
-- Note: transactions_1k is a sample — results are indicative, not exact totals
SELECT
	c.Segment,
	COUNT(DISTINCT t.CustomerID) AS customer_count,
	SUM(t.Amount) AS total_amount,
	ROUND(AVG(t.Amount), 2) AS avg_transaction_amount
FROM transactions_1k t
JOIN customers c ON t.CustomerID = c.CustomerID
GROUP BY c.Segment
ORDER BY total_amount DESC;
```

---

## Transactions by Gas Station Country

```sql
SELECT
	g.Country,
	COUNT(*) AS transaction_count,
	SUM(t.Amount) AS total_amount
FROM transactions_1k t
JOIN gasstations g ON t.GasStationID = g.GasStationID
GROUP BY g.Country
ORDER BY transaction_count DESC;
```

---

## Monthly Consumption Trend (all customers)

```sql
-- Total consumption across all customers by month
SELECT
	Date AS year_month,
	Date / 100 AS year,
	Date % 100 AS month,
	SUM(Consumption) AS total_consumption,
	COUNT(DISTINCT CustomerID) AS active_customers
FROM yearmonth
GROUP BY Date
ORDER BY Date;
```

---

## Product Mix by Transaction Volume

```sql
SELECT
	p.ProductID,
	p.Description,
	COUNT(*) AS transaction_count,
	SUM(t.Amount) AS total_amount
FROM transactions_1k t
JOIN products p ON t.ProductID = p.ProductID
GROUP BY p.ProductID, p.Description
ORDER BY transaction_count DESC;
```

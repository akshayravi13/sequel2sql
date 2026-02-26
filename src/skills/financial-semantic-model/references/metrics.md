# Metric Definitions — financial

## Loan Default Rate (Finished Loans Only)

```sql
-- Among finished loans, what fraction ended with an unpaid balance?
-- status 'A' = finished OK, 'B' = finished unpaid (defaulted)
SELECT
	ROUND(
		SUM(CASE WHEN status = 'B' THEN 1 ELSE 0 END)::numeric / COUNT(*),
		4
	) AS default_rate
FROM loan
WHERE status IN ('A', 'B');
```

---

## Average Loan Amount by Status

```sql
-- Average loan size for each status category
SELECT
	status,
	CASE status
		WHEN 'A' THEN 'Finished/OK'
		WHEN 'B' THEN 'Finished/Unpaid'
		WHEN 'C' THEN 'Running/OK'
		WHEN 'D' THEN 'Running/Debt'
	END AS status_description,
	COUNT(*) AS loan_count,
	ROUND(AVG(amount), 2) AS avg_amount
FROM loan
GROUP BY status
ORDER BY status;
```

---

## Net Transaction Flow per Account

```sql
-- Credit minus debit per account (net balance change from transactions)
SELECT
	account_id,
	SUM(CASE WHEN type = 'PRIJEM' THEN amount ELSE 0 END) AS total_credit,
	SUM(CASE WHEN type = 'VYDAJ' THEN amount ELSE 0 END) AS total_debit,
	SUM(CASE WHEN type = 'PRIJEM' THEN amount ELSE -amount END) AS net_flow
FROM trans
GROUP BY account_id
ORDER BY net_flow DESC;
```

---

## Average Salary by Region

```sql
-- Average salary across districts, grouped by region
SELECT
	a3 AS region,
	ROUND(AVG(a11), 2) AS avg_salary,
	COUNT(*) AS district_count
FROM district
GROUP BY a3
ORDER BY avg_salary DESC;
```

---

## Card Type Distribution

```sql
-- How many of each card type have been issued?
SELECT
	type AS card_type,
	COUNT(*) AS issued_count
FROM card
GROUP BY type
ORDER BY issued_count DESC;
```

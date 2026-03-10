# Query Patterns — financial

## "Find all account owners in a specific district"

```sql
-- Uses district.a2 for district name (not a column called 'name')
SELECT c.client_id, a.account_id, dist.a2 AS district_name
FROM client c
JOIN disp d ON c.client_id = d.client_id AND d.type = 'OWNER'
JOIN account a ON d.account_id = a.account_id
JOIN district dist ON c.district_id = dist.a1
WHERE dist.a2 = 'Hl.m. Praha'
ORDER BY c.client_id;
```

---

## "List loans that are currently in debt (running with missed payments)"

```sql
-- status 'D' = running loan with arrears
SELECT
	l.loan_id,
	l.account_id,
	l.amount,
	l.payments,
	TO_DATE(l.date::text, 'YYMMDD') AS loan_start_date
FROM loan l
WHERE l.status = 'D'
ORDER BY l.amount DESC;
```

---

## "Show the complete client → account → loan chain for a specific client"

```sql
SELECT
	c.client_id,
	c.birth_date,
	a.account_id,
	TO_DATE(a.date::text, 'YYMMDD') AS account_opened,
	l.loan_id,
	l.amount AS loan_amount,
	l.status AS loan_status
FROM client c
JOIN disp d ON c.client_id = d.client_id AND d.type = 'OWNER'
JOIN account a ON d.account_id = a.account_id
LEFT JOIN loan l ON a.account_id = l.account_id
WHERE c.client_id = 1;
```

---

## "What is the transaction history for a given account in a date range?"

```sql
-- Dates stored as YYMMDD integers — must cast for range comparison
SELECT
	trans_id,
	TO_DATE(date::text, 'YYMMDD') AS trans_date,
	type,
	operation,
	amount,
	balance
FROM trans
WHERE account_id = 1
  AND TO_DATE(date::text, 'YYMMDD') BETWEEN '1998-01-01' AND '1998-12-31'
ORDER BY date;
```

---

## "Which regions have the highest average loan default rates?"

```sql
SELECT
	dist.a3 AS region,
	COUNT(l.loan_id) AS total_loans,
	SUM(CASE WHEN l.status = 'B' THEN 1 ELSE 0 END) AS defaulted,
	ROUND(
		SUM(CASE WHEN l.status = 'B' THEN 1 ELSE 0 END)::numeric /
		NULLIF(SUM(CASE WHEN l.status IN ('A','B') THEN 1 ELSE 0 END), 0),
		4
	) AS default_rate
FROM district dist
JOIN account a ON a.district_id = dist.a1
JOIN loan l ON l.account_id = a.account_id
GROUP BY dist.a3
ORDER BY default_rate DESC NULLS LAST;
```

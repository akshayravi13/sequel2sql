# Metric Definitions — student_club

## Attendance Count per Event

```sql
SELECT
	e.event_name,
	e.type AS event_type,
	e.event_date,
	COUNT(a.link_to_member) AS attendee_count
FROM event e
LEFT JOIN attendance a ON a.link_to_event = e.event_id
GROUP BY e.event_id, e.event_name, e.type, e.event_date
ORDER BY attendee_count DESC;
```

---

## Budget Utilisation by Category

```sql
-- amount = allocated, spent = actual, remaining = pre-computed
SELECT
	category,
	SUM(amount) AS total_budgeted,
	SUM(spent) AS total_spent,
	SUM(remaining) AS total_remaining,
	ROUND(SUM(spent)::numeric / NULLIF(SUM(amount), 0), 4) AS utilisation_rate
FROM budget
GROUP BY category
ORDER BY utilisation_rate DESC;
```

---

## Total Approved Expenses per Member

```sql
-- expense.approved is a string 'true'/'false'
SELECT
	m.name AS member_name,
	m.role,
	COUNT(*) AS approved_expense_count,
	SUM(ex.cost) AS total_approved_spend
FROM expense ex
JOIN member m ON ex.link_to_member = m.member_id
WHERE ex.approved = 'true'
GROUP BY m.member_id, m.name, m.role
ORDER BY total_approved_spend DESC;
```

---

## Income by Source

```sql
SELECT
	source,
	COUNT(*) AS income_entries,
	SUM(amount) AS total_income
FROM income
GROUP BY source
ORDER BY total_income DESC;
```

---

## Member Attendance Rate (Events Attended / Total Events)

```sql
SELECT
	m.name,
	m.role,
	COUNT(a.link_to_event) AS events_attended,
	(SELECT COUNT(*) FROM event) AS total_events,
	ROUND(
		COUNT(a.link_to_event)::numeric / NULLIF((SELECT COUNT(*) FROM event), 0),
		4
	) AS attendance_rate
FROM member m
LEFT JOIN attendance a ON m.member_id = a.link_to_member
GROUP BY m.member_id, m.name, m.role
ORDER BY attendance_rate DESC;
```

# Query Patterns — student_club

## "Who attended a specific event?"

```sql
-- FK columns use link_to_* naming, not _id suffix
SELECT m.name, m.role, m.email
FROM attendance a
JOIN event e ON a.link_to_event = e.event_id
JOIN member m ON a.link_to_member = m.member_id
WHERE e.event_name = 'October Meeting'
ORDER BY m.name;
```

---

## "What expenses have been approved for a specific event?"

```sql
-- No direct expense→event FK; go through budget
SELECT
	e.event_name,
	b.category,
	ex.expense_description,
	ex.cost,
	ex.expense_date
FROM expense ex
JOIN budget b ON ex.link_to_budget = b.budget_id
JOIN event e ON b.link_to_event = e.event_id
WHERE ex.approved = 'true'    -- string, not boolean
  AND e.event_name = 'Annual Banquet'
ORDER BY ex.cost DESC;
```

---

## "Which events are currently open?"

```sql
SELECT
	event_id,
	event_name,
	type,
	event_date,
	location
FROM event
WHERE status = 'Open'
ORDER BY event_date;
```

---

## "Show the budget vs actual spend for all events"

```sql
SELECT
	e.event_name,
	e.event_date,
	SUM(b.amount) AS total_budgeted,
	SUM(b.spent) AS total_spent,
	SUM(b.remaining) AS total_remaining
FROM event e
JOIN budget b ON b.link_to_event = e.event_id
GROUP BY e.event_id, e.event_name, e.event_date
ORDER BY e.event_date;
```

---

## "Which members are officers?"

```sql
SELECT
	member_id,
	name,
	email,
	role,
	major
FROM member
WHERE role = 'Officer'
ORDER BY name;
```

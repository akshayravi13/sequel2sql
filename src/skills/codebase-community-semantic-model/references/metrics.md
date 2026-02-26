# Metric Definitions — codebase_community

## Answer Acceptance Rate

```sql
-- Fraction of questions that have an accepted answer
SELECT
	ROUND(
		COUNT(*) FILTER (WHERE AcceptedAnswerId IS NOT NULL)::numeric / COUNT(*),
		4
	) AS acceptance_rate,
	COUNT(*) AS total_questions,
	COUNT(*) FILTER (WHERE AcceptedAnswerId IS NOT NULL) AS accepted_count
FROM posts
WHERE PostTypeId = 1;
```

---

## Questions with No Answers

```sql
SELECT
	COUNT(*) AS unanswered_questions,
	ROUND(
		COUNT(*)::numeric / (SELECT COUNT(*) FROM posts WHERE PostTypeId = 1),
		4
	) AS unanswered_rate
FROM posts
WHERE PostTypeId = 1
  AND AnswerCount = 0;
```

---

## Top Users by Reputation

```sql
SELECT
	Id,
	DisplayName,
	Reputation,
	UpVotes,
	DownVotes,
	Views AS profile_views
FROM users
ORDER BY Reputation DESC
LIMIT 20;
```

---

## Most Popular Tags by Post Count

```sql
SELECT
	TagName,
	Count AS post_count
FROM tags
ORDER BY Count DESC
LIMIT 30;
```

---

## Average Answer Score by Question Tag

```sql
-- Filter to top tags; tags stored as '<tag>' substring
SELECT
	'python' AS tag,
	COUNT(*) AS answer_count,
	ROUND(AVG(a.Score), 2) AS avg_answer_score
FROM posts q
JOIN posts a ON a.ParentId = q.Id AND a.PostTypeId = 2
WHERE q.Tags LIKE '%<python>%'
UNION ALL
SELECT
	'sql',
	COUNT(*),
	ROUND(AVG(a.Score), 2)
FROM posts q
JOIN posts a ON a.ParentId = q.Id AND a.PostTypeId = 2
WHERE q.Tags LIKE '%<sql>%';
```

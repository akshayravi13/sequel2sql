# Query Patterns — codebase_community

## "Find the top-voted questions tagged with a specific tag"

```sql
-- Tags stored as '<tag>' substrings — use LIKE
SELECT
	p.Id,
	p.Title,
	p.Score,
	p.AnswerCount,
	p.ViewCount,
	COALESCE(u.DisplayName, '[deleted]') AS author
FROM posts p
LEFT JOIN users u ON p.OwnerUserId = u.Id
WHERE p.PostTypeId = 1
  AND p.Tags LIKE '%<python>%'
ORDER BY p.Score DESC
LIMIT 20;
```

---

## "Which questions have the most answers?"

```sql
SELECT
	p.Id,
	p.Title,
	p.AnswerCount,
	p.Score,
	p.AcceptedAnswerId IS NOT NULL AS has_accepted_answer
FROM posts p
WHERE p.PostTypeId = 1
ORDER BY p.AnswerCount DESC
LIMIT 20;
```

---

## "Show all answers to a specific question, ordered by votes"

```sql
-- Self-join posts: answers have ParentId pointing to the question's Id
SELECT
	a.Id AS answer_id,
	a.Score,
	a.CreationDate,
	COALESCE(u.DisplayName, '[deleted]') AS answerer,
	q.AcceptedAnswerId = a.Id AS is_accepted
FROM posts q
JOIN posts a ON a.ParentId = q.Id AND a.PostTypeId = 2
LEFT JOIN users u ON a.OwnerUserId = u.Id
WHERE q.Id = 11227809   -- replace with target question Id
ORDER BY (q.AcceptedAnswerId = a.Id) DESC, a.Score DESC;
```

---

## "Find duplicate questions (linked as duplicates)"

```sql
-- LinkTypeId = 3 means the source is a duplicate of the target
SELECT
	q_orig.Title AS original_question,
	q_dup.Title AS duplicate_question,
	pl.CreationDate AS marked_duplicate_on
FROM postlinks pl
JOIN posts q_orig ON pl.RelatedPostId = q_orig.Id
JOIN posts q_dup ON pl.PostId = q_dup.Id
WHERE pl.LinkTypeId = 3
ORDER BY pl.CreationDate DESC
LIMIT 20;
```

---

## "Which users have earned the most badges?"

```sql
SELECT
	u.DisplayName,
	u.Reputation,
	COUNT(b.Id) AS badge_count,
	COUNT(DISTINCT b.Name) AS unique_badge_types
FROM users u
JOIN badges b ON u.Id = b.UserId
GROUP BY u.Id, u.DisplayName, u.Reputation
ORDER BY badge_count DESC
LIMIT 20;
```

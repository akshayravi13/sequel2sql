# Gotchas — codebase_community

## 1. `posts` contains both questions and answers — always filter by `PostTypeId`

**Problem**: All posts — questions, answers, wiki entries — share the same table.
Omitting the `PostTypeId` filter mixes question and answer rows and skews all
aggregations.

**Correct usage**:
```sql
-- CORRECT: questions only
SELECT COUNT(*) FROM posts WHERE PostTypeId = 1;

-- CORRECT: answers only
SELECT COUNT(*) FROM posts WHERE PostTypeId = 2;

-- WRONG — counts questions + answers + other post types
SELECT COUNT(*) FROM posts;
SELECT AVG(Score) FROM posts;   -- averages across heterogeneous post types
```

---

## 2. `posts.Tags` is a delimited string `'<tag1><tag2>'` — use LIKE, not a join

**Problem**: Tags are stored inline as `'<python><pandas><sql>'`. The `tags`
table holds aggregate statistics, not per-post membership. To filter posts by
tag, use `LIKE`.

**Correct usage**:
```sql
-- CORRECT: posts tagged with 'python'
SELECT Id, Title FROM posts
WHERE PostTypeId = 1
  AND Tags LIKE '%<python>%';

-- CORRECT: posts tagged with both 'python' and 'pandas'
SELECT Id, Title FROM posts
WHERE Tags LIKE '%<python>%'
  AND Tags LIKE '%<pandas>%';

-- WRONG — tags table is not per-post; this join is not valid
JOIN tags t ON posts.Tags = t.TagName
```

---

## 3. `posts.OwnerUserId` is NULL for deleted/anonymous users

**Problem**: When a user deletes their account, their posts remain but
`OwnerUserId` becomes NULL. `INNER JOIN users` silently drops these posts.

**Correct usage**:
```sql
-- CORRECT: include all posts, show 'deleted' for anonymous
SELECT
	p.Title,
	COALESCE(u.DisplayName, '[deleted]') AS author
FROM posts p
LEFT JOIN users u ON p.OwnerUserId = u.Id
WHERE p.PostTypeId = 1;

-- WRONG — drops posts from deleted users
INNER JOIN users u ON p.OwnerUserId = u.Id
```

---

## 4. To link an answer to its question, self-join `posts` on `ParentId`

**Problem**: Answers don't have a separate table — they are rows in `posts`
with `PostTypeId = 2` and `ParentId` pointing to the question's `Id`. Joining
answer to question requires a self-join.

**Correct usage**:
```sql
-- CORRECT: get each question with its answers
SELECT
	q.Title AS question,
	a.Body AS answer,
	a.Score AS answer_score
FROM posts q
JOIN posts a ON a.ParentId = q.Id
WHERE q.PostTypeId = 1
  AND a.PostTypeId = 2;

-- WRONG — no separate 'answers' table
FROM answers JOIN posts ...
```

---

## 5. `VoteTypeId` is not simply 2 = upvote, 3 = downvote

**Problem**: There are more VoteTypeId values than just up/down. Summing all
vote types as if they were upvotes overcounts engagement.

**Key VoteTypeId values**:
| VoteTypeId | Meaning |
|---|---|
| 1 | AcceptedByOriginator |
| 2 | UpMod (upvote) |
| 3 | DownMod (downvote) |
| 4 | Offensive |
| 5 | Favorite |
| 8 | BountyStart |
| 9 | BountyClose |

```sql
-- CORRECT: count only upvotes
SELECT PostId, COUNT(*) AS upvote_count
FROM votes
WHERE VoteTypeId = 2
GROUP BY PostId;

-- WRONG — counts all vote types as upvotes
SELECT PostId, COUNT(*) AS upvote_count FROM votes GROUP BY PostId;
```

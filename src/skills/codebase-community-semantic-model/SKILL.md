---
name: codebase-community-semantic-model
description: Semantic model for the codebase_community database (StackOverflow-like Q&A community — posts, users, comments, votes, tags, badges). Load this skill when the user is querying the codebase_community database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-25T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 5
---

# Codebase Community — Semantic Model

## Available Resources

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | PostTypeId filtering, tag string format, NULL OwnerUserId, PostLinks types | `read_skill_resource("codebase-community-semantic-model", "references/gotchas.md")` |
| Metric definitions | Answer acceptance rate, user engagement, tag popularity | `read_skill_resource("codebase-community-semantic-model", "references/metrics.md")` |
| Query patterns | Top users, unanswered questions, tag-filtered posts, duplicate detection | `read_skill_resource("codebase-community-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If querying the `posts` table → load `references/gotchas.md` (must filter by PostTypeId)
- If filtering by tag → load `references/gotchas.md` (tags are a delimited string, not a join)
- If computing engagement metrics → load `references/metrics.md`
- For simple user or reputation lookups → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "question" | `posts.PostTypeId = 1` | verified |
| "answer" | `posts.PostTypeId = 2` | verified |
| "accepted answer" | `posts.AcceptedAnswerId IS NOT NULL` (question has an accepted answer) | verified |
| "answer to a question" | `answers.ParentId = question.Id` (self-join on `posts`) | verified |
| "tag" | substring of `posts.Tags` — format: `'<python><sql><pandas>'` | verified |
| "reputation" | `users.Reputation` — numeric score | verified |
| "post owner" | `posts.OwnerUserId` → `users.Id` (nullable — deleted users are NULL) | verified |
| "duplicate question" | `postlinks.LinkTypeId = 3` | verified |
| "related question" | `postlinks.LinkTypeId = 1` | verified |
| "upvote" | `votes.VoteTypeId = 2` | verified |

## Gotchas

1. **`posts` contains questions AND answers — always filter by `PostTypeId`** —
   `PostTypeId = 1` for questions, `2` for answers. Omitting the filter mixes
   question metrics with answer metrics.

2. **`posts.Tags` is a concatenated string, not a join** — tags are stored as
   `'<python><sql>'`. Use `LIKE '%<tagname>%'` to filter. The `tags` table
   stores global tag statistics, not per-post membership.

3. **`posts.OwnerUserId` can be NULL** — deleted accounts are anonymised and
   their posts have `NULL` in `OwnerUserId`. Use `LEFT JOIN users` and handle
   NULL in output.

4. **An answer's parent question is `posts.ParentId`** — to join answers to
   their questions, do a self-join: `JOIN posts q ON a.ParentId = q.Id`.

5. **`VoteTypeId` is not simply up/down** — `2` = UpVote, `3` = DownVote,
   `5` = Favorite. There are other types for spam flags, close votes, etc.

For extended gotchas and SQL examples, call:
```python
read_skill_resource(
	skill_name="codebase-community-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
posts.OwnerUserId     ──→  users.Id                   (post ↔ author, nullable)
posts.AcceptedAnswerId ──→  posts.Id                  (question ↔ accepted answer)
posts.ParentId         ──→  posts.Id                  (answer ↔ its question)
comments.PostId        ──→  posts.Id
comments.UserId        ──→  users.Id
votes.PostId           ──→  posts.Id
badges.UserId          ──→  users.Id
postlinks.PostId       ──→  posts.Id  (source)
postlinks.RelatedPostId ──→ posts.Id  (target)
```

## Frequently Asked Queries

For canonical query patterns (top users, unanswered questions, tag analysis),
call:
```python
read_skill_resource(
	skill_name="codebase-community-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas (acceptance rate, answer latency, tag popularity), call:
```python
read_skill_resource(
	skill_name="codebase-community-semantic-model",
	resource_name="references/metrics.md"
)
```

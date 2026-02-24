---
name: codebase-community-semantic-model
description: Semantic model for the codebase_community database (StackOverflow clone).
metadata:
  author: manual
  version: "1.0"
---

# Codebase Community — Semantic Model
| Resource | How to load |
|---|---|
| Extended gotchas | `read_skill_resource("codebase-community-semantic-model", "references/gotchas.md")` |
| Metric definitions | `read_skill_resource("codebase-community-semantic-model", "references/metrics.md")` |
| Query patterns | `read_skill_resource("codebase-community-semantic-model", "references/query_patterns.md")` |

| Term | Actual meaning |
|---|---|
| "question" | `posts.PostTypeId = 1` |
| "answer" | `posts.PostTypeId = 2` |

**Core Join Path:** `users.Id` ──→ `posts.OwnerUserId`


## ENRICHMENT: recommended improvements
- Store `tags` as an array or JSON for efficient filtering; add full-text index on `posts.Body` and `posts.Title` for search use-cases.
- Suggested metrics: question response time median, active-user churn by month.

### Extra Query Patterns
-- Median time-to-first-answer for questions
WITH first_answer AS (
 SELECT p.Id as question_id, MIN(a.CreationDate) as first_answer_time
 FROM posts p LEFT JOIN posts a ON a.ParentId = p.Id AND a.PostTypeId=2
 WHERE p.PostTypeId = 1 GROUP BY p.Id
)
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY (first_answer_time - q.CreationDate)) as median_time
FROM first_answer fa JOIN posts q ON q.Id = fa.question_id;

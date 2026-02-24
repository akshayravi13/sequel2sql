---
name: student-club-semantic-model
description: Semantic model for the student_club database.
metadata:
  author: manual
  version: "1.0"
---
# Student Club — Semantic Model
| Resource | How to load |
|---|---|
| Extended gotchas | `read_skill_resource("student-club-semantic-model", "references/gotchas.md")` |
| Metric definitions | `read_skill_resource("student-club-semantic-model", "references/metrics.md")` |
| Query patterns | `read_skill_resource("student-club-semantic-model", "references/query_patterns.md")` |


## ENRICHMENT: recommended improvements
- Add membership role (member/officer/founder) to `member_of` bridge table and `joined_at` timestamp for churn analysis.
- Suggested metrics: active-members per club (last 12 months), officer-to-member ratio.

### Extra Query Patterns
-- Clubs with declining membership
SELECT c.club_name, COUNT(m.student_id) as members, date_trunc('year', m.joined_at) as year
FROM club c JOIN member_of m ON c.club_id = m.club_id GROUP BY c.club_name, year ORDER BY c.club_name, year;

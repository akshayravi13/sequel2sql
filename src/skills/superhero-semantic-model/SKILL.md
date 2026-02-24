---
name: superhero-semantic-model
description: Semantic model for the superhero database (publishers, attributes, powers).
metadata:
  author: manual
  version: "1.0"
---
# Superhero — Semantic Model
| Resource | How to load |
|---|---|
| Extended gotchas | `read_skill_resource("superhero-semantic-model", "references/gotchas.md")` |
| Metric definitions | `read_skill_resource("superhero-semantic-model", "references/metrics.md")` |
| Query patterns | `read_skill_resource("superhero-semantic-model", "references/query_patterns.md")` |


## ENRICHMENT: recommended improvements
- Treat `-99` as sentinel; add a data-quality flag `height_cm_valid` and `weight_kg_valid` and prefer NULL for missing values in downstream tables.
- Add `canonical_alignment` enum (good/neutral/bad) and `first_appearance_date` for historical analyses.

### Extra Query Patterns
-- Average power level by publisher (exclude invalid heights)
SELECT p.publisher_name, AVG(s.power_level) FROM superhero s JOIN publisher p ON s.publisher_id = p.id WHERE s.height_cm > 0 GROUP BY p.publisher_name;

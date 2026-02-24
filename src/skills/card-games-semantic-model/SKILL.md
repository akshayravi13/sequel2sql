---
name: card-games-semantic-model
description: Semantic model for the card_games database.
metadata:
  author: manual
  version: "1.0"
---

# Card Games — Semantic Model
| Resource | How to load |
|---|---|
| Extended gotchas | `read_skill_resource("card-games-semantic-model", "references/gotchas.md")` |
| Metric definitions | `read_skill_resource("card-games-semantic-model", "references/metrics.md")` |
| Query patterns | `read_skill_resource("card-games-semantic-model", "references/query_patterns.md")` |


## ENRICHMENT: recommended improvements
- Add canonical fields: `set_release_date`, `is_promo` boolean, `normalized_type` (array) for multi-type cards.
- Suggested metrics: price median by rarity, set completeness percentage for collectors.

### Extra Query Patterns
-- Sets missing expansion data
SELECT set_name, COUNT(*) as missing_count FROM cards WHERE expansion IS NULL GROUP BY set_name HAVING COUNT(*) > 0;

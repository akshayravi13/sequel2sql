---
name: european-football-semantic-model
description: Semantic model for the european_football_2 database. Contains definitions for matches, players, team attributes, and leagues.
metadata:
  author: manual
  version: "1.0"
---

# European Football — Semantic Model
| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | API IDs vs standard IDs, home/away logic | `read_skill_resource("european-football-semantic-model", "references/gotchas.md")` |
| Metric definitions | Win rates, average goals, player ratings | `read_skill_resource("european-football-semantic-model", "references/metrics.md")` |
| Query patterns | Team standings, player attribute queries | `read_skill_resource("european-football-semantic-model", "references/query_patterns.md")` |

| Term | Actual meaning |
|---|---|
| "home team" / "away team" | `Match.home_team_api_id` / `Match.away_team_api_id` |
| "overall rating" | `Player_Attributes.overall_rating` |

**Core Join Path:** `Match.home_team_api_id` ──→ `Team.team_api_id`


## ENRICHMENT: recommended improvements
- Canonicalize ID mapping: keep `team_api_id`/`player_api_id` as stable keys and include `external_ids` JSON for alternate sources.
- Add time-versioned dimension handling for `Player_Attributes` (valid_from/valid_to) to avoid ambiguous joins.
- Suggested metrics: weighted player-impact (minutes-weighted ratings), rolling form over last N matches.

### Extra Query Patterns
-- Team goals across home/away (combined)
SELECT t.team_api_id, t.team_long_name,
 SUM(CASE WHEN m.home_team_api_id = t.team_api_id THEN m.home_team_goal WHEN m.away_team_api_id = t.team_api_id THEN m.away_team_goal ELSE 0 END) as total_goals
FROM Team t JOIN Match m ON m.home_team_api_id = t.team_api_id OR m.away_team_api_id = t.team_api_id
WHERE m.season = {{season}} GROUP BY t.team_api_id, t.team_long_name;

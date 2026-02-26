---
name: european-football-semantic-model
description: Semantic model for the european_football_2 database (Kaggle European Soccer dataset — matches, players, teams, leagues across 11 European countries). Load this skill when the user is querying the european_football_2 database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-25T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 4
---

# European Football — Semantic Model

## Available Resources

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | API IDs vs primary keys, time-series attribute joins, home/away goal logic | `read_skill_resource("european-football-semantic-model", "references/gotchas.md")` |
| Metric definitions | Win rates, average goals per match, player ratings, form metrics | `read_skill_resource("european-football-semantic-model", "references/metrics.md")` |
| Query patterns | Team standings, top-rated players, head-to-head records | `read_skill_resource("european-football-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If joining teams or players to matches → load `references/gotchas.md` (API ID vs id is critical)
- If querying `Player_Attributes` or `Team_Attributes` → load `references/gotchas.md` (time-series trap)
- If computing total goals or wins → load `references/gotchas.md` + `references/metrics.md`
- For simple league or country lookups → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "home team" | `Match.home_team_api_id` (join to `Team.team_api_id`) | verified |
| "away team" | `Match.away_team_api_id` (join to `Team.team_api_id`) | verified |
| "overall rating" | `Player_Attributes.overall_rating` (0–100 scale) | verified |
| "season" | `Match.season` — stored as text: `'2008/2009'`, `'2009/2010'`, etc. | verified |
| "league" | `League.name` — join: `Match.league_id → League.id` | verified |
| "country" | `Country.name` — join: `League.country_id → Country.id` | verified |
| "team rating" | `Team_Attributes.buildUpPlaySpeed` / `overall` etc. — time-series, filter by date | verified |
| "lineup" | `Match.home_player_1` … `Match.home_player_11` — store `player_api_id` values | verified |

## Gotchas

1. **Always join on `team_api_id` / `player_api_id`, NOT `id`** — the `id`
   column is an internal SQLite/PostgreSQL row ID. The stable cross-table key
   is `team_api_id` for teams and `player_api_id` for players.

2. **`Player_Attributes` and `Team_Attributes` are time-series** — each player/team
   has multiple rows across different dates. Joining without a date filter creates
   a Cartesian product. Use a subquery to get the most recent record.

3. **A team's total goals requires combining home and away** — `Match` stores
   `home_team_goal` and `away_team_goal` separately. You need a CASE expression
   to aggregate from both perspectives.

4. **`Match.season` is a text field** — format is `'2008/2009'`. Filter with
   `= '2008/2009'`, not `= 2008` or `= 2009`.

5. **`Match` has 11 player columns per side** — `home_player_1` through
   `home_player_11` each store a `player_api_id`. There is no normalised
   player-per-match table; lineup queries require unpivoting these columns.

For extended gotchas and SQL examples, call:
```python
read_skill_resource(
	skill_name="european-football-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
Match.home_team_api_id  ──→  Team.team_api_id        (match ↔ home team)
Match.away_team_api_id  ──→  Team.team_api_id        (match ↔ away team)
Match.league_id         ──→  League.id               (match ↔ league)
League.country_id       ──→  Country.id              (league ↔ country)
Player_Attributes.player_api_id ──→ Player.player_api_id  (attributes ↔ player)
Team_Attributes.team_api_id     ──→ Team.team_api_id      (attributes ↔ team)
Match.home_player_1..11 ──→  Player.player_api_id    (lineup ↔ player)
```

There is no direct join between `Match` and `Player_Attributes`. Go through
`Player` via `player_api_id`.

## Frequently Asked Queries

For canonical query patterns (season standings, top scorers, player ratings),
call:
```python
read_skill_resource(
	skill_name="european-football-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas (goals per game, win rates, player rating trends), call:
```python
read_skill_resource(
	skill_name="european-football-semantic-model",
	resource_name="references/metrics.md"
)
```

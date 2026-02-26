---
name: formula1-semantic-model
description: Semantic model for the formula_1 database (Ergast F1 historical dataset — races, drivers, constructors, results, qualifying, pit stops, lap times). Load this skill when the user is querying the formula_1 database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-25T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 5
---

# Formula 1 — Semantic Model

## Available Resources

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | Time string vs milliseconds, NULL positions, positionText values, standings pitfalls | `read_skill_resource("formula1-semantic-model", "references/gotchas.md")` |
| Metric definitions | Points totals, win counts, pit stop averages, championship standings | `read_skill_resource("formula1-semantic-model", "references/metrics.md")` |
| Query patterns | Driver standings, constructor wins, fastest laps, DNF analysis | `read_skill_resource("formula1-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If the query involves timing or lap times → load `references/gotchas.md` (time columns are strings)
- If the query involves standings or season totals → load `references/gotchas.md` (standings are cumulative)
- If aggregating wins, points, or positions → load `references/metrics.md`
- For simple race or driver lookups → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "race winner" | `results.position = 1` (integer — NULL for non-finishers) | verified |
| "did not finish" / "DNF" | `results.position IS NULL` or `status.status` not equal to `'Finished'` | verified |
| "constructor" / "team" | `constructors.name` — joined via `results.constructorId` | verified |
| "grid position" | `results.grid` (starting position) — separate from finishing `results.position` | verified |
| "fastest lap" | `results.rank = 1` (fastest lap rank within the race) | verified |
| "season" | `races.year` (integer, e.g. `2021`) | verified |
| "race time" | `results.milliseconds` — use this for arithmetic; `results.time` is a formatted string | verified |
| "DNF reason" | `status.status` — joined via `results.statusId → status.statusId` | verified |

## Gotchas

1. **Time columns are strings — use `milliseconds` for arithmetic** — `results.time`,
   `qualifying.q1/q2/q3`, `laptimes.time`, and `pitstops.duration` are formatted
   strings like `"1:23.456"`. Only the `milliseconds` integer column is safe for
   math and aggregation.

2. **`results.position` is NULL for non-finishers** — drivers who retired,
   were disqualified, or did not start have NULL in `position`. Use `positionOrder`
   (always populated) to rank all starters, or filter on `status` for DNF analysis.

3. **`driverstandings` and `constructorstandings` are cumulative per race** —
   these tables store the running championship total after each race, not per-race
   points. For the season total, filter to the last race of the season.

4. **`results.positionText` contains non-numeric codes** — values include `'R'`
   (retired), `'D'` (disqualified), `'W'` (withdrawn), `'F'` (failed to qualify),
   `'N'` (not classified). Never cast `positionText` to integer without guarding.

5. **`pitstops` has both `duration` (text) and `milliseconds` (integer)** —
   always use `milliseconds` for pit stop duration math.

For extended gotchas and SQL examples, call:
```python
read_skill_resource(
	skill_name="formula1-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
races.raceId          ──→  results.raceId       ──→  drivers.driverId
races.raceId          ──→  results.raceId       ──→  constructors.constructorId
races.raceId          ──→  qualifying.raceId    ──→  drivers.driverId
races.raceId          ──→  laptimes.raceId      ──→  drivers.driverId
races.raceId          ──→  pitstops.raceId      ──→  drivers.driverId
races.circuitId       ──→  circuits.circuitId
results.statusId      ──→  status.statusId      (DNF reason)
races.raceId          ──→  driverstandings.raceId
races.raceId          ──→  constructorstandings.raceId
```

## Frequently Asked Queries

For canonical query patterns (season champions, win counts, fastest laps), call:
```python
read_skill_resource(
	skill_name="formula1-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas (points per season, pit stop averages, constructor wins),
call:
```python
read_skill_resource(
	skill_name="formula1-semantic-model",
	resource_name="references/metrics.md"
)
```

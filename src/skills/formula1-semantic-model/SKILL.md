---
name: formula1-semantic-model
description: Semantic model for the formula_1 database (Ergast F1 dataset).
metadata:
  author: manual
  version: "1.0"
---

# Formula 1 — Semantic Model
| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | Milliseconds vs formatted times, status codes | `read_skill_resource("formula1-semantic-model", "references/gotchas.md")` |
| Metric definitions | Points, win counts, pit stop durations | `read_skill_resource("formula1-semantic-model", "references/metrics.md")` |
| Query patterns | Driver standings, constructor results | `read_skill_resource("formula1-semantic-model", "references/query_patterns.md")` |

| Term | Actual meaning |
|---|---|
| "race winner" | `results.position = 1` |
| "constructor" | `constructors.name` (The team) |

**Core Join Path:** `races.raceId` ──→ `results.raceId` ──→ `drivers.driverId`


## ENRICHMENT: recommended improvements
- Prefer integer `milliseconds` columns for timing math; store formatted `time` only for display.
- Add `session_type` (race/qualifying/practice) to disambiguate aggregated metrics, and a `season` surrogate key for partitioning.
- Suggested metrics: points per race, pit-stop efficiency (pit_stop_time_ms percentiles).

### Extra Query Patterns
-- Average lap time (milliseconds) per driver across a season
SELECT d.driverId, d.forename || ' ' || d.surname as driver_name, AVG(lap_time_ms) as avg_lap_ms
FROM drivers d JOIN lap_times l ON d.driverId = l.driverId
JOIN races r ON l.raceId = r.raceId WHERE r.season = {{season}} GROUP BY d.driverId ORDER BY avg_lap_ms;

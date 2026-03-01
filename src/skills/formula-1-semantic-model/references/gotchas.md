# Gotchas — formula_1

## 1. Time columns are formatted strings — use `milliseconds` for arithmetic

**Problem**: `results.time`, `qualifying.q1`, `qualifying.q2`, `qualifying.q3`,
`laptimes.time`, and `pitstops.duration` are text strings like `"1:23.456"`.
Arithmetic, MIN/MAX, and ORDER BY on these strings gives wrong results.

**Correct usage**:
```sql
-- CORRECT: fastest race completion time using milliseconds
SELECT d.forename, d.surname, MIN(r.milliseconds) AS fastest_ms
FROM results r
JOIN drivers d ON r.driverId = d.driverId
WHERE r.milliseconds IS NOT NULL
GROUP BY d.driverId
ORDER BY fastest_ms;

-- WRONG — string comparison, not numeric
SELECT MIN(r.time) FROM results r   -- '1:20.000' sorts before '1:19.999' as strings
```

---

## 2. `results.position` is NULL for non-finishers

**Problem**: Drivers who retired, were disqualified, or failed to start have
`NULL` in `results.position`. Filtering `WHERE position > 0` silently drops
these rows; aggregating position can give misleading averages.

**Correct usage**:
```sql
-- CORRECT: all finishers
SELECT * FROM results WHERE position IS NOT NULL;

-- CORRECT: all starters in finishing order (including DNFs)
SELECT * FROM results ORDER BY positionOrder;

-- CORRECT: count DNFs
SELECT COUNT(*) FROM results r
JOIN status s ON r.statusId = s.statusId
WHERE s.status != 'Finished';

-- WRONG — drops non-finishers silently
WHERE position BETWEEN 1 AND 20
```

---

## 3. `driverstandings` / `constructorstandings` are cumulative, not per-race

**Problem**: These tables store the running championship points AFTER each race.
Summing all rows for a season returns the sum of all running totals, not the
season total.

**Correct usage — season final standings**:
```sql
-- CORRECT: championship standings after the last race of 2021
SELECT
	d.forename, d.surname,
	ds.points AS season_total,
	ds.position AS championship_position
FROM driverstandings ds
JOIN drivers d ON ds.driverId = d.driverId
WHERE ds.raceId = (
	SELECT MAX(raceId) FROM races WHERE year = 2021
)
ORDER BY ds.position;

-- WRONG — sums all intermediate totals
SELECT driverId, SUM(points) FROM driverstandings
WHERE raceId IN (SELECT raceId FROM races WHERE year = 2021)
GROUP BY driverId;
```

---

## 4. `results.positionText` contains non-numeric codes

**Problem**: `positionText` stores things like `'R'` (retired), `'D'`
(disqualified), `'W'` (withdrawn). Casting to integer fails for these rows.

**Correct usage**:
```sql
-- CORRECT: only numeric positions
SELECT * FROM results WHERE positionText ~ '^\d+$';

-- CORRECT: cast safely
SELECT CASE WHEN positionText ~ '^\d+$' THEN positionText::integer
            ELSE NULL END AS position_int
FROM results;

-- WRONG — error on 'R', 'D', etc.
SELECT positionText::integer FROM results;
```

---

## 5. `results.grid = 0` means started from the pit lane

**Problem**: A `grid` value of `0` does not mean the driver started first — it
means they started from the pit lane (e.g. after a penalty or car change).

**Correct usage**:
```sql
-- CORRECT: exclude pit lane starts when analysing grid positions
SELECT * FROM results WHERE grid > 0;

-- To identify pit lane starts:
SELECT r.raceId, d.forename, d.surname
FROM results r
JOIN drivers d ON r.driverId = d.driverId
WHERE r.grid = 0;
```

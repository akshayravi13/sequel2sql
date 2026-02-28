# Query Patterns — formula_1

## "Who won the most races in a given season?"

```sql
SELECT
	d.forename || ' ' || d.surname AS driver_name,
	COUNT(*) AS wins
FROM results r
JOIN drivers d ON r.driverId = d.driverId
JOIN races ra ON r.raceId = ra.raceId
WHERE r.position = 1
  AND ra.year = 2021
GROUP BY d.driverId, d.forename, d.surname
ORDER BY wins DESC;
```

---

## "What were the final championship standings for the 2021 season?"

```sql
-- Use the last race of the season for final points totals
SELECT
	ds.position AS rank,
	d.forename || ' ' || d.surname AS driver,
	d.nationality,
	ds.points,
	ds.wins
FROM driverstandings ds
JOIN drivers d ON ds.driverId = d.driverId
WHERE ds.raceId = (
	SELECT MAX(raceId) FROM races WHERE year = 2021
)
ORDER BY ds.position;
```

---

## "Why did a driver retire from a specific race?"

```sql
-- Join results to status for the DNF reason
SELECT
	d.forename || ' ' || d.surname AS driver,
	ra.name AS race,
	ra.year,
	s.status AS retirement_reason,
	r.laps AS laps_completed
FROM results r
JOIN drivers d ON r.driverId = d.driverId
JOIN races ra ON r.raceId = ra.raceId
JOIN status s ON r.statusId = s.statusId
WHERE ra.name = 'British Grand Prix'
  AND ra.year = 2021
  AND s.status != 'Finished'
ORDER BY r.positionOrder;
```

---

## "Which circuit has the most races in F1 history?"

```sql
SELECT
	ci.name AS circuit_name,
	ci.country,
	COUNT(*) AS race_count
FROM races ra
JOIN circuits ci ON ra.circuitId = ci.circuitId
GROUP BY ci.circuitId, ci.name, ci.country
ORDER BY race_count DESC
LIMIT 10;
```

---

## "What is the qualifying vs race position change for each driver in a race?"

```sql
SELECT
	d.forename || ' ' || d.surname AS driver,
	r.grid AS qualifying_position,
	r.position AS finish_position,
	r.grid - r.position AS positions_gained,
	s.status
FROM results r
JOIN drivers d ON r.driverId = d.driverId
JOIN races ra ON r.raceId = ra.raceId
JOIN status s ON r.statusId = s.statusId
WHERE ra.name = 'Monaco Grand Prix'
  AND ra.year = 2021
  AND r.grid > 0            -- exclude pit lane starts
ORDER BY r.positionOrder;
```

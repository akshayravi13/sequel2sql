# Metric Definitions — formula_1

## Total Championship Points per Driver in a Season

```sql
-- Use the last race of the season to get final standings
SELECT
	d.forename || ' ' || d.surname AS driver_name,
	d.nationality,
	ds.points AS season_points,
	ds.wins,
	ds.position AS championship_rank
FROM driverstandings ds
JOIN drivers d ON ds.driverId = d.driverId
WHERE ds.raceId = (
	SELECT MAX(raceId) FROM races WHERE year = 2021
)
ORDER BY ds.position;
```

---

## Win Count by Driver (All Time)

```sql
SELECT
	d.forename || ' ' || d.surname AS driver_name,
	d.nationality,
	COUNT(*) AS race_wins
FROM results r
JOIN drivers d ON r.driverId = d.driverId
WHERE r.position = 1
GROUP BY d.driverId, d.forename, d.surname, d.nationality
ORDER BY race_wins DESC
LIMIT 20;
```

---

## Constructor Wins by Season

```sql
SELECT
	c.name AS constructor,
	ra.year AS season,
	COUNT(*) AS wins
FROM results r
JOIN constructors c ON r.constructorId = c.constructorId
JOIN races ra ON r.raceId = ra.raceId
WHERE r.position = 1
GROUP BY c.constructorId, c.name, ra.year
ORDER BY ra.year DESC, wins DESC;
```

---

## Average Pit Stop Duration per Driver per Race

```sql
-- pitstops.milliseconds is reliable; pitstops.duration is a text string
SELECT
	ra.name AS race_name,
	d.forename || ' ' || d.surname AS driver_name,
	COUNT(ps.stop) AS pit_stop_count,
	ROUND(AVG(ps.milliseconds), 0) AS avg_pit_ms,
	SUM(ps.milliseconds) AS total_pit_ms
FROM pitstops ps
JOIN races ra ON ps.raceId = ra.raceId
JOIN drivers d ON ps.driverId = d.driverId
WHERE ra.year = 2021
GROUP BY ra.raceId, ra.name, d.driverId, d.forename, d.surname
ORDER BY avg_pit_ms;
```

---

## DNF Rate by Constructor

```sql
SELECT
	c.name AS constructor,
	COUNT(*) AS total_entries,
	SUM(CASE WHEN s.status != 'Finished' AND s.status NOT LIKE '+%' THEN 1 ELSE 0 END) AS dnfs,
	ROUND(
		SUM(CASE WHEN s.status != 'Finished' AND s.status NOT LIKE '+%' THEN 1 ELSE 0 END)::numeric
		/ COUNT(*),
		4
	) AS dnf_rate
FROM results r
JOIN constructors c ON r.constructorId = c.constructorId
JOIN status s ON r.statusId = s.statusId
GROUP BY c.constructorId, c.name
ORDER BY dnf_rate DESC;
```

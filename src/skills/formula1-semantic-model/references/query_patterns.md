-- Most Wins by Constructor
SELECT c.name, COUNT(*) as wins
FROM constructors c JOIN results r ON c.constructorId = r.constructorId
WHERE r.position = 1 GROUP BY c.name ORDER BY wins DESC LIMIT 10;


-- EXTRA CANONICAL QUERIES

-- Average lap time (milliseconds) per driver across a season
SELECT d.driverId, d.forename || ' ' || d.surname as driver_name, AVG(lap_time_ms) as avg_lap_ms
FROM drivers d JOIN lap_times l ON d.driverId = l.driverId
JOIN races r ON l.raceId = r.raceId WHERE r.season = {{season}} GROUP BY d.driverId ORDER BY avg_lap_ms;

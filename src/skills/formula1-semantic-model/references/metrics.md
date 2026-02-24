-- Total Points per Driver
SELECT d.forename, d.surname, SUM(r.points) AS total_points
FROM drivers d JOIN results r ON d.driverId = r.driverId GROUP BY d.driverId;

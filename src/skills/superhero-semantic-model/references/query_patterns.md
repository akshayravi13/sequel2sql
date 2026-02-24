-- Find Villains (Bad alignment)
SELECT superhero_name FROM superhero JOIN alignment a ON superhero.alignment_id = a.id WHERE a.alignment = 'Bad';


-- EXTRA CANONICAL QUERIES

-- Average power level by publisher (exclude invalid heights)
SELECT p.publisher_name, AVG(s.power_level) FROM superhero s JOIN publisher p ON s.publisher_id = p.id WHERE s.height_cm > 0 GROUP BY p.publisher_name;

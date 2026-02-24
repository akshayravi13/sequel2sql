-- Average Height by Publisher
SELECT p.publisher_name, AVG(s.height_cm) FROM superhero s JOIN publisher p ON s.publisher_id = p.id WHERE s.height_cm > 0 GROUP BY p.publisher_name;

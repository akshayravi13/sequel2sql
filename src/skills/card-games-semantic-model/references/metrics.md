-- Count of cards per set
SELECT set_name, COUNT(*) FROM cards GROUP BY set_name;

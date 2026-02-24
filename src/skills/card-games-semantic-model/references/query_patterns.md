-- Cards by Rarity in a Specific Set
SELECT name, rarity FROM cards WHERE set_id = {{set_id}} ORDER BY rarity;


-- EXTRA CANONICAL QUERIES

-- Sets missing expansion data
SELECT set_name, COUNT(*) as missing_count FROM cards WHERE expansion IS NULL GROUP BY set_name HAVING COUNT(*) > 0;

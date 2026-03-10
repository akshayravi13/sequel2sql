# Metric Definitions — superhero

## Hero Count by Publisher

```sql
SELECT
	COALESCE(p.publisher_name, 'Unknown') AS publisher,
	COUNT(*) AS hero_count
FROM superhero s
LEFT JOIN publisher p ON s.publisher_id = p.id
GROUP BY p.publisher_name
ORDER BY hero_count DESC;
```

---

## Average Physical Attributes by Publisher (Excluding Missing Values)

```sql
-- height_cm = 0 and weight_kg = 0 are sentinels for missing data
SELECT
	p.publisher_name,
	ROUND(AVG(s.height_cm) FILTER (WHERE s.height_cm != 0), 1) AS avg_height_cm,
	ROUND(AVG(s.weight_kg) FILTER (WHERE s.weight_kg != 0), 1) AS avg_weight_kg,
	COUNT(*) AS hero_count
FROM superhero s
JOIN publisher p ON s.publisher_id = p.id
GROUP BY p.publisher_name
ORDER BY hero_count DESC;
```

---

## Power Count Distribution

```sql
-- How many heroes have each number of superpowers?
SELECT
	power_count,
	COUNT(*) AS hero_count
FROM (
	SELECT s.id, COUNT(hp.power_id) AS power_count
	FROM superhero s
	LEFT JOIN hero_power hp ON s.id = hp.hero_id
	GROUP BY s.id
) counts
GROUP BY power_count
ORDER BY power_count;
```

---

## Average Attribute Score by Alignment

```sql
-- attribute scores 0-100 for Intelligence, Strength, Speed, Durability, Power, Combat
SELECT
	a.alignment,
	attr.attribute_name,
	ROUND(AVG(ha.attribute_value), 1) AS avg_score
FROM superhero s
JOIN alignment a ON s.alignment_id = a.id
JOIN hero_attribute ha ON s.id = ha.hero_id
JOIN attribute attr ON ha.attribute_id = attr.id
WHERE a.alignment IN ('Good', 'Bad', 'Neutral')
GROUP BY a.alignment, attr.attribute_name
ORDER BY attr.attribute_name, a.alignment;
```

---

## Most Common Superpowers Across All Heroes

```sql
SELECT
	sp.power_name,
	COUNT(*) AS hero_count
FROM hero_power hp
JOIN superpower sp ON hp.power_id = sp.id
GROUP BY sp.power_id, sp.power_name
ORDER BY hero_count DESC
LIMIT 20;
```

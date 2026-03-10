# Query Patterns — superhero

## "Find all villains (bad alignment) published by DC Comics"

```sql
SELECT s.superhero_name, s.full_name
FROM superhero s
JOIN alignment a ON s.alignment_id = a.id
JOIN publisher p ON s.publisher_id = p.id
WHERE a.alignment = 'Bad'
  AND p.publisher_name = 'DC Comics'
ORDER BY s.superhero_name;
```

---

## "Which heroes have the most superpowers?"

```sql
SELECT
	s.superhero_name,
	COALESCE(p.publisher_name, 'Unknown') AS publisher,
	COUNT(hp.power_id) AS power_count
FROM superhero s
LEFT JOIN publisher p ON s.publisher_id = p.id
LEFT JOIN hero_power hp ON s.id = hp.hero_id
GROUP BY s.id, s.superhero_name, p.publisher_name
ORDER BY power_count DESC
LIMIT 20;
```

---

## "Who has the highest Intelligence score?"

```sql
-- hero_attribute.attribute_value (0–100); attribute_name = 'Intelligence'
SELECT
	s.superhero_name,
	COALESCE(p.publisher_name, 'Unknown') AS publisher,
	ha.attribute_value AS intelligence
FROM superhero s
JOIN hero_attribute ha ON s.id = ha.hero_id
JOIN attribute attr ON ha.attribute_id = attr.id
LEFT JOIN publisher p ON s.publisher_id = p.id
WHERE attr.attribute_name = 'Intelligence'
ORDER BY ha.attribute_value DESC
LIMIT 10;
```

---

## "Show all colour attributes for a specific hero"

```sql
-- Three colour FK columns all join the same colour table — must alias
SELECT
	s.superhero_name,
	ec.colour AS eye_colour,
	hc.colour AS hair_colour,
	sc.colour AS skin_colour
FROM superhero s
LEFT JOIN colour ec ON s.eye_colour_id = ec.id
LEFT JOIN colour hc ON s.hair_colour_id = hc.id
LEFT JOIN colour sc ON s.skin_colour_id = sc.id
WHERE s.superhero_name = 'Batman';
```

---

## "Compare average strength between Marvel and DC heroes"

```sql
SELECT
	p.publisher_name,
	ROUND(AVG(ha.attribute_value), 1) AS avg_strength
FROM superhero s
JOIN publisher p ON s.publisher_id = p.id
JOIN hero_attribute ha ON s.id = ha.hero_id
JOIN attribute attr ON ha.attribute_id = attr.id
WHERE attr.attribute_name = 'Strength'
  AND p.publisher_name IN ('DC Comics', 'Marvel Comics')
GROUP BY p.publisher_name;
```

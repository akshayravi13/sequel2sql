# Gotchas — superhero

## 1. `height_cm` and `weight_kg` use `0` as the sentinel for missing data

**Problem**: Heroes without known height or weight have `0` stored — not NULL.
Averaging without filtering includes zeroes and significantly skews results.

**Correct usage**:
```sql
-- CORRECT: average height for heroes with valid data
SELECT
	p.publisher_name,
	ROUND(AVG(s.height_cm), 1) AS avg_height_cm
FROM superhero s
JOIN publisher p ON s.publisher_id = p.id
WHERE s.height_cm != 0   -- exclude missing values
GROUP BY p.publisher_name;

-- WRONG — includes zeroes, lowering the average
SELECT p.publisher_name, AVG(s.height_cm)
FROM superhero s JOIN publisher p ON s.publisher_id = p.id
GROUP BY p.publisher_name;
```

---

## 2. Three colour FK columns all reference the same `colour` table — must alias

**Problem**: `superhero` has `eye_colour_id`, `hair_colour_id`, and
`skin_colour_id`, all FKs to `colour.id`. Joining the `colour` table once
and not aliasing causes PostgreSQL to error or return ambiguous results.

**Correct usage**:
```sql
-- CORRECT: alias colour table three times
SELECT
	s.superhero_name,
	ec.colour AS eye_colour,
	hc.colour AS hair_colour,
	sc.colour AS skin_colour
FROM superhero s
LEFT JOIN colour ec ON s.eye_colour_id = ec.id
LEFT JOIN colour hc ON s.hair_colour_id = hc.id
LEFT JOIN colour sc ON s.skin_colour_id = sc.id;

-- WRONG — ambiguous, or only one colour joined
JOIN colour c ON s.eye_colour_id = c.id  -- hair and skin are missing
```

---

## 3. `publisher_id` is NULL for some heroes

**Problem**: Independent or unknown-publisher heroes have `NULL` in
`publisher_id`. Using `INNER JOIN publisher` silently drops these heroes.

**Correct usage**:
```sql
-- CORRECT: keep all heroes, show NULL publisher as 'Unknown'
SELECT
	s.superhero_name,
	COALESCE(p.publisher_name, 'Unknown') AS publisher
FROM superhero s
LEFT JOIN publisher p ON s.publisher_id = p.id;

-- WRONG — drops heroes with no publisher record
INNER JOIN publisher p ON s.publisher_id = p.id
```

---

## 4. `alignment.alignment` includes `'-'` for unknown alignment

**Problem**: The alignment table has four values: `'Good'`, `'Bad'`,
`'Neutral'`, and `'-'` (unknown). Filtering `WHERE alignment IN ('Good','Bad','Neutral')`
silently excludes heroes with unknown alignment.

**Correct usage**:
```sql
-- Heroes with a defined alignment
SELECT COUNT(*) FROM superhero s
JOIN alignment a ON s.alignment_id = a.id
WHERE a.alignment != '-';

-- Heroes with unknown alignment
SELECT COUNT(*) FROM superhero s
JOIN alignment a ON s.alignment_id = a.id
WHERE a.alignment = '-';
```

---

## 5. `hero_power` is a many-to-many junction — aggregate at the hero level

**Problem**: Each superpower a hero has is one row in `hero_power`. Joining
`hero_power` without aggregating multiplies rows — one result row per power.

**Correct usage**:
```sql
-- CORRECT: count of powers per hero
SELECT
	s.superhero_name,
	COUNT(hp.power_id) AS power_count
FROM superhero s
LEFT JOIN hero_power hp ON s.id = hp.hero_id
GROUP BY s.id, s.superhero_name
ORDER BY power_count DESC;

-- CORRECT: list powers for a specific hero
SELECT sp.power_name
FROM superhero s
JOIN hero_power hp ON s.id = hp.hero_id
JOIN superpower sp ON hp.power_id = sp.id
WHERE s.superhero_name = 'Superman';
```

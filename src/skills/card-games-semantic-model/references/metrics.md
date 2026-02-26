# Metric Definitions — card_games

## Card Count by Rarity

```sql
-- Distribution of cards across rarity tiers
SELECT
	rarity,
	COUNT(*) AS card_count,
	ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER (), 4) AS fraction
FROM cards
GROUP BY rarity
ORDER BY
	CASE rarity
		WHEN 'common' THEN 1
		WHEN 'uncommon' THEN 2
		WHEN 'rare' THEN 3
		WHEN 'mythic' THEN 4
		ELSE 5
	END;
```

---

## Cards per Set (Set Size)

```sql
-- Number of unique cards in each set, joined to set name
SELECT
	s.name AS set_name,
	s.releaseDate,
	COUNT(c.id) AS card_count
FROM sets s
LEFT JOIN cards c ON c.setCode = s.code
GROUP BY s.code, s.name, s.releaseDate
ORDER BY s.releaseDate DESC;
```

---

## Average Converted Mana Cost by Card Type

```sql
-- Average CMC for each major card type category
SELECT
	CASE
		WHEN type LIKE '%Creature%' THEN 'Creature'
		WHEN type LIKE '%Instant%' THEN 'Instant'
		WHEN type LIKE '%Sorcery%' THEN 'Sorcery'
		WHEN type LIKE '%Enchantment%' THEN 'Enchantment'
		WHEN type LIKE '%Artifact%' THEN 'Artifact'
		WHEN type LIKE '%Planeswalker%' THEN 'Planeswalker'
		WHEN type LIKE '%Land%' THEN 'Land'
		ELSE 'Other'
	END AS card_category,
	COUNT(*) AS card_count,
	ROUND(AVG(convertedManaCost), 2) AS avg_cmc
FROM cards
WHERE convertedManaCost IS NOT NULL
GROUP BY card_category
ORDER BY avg_cmc DESC;
```

---

## Color Distribution

```sql
-- How many cards are each color (including multi-color)
SELECT
	CASE
		WHEN colors IS NULL OR colors = '' THEN 'Colorless'
		WHEN colors NOT LIKE '%|%' THEN colors   -- mono-color
		ELSE 'Multi'
	END AS color_category,
	COUNT(*) AS card_count
FROM cards
GROUP BY color_category
ORDER BY card_count DESC;
```

---

## Format Legality Breakdown

```sql
-- Count of cards that are legal in each major format
SELECT
	format,
	SUM(CASE WHEN status = 'Legal' THEN 1 ELSE 0 END) AS legal_count,
	SUM(CASE WHEN status = 'Banned' THEN 1 ELSE 0 END) AS banned_count,
	SUM(CASE WHEN status = 'Restricted' THEN 1 ELSE 0 END) AS restricted_count
FROM legalities
GROUP BY format
ORDER BY legal_count DESC;
```

# Query Patterns — card_games

## "Find all rare and mythic creatures in a specific set"

```sql
-- Use LIKE for type matching; rarity values are lowercase
SELECT c.name, c.type, c.rarity, c.convertedManaCost
FROM cards c
JOIN sets s ON c.setCode = s.code
WHERE s.name = 'Innistrad'
  AND c.type LIKE '%Creature%'
  AND c.rarity IN ('rare', 'mythic')
ORDER BY c.rarity, c.convertedManaCost;
```

---

## "Which cards are legal in Modern but banned in Legacy?"

```sql
SELECT c.name, c.setCode
FROM cards c
JOIN legalities l_mod ON c.uuid = l_mod.uuid AND l_mod.format = 'modern' AND l_mod.status = 'Legal'
JOIN legalities l_leg ON c.uuid = l_leg.uuid AND l_leg.format = 'legacy' AND l_leg.status = 'Banned'
ORDER BY c.name;
```

---

## "List all rulings for a specific card"

```sql
-- Find rulings by card name
SELECT c.name, r.date, r.text
FROM cards c
JOIN rulings r ON c.uuid = r.uuid
WHERE c.name = 'Black Lotus'
ORDER BY r.date;
```

---

## "Find the highest-CMC cards that are not lands"

```sql
-- power/toughness are text; use convertedManaCost (numeric) for sorting
SELECT name, type, convertedManaCost, manaCost
FROM cards
WHERE type NOT LIKE '%Land%'
  AND convertedManaCost IS NOT NULL
ORDER BY convertedManaCost DESC
LIMIT 20;
```

---

## "Get the French translation of cards in a set"

```sql
-- foreign_data joins via uuid; filter by language
SELECT c.name AS english_name, fd.name AS french_name, fd.text AS french_text
FROM cards c
JOIN foreign_data fd ON c.uuid = fd.uuid
JOIN sets s ON c.setCode = s.code
WHERE fd.language = 'French'
  AND s.name = 'Core Set 2021'
ORDER BY c.name;
```

# Gotchas — card_games

## 1. `cards.type` is a compound string — use `LIKE`, not `=`

**Problem**: A card's `type` field combines supertypes, types, and subtypes into
one string, e.g. `"Legendary Creature — Dragon"` or `"Artifact Creature — Construct"`.
Filtering with `= 'Creature'` always returns zero rows.

**Correct usage**:
```sql
-- CORRECT
SELECT name FROM cards WHERE type LIKE '%Creature%';
SELECT name FROM cards WHERE type LIKE '%Instant%';
SELECT name FROM cards WHERE type LIKE '%Legendary%' AND type LIKE '%Creature%';

-- WRONG — zero rows
SELECT name FROM cards WHERE type = 'Creature';
SELECT name FROM cards WHERE type = 'Legendary Creature';
```

---

## 2. `cards.power` and `cards.toughness` are TEXT, not numeric

**Problem**: Power and toughness are stored as strings to handle non-numeric
values like `'*'`, `'X'`, `'1+*'`, `'2+*'`. Casting directly to integer or
using numeric comparisons fails for these rows.

**Correct usage**:
```sql
-- CORRECT: filter to numeric-only values before casting
SELECT name, power::integer AS power_int
FROM cards
WHERE power ~ '^\d+$'   -- only rows that are pure integers
ORDER BY power_int DESC;

-- CORRECT: count cards with non-numeric power
SELECT COUNT(*) FROM cards WHERE power !~ '^\d+$';

-- WRONG — error on rows with '*' or 'X'
SELECT name FROM cards ORDER BY power::integer DESC;
```

---

## 3. `cards.colors` is a pipe-separated string

**Problem**: Multi-color cards store colors as a pipe-delimited string: `'W|U'`,
`'R|G|B'`. A simple `= 'W'` check misses multi-color cards that include white.

**Correct usage**:
```sql
-- CORRECT: cards that include White (may also be other colors)
SELECT name FROM cards WHERE colors LIKE '%W%';

-- CORRECT: strictly mono-White cards
SELECT name FROM cards WHERE colors = 'W';

-- CORRECT: using array splitting for precise matching
SELECT name FROM cards
WHERE 'W' = ANY(string_to_array(colors, '|'));

-- WRONG — misses 'W|U', 'W|B|R', etc.
SELECT name FROM cards WHERE colors = 'W';   -- only finds mono-White
```

---

## 4. `rarity` values are lowercase strings

**Problem**: Rarity is stored as lowercase: `'common'`, `'uncommon'`, `'rare'`,
`'mythic'`. Using title case or uppercase returns zero rows.

**Correct usage**:
```sql
-- CORRECT
SELECT name FROM cards WHERE rarity = 'rare';
SELECT name FROM cards WHERE rarity = 'mythic';

-- WRONG
SELECT name FROM cards WHERE rarity = 'Rare';
SELECT name FROM cards WHERE rarity = 'MYTHIC';
```

---

## 5. Promotional and special cards have many NULL fields

**Problem**: Promo cards (`promoTypes IS NOT NULL` or `isPromo = 1`) often
have NULL values for `multiverseId`, `number`, and other standard fields.
Aggregations that assume all cards have complete data will silently drop promos.

**Correct usage**:
```sql
-- CORRECT: exclude promos when you need complete data
SELECT * FROM cards WHERE isPromo = 0 OR isPromo IS NULL;

-- CORRECT: check for promos explicitly
SELECT COUNT(*) FROM cards WHERE isPromo = 1;

-- Gotcha: 'number' is also NULL for some non-promo reprint sets
-- Always use NULLIF or filter before using 'number' in ORDER BY
```

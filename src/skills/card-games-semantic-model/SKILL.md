---
name: card-games-semantic-model
description: Semantic model for the card_games database (Magic: The Gathering card data). Contains definitions for cards, sets, legalities, rulings, and foreign language data. Load this skill when the user is querying the card_games database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-25T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 4
---

# Card Games — Semantic Model

## Available Resources

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | Compound type fields, text power/toughness, color encoding, promo NULLs | `read_skill_resource("card-games-semantic-model", "references/gotchas.md")` |
| Metric definitions | Card counts by rarity, set size, color distribution | `read_skill_resource("card-games-semantic-model", "references/metrics.md")` |
| Query patterns | Canonical SQL for card searches, legality queries, set lookups | `read_skill_resource("card-games-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If filtering by card type, color, or power/toughness → load `references/gotchas.md` (these fields are not simple scalars)
- If querying legality across formats → load `references/gotchas.md` + `references/query_patterns.md`
- If counting or aggregating cards → load `references/metrics.md`
- For simple name or set lookups → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "creature card" | `cards.type LIKE '%Creature%'` — type field contains compound values | verified |
| "instant" / "sorcery" | `cards.type LIKE '%Instant%'` / `cards.type LIKE '%Sorcery%'` | verified |
| "rarity" | `cards.rarity` — values: `'common'`, `'uncommon'`, `'rare'`, `'mythic'` (all lowercase) | verified |
| "mana cost" | `cards.manaCost` (formatted string like `'{2}{W}{U}'`) | verified |
| "converted mana cost" / "CMC" | `cards.convertedManaCost` (numeric) | verified |
| "set" / "edition" | `sets` table — join via `cards.setCode = sets.code` | verified |
| "format legality" | `legalities` table — join via `cards.uuid = legalities.uuid` | verified |
| "ruling" | `rulings` table — join via `cards.uuid = rulings.uuid` | verified |
| "non-English card text" | `foreign_data` table — join via `cards.uuid = foreign_data.uuid` | verified |

## Gotchas

1. **`cards.type` is a compound string** — a card can be `"Legendary Creature — Dragon"`.
   Never filter with `= 'Creature'`; always use `LIKE '%Creature%'`.

2. **`cards.power` and `cards.toughness` are TEXT** — they can be `'*'`, `'X'`,
   `'1+*'`, or a number stored as text. Do not cast to integer without guarding
   for non-numeric values.

3. **`cards.colors` is a pipe-separated string** — e.g. `'W'`, `'U|B'`, `'R|G'`.
   To filter for a specific color, use `LIKE '%W%'` or
   `'W' = ANY(string_to_array(colors, '|'))`.

4. **Rarity values are lowercase** — `'common'`, `'uncommon'`, `'rare'`,
   `'mythic'`. Never use `'Rare'` or `'RARE'`.

5. **Promotional cards have NULL in many columns** — `number`, `multiverseId`,
   and set-related fields are often NULL for promos. Use `IS NULL` checks
   rather than assuming all cards have complete data.

For extended gotchas and SQL examples, call:
```python
read_skill_resource(
	skill_name="card-games-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
cards.setCode  ──→  sets.code                 (card ↔ its set/edition)
cards.uuid     ──→  legalities.uuid           (card ↔ format legality)
cards.uuid     ──→  rulings.uuid              (card ↔ official rulings)
cards.uuid     ──→  foreign_data.uuid         (card ↔ non-English text)
sets.code      ──→  set_translations.setCode  (set ↔ translated set names)
```

There is no direct join between `legalities` and `sets`; go through `cards`.

## Frequently Asked Queries

For canonical query patterns (cards by format, rarity breakdowns, set contents),
call:
```python
read_skill_resource(
	skill_name="card-games-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas (card counts, color distribution, CMC stats), call:
```python
read_skill_resource(
	skill_name="card-games-semantic-model",
	resource_name="references/metrics.md"
)
```

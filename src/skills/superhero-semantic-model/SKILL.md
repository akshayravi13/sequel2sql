---
name: superhero-semantic-model
description: Semantic model for the superhero database (comic book heroes and villains — publishers, physical attributes, superpowers, alignment). Load this skill when the user is querying the superhero database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-25T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 4
---

# Superhero — Semantic Model

## Available Resources

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | Zero sentinel for height/weight, three colour FK columns, NULL publishers, alignment values | `read_skill_resource("superhero-semantic-model", "references/gotchas.md")` |
| Metric definitions | Average height/weight by publisher, power score distributions | `read_skill_resource("superhero-semantic-model", "references/metrics.md")` |
| Query patterns | Heroes by alignment, publisher comparisons, power queries | `read_skill_resource("superhero-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If aggregating height or weight → load `references/gotchas.md` (zero sentinel values skew averages)
- If joining to the `colour` table → load `references/gotchas.md` (three FK columns, all to the same table)
- If counting powers or attribute scores → load `references/metrics.md`
- For simple alignment or publisher lookups → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "hero" / "villain" | `alignment.alignment = 'Good'` / `alignment.alignment = 'Bad'` | verified |
| "neutral" | `alignment.alignment = 'Neutral'` | verified |
| "unknown alignment" | `alignment.alignment = '-'` | verified |
| "publisher" | `publisher.publisher_name` — e.g. `'DC Comics'`, `'Marvel Comics'` | verified |
| "eye colour" | `superhero.eye_colour_id` → `colour.colour` | verified |
| "hair colour" | `superhero.hair_colour_id` → `colour.colour` | verified |
| "skin colour" | `superhero.skin_colour_id` → `colour.colour` | verified |
| "power score" | `hero_attribute.attribute_value` (0–100) for a specific `attribute.attribute_name` | verified |
| "no colour" | `colour.colour = 'No Colour'` — treat as missing/not applicable | verified |

## Gotchas

1. **`height_cm` and `weight_kg` use `0` as the sentinel for missing data** —
   always filter `WHERE height_cm != 0` and `WHERE weight_kg != 0` before
   aggregating physical measurements.

2. **Three colour FK columns all join to the same `colour` table** — you must
   alias the table three times: once for eye colour, once for hair colour, once
   for skin colour. Joining without aliases causes ambiguity errors.

3. **`publisher_id` is NULL for some heroes** — not all heroes have a known
   publisher. Use `LEFT JOIN publisher` and handle NULL in output.

4. **`alignment.alignment` includes `'-'` for unknown** — do not assume the
   three string values 'Good', 'Bad', 'Neutral' are exhaustive.

5. **`hero_power` is a junction table — one row per hero-power pair** — to
   count all powers for a hero, `COUNT(*)` on `hero_power` after filtering by
   `hero_id`.

For extended gotchas and SQL examples, call:
```python
read_skill_resource(
	skill_name="superhero-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
superhero.alignment_id   ──→  alignment.id
superhero.gender_id      ──→  gender.id
superhero.race_id        ──→  race.id
superhero.publisher_id   ──→  publisher.id             (nullable)
superhero.eye_colour_id  ──→  colour.id  (alias: eye_col)
superhero.hair_colour_id ──→  colour.id  (alias: hair_col)
superhero.skin_colour_id ──→  colour.id  (alias: skin_col)
hero_attribute.hero_id   ──→  superhero.id
hero_attribute.attribute_id ─→ attribute.id
hero_power.hero_id       ──→  superhero.id
hero_power.power_id      ──→  superpower.id
```

## Frequently Asked Queries

For canonical query patterns (heroes by publisher, power counts, attribute
comparisons), call:
```python
read_skill_resource(
	skill_name="superhero-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas (average attributes, power distributions, hero counts),
call:
```python
read_skill_resource(
	skill_name="superhero-semantic-model",
	resource_name="references/metrics.md"
)
```

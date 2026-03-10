---
name: toxicology-semantic-model
description: Semantic model for the toxicology database (mutagenesis molecular data — molecules, atoms, bonds, connectivity). Load this skill when the user is querying the toxicology database.
metadata:
  author: manual
  version: "1.1"
  last_updated: "2026-02-25T00:00:00Z"
  learned_patterns: 0
  verified_patterns: 4
---

# Toxicology — Semantic Model

## Available Resources

| Resource | What it contains | How to load |
|---|---|---|
| Extended gotchas | Label encoding, atom ID format, graph traversal pitfalls | `read_skill_resource("toxicology-semantic-model", "references/gotchas.md")` |
| Metric definitions | Atom counts, toxicity prevalence, bond type distributions | `read_skill_resource("toxicology-semantic-model", "references/metrics.md")` |
| Query patterns | Canonical SQL for toxic molecules, element queries, graph traversal | `read_skill_resource("toxicology-semantic-model", "references/query_patterns.md")` |

**When to load resources:**
- If querying for toxic/non-toxic molecules → load `references/gotchas.md` (label encoding is critical)
- If traversing the molecular graph (paths, connectivity) → load `references/gotchas.md` + `references/query_patterns.md`
- If counting atoms, bonds, or computing distributions → load `references/metrics.md`
- For simple lookups by molecule ID → the information below is sufficient

## Key Concepts

| Term (user says) | Actual meaning | Confidence |
|---|---|---|
| "toxic" / "mutagenic" / "positive" | `molecule.label = '+'` — string plus sign, NOT integer 1 | verified |
| "non-toxic" / "non-mutagenic" / "negative" | `molecule.label = '-'` — string minus sign, NOT integer 0 | verified |
| "single bond" | `bond.bond_type = '-'` | verified |
| "double bond" | `bond.bond_type = '='` | verified |
| "triple bond" | `bond.bond_type = '#'` | verified |
| "aromatic bond" | `bond.bond_type = ':'` | verified |
| "carbon atom" | `atom.element = 'c'` (lowercase) | verified |
| "connected atoms" | `connected` table — links atom pairs via `atom_id`, `atom_id2`, `bond_id` | verified |

## Gotchas

1. **`molecule.label` is a string, not an integer** — toxic molecules have
   `label = '+'`, non-toxic have `label = '-'`. Writing `WHERE label = 1`
   will silently return zero rows.

2. **`atom.element` values are lowercase** — carbon is `'c'`, not `'C'` or
   `'Carbon'`. Chlorine is `'cl'`, nitrogen is `'n'`, oxygen is `'o'`.

3. **Atom and bond IDs encode structure** — `'TR000_1'` means molecule TR000,
   atom position 1. Bond ID `'TR000_1_2'` is the bond between atoms 1 and 2
   in TR000. Do not treat these as opaque strings when debugging.

4. **Graph traversal requires recursive CTEs** — single-hop joins on `connected`
   only find immediate neighbours. For path-length queries, use `WITH RECURSIVE`.

5. **`bond` and `connected` serve different purposes** — `bond` stores bond type
   per molecule; `connected` maps which atom pairs share a bond. Both are needed
   for element-and-bond-type queries.

For extended gotchas and SQL examples, call:
```python
read_skill_resource(
	skill_name="toxicology-semantic-model",
	resource_name="references/gotchas.md"
)
```

## Core Join Paths

```text
molecule.molecule_id  ──→  atom.molecule_id          (molecule ↔ its atoms)
molecule.molecule_id  ──→  bond.molecule_id          (molecule ↔ its bonds)
atom.atom_id          ──→  connected.atom_id         (atom ↔ connections, one end)
atom.atom_id          ──→  connected.atom_id2        (atom ↔ connections, other end)
bond.bond_id          ──→  connected.bond_id         (bond ↔ atom pair sharing it)
```

There is no direct FK between `atom` and `bond`; go through `connected` to
link a specific atom to the bonds it participates in.

## Frequently Asked Queries

For canonical query patterns (toxic molecules by element, bond type filters,
graph traversal), call:
```python
read_skill_resource(
	skill_name="toxicology-semantic-model",
	resource_name="references/query_patterns.md"
)
```

## Metric Definitions

For full metric formulas (atom counts, toxicity rates, bond distributions), call:
```python
read_skill_resource(
	skill_name="toxicology-semantic-model",
	resource_name="references/metrics.md"
)
```

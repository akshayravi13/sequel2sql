# Gotchas — toxicology

## 1. `molecule.label` is a string character, not an integer

**Problem**: The `molecule` table uses `label = '+'` for mutagenic (toxic)
molecules and `label = '-'` for non-mutagenic. A very common mistake is
filtering `WHERE label = 1` (integer) — this will return zero rows without
an error because PostgreSQL will attempt an implicit cast.

**Correct usage**:
```sql
-- CORRECT: toxic molecules
SELECT molecule_id FROM molecule WHERE label = '+';

-- CORRECT: non-toxic molecules
SELECT molecule_id FROM molecule WHERE label = '-';

-- WRONG — returns zero rows (integer vs. text mismatch or cast failure)
SELECT molecule_id FROM molecule WHERE label = 1;
SELECT molecule_id FROM molecule WHERE label = 0;
```

---

## 2. `atom.element` symbols are lowercase

**Problem**: Element symbols are stored in lowercase: `'c'` (carbon), `'n'`
(nitrogen), `'o'` (oxygen), `'cl'` (chlorine), `'s'` (sulphur), `'p'`
(phosphorus), `'h'` (hydrogen). Querying with uppercase or full names returns
zero rows.

**Correct usage**:
```sql
-- CORRECT
SELECT * FROM atom WHERE element = 'c';   -- carbon
SELECT * FROM atom WHERE element = 'cl';  -- chlorine
SELECT * FROM atom WHERE element = 'n';   -- nitrogen

-- WRONG — case mismatch
SELECT * FROM atom WHERE element = 'C';
SELECT * FROM atom WHERE element = 'Carbon';
```

---

## 3. Bond type characters conflict with SQL operators

**Problem**: `bond.bond_type` values are single characters: `'-'` (single),
`'='` (double), `'#'` (triple), `':'` (aromatic). These must be quoted as
string literals — they look like SQL operators but are data values.

**Correct usage**:
```sql
-- CORRECT
SELECT * FROM bond WHERE bond_type = '-';   -- single bond
SELECT * FROM bond WHERE bond_type = '=';   -- double bond
SELECT * FROM bond WHERE bond_type = '#';   -- triple bond
SELECT * FROM bond WHERE bond_type = ':';   -- aromatic bond

-- Note: single bond '-' is the same character as SQL minus — always quote it
```

---

## 4. Atom IDs and bond IDs encode molecule and position

**Problem**: IDs are composite strings, not opaque keys. `atom.atom_id =
'TR000_1'` means molecule `TR000`, atom position 1. `bond.bond_id =
'TR000_1_2'` means the bond between atoms 1 and 2 in molecule TR000. Filtering
on partial strings (e.g. `LIKE 'TR000%'`) is a valid and idiomatic way to
retrieve all atoms/bonds for a molecule when you don't want to join on
`molecule_id`.

```sql
-- Both of these return the same atoms:
SELECT * FROM atom WHERE molecule_id = 'TR000';
SELECT * FROM atom WHERE atom_id LIKE 'TR000_%';
```

---

## 5. Graph traversal needs `connected`, not just `bond`

**Problem**: `bond` stores bond type per molecule but does NOT directly list
which two atoms are connected. The `connected` table provides the atom-pair
mapping (`atom_id`, `atom_id2`, `bond_id`). For any query that needs to walk
the molecular graph, you must join through `connected`.

**Correct multi-hop traversal skeleton**:
```sql
WITH RECURSIVE graph(molecule_id, current_atom, depth) AS (
	-- Base: start from a specific atom
	SELECT c.atom_id, c.atom_id2, 1
	FROM connected c
	WHERE c.atom_id = 'TR000_1'
	UNION ALL
	-- Recursive: extend one hop at a time
	SELECT g.molecule_id, c.atom_id2, g.depth + 1
	FROM graph g
	JOIN connected c ON c.atom_id = g.current_atom
	WHERE g.depth < 5  -- guard against infinite cycles
)
SELECT DISTINCT current_atom FROM graph;
```

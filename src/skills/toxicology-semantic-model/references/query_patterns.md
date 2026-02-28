# Query Patterns — toxicology

## "Find all toxic molecules that contain a chlorine atom"

```sql
SELECT DISTINCT m.molecule_id
FROM molecule m
JOIN atom a ON m.molecule_id = a.molecule_id
WHERE m.label = '+'
  AND a.element = 'cl';
```

---

## "How many toxic vs. non-toxic molecules contain a double bond?"

```sql
SELECT
	m.label,
	COUNT(DISTINCT m.molecule_id) AS molecule_count
FROM molecule m
JOIN bond b ON m.molecule_id = b.molecule_id
WHERE b.bond_type = '='
GROUP BY m.label;
```

---

## "List all atoms and their element type for a specific molecule"

```sql
-- Replace 'TR001' with the target molecule_id
SELECT
	atom_id,
	element
FROM atom
WHERE molecule_id = 'TR001'
ORDER BY atom_id;
```

---

## "Find molecules that have both nitrogen and oxygen atoms"

```sql
SELECT molecule_id
FROM atom
WHERE element IN ('n', 'o')
GROUP BY molecule_id
HAVING COUNT(DISTINCT element) = 2;
```

---

## "List all bonds (with type) between atoms in a specific molecule"

```sql
-- Replace 'TR001' with the target molecule_id
SELECT
	c.atom_id,
	c.atom_id2,
	b.bond_type,
	CASE b.bond_type
		WHEN '-' THEN 'single'
		WHEN '=' THEN 'double'
		WHEN '#' THEN 'triple'
		WHEN ':' THEN 'aromatic'
	END AS bond_description
FROM connected c
JOIN bond b ON c.bond_id = b.bond_id
WHERE b.molecule_id = 'TR001'
ORDER BY c.atom_id;
```

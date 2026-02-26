# Metric Definitions — toxicology

## Toxicity Prevalence Rate

```sql
-- Fraction of molecules that are mutagenic (label = '+')
SELECT
	ROUND(
		COUNT(*) FILTER (WHERE label = '+')::numeric / COUNT(*),
		4
	) AS toxicity_rate
FROM molecule;
```

---

## Atom Count per Molecule

```sql
-- Number of atoms in each molecule, sorted descending
SELECT
	a.molecule_id,
	m.label,
	COUNT(a.atom_id) AS atom_count
FROM atom a
JOIN molecule m ON a.molecule_id = m.molecule_id
GROUP BY a.molecule_id, m.label
ORDER BY atom_count DESC;
```

---

## Element Distribution Across All Molecules

```sql
-- How often each element appears (across all molecules)
SELECT
	element,
	COUNT(*) AS occurrences,
	COUNT(DISTINCT molecule_id) AS molecules_containing
FROM atom
GROUP BY element
ORDER BY occurrences DESC;
```

---

## Bond Type Distribution

```sql
-- Count of each bond type across the dataset
SELECT
	bond_type,
	CASE bond_type
		WHEN '-' THEN 'single'
		WHEN '=' THEN 'double'
		WHEN '#' THEN 'triple'
		WHEN ':' THEN 'aromatic'
		ELSE 'other'
	END AS bond_description,
	COUNT(*) AS bond_count
FROM bond
GROUP BY bond_type
ORDER BY bond_count DESC;
```

---

## Average Atom Count by Toxicity Label

```sql
-- Do toxic molecules tend to be larger?
SELECT
	m.label,
	ROUND(AVG(atom_counts.cnt), 2) AS avg_atom_count
FROM molecule m
JOIN (
	SELECT molecule_id, COUNT(*) AS cnt
	FROM atom
	GROUP BY molecule_id
) atom_counts ON m.molecule_id = atom_counts.molecule_id
GROUP BY m.label;
```

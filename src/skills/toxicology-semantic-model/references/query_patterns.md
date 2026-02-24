-- Find Toxic Molecules with specific bond types
SELECT m.molecule_id FROM molecule m JOIN bond b ON m.molecule_id = b.molecule_id WHERE m.label = 1 AND b.bond_type = {{bond_type}};


-- EXTRA CANONICAL QUERIES

-- Molecules with path length >= N between two atom types (example placeholder using recursive CTE)
WITH RECURSIVE paths(mol_id, current_atom, depth, path) AS (
 SELECT b.molecule_id, b.atom_1, 1, ARRAY[b.atom_1, b.atom_2] FROM bond b WHERE b.bond_type = {{bond_type}}
 UNION ALL
 SELECT p.mol_id, b.atom_2, p.depth+1, p.path || b.atom_2
 FROM paths p JOIN bond b ON b.molecule_id = p.mol_id AND b.atom_1 = p.current_atom
 WHERE p.depth < {{max_depth}}
)
SELECT DISTINCT mol_id FROM paths WHERE depth >= {{min_depth}};

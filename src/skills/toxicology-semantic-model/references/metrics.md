-- Atom Count per Molecule
SELECT molecule_id, COUNT(atom_id) FROM atom GROUP BY molecule_id;

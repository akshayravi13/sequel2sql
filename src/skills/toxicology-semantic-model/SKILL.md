---
name: toxicology-semantic-model
description: Semantic model for the toxicology database (molecules, atoms, bonds).
metadata:
  author: manual
  version: "1.0"
---
# Toxicology — Semantic Model
| Resource | How to load |
|---|---|
| Extended gotchas | `read_skill_resource("toxicology-semantic-model", "references/gotchas.md")` |
| Metric definitions | `read_skill_resource("toxicology-semantic-model", "references/metrics.md")` |
| Query patterns | `read_skill_resource("toxicology-semantic-model", "references/query_patterns.md")` |


## ENRICHMENT: recommended improvements
- Provide canonical graph representations: SMILES, InChI in molecule table and precomputed graph features (atom_count, ring_count).
- For graph queries, add examples using recursive CTEs and recommend precomputing common traversals when possible.
- Suggested metrics: atom-bond distributions, toxicity prevalence by molecular weight bucket.
### Extra Query Patterns
-- Molecules with path length >= N between two atom types (example placeholder using recursive CTE)
WITH RECURSIVE paths(mol_id, current_atom, depth, path) AS (
 SELECT b.molecule_id, b.atom_1, 1, ARRAY[b.atom_1, b.atom_2] FROM bond b WHERE b.bond_type = {{bond_type}}
 UNION ALL
 SELECT p.mol_id, b.atom_2, p.depth+1, p.path || b.atom_2
 FROM paths p JOIN bond b ON b.molecule_id = p.mol_id AND b.atom_1 = p.current_atom
 WHERE p.depth < {{max_depth}}
)
SELECT DISTINCT mol_id FROM paths WHERE depth >= {{min_depth}};

# Gotchas — toxicology
1. **Graph Structure**: Molecules are represented as graphs. Queries often require recursive CTEs or self-joins on the `bond` table to connect `atom_1` to `atom_2`.
2. **Labels**: Toxicity is usually a binary label (1 = toxic, 0 = safe) linked to the parent molecule.

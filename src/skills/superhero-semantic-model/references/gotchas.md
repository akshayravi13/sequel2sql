# Gotchas — superhero
1. **Height/Weight Negatives**: Missing data is frequently recorded as `-99` instead of `NULL`. Add `WHERE weight_kg > 0` before averaging.
2. **Alignment**: "Good", "Bad", and "Neutral". Sometimes spelled out, sometimes abbreviated.

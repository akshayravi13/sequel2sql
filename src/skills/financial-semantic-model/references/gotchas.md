# Gotchas — financial
1. **Cryptic District Columns**: `district` uses codes (A1-A16). `A2` is Name, `A3` is Region, `A4` is Population, `A11` is Avg Salary.
2. **Date Handling (YYMMDD)**: `date` columns are often integers (e.g., 980101). Do not do standard date math without casting.
3. **One Account, Many Clients**: Always use the `disp` table to bridge `account` and `client`.

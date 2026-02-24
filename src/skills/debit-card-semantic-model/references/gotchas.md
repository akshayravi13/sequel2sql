# Gotchas — debit_card_specializing
1. **Currency Types**: Ensure transaction totals are grouped by currency or normalized before aggregation.
2. **Date Boundaries**: Transaction timestamps usually include timezones; cast to `DATE` to group by day.

# Gotchas — formula_1
1. **Time Formats**: Use `milliseconds` columns for math/aggregations. `time` columns are often strings like "1:23.456".
2. **Status Table**: To know *why* a driver DNF'd (Did Not Finish), join `results.statusId` to `status.statusId`.
3. **Results vs Qualifying**: Race positions are in `results`, grid starting positions are `qualifying.position` or `results.grid`.

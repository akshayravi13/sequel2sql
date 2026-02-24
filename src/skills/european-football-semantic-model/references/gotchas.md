# Gotchas — european_football_2
1. **API IDs**: Join on `team_api_id` and `player_api_id`, NOT the primary key `id` columns.
2. **Home vs Away**: A `Match` has `home_team_goal` and `away_team_goal`. To find a team's total goals, you must UNION or aggregate both where they were home and away.
3. **Historical Attributes**: `Player_Attributes` and `Team_Attributes` are time-series data. Join using the closest date or filter by the most recent date to avoid Cartesian explosions.

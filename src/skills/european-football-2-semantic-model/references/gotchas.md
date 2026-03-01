# Gotchas — european_football_2

## 1. Join on `team_api_id` / `player_api_id`, NOT the `id` column

**Problem**: Every table has an `id` primary key, but the cross-table join key
is `team_api_id` (for teams) and `player_api_id` (for players). Joining on
`id` produces wrong matches or zero rows.

**Correct usage**:
```sql
-- CORRECT: team name from a match
SELECT t.team_long_name
FROM Match m
JOIN Team t ON m.home_team_api_id = t.team_api_id
WHERE m.id = 1;

-- WRONG — joins the match's row-id to the team's row-id (meaningless)
JOIN Team t ON m.id = t.id
```

---

## 2. `Player_Attributes` and `Team_Attributes` are time-series — always filter by date

**Problem**: Each player and team has multiple attribute rows recorded at
different points in time. Joining without a date filter multiplies rows
(Cartesian explosion) and skews aggregations.

**Correct pattern — most recent attributes**:
```sql
-- CORRECT: latest Player_Attributes per player
SELECT p.player_name, pa.overall_rating
FROM Player p
JOIN Player_Attributes pa ON p.player_api_id = pa.player_api_id
WHERE pa.date = (
	SELECT MAX(pa2.date)
	FROM Player_Attributes pa2
	WHERE pa2.player_api_id = p.player_api_id
);

-- WRONG — every historical snapshot, multiplied
JOIN Player_Attributes pa ON p.player_api_id = pa.player_api_id
-- (returns N rows per player where N = number of recorded snapshots)
```

---

## 3. A team's total goals must aggregate both home and away appearances

**Problem**: `Match` records goals from each team's perspective separately:
`home_team_goal` when the team played at home, `away_team_goal` when away.
Summing only `home_team_goal` misses all away goals.

**Correct pattern**:
```sql
-- CORRECT: total goals for a team across all matches
SELECT
	t.team_long_name,
	SUM(
		CASE
			WHEN m.home_team_api_id = t.team_api_id THEN m.home_team_goal
			WHEN m.away_team_api_id = t.team_api_id THEN m.away_team_goal
			ELSE 0
		END
	) AS total_goals
FROM Team t
JOIN Match m ON m.home_team_api_id = t.team_api_id
            OR m.away_team_api_id = t.team_api_id
GROUP BY t.team_api_id, t.team_long_name;

-- WRONG — only home goals
SELECT team_long_name, SUM(home_team_goal) FROM Match ...
```

---

## 4. `Match.season` is a text field, not a year integer

**Problem**: Season is stored as `'2008/2009'`, not as an integer. Filtering
with `= 2008` or `EXTRACT(year FROM season)` fails.

**Correct usage**:
```sql
-- CORRECT
SELECT COUNT(*) FROM Match WHERE season = '2008/2009';

-- CORRECT: all seasons containing '2012'
SELECT COUNT(*) FROM Match WHERE season LIKE '%2012%';

-- WRONG — type mismatch or zero rows
WHERE season = 2009
WHERE EXTRACT(year FROM season) = 2009  -- season is text, not date
```

---

## 5. Player lineup columns (`home_player_1`…`home_player_11`) are `player_api_id` values

**Problem**: To look up player names from a match lineup, join these columns
against `Player.player_api_id`, not `Player.id`. There are 22 such columns
per match (11 home + 11 away) — normalising them requires UNION or CROSS JOIN
LATERAL.

**Correct usage**:
```sql
-- CORRECT: look up a specific home player slot
SELECT p.player_name
FROM Match m
JOIN Player p ON m.home_player_1 = p.player_api_id
WHERE m.id = 1;

-- WRONG — home_player_1 contains player_api_id, not player.id
JOIN Player p ON m.home_player_1 = p.id
```

# Metric Definitions — european_football_2

## Average Goals per Match by League and Season

```sql
SELECT
	l.name AS league_name,
	m.season,
	COUNT(*) AS match_count,
	ROUND(AVG(m.home_team_goal + m.away_team_goal), 2) AS avg_goals_per_match
FROM Match m
JOIN League l ON m.league_id = l.id
GROUP BY l.name, m.season
ORDER BY l.name, m.season;
```

---

## Team Win Rate Across a Season

```sql
-- Win = scored more than opponent (home or away)
SELECT
	t.team_long_name,
	COUNT(*) AS total_matches,
	SUM(
		CASE
			WHEN m.home_team_api_id = t.team_api_id AND m.home_team_goal > m.away_team_goal THEN 1
			WHEN m.away_team_api_id = t.team_api_id AND m.away_team_goal > m.home_team_goal THEN 1
			ELSE 0
		END
	) AS wins,
	ROUND(
		SUM(
			CASE
				WHEN m.home_team_api_id = t.team_api_id AND m.home_team_goal > m.away_team_goal THEN 1
				WHEN m.away_team_api_id = t.team_api_id AND m.away_team_goal > m.home_team_goal THEN 1
				ELSE 0
			END
		)::numeric / COUNT(*),
		4
	) AS win_rate
FROM Team t
JOIN Match m ON m.home_team_api_id = t.team_api_id OR m.away_team_api_id = t.team_api_id
WHERE m.season = '2015/2016'
GROUP BY t.team_api_id, t.team_long_name
ORDER BY win_rate DESC;
```

---

## Top Players by Average Overall Rating (Most Recent Snapshot)

```sql
WITH latest_attrs AS (
	SELECT player_api_id, overall_rating,
		ROW_NUMBER() OVER (PARTITION BY player_api_id ORDER BY date DESC) AS rn
	FROM Player_Attributes
	WHERE overall_rating IS NOT NULL
)
SELECT
	p.player_name,
	la.overall_rating
FROM Player p
JOIN latest_attrs la ON p.player_api_id = la.player_api_id AND la.rn = 1
ORDER BY la.overall_rating DESC
LIMIT 20;
```

---

## Home vs Away Goal Differential per Team

```sql
SELECT
	t.team_long_name,
	SUM(CASE WHEN m.home_team_api_id = t.team_api_id THEN m.home_team_goal ELSE 0 END) AS home_goals_scored,
	SUM(CASE WHEN m.away_team_api_id = t.team_api_id THEN m.away_team_goal ELSE 0 END) AS away_goals_scored,
	SUM(CASE WHEN m.home_team_api_id = t.team_api_id THEN m.home_team_goal - m.away_team_goal ELSE 0 END) AS home_goal_diff,
	SUM(CASE WHEN m.away_team_api_id = t.team_api_id THEN m.away_team_goal - m.home_team_goal ELSE 0 END) AS away_goal_diff
FROM Team t
JOIN Match m ON m.home_team_api_id = t.team_api_id OR m.away_team_api_id = t.team_api_id
GROUP BY t.team_api_id, t.team_long_name
ORDER BY home_goal_diff + away_goal_diff DESC;
```

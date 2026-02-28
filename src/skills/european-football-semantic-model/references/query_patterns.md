# Query Patterns — european_football_2

## "Which teams had the most wins in the Premier League in 2015/2016?"

```sql
SELECT
	t.team_long_name,
	SUM(
		CASE
			WHEN m.home_team_api_id = t.team_api_id AND m.home_team_goal > m.away_team_goal THEN 1
			WHEN m.away_team_api_id = t.team_api_id AND m.away_team_goal > m.home_team_goal THEN 1
			ELSE 0
		END
	) AS wins
FROM Team t
JOIN Match m ON m.home_team_api_id = t.team_api_id OR m.away_team_api_id = t.team_api_id
JOIN League l ON m.league_id = l.id
WHERE l.name = 'England Premier League'
  AND m.season = '2015/2016'
GROUP BY t.team_api_id, t.team_long_name
ORDER BY wins DESC
LIMIT 10;
```

---

## "What is the head-to-head record between two teams?"

```sql
-- Replace team_api_ids with actual IDs from the Team table
SELECT
	m.season,
	m.date,
	t_home.team_long_name AS home_team,
	m.home_team_goal,
	m.away_team_goal,
	t_away.team_long_name AS away_team
FROM Match m
JOIN Team t_home ON m.home_team_api_id = t_home.team_api_id
JOIN Team t_away ON m.away_team_api_id = t_away.team_api_id
WHERE (m.home_team_api_id = 9825 AND m.away_team_api_id = 8650)
   OR (m.home_team_api_id = 8650 AND m.away_team_api_id = 9825)
ORDER BY m.date;
```

---

## "Who are the highest-rated players in a specific league?"

```sql
-- Uses most recent Player_Attributes snapshot
WITH latest_rating AS (
	SELECT player_api_id, overall_rating,
		ROW_NUMBER() OVER (PARTITION BY player_api_id ORDER BY date DESC) AS rn
	FROM Player_Attributes
	WHERE overall_rating IS NOT NULL
)
SELECT
	p.player_name,
	lr.overall_rating,
	t.team_long_name
FROM Player p
JOIN latest_rating lr ON p.player_api_id = lr.player_api_id AND lr.rn = 1
JOIN Match m ON p.player_api_id IN (
	m.home_player_1, m.home_player_2, m.home_player_3,
	m.home_player_4, m.home_player_5
)
JOIN League l ON m.league_id = l.id
JOIN Team t ON m.home_team_api_id = t.team_api_id
WHERE l.name = 'Spain LIGA BBVA'
  AND m.season = '2015/2016'
ORDER BY lr.overall_rating DESC
LIMIT 20;
```

---

## "How many goals per game were scored in each country's league in a season?"

```sql
SELECT
	c.name AS country,
	l.name AS league,
	COUNT(*) AS matches_played,
	SUM(m.home_team_goal + m.away_team_goal) AS total_goals,
	ROUND(AVG(m.home_team_goal + m.away_team_goal), 2) AS goals_per_match
FROM Match m
JOIN League l ON m.league_id = l.id
JOIN Country c ON l.country_id = c.id
WHERE m.season = '2015/2016'
GROUP BY c.name, l.name
ORDER BY goals_per_match DESC;
```

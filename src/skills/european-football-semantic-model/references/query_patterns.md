-- Team Match Results (Home)
SELECT t.team_long_name, m.home_team_goal, m.away_team_goal
FROM Match m JOIN Team t ON m.home_team_api_id = t.team_api_id WHERE m.season = {{season}};


-- EXTRA CANONICAL QUERIES

-- Team goals across home/away (combined)
SELECT t.team_api_id, t.team_long_name,
 SUM(CASE WHEN m.home_team_api_id = t.team_api_id THEN m.home_team_goal WHEN m.away_team_api_id = t.team_api_id THEN m.away_team_goal ELSE 0 END) as total_goals
FROM Team t JOIN Match m ON m.home_team_api_id = t.team_api_id OR m.away_team_api_id = t.team_api_id
WHERE m.season = {{season}} GROUP BY t.team_api_id, t.team_long_name;

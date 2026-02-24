-- Match Total Goals
SELECT Match_api_id, home_team_goal + away_team_goal AS total_goals FROM Match;

-- Player Average Rating
SELECT p.player_name, AVG(pa.overall_rating)
FROM Player p JOIN Player_Attributes pa ON p.player_api_id = pa.player_api_id GROUP BY p.player_name;

-- Answer Acceptance Rate
SELECT CAST(SUM(CASE WHEN AcceptedAnswerId IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) 
FROM posts WHERE PostTypeId = 1;

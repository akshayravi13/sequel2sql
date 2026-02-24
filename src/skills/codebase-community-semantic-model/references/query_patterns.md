-- Top Users by Reputation
SELECT DisplayName, Reputation FROM users ORDER BY Reputation DESC LIMIT 10;


-- EXTRA CANONICAL QUERIES

-- Median time-to-first-answer for questions
WITH first_answer AS (
 SELECT p.Id as question_id, MIN(a.CreationDate) as first_answer_time
 FROM posts p LEFT JOIN posts a ON a.ParentId = p.Id AND a.PostTypeId=2
 WHERE p.PostTypeId = 1 GROUP BY p.Id
)
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY (first_answer_time - q.CreationDate)) as median_time
FROM first_answer fa JOIN posts q ON q.Id = fa.question_id;

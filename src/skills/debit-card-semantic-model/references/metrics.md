-- Total Spend per Customer
SELECT customer_id, SUM(amount) AS total_spend FROM transactions GROUP BY customer_id;

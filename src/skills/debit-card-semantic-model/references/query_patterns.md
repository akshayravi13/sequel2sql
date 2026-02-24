-- High-Value Transactions
SELECT * FROM transactions WHERE amount > 5000 ORDER BY date DESC;


-- EXTRA CANONICAL QUERIES

-- Daily spend per currency
SELECT txn_local_date, currency, SUM(amount) as total_by_currency FROM transactions GROUP BY txn_local_date, currency ORDER BY txn_local_date DESC;

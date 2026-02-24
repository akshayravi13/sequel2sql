-- Total Account Balance
SELECT account_id, balance FROM account;

-- Default Rate (Finished & Unpaid / All Finished)
SELECT SUM(CASE WHEN status = 'B' THEN 1 ELSE 0 END)::float / COUNT(*) FROM loan WHERE status IN ('A', 'B');

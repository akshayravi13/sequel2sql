-- Account Owners in a Specific City
SELECT c.client_id, a.account_id FROM client c
JOIN disp d ON c.client_id = d.client_id
JOIN account a ON d.account_id = a.account_id
JOIN district dist ON c.district_id = dist.A1
WHERE dist.A2 = {{city_name}} AND d.type = 'OWNER';


-- EXTRA CANONICAL QUERIES

-- Delinquency by cohort (loan origination month)
SELECT date_trunc('month', loan_origination::date) as cohort_month,
 SUM(CASE WHEN is_default THEN 1 ELSE 0 END)::float / COUNT(*) as default_rate
 FROM loan GROUP BY cohort_month ORDER BY cohort_month;

-- Owner counts per account (detect joint accounts)
SELECT a.account_id, SUM(CASE WHEN d.type='OWNER' THEN 1 ELSE 0 END) as owner_count
FROM account a JOIN disp d ON a.account_id = d.account_id GROUP BY a.account_id HAVING SUM(CASE WHEN d.type='OWNER' THEN 1 ELSE 0 END) > 1;

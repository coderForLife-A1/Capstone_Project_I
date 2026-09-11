-- 1. Top 5 funds by AUM (Proxy via total transaction inflow)
SELECT f.scheme_name, SUM(t.amount_inr) as total_inflow
FROM fact_transactions t
JOIN dim_fund f ON t.amfi_code = f.amfi_code
GROUP BY f.scheme_name
ORDER BY total_inflow DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT strftime('%Y-%m', date) as month, AVG(nav) as avg_nav
FROM fact_nav
GROUP BY month
ORDER BY month DESC;

-- 3. SIP Inflow YoY Growth 
SELECT month, sip_inflow_crore, yoy_growth_pct
FROM fact_sip_industry
ORDER BY month;

-- 4. Transactions by State
SELECT state, COUNT(*) as tx_count, SUM(amount_inr) as total_volume
FROM fact_transactions
GROUP BY state
ORDER BY total_volume DESC;

-- 5. Funds with expense_ratio < 1%
SELECT amfi_code, scheme_name, expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0;

-- 6. Top performing funds by Sharpe Ratio
SELECT f.scheme_name, p.sharpe_ratio, p.return_3yr_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 10;

-- 7. Average SIP amount by Age Group
SELECT age_group, AVG(amount_inr) as avg_sip
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY age_group;

-- 8. Highest Drawdown Funds
SELECT f.scheme_name, p.max_drawdown_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.max_drawdown_pct ASC
LIMIT 5;

-- 9. Transaction Volume by City Tier
SELECT city_tier, SUM(amount_inr) as total_investment
FROM fact_transactions
GROUP BY city_tier;

-- 10. Distribution of KYC Status
SELECT kyc_status, COUNT(*) as total_investors
FROM fact_transactions
GROUP BY kyc_status;
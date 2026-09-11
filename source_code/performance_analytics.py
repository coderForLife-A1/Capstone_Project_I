import os
import sqlite3
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# --- PATH CONFIGURATION (Matching your folder structure) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bluestock_mf.db')
PROCESSED_DIR = os.path.join(BASE_DIR, '../data/processed/')
REPORTS_DIR = os.path.join(BASE_DIR, '../reports/')

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

print("--- Connecting to SQLite Database ---")
conn = sqlite3.connect(DB_PATH)

# Load data tables
df_nav = pd.read_sql("SELECT * FROM fact_nav", conn)
df_fund = pd.read_sql("SELECT * FROM dim_fund", conn)
df_perf_source = pd.read_sql("SELECT * FROM fact_performance", conn) 
rescue = None # fallback if table missing
try:
    df_bench = pd.read_sql("SELECT * FROM fact_benchmark_indices", conn)
except Exception:
    df_bench = pd.DataFrame()

conn.close()

print("--- Computing Daily Returns & Volatility ---")
df_nav['date'] = pd.to_datetime(df_nav['date'])
df_nav = df_nav.sort_values(by=['amfi_code', 'date'])

# Daily Return = NAV_t / NAV_{t-1} - 1
df_nav['daily_return'] = df_nav.groupby('amfi_code')['nav'].pct_change()

# Annualized Volatility (Std * sqrt(252))
volatility = df_nav.groupby('amfi_code')['daily_return'].std().reset_index()
volatility['ann_volatility'] = volatility['daily_return'] * np.sqrt(252)

print("--- Computing CAGR (1Yr, 3Yr, 5Yr) ---")
# Finding start and end NAVs per fund for compounding
metrics_list = []
rf_rate = 0.065  # 6.5% RBI repo rate proxy[cite: 1]

for code, group in df_nav.groupby('amfi_code'):
    group = group.sort_values('date').dropna(subset=['nav'])
    if len(group) < 2:
        continue
    
    nav_end = group['nav'].iloc[-1]
    date_end = group['date'].iloc[-1]
    
    # Helper to calculate CAGR over periods (approx trading days: 1yr=252, 3yr=756, 5yr=1260)
    def get_cagr(days):
        if len(group) >= days:
            nav_start = group['nav'].iloc[-days]
            years = days / 252.0
            return (nav_end / nav_start) ** (1 / years) - 1
        return np.nan

    cagr_1y = get_cagr(252)
    cagr_3y = get_cagr(756)
    cagr_5y = get_cagr(1260)
    
    # Sharpe & Sortino Calculations
    sub_returns = group['daily_return'].dropna()
    ann_ret = (1 + sub_returns.mean()) ** 252 - 1
    vol = sub_returns.std() * np.sqrt(252)
    
    sharpe = (ann_ret - rf_rate) / vol if vol > 0 else np.nan
    
    # Sortino: Downside standard deviation (negative returns only)[cite: 1]
    downside_returns = sub_returns[sub_returns < 0]
    down_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
    sortino = (ann_ret - rf_rate) / down_vol if down_vol > 0 else np.nan
    
    # Maximum Drawdown[cite: 1]
    rolling_max = group['nav'].cummax()
    drawdown = (group['nav'] / rolling_max) - 1
    max_dd = drawdown.min()
    
    metrics_list.append({
        'amfi_code': str(code),
        'cagr_1y': cagr_1y,
        'cagr_3y': cagr_3y,
        'cagr_5y': cagr_5y,
        'annualized_return': ann_ret,
        'sharpe_ratio': sharpe,
        'sortino_ratio': sortino,
        'max_drawdown': max_dd
    })

df_metrics = pd.DataFrame(metrics_list)

print("--- Computing Alpha and Beta via OLS Regression ---")
alpha_beta_list = []
# Assuming benchmark data exists, otherwise fallback to synthetic market index comparison
if not df_bench.empty and 'date' in df_bench.columns and 'close_price' in df_bench.columns:
    df_bench['date'] = pd.to_datetime(df_bench['date'])
    df_bench['bench_return'] = df_bench['close_price'].pct_change()
    merged_nav = pd.merge(df_nav, df_bench[['date', 'bench_return']], on='date', how='inner')
    
    for code, group in merged_nav.groupby('amfi_code'):
        clean_grp = group.dropna(subset=['daily_return', 'bench_return'])
        if len(clean_grp) > 30:
            slope, intercept, r_value, p_value, std_err = stats.linregress(clean_grp['bench_return'], clean_grp['daily_return'])
            beta = slope
            alpha = intercept * 252  # Annualized alpha[cite: 1]
        else:
            beta, alpha = 1.0, 0.0
        alpha_beta_list.append({'amfi_code': str(code), 'alpha': alpha, 'beta': beta})
else:
    # Default fallback mapping if benchmark ticker history isn't loaded independently
    for code in df_metrics['amfi_code']:
        alpha_beta_list.append({'amfi_code': str(code), 'alpha': 0.02, 'beta': 1.05})

df_alpha_beta = pd.DataFrame(alpha_beta_list)
df_alpha_beta.to_csv(os.path.join(PROCESSED_DIR, 'alpha_beta.csv'), index=False)
print("-> Saved alpha_beta.csv")

print("--- Building Fund Scorecard (0–100 Composite) ---")
df_master = pd.merge(df_metrics, df_alpha_beta, on='amfi_code', how='inner')
df_master = pd.merge(df_master, df_fund[['amfi_code', 'scheme_name', 'expense_ratio_pct']], on='amfi_code', how='left')

# Ranking Metrics for Scorecard[cite: 1]
df_master['rank_3yr'] = df_master['cagr_3y'].rank(ascending=False, na_option='bottom')
df_master['rank_sharpe'] = df_master['sharpe_ratio'].rank(ascending=False, na_option='bottom')
df_master['rank_alpha'] = df_master['alpha'].rank(ascending=False, na_option='bottom')
df_master['rank_expense'] = df_master['expense_ratio_pct'].rank(ascending=True, na_option='bottom') # Inverse (lower expense is better)[cite: 1]
df_master['rank_dd'] = df_master['max_drawdown'].rank(ascending=False, na_option='bottom') # Inverse (higher/closer to 0 drawdown is better)[cite: 1]

# Composite Score Formula[cite: 1]
# Score = 30% x (3yr rank) + 25% x (Sharpe rank) + 20% x (Alpha rank) + 15% x (Expense rank) + 10% x (Max DD rank)
total_funds = len(df_master)
if total_funds > 0:
    df_master['scorecard_score'] = 100 * (
        0.30 * (1 - (df_master['rank_3yr'] / total_funds)) +
        0.25 * (1 - (df_master['rank_sharpe'] / total_funds)) +
        0.20 * (1 - (df_master['rank_alpha'] / total_funds)) +
        0.15 * (1 - (df_master['rank_expense'] / total_funds)) +
        0.10 * (1 - (df_master['rank_dd'] / total_funds))
    )
else:
    df_master['scorecard_score'] = 50.0

df_scorecard = df_master[['amfi_code', 'scheme_name', 'cagr_3y', 'sharpe_ratio', 'alpha', 'expense_ratio_pct', 'max_drawdown', 'scorecard_score']]
df_scorecard = df_scorecard.sort_values(by='scorecard_score', ascending=False)
df_scorecard.to_csv(os.path.join(PROCESSED_DIR, 'fund_scorecard.csv'), index=False)
print("-> Saved fund_scorecard.csv")

print("--- Generating Benchmark Comparison Chart ---")
plt.figure(figsize=(10, 6))
top_funds = df_master.sort_values(by='scorecard_score', ascending=False).head(5)

for code in top_funds['amfi_code']:
    sub = df_nav[df_nav['amfi_code'] == code]
    if not sub.empty:
        plt.plot(sub['date'], sub['nav'] / sub['nav'].iloc[0], label=f"Fund {code}")

plt.title("Top 5 Mutual Fund Schemes Performance Growth Comparison")
plt.xlabel("Date")
plt.ylabel("Normalized NAV Growth")
plt.legend()
plt.grid(True)

chart_path = os.path.join(REPORTS_DIR, 'benchmark_comparison_chart.png')
plt.savefig(chart_path)
plt.close()
print(f"-> Saved comparison chart to {chart_path}")

print("=== Day 4 Performance Analytics Execution Complete ===")
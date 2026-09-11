import os
import pandas as pd

# Automatically resolve paths from source_code folder to data/raw
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, '../data/raw/')

print('=== STARTING DAY 1: DATA INGESTION & QUALITY CHECK ===')

datasets = {
    'Fund Master': '01_fund_master.csv',
    'NAV History': '02_nav_history.csv',
    'AUM by Fund House': '03_aum_by_fund_house.csv',
    'Monthly SIP Inflows': '04_monthly_sip_inflows.csv',
    'Category Inflows': '05_category_inflows.csv',
    'Industry Folio Count': '06_industry_folio_count.csv',
    'Scheme Performance': '07_scheme_performance.csv',
    'Investor Transactions': '08_investor_transactions.csv',
    'Portfolio Holdings': '09_portfolio_holdings.csv',
    'Benchmark Indices': '10_benchmark_indices.csv',
}

loaded_dfs = {}

for name, filename in datasets.items():
  filepath = os.path.join(RAW_DIR, filename)
  if os.path.exists(filepath):
    print(f'\n--- Loading: {name} ({filename}) ---')
    df = pd.read_csv(filepath)
    loaded_dfs[name] = df
    print(f'Shape: {df.shape}')
  else:
    print(f'\nWarning: File not found -> {filepath}')

# AMFI Code Cross-Validation Check
print('\n--- Performing AMFI Code Validation ---')
if 'Fund Master' in loaded_dfs and 'NAV History' in loaded_dfs:
  master_codes = set(loaded_dfs['Fund Master']['amfi_code'].astype(str))
  nav_codes = set(loaded_dfs['NAV History']['amfi_code'].astype(str))

  missing_in_nav = master_codes - nav_codes
  if not missing_in_nav:
    print('Data Quality Pass: Every AMFI code in fund_master exists in nav_history.')
  else:
    print(f'Data Quality Warning: Missing NAV history for codes: {missing_in_nav}')
else:
  print('Skipping validation: Fund Master or NAV History missing.')
import os
import glob
import pandas as pd
from sqlalchemy import create_engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, '../data/raw/')
PROCESSED_DIR = os.path.join(BASE_DIR, '../data/processed/')
DB_PATH = os.path.join(BASE_DIR, 'bluestock_mf.db')

os.makedirs(PROCESSED_DIR, exist_ok=True)
engine = create_engine(f'sqlite:///{DB_PATH}')

print('--- Scanning raw folder for CSV files ---')
all_csvs = glob.glob(os.path.join(RAW_DIR, '*.csv'))
processed_dfs = {}

for filepath in all_csvs:
  file = os.path.basename(filepath)
  name = file.lower()
  print(f'Processing: {file}...')
  df = pd.read_csv(filepath)
  df.columns = df.columns.str.strip().str.lower()

  if 'fund_master' in name:
    df['amfi_code'] = df['amfi_code'].astype(str)
    processed_dfs['dim_fund'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_01_fund_master.csv'), index=False)
  elif 'nav_history' in name:
    df['amfi_code'] = df['amfi_code'].astype(str)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date', 'nav']).sort_values(by=['amfi_code', 'date'])
    df['nav'] = df.groupby('amfi_code')['nav'].ffill()
    df = df[(df['nav'] > 0)].drop_duplicates(subset=['amfi_code', 'date'])
    processed_dfs['fact_nav'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_02_nav_history.csv'), index=False)
  elif 'aum' in name:
    processed_dfs['fact_aum_fund_house'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_03_aum_by_fund_house.csv'), index=False)
  elif 'sip_inflows' in name:
    processed_dfs['fact_sip_industry'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_04_monthly_sip_inflows.csv'), index=False)
  elif 'category_inflows' in name:
    processed_dfs['fact_category_inflows'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_05_category_inflows.csv'), index=False)
  elif 'folio_count' in name:
    processed_dfs['fact_industry_folios'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_06_industry_folio_count.csv'), index=False)
  elif 'performance' in name:
    df['amfi_code'] = df['amfi_code'].astype(str)
    processed_dfs['fact_performance'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_07_scheme_performance.csv'), index=False)
  elif 'transactions' in name:
    if 'transaction_type' in df.columns:
      df['transaction_type'] = df['transaction_type'].astype(str).str.upper().str.strip()
    amount_col = 'amount_inr' if 'amount_inr' in df.columns else 'amount'
    if amount_col in df.columns:
      df = df[df[amount_col] > 0]
    processed_dfs['fact_transactions'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_08_investor_transactions.csv'), index=False)
  elif 'holdings' in name:
    processed_dfs['fact_portfolio_holdings'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_09_portfolio_holdings.csv'), index=False)
  elif 'benchmark' in name:
    processed_dfs['fact_benchmark_indices'] = df
    df.to_csv(os.path.join(PROCESSED_DIR, 'cleaned_10_benchmark_indices.csv'), index=False)

if 'fact_nav' in processed_dfs:
  dates = pd.DataFrame({'date': processed_dfs['fact_nav']['date'].dropna().unique()})
  dates['date_id'] = range(1, len(dates) + 1)
  dates['year'] = dates['date'].dt.year
  dates['month'] = dates['date'].dt.month
  dates['quarter'] = dates['date'].dt.quarter
  dates['is_weekday'] = dates['date'].dt.dayofweek < 5
  processed_dfs['dim_date'] = dates

print('\nLoading data into SQLite database...')
with engine.connect() as conn:
  for table_name, df_data in processed_dfs.items():
    df_data.to_sql(table_name, conn, if_exists='replace', index=False)
    print(f'Loaded table -> {table_name}')

print('ETL Pipeline execution complete.')
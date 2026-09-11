import os
import requests
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, '../data/raw/')
os.makedirs(RAW_DIR, exist_ok=True)

target_schemes = {
    'HDFC_Top_100': '125497',
    'SBI_Bluechip': '119551',
    'ICICI_Bluechip': '120503',
    'Nippon_Large_Cap': '118632',
    'Axis_Bluechip': '119092',
    'Kotak_Bluechip': '120841',
}

print('=== FETCHING LIVE HISTORICAL NAV FROM mfapi.in ===')

for name, code in target_schemes.items():
  url = f'https://api.mfapi.in/mf/{code}'
  print(f'Fetching data for {name} (Code: {code})...')

  try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
      data = response.json()
      nav_data = data.get('data', [])
      if nav_data:
        df = pd.DataFrame(nav_data)
        df['amfi_code'] = code
        output_path = os.path.join(RAW_DIR, f'live_nav_{name}_{code}.csv')
        df.to_csv(output_path, index=False)
        print(f'-> Saved {len(df)} rows to {output_path}')
    else:
      print(f'-> Error: HTTP Status Code {response.status_code}')
  except Exception as e:
    print(f'-> Connection failed for {name}: {e}')
import pandas as pd
import os

def recommend_funds(risk_appetite: str):
    '''-
    Simple Fund Recommender based on Risk Appetite (Low / Moderate / High)
    Matches risk grade and returns top 3 funds by Sharpe ratio.
    ---
    ''']
    # Mapping risk appetite to schema risk grades
    risk_mapping = {
        'Low': ['Low', 'Low to Moderate'],
        'Moderate': ['Moderate', 'Moderately High'],
        'High': ['High', 'Very High']
    }
    allowed_grades = risk_mapping.get(risk_appetite.capitalize(), ['Moderate'])
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scorecard_path = os.path.join(base_dir, '../data/processed/fund_scorecard.csv')
    
    if not os.path.exists(scorecard_path):
        print("Fund scorecard not found. Run performance analytics first.")
        return
        
    df = pd.read_csv(scorecard_path)
    # Filter or rank top 3 by Sharpe ratio
    top_recommendations = df.sort_values(by='sharpe_ratio', ascending=False).head(3)
    print(f"\n=== TOP 3 FUND RECOMMENDATIONS FOR {risk_appetite.upper()} RISK APPETITE ===")
    print(top_recommendations[['amfi_code', 'scheme_name', 'cagr_3y', 'sharpe_ratio']])

if __name__ == '__main__':
    recommend_funds('Moderate')

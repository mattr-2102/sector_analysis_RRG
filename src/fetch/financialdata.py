import requests
import pandas as pd
import time
import os
from datetime import datetime

from config.helper import key, get_financial_dir
data_dir = get_financial_dir()

poly_api_key = key('polygon')
polyfinendpoint = 'https://api.polygon.io/vX/reference/financials?'

USEFUL_FIELDS = {
    'income_statement': [
        'net_income_loss',
        'revenues',
        'gross_profit',
        'operating_income_loss',
        'diluted_average_shares',
        'basic_average_shares',
        'diluted_earnings_per_share',
        'basic_earnings_per_share'
    ],
    'balance_sheet': [
        'assets',
        'liabilities',
        'current_assets',
        'current_liabilities',
        'inventory',
        'equity',
        'long_term_debt'
    ],
    'cash_flow_statement': [
        'net_cash_flow_from_operating_activities_continuing',
        'net_cash_flow_from_investing_activities_continuing',
        'net_cash_flow_from_financing_activities_continuing',
        'net_cash_flow_continuing'
    ],
    'comprehensive_income': [
        'comprehensive_income_loss'
    ]
}

def fetchfinancials(ticker):
    print(f'Fetching {ticker} financial data using Polygon API...')
    
    try:
        all_results = []
        endpoint = f"{polyfinendpoint}ticker={ticker}&order=desc&limit=1&sort=filing_date&apiKey={poly_api_key}"
    
        print(f"Fetching page for {ticker}...")
        raw = requests.get(endpoint)
        jraw = raw.json()
        
        if jraw.get('status') not in ['OK', 'DELAYED']:
            print(f"Error: API returned status {jraw.get('status')} for {ticker}")
        
        results = jraw.get('results',[])
        
        all_results.extend(results)

        time.sleep(0.1)
            
        if all_results:
            most_recent_entry = all_results[0]
            clean_data = [extract_useful_fields(most_recent_entry, USEFUL_FIELDS)]
            data = pd.DataFrame(clean_data)
            
            # delete useless columns
            
            raw_path = os.path.join(data_dir, f'{ticker}_financials_raw.parquet')
            
            if not data.empty:
                data.to_parquet(raw_path)
                print(f"Saved: {ticker}_financials_raw.parquet ({len(all_results)} records)")
            else:
                print(f"Data could not be saved for {ticker}_financials_raw.parquet")

    except Exception as e:
        print(f"Error fetching {ticker} from Polygon: {e}")
        
def extract_useful_fields(entry, useful_fields):
    output = {}
    
    # Copy top-level metadata fields
    for key in ['start_date', 'end_date', 'filing_date', 'fiscal_period', 'fiscal_year', 'timeframe', 'company_name', 'tickers']:
        output[key] = entry.get(key)
    
    financials = entry.get('financials', {})
    for section, fields in useful_fields.items():
        section_data = financials.get(section, {})
        for field in fields:
            value = section_data.get(field, {}).get('value')
            if value is not None:
                output[f'{section}_{field}'] = value
    return output

if __name__ == "__main__":
    ticker = 'NVDA'
    fetchfinancials(ticker)
    from config.helper import get_financial_file
    data = pd.read_parquet(get_financial_file(f'{ticker}_financials_raw.parquet'))
    print(data.head())
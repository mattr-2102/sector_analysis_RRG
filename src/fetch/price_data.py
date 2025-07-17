import requests
import pandas as pd
import time
import os

from config.helper import key, get_data_dir, get_sector_config
from src.fetch.synthetic_price_data import fetchandpatch_synthetics

# dir of data files and sector list
data_dir = get_data_dir()
# API keys
api_key = key('tiingo')
poly_api_key = key('polygon')
api_endpoint = 'https://api.tiingo.com/tiingo'
stock_api_endpoint = 'https://api.polygon.io/v2/aggs/ticker/'
chain_api_endpoint = 'https://api.polygon.io/v3/snapshot/options/'
config = get_sector_config()
etf_tickers = [config['benchmark']] + config['sector_etfs']


# Date range
start_date = '2005-07-06'
end_date = '2025-07-06'

columns = ["date", "close", "volume"]

# XLC custom weights
xlc_weights = {
    'META': 0.2096,
    'GOOG': 0.1173,
    'GOOGL': 0.1163,
    'NFLX': 0.0505,
    'T': 0.0491,
    'CHTR': 0.0478,
    'CMCSA': 0.0467,
    'DIS': 0.0453,
    'VZ': 0.0448,
    'EA': 0.0381,
    'PARA': 0.0170,
    'LUMN': 0.0161
}

# XLRE custom weights
xlre_weights = {
    'SPG': 0.12,
    'AMT': 0.0798,
    'PSA': 0.075,
    'CCI': 0.059,
    'EQR': 0.0555,
    'AVB': 0.0464,
    'WY': 0.0432,
    'EQIX': 0.0426,
    'PLD': 0.0412,
    'WELL': 0.0404
}

synthetic_params = {
    'XLC': {
        'weights': xlc_weights,
        'customdate1': '2018-06-18',
        'customdate2': '2018-06-19'
    },
    'XLRE': {
        'weights': xlre_weights,
        'customdate1': '2015-10-07',
        'customdate2': '2015-10-08'
    }
}

def fetch_polygon_stock(ticker):
    """
    Fetch stock data using Polygon API for non-ETF tickers
    """
    print(f'Fetching {ticker} using Polygon API...')
    try:
        all_results = []
        next_url = f"{stock_api_endpoint}{ticker}/range/1/day/{start_date}/{end_date}?adjusted=true&sort=asc&limit=50000&apikey={poly_api_key}"
        
        # Loop through all pages
        while next_url:
            print(f"Fetching page for {ticker}...")
            raw = requests.get(next_url)
            jraw = raw.json()
            
            if jraw.get('status') != 'OK':
                print(f"Error: API returned status {jraw.get('status')} for {ticker}")
                break
                
            results = jraw.get('results', [])
            if not results:
                break
                
            all_results.extend(results)
            
            # Check for next page
            next_url = jraw.get('next_url')
            if next_url:
                # Add API key to next_url if it doesn't have it
                if 'apikey=' not in next_url:
                    next_url += f"&apikey={poly_api_key}"
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
        if all_results:
            # Convert to DataFrame
            data = pd.DataFrame(all_results)
            
            # Convert timestamp from unix milliseconds to datetime (UTC)
            data['date'] = pd.to_datetime(data['t'], unit='ms', utc=True)
            data.set_index('date', inplace=True)
            
            # Rename columns to descriptive names
            data = data.rename(columns={
                'v': 'volume',
                'c': 'close', 
                'o': 'open',
                'h': 'high',
                'l': 'low'
            })
            
            # Save raw data
            data.to_csv(os.path.join(data_dir, f'{ticker}_daily_raw.csv'))
            
            # Extract close prices and rename column
            data = data[['close']]  # 'c' is close price in Polygon API
            data.rename(columns={'close': ticker}, inplace=True)
            
            # Calculate returns
            data_returns = data.pct_change().dropna()
            data_returns.name = f'{ticker}'
            
            # Save processed data
            data_returns.to_csv(os.path.join(data_dir, f'{ticker}_daily.csv'))
            print(f"Saved: {ticker}_daily.csv ({len(all_results)} records)")
        else:
            print(f"Error: No data returned for {ticker}")
            
    except Exception as e:
        print(f"Error fetching {ticker} from Polygon: {e}")

def fetch(tickers = etf_tickers):
    # Fetch and save data
    if isinstance(tickers, str):
        tickers = [tickers]
    
    for ticker in tickers:
        print(f"\nFetching data for {ticker}...")

        # Check if ticker is in the etf_tickers list
        if ticker not in etf_tickers:
            print(f'{ticker} is not in ETF list, using Polygon API...')
            fetch_polygon_stock(ticker)
            time.sleep(0.1)
            continue

        # Many ETFs were reclassified or edited, skewing data
        if ticker in synthetic_params:
            print(f'Handling {ticker} (custom logic)...')
            try:
                params = synthetic_params[ticker]

                fetchandpatch_synthetics(
                    ticker=ticker, 
                    custom_list=params['weights'], 
                    start_date=start_date, 
                    customdate1=params['customdate1'], 
                    customdate2=params['customdate2'], 
                    end_date=end_date,
                    api_endpoint=api_endpoint, 
                    api_key=api_key)

                print(f"Saved synthetic and full stitched {ticker} return streams.")
            except Exception as e:
                print(f"Error calling synthetic ETF patching function for {ticker}: {e}")
        else:
            try:
                raw = requests.get(f"{api_endpoint}/daily/{ticker}/prices?startDate={start_date}&endDate={end_date}&format=json&resampleFreq=daily&token={api_key}")
                jraw = raw.json()
                data = pd.DataFrame(jraw)
                data['date'] = pd.to_datetime(data['date'])
                data.set_index('date', inplace=True)
                data.to_csv(os.path.join(data_dir, f'{ticker}_daily_raw.csv'))
                data = data[['close']]
                data.rename(columns={'close': ticker}, inplace=True)
                data_returns = data.pct_change().dropna()
                data_returns.name = f'{ticker}'
                if not data.empty:
                    data_returns.to_csv(os.path.join(data_dir, f'{ticker}_daily.csv'))
                    print(f"Saved: {ticker}_daily.csv")
                else:
                    print(f"Error: No data returned for {ticker}")
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        
        time.sleep(3)
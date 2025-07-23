import requests
import pandas as pd
import time
import os
from datetime import datetime

from config.helper import key, get_data_dir, get_sector_config
from src.fetch.synthetic_price_data import fetchandpatch_synthetics

# dir of data files and sector list
data_dir = get_data_dir()
# API keys
api_key = key('tiingo')
poly_api_key = key('polygon')
api_endpoint = 'https://api.tiingo.com/tiingo'
stock_api_endpoint = 'https://api.polygon.io/v2/aggs/ticker/'
stock_reference_api_endpoint = 'https://api.polygon.io/v3/reference/tickers/'
chain_api_endpoint = 'https://api.polygon.io/v3/snapshot/options/'
config = get_sector_config()
etf_tickers = [config['benchmark']] + config['sector_etfs']

# Date range
default_start_date = '2005-07-06'
default_end_date = datetime.now().strftime('%Y-%m-%d')

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

def fetch_polygon_stock(ticker, start_date=default_start_date, end_date=default_end_date, update=False):

    print(f'Fetching {ticker} using Polygon API...')
    try:
        all_results = []
        next_url = f"{stock_api_endpoint}{ticker}/range/1/day/{start_date}/{end_date}?adjusted=true&sort=asc&limit=50000&apikey={poly_api_key}"
        
        # Loop through all pages
        while next_url:
            print(f"Fetching page for {ticker}...")
            raw = requests.get(next_url)
            jraw = raw.json()
            
            if jraw.get('status') not in ['OK', 'DELAYED']:
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
            # Normalize to date-only to match sector ETF indexing
            data['date'] = pd.to_datetime(data['date'].dt.normalize())
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
            raw_path = os.path.join(data_dir, f'{ticker}_daily_raw.parquet')
            daily_path = os.path.join(data_dir, f'{ticker}_daily.parquet')
            # Append logic
            if update and os.path.exists(raw_path):
                old_raw = pd.read_parquet(raw_path)
                data = data[~data.index.isin(old_raw.index)]
                if not data.empty:
                    data = pd.concat([old_raw, data]).sort_index()
                else:
                    data = old_raw
            if not data.empty:
                data.to_parquet(raw_path)
            
            # Extract close prices and rename column
            close_df = data[['close']].copy()
            close_df.rename(columns={'close': ticker}, inplace=True)
            
            # Calculate returns
            data_returns = close_df.pct_change().dropna()
            data_returns.name = f'{ticker}'
            
            # Save processed data
            if update and os.path.exists(daily_path):
                old_daily = pd.read_parquet(daily_path)
                # Ensure old_daily is a DataFrame
                if isinstance(old_daily, pd.Series):
                    old_daily = old_daily.to_frame()
                data_returns = data_returns[~data_returns.index.isin(old_daily.index)]
                if not data_returns.empty:
                    data_returns = pd.concat([old_daily, data_returns]).sort_index()
                else:
                    data_returns = old_daily
            if not data_returns.empty:
                data_returns.to_parquet(daily_path)
            print(f"Saved: {ticker}_daily.parquet ({len(all_results)} records)")
        else:
            print(f"Error: No data returned for {ticker}")
            
    except Exception as e:
        print(f"Error fetching {ticker} from Polygon: {e}")

def fetch(tickers=etf_tickers, start_date=default_start_date, end_date=default_end_date, update=False):
    # Fetch and save data
    if isinstance(tickers, str):
        tickers = [tickers]
    
    for ticker in tickers:
        print(f"\nFetching data for {ticker}...")

        # Check if ticker is in the etf_tickers list
        if ticker not in etf_tickers:
            print(f'{ticker} is not in ETF list, using Polygon API...')
            fetch_polygon_stock(ticker, start_date, end_date, update)
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
                    api_key=api_key,
                    update=update
                )

                print(f"Saved synthetic and full stitched {ticker} return streams.")
            except Exception as e:
                print(f"Error calling synthetic ETF patching function for {ticker}: {e}")
        else:
            try:
                raw = requests.get(f"{api_endpoint}/daily/{ticker}/prices?startDate={start_date}&endDate={end_date}&format=json&resampleFreq=daily&token={api_key}")
                jraw = raw.json()
                
                # Debug: Check if we got valid data
                if not jraw or len(jraw) == 0:
                    print(f"Warning: No data returned from API for {ticker}")
                    continue
                    
                # Create DataFrame with explicit index to avoid scalar values error
                try:
                    data = pd.DataFrame(jraw)
                except ValueError as e:
                    raise e
                
                data['date'] = pd.to_datetime(data['date'])
                
                data.set_index('date', inplace=True)
                raw_path = os.path.join(data_dir, f'{ticker}_daily_raw.parquet')
                daily_path = os.path.join(data_dir, f'{ticker}_daily.parquet')
                # Append logic
                if update and os.path.exists(raw_path):
                    old_raw = pd.read_parquet(raw_path)
                    data = data[~data.index.isin(old_raw.index)]
                    if not data.empty:
                        data = pd.concat([old_raw, data]).sort_index()
                    else:
                        data = old_raw
                if not data.empty:
                    data.to_parquet(raw_path)
                data = data[['close']].copy()
                data.rename(columns={'close': ticker}, inplace=True)
                data_returns = data.pct_change().dropna()
                # Ensure data_returns is a Series and set its name
                if isinstance(data_returns, pd.DataFrame):
                    data_returns = data_returns.iloc[:, 0]  # Take first column if it's a DataFrame
                data_returns.name = f'{ticker}'
                if update and os.path.exists(daily_path):
                    old_daily = pd.read_parquet(daily_path)
                    # Ensure old_daily is a DataFrame
                    if isinstance(old_daily, pd.Series):
                        old_daily = old_daily.to_frame()
                    data_returns = data_returns[~data_returns.index.isin(old_daily.index)]
                    if not data_returns.empty:
                        data_returns = pd.concat([old_daily, data_returns]).sort_index()
                    else:
                        data_returns = old_daily
                if not data_returns.empty:
                    data_returns.to_parquet(daily_path)
                    print(f"Saved: {ticker}_daily.parquet")
                else:
                    print(f"Error: No data returned for {ticker}")
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        
        time.sleep(1)
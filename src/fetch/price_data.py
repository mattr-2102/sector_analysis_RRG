import requests
import pandas as pd
import time
import sys
import os

from config.helper import get_paths, key
from src.fetch.synthetic_price_data import fetchandpatch_synthetics

paths = get_paths()
data_dir = paths['data_dir']
config_dir = paths['config_dir']

# API keys
api_key = key('tiingo')
api_endpoint = 'https://api.tiingo.com/tiingo'

# Date range
start_date = '2005-07-06'
end_date = '2025-07-06'

columns = ["date", "close", "volume"]

# List of sector ETF tickers, each holds roughly 30-70 stocks (X = SPDR family ETFs, L = Large-cap Exposure i.e. S&P500 based which is large-cap)
tickers = [
    'SPY',  # The S&P, idk
    'XLE',  # Energy (Exxon, Chevron...)
    'XLB',  # Materials (Basic Materials) (Linde, Sherwin-Williams...)
    'XLI',  # Industrials (GE Aero, RTX, CAT...)
    'XLU',  # Utilities (NextEra Energy, Southern comp, Duke...)
    'XLV',  # Healthcare (Vitality/Vitality of Health) (Eli Lilly, UnitedHealth, JnJ...)
    'XLF',  # Financials (Berkshire, JPMorgan, Visa...)
    'XLY',  # Consumer Discretionary (Y arbitrary, Youth, etc) (Amazon, Tesla, Home Depot...)
    'XLP',  # Consumer Staples (Pantry/Provisions) (Costco, PnG, Walmart...)
    'XLK',  # Information Technology (K arbitrary, Key tech firms) (Apple, Microsoft, Nvidia...)
    'XLC',  # Communication Services (Meta, Google...)
    'XLRE'  # Real Estate (ProLogis, American Tower, Welltower...)
]

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

def fetch():
    # Fetch and save data
    for ticker in tickers:
        print(f"\nFetching data for {ticker}...")

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
        
        time.sleep(5)
        
if __name__ == "__main__":
    fetch()
import yfinance as yf
import pandas as pd
import time
import sys
import os

from config.paths import get_paths

paths = get_paths()
data_dir = paths['data_dir']

# Path to the API keys file
api_keys_path = os.path.join('../../config', 'api_keys.yaml')

def fetchandpatch_synthetics(ticker, custom_list, start_date, customdate1, customdate2, end_date):
    
    # normalize weights
    weights = pd.Series(custom_list)
    weights /= weights.sum()

    # download synthetic ETF
    custom_tickers = list(weights.index)
    prices = yf.download(custom_tickers, start=start_date, end=customdate1, interval='1d', auto_adjust=True)
    prices.to_csv(os.path.join(data_dir, f'{ticker}_synthetic_raw.csv'))
    close_prices = prices['Close']
    returns = close_prices.pct_change()

    # Drop any tickers that failed
    available_tickers = [t for t in custom_tickers if t in returns.columns]
    weights = weights[available_tickers]
    weights /= weights.sum()
    returns = returns[available_tickers]

    # Create weighted synthetic return stream
    synthetic_returns = (returns * weights).sum(axis=1)

    # Download real XLC data (2018–2025)
    real = yf.download(ticker, start=customdate2, end=end_date, interval='1d', auto_adjust=True)
    real.to_csv(os.path.join(data_dir, f'{ticker}_real_raw.csv'))
    close_prices = real['Close']
    real_returns = real.pct_change()


    # Combine data
    full_returns = pd.concat([synthetic_returns, real_returns])

    # Save CSVs
    synthetic_returns.to_csv(os.path.join(data_dir, f'{ticker}_synthetic_returns.csv'))
    full_returns.to_csv(os.path.join(data_dir, f'{ticker}_daily.csv'))
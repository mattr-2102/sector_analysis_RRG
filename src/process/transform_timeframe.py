import pandas as pd
from pathlib import Path
from src.fetch.price_data import fetch
from config.helper import get_data_file, get_sector_config
from src.fetch.update_data import update_data

config = get_sector_config()
synth_tickers = config['synthetic_etfs']

def get_resampled_data(ticker: str, freq: str = 'weekly', save: bool = True):
    
    if freq not in ['weekly', 'monthly']:
        raise ValueError("freq must be 'weekly' or 'monthly'")

    update_data(ticker)
    
    if ticker in synth_tickers:
        get_resampled_synth_data(ticker=ticker, freq=freq, save=save)
        return
        
    file_suffix_raw = {'weekly': '_weekly_raw.parquet', 'monthly': '_monthly_raw.parquet'}[freq]
    file_suffix_ret = {'weekly': '_weekly.parquet', 'monthly': '_monthly.parquet'}[freq]

    raw_output_path = get_data_file(ticker + file_suffix_raw)
    returns_output_path = get_data_file(ticker + file_suffix_ret)

    # If both raw and returns files exist, skip processing
    if save and Path(raw_output_path).exists() and Path(returns_output_path).exists():
        return

    # Ensure raw daily data exists
    raw_parquet_path = get_data_file(f"{ticker}_daily_raw.parquet")
    if not Path(raw_parquet_path).exists():
        print(f"{ticker}_daily_raw.parquet not found. Attempting to fetch...")
        fetch(ticker)

    # Load raw daily data
    df = pd.read_parquet(raw_parquet_path)
    df.sort_index(inplace=True)

    # Choose resampling rule
    rule = {'weekly': 'W-SUN', 'monthly': 'ME'}[freq]

    # Resample OHLCV
    resampled = df.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    if save:
        # Save raw resampled OHLCV
        resampled.to_parquet(raw_output_path)

        # Save percentage returns
        close_series = resampled[['close']].copy()
        close_series.rename(columns={'close': ticker}, inplace=True)
        returns = close_series.pct_change().dropna()

        if not returns.empty:
            returns.to_parquet(returns_output_path)
            print(f"Saved: {Path(returns_output_path).name}")
        else:
            print(f"Warning: No returns data generated for {ticker}")

def get_resampled_synth_data(ticker: str, freq: str = 'weekly', save: bool = True):
    update_data(ticker)
    file_suffix_ret = {'weekly': '_weekly.parquet', 'monthly': '_monthly.parquet'}[freq]
    
    returns_output_path = get_data_file(ticker + file_suffix_ret)
    
    if save and Path(returns_output_path).exists():
        return
    
    # Ensure raw daily data exists
    returns_parquet_path = get_data_file(f"{ticker}_daily.parquet")
    if not Path(returns_parquet_path).exists():
        print(f"{ticker}_daily.parquet not found. Attempting to fetch...")
        fetch(ticker)
        
    # Load raw daily data
    df = pd.read_parquet(returns_parquet_path)
    df.sort_index(inplace=True)
    
    # Convert % returns to cumulative to preserve compounding, then resample
    cumulative = (1 + df).cumprod()

    rule = {'weekly': 'W-SUN', 'monthly': 'ME'}[freq]
    resampled_cumulative = cumulative.resample(rule).last().dropna()

    # Reconvert back to % return from cumulative
    resampled_returns = resampled_cumulative.pct_change().dropna()

    if save:
        if not resampled_returns.empty:
            resampled_returns.to_parquet(returns_output_path)
            print(f"Saved: {Path(returns_output_path).name}")
        else:
            print(f"Warning: No resampled returns generated for {ticker}")
import pandas as pd
from typing import Optional
from pathlib import Path
from config.helper import get_data_file
from src.fetch.price_data import fetch
from src.process.transform_timeframe import get_resampled_data

def get_cumulative_returns(ticker: str, timeframe: str = 'daily', lookback_days: Optional[int] = None) -> pd.DataFrame:
    if timeframe not in ['daily', 'weekly', 'monthly']:
        raise ValueError("Timeframe must be 'daily', 'weekly', or 'monthly'.")

    file_suffix = {
        'daily': f'{ticker}_daily.csv',
        'weekly': f'{ticker}_weekly.csv',
        'monthly': f'{ticker}_monthly.csv'
    }[timeframe]

    file_path = get_data_file(file_suffix)

    if not Path(file_path).exists():
        print(f"{file_path} not found.")
        if timeframe == 'daily':
            print("Attempting to fetch daily data...")
            fetch(ticker)
        else:
            print(f"Generating {timeframe} data from raw daily data...")
            get_resampled_data(ticker, freq=timeframe)

    data = pd.read_csv(file_path, parse_dates=['date'], index_col='date')

    if data.empty:
        raise ValueError(f"{ticker} could not be retrieved. The ticker may be invalid or missing data.")
    

    df = data.select_dtypes(include='number')

    if lookback_days is not None:
        df = df.tail(lookback_days + 1)
    
    # Apply cumulative product
    cumulative = (1 + df).cumprod()

    return cumulative

import pandas as pd
from typing import Optional
from pathlib import Path
from config.helper import get_data_file
from src.fetch.price_data import fetch
from src.process.transform_timeframe import get_resampled_data
from src.fetch.update_data import update_data
from src.process.transform_timeframe import get_resampled_data

def get_cumulative_returns(ticker: str, timeframe: str = 'daily', lookback_days: Optional[int] = None) -> pd.DataFrame:
    if timeframe not in ['daily', 'weekly', 'monthly']:
        raise ValueError("Timeframe must be 'daily', 'weekly', or 'monthly'.")

    file_suffix = {
        'daily': f'{ticker}_daily.parquet',
        'weekly': f'{ticker}_weekly.parquet',
        'monthly': f'{ticker}_monthly.parquet'
    }[timeframe]

    update_data(ticker)
    file_path = get_data_file(file_suffix)
    
    if not Path(file_path).exists():
        get_resampled_data(ticker, timeframe)
        file_path = get_data_file(file_suffix)

    
    data = pd.read_parquet(file_path)
    
    
    if data.empty:
        raise ValueError(f"{ticker} could not be retrieved. The ticker may be invalid or missing data.")
    

    # Handle different data structures
    if isinstance(data, pd.Series):
        # If it's a Series, convert to DataFrame
        df = data.to_frame()
    else:
        # If it's a DataFrame, select numeric columns
        df = data.select_dtypes(include='number')
        
    if lookback_days is not None:
        df = df.tail(lookback_days + 1)
    
    # Apply cumulative product
    cumulative = (1 + df).cumprod()

    return cumulative

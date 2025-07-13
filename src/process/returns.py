import pandas as pd
from typing import Optional
from pathlib import Path
from config.helper import get_data_file
from src.fetch.price_data import fetch

def get_cumulative_returns(daily_pct_change: str) -> pd.DataFrame:
    file_path = get_data_file(f'{daily_pct_change}_daily.csv')

    if not Path(file_path).exists():
        print(f"{file_path} not found. Attempting to fetch...")
        fetch(daily_pct_change)
        
    data = pd.read_csv(file_path, parse_dates=['date'], index_col='date')
        
    if data.empty:
        raise ValueError(f"{daily_pct_change} could not be retrieved. The ticker is possibly invalid.")
        
    df = data.select_dtypes(include='number')
        
    # Apply cumulative product
    cumulative = (1 + df).cumprod()

    return cumulative
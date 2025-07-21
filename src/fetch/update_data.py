import os
import pandas as pd
from datetime import datetime, timedelta
from config.helper import get_data_file
from src.fetch.price_data import fetch

def update_data(ticker):
    """
    Ensures ticker_daily.parquet is up-to-date. If missing, fetches all data. If outdated, fetches only missing days and appends.
    """
    parquet_path = get_data_file(f"{ticker}_daily.parquet")
    today = datetime.now().date()

    if not os.path.exists(parquet_path):
        # File doesn't exist, fetch all data
        fetch(ticker)
        return

    # File exists, check most recent date
    df = pd.read_parquet(parquet_path)
    if df.empty:
        fetch(ticker)
        return
    
    # Check if we have a datetime index or a date column
    if isinstance(df.index, pd.DatetimeIndex):
        last_date = df.index.max().date()
    elif 'date' in df.columns:
        last_date = df['date'].max().date()
    else:
        print(f"Warning: No date information found in {parquet_path}")
        fetch(ticker)
        return
    
    if (today - last_date).days <= 3:
        return        # Data is up to date (allowing for weekends)
    
    if today.weekday() < 5:
        start_date = last_date + timedelta(days=1)
        end_date = today
        fetch(ticker, start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'), update=True)
        
    # Find first missing date (day after last_date)
    start_date = last_date + timedelta(days=1)
    end_date = today
    # Call fetch with update=True and date range
    fetch(ticker, start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'), update=True)
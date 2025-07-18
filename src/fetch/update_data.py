import os
import pandas as pd
from datetime import datetime, timedelta
from config.helper import get_data_file
from src.fetch.price_data import fetch

def update_data(ticker):
    """
    Ensures ticker_daily.csv is up-to-date. If missing, fetches all data. If outdated, fetches only missing days and appends.
    """
    csv_path = get_data_file(f"{ticker}_daily.csv")
    today = datetime.now().date()

    if not os.path.exists(csv_path):
        # File doesn't exist, fetch all data
        fetch(ticker)
        return

    # File exists, check most recent date
    df = pd.read_csv(csv_path, parse_dates=['date'])
    if df.empty:
        fetch(ticker)
        return
    last_date = df['date'].max().date()
    if last_date >= today - timedelta(days=1):
        # Data is up to date (allowing for weekends)
        return
    # Find first missing date (day after last_date)
    start_date = last_date + timedelta(days=1)
    end_date = today
    # Call fetch with update=True and date range
    fetch(ticker, start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'), update=True) 
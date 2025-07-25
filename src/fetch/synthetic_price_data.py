import pandas as pd
import requests
import os

from config.helper import get_data_dir

data_dir = get_data_dir()

def fetchandpatch_synthetics(ticker, custom_list, start_date, customdate1, customdate2, end_date, api_endpoint, api_key, update = False):

    all_data = []
    if (start_date <= customdate1):
        # download synthetic ETF
        for tempticker in custom_list:
            try:
                print(f"Fetching holding {tempticker}, part of {ticker}...")
                raw = requests.get(f"{api_endpoint}/daily/{tempticker}/prices?startDate={start_date}&endDate={customdate1}&format=json&resampleFreq=daily&token={api_key}")
                raw.raise_for_status()
                jraw = raw.json()

                prices = pd.DataFrame(jraw)
                prices['date'] = pd.to_datetime(prices['date'])
                prices.set_index('date', inplace=True)
                prices = prices[['adjClose']]
                prices.rename(columns={'adjClose': tempticker}, inplace= True)
                
                all_data.append(prices)
            except Exception as e:
                print(f"Error fetching {tempticker}: {e}")
        
        combined = pd.concat(all_data, axis=1)
        combined.dropna(axis=0, how='any', inplace=True)
        combined.to_parquet(os.path.join(data_dir, f'{ticker}_synthetic_prices_raw.parquet'))

        # normalize weights
        weights = pd.Series(custom_list)
        # Keep only weights for tickers actually present in the data
        valid_weights = weights[weights.index.isin(combined.columns)]
        valid_weights /= valid_weights.sum()

        # calc daily returns
        returns = combined.pct_change().dropna()
        returns = returns[valid_weights.index]

        # create weighted synthetic returns
        synthetic_returns = returns.dot(valid_weights)
        synthetic_returns.name = f"{ticker}"
        synthetic_returns.to_frame().to_parquet(os.path.join(data_dir, f'{ticker}_synthetic_returns.parquet'))

    # Download real data
    try:
        print(f"Fetching real {ticker} data non-synthetic...")
        if (start_date <= customdate1):
            raw = requests.get(f"{api_endpoint}/daily/{ticker}/prices?startDate={customdate2}&endDate={end_date}&format=json&resampleFreq=daily&token={api_key}")
        else:
            raw = requests.get(f"{api_endpoint}/daily/{ticker}/prices?startDate={start_date}&endDate={end_date}&format=json&resampleFreq=daily&token={api_key}")
        jraw = raw.json()

        real = pd.DataFrame(jraw)
        real['date'] = pd.to_datetime(real['date'])
        real.set_index('date', inplace=True)
        real_raw_path = os.path.join(data_dir, f'{ticker}_real_raw.parquet')
        if update and os.path.exists(real_raw_path):
            old_real_raw = pd.read_parquet(real_raw_path)
            real = real[~real.index.isin(old_real_raw.index)]
            if not real.empty:
                real = pd.concat([old_real_raw, real]).sort_index()
            else:
                real = old_real_raw
        real.to_parquet(real_raw_path)

        real = real[['close']]
        real.rename(columns={'close': ticker}, inplace=True)
        real_returns = real.pct_change().dropna()
        real_returns.name = f'{ticker}'
        if (start_date <= customdate1):
            full_returns = pd.concat([synthetic_returns, real_returns])
        else:
            full_returns = real_returns
        daily_path = os.path.join(data_dir, f'{ticker}_daily.parquet')
        if update and os.path.exists(daily_path):
            old_daily = pd.read_parquet(daily_path)
            # Ensure old_daily is a DataFrame
            if isinstance(old_daily, pd.Series):
                old_daily = old_daily.to_frame()
            full_returns = full_returns[~full_returns.index.isin(old_daily.index)]
            if not full_returns.empty:
                full_returns = pd.concat([old_daily, full_returns]).sort_index()
            else:
                full_returns = old_daily
        full_returns.to_parquet(daily_path)

        print(f"Saved full stitched returns for {ticker}.")

    except Exception as e:
        print(f"Error fetching real {ticker}: {e}")
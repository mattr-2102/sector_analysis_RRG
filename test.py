

import yfinance as yf

start_date = '2005-07-06'
end_date = '2025-07-06'
ticker = 'SPY'
try:
    data = yf.download(ticker, start=start_date, end=end_date, interval='1d', auto_adjust=True)
    if not data.empty:
        data.to_csv(f'{ticker}_daily.csv')
        print(f"Saved: {ticker}_daily.csv")
    else:
        print(f"Error: No data returned for {ticker}")
except Exception as e:
    print(f"Error fetching: {e}")
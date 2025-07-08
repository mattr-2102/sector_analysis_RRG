import yfinance as yf
import time
import os

# Create output directory if it doesn't exist
os.makedirs('data', exist_ok=True)

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

# Date range
start_date = '2005-07-06'
end_date = '2025-07-06'

# Fetch and save data
for ticker in tickers:
    print(f"\nFetching data for {ticker}...")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval='1d')
        if not data.empty:
            data.to_csv(f'data/{ticker}_daily.csv')
            print(f"Saved: data/{ticker}_daily.csv")
        else:
            print(f"Error: No data returned for {ticker}")
    except Exception as e:
        print(f"Error fetching {ticker}, doesn't exist or rate limited probably: {e}")
    
    # Delay to avoid rate limits
    time.sleep(2)
    
    
    
#need to transition to Tiingo, then start messing with data. can either start with coorelation or RRG

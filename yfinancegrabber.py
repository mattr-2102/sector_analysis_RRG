import yfinance as yf
import pandas as pd
import time
import sys
import os

# Ensure config directory exists
os.makedirs('config', exist_ok=True)

# Path to the API keys file
api_keys_path = os.path.join('config', 'api_keys.yaml')

# Create the file if it doesn't exist, then exit
if not os.path.exists(api_keys_path):
    with open(api_keys_path, 'w') as f:
        f.write("# Add your API keys here. For example:\n")
        f.write("# tiingo: YOUR_TIINGO_API_KEY\n")
    print("api_keys.yaml created in /config. Input keys if applicable and restart the program.")
    sys.exit(0)

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
end_pre_xlc = '2018-06-18'
start_real_xlc = '2018-06-19'
end_pre_xlre = '2015-10-07'
start_real_xlre = '2015-10-08'
end_date = '2025-07-06'

# XLC launch weights from 2018-06
xlc_weights = {
    'META': 0.2096,
    'GOOG': 0.1173,
    'GOOGL': 0.1163,
    'NFLX': 0.0505,
    'T': 0.0491,
    'CHTR': 0.0478,
    'CMCSA': 0.0467,
    'DIS': 0.0453,
    'VZ': 0.0448,
    'EA': 0.0381,
    'PARA': 0.0170,
    'LUMN': 0.0161
}

# XLRE launch weights October 2015-10
xlre_weights = {
    'SPG': 0.12,
    'AMT': 0.0798,
    'PSA': 0.075,
    'CCI': 0.059,
    'EQR': 0.0555,
    'AVB': 0.0464,
    'WY': 0.0432,
    'EQIX': 0.0426,
    'PLD': 0.0412,
    'WELL': 0.0404
}

# Fetch and save data
for ticker in tickers:
    print(f"\nFetching data for {ticker}...")

    # XLC was reclassified from specific XLK and XLY stocks 2018-06-19
    if ticker == 'XLC':
        print("Handling XLC (custom pre-2018 logic)...")
        try:
            # Normalize weights
            weights = pd.Series(xlc_weights)
            weights /= weights.sum()

            # Download synthetic ETF (2005–2018)
            custom_tickers = list(weights.index)
            prices = yf.download(custom_tickers, start=start_date, end=end_pre_xlc, interval='1d', auto_adjust=True)
            prices.to_csv('data/XLC_synthetic_prices_raw.csv')
            returns = prices.pct_change()

            # Drop any tickers that failed
            available_tickers = [t for t in custom_tickers if t in returns.columns]
            weights = weights[available_tickers]
            weights /= weights.sum()
            returns = returns[available_tickers]

            # Create weighted synthetic return stream
            synthetic_xlc_returns = (returns * weights).sum(axis=1)

            # Download real XLC data (2018–2025)
            xlc_real = yf.download('XLC', start=start_real_xlc, end=end_date, interval='1d', auto_adjust=True)
            xlc_real.to_csv('data/XLC_real_prices_raw.csv')
            xlc_real_returns = xlc_real.pct_change()

            # Combine data
            xlc_full_returns = pd.concat([synthetic_xlc_returns, xlc_real_returns])

            # Save CSVs
            synthetic_xlc_returns.to_csv(f'data/XLC_synthetic_returns.csv')
            xlc_full_returns.to_csv(f'data/XLC_daily.csv')

            print("Saved synthetic and full stitched XLC return streams.")
        except Exception as e:
            print(f"Error handling XLC: {e}")

    # XLRE was derived from XLF on 2015-10-08
    elif ticker == 'XLRE':
        print("Handling XLRE (custom pre-2015 logic)...")
        try:
            # Normalize weights
            weights = pd.Series(xlre_weights)
            weights /= weights.sum()

            # donwload synthetic ETF
            custom_tickers = list(weights.index)
            prices = yf.download(custom_tickers, start=start_date, end=end_pre_xlre, interval='1d', auto_adjust=True)
            prices.to_csv('data/XLRE_synthetic_prices_raw.csv')
            returns = prices.pct_change()

            # Drop failed tickers
            available_tickers = [t for t in custom_tickers if t in returns.columns]
            weights = weights[available_tickers]
            weights /= weights.sum()
            returns = returns[available_tickers]

            # Compute synthetic XLRE returns
            synthetic_xlre_returns = (returns * weights).sum(axis=1)

            # Download real XLRE data
            xlre_real_prices = yf.download('XLRE', start=start_real_xlre, end=end_date, interval='1d', auto_adjust=True)
            prices.to_csv('data/XLRE_real_prices_raw.csv')
            xlre_real_returns = xlre_real_prices.pct_change()

            # Combine return series
            xlre_full_returns = pd.concat([synthetic_xlre_returns, xlre_real_returns])

            # Save to files
            synthetic_xlre_returns.to_csv(f'data/XLRE_synthetic_returns.csv')
            xlre_full_returns.to_csv(f'data/XLRE_daily.csv')

            print("Saved synthetic and full XLRE return streams.")
        except Exception as e:
            print(f"Error handling XLRE: {e}")

    else:
        try:
            data = yf.download(ticker, start=start_date, end=end_date, interval='1d', auto_adjust=True)
            if not data.empty:
                data.to_csv(f'data/{ticker}_daily.csv')
                print(f"Saved: data/{ticker}_daily.csv")
            else:
                print(f"Error: No data returned for {ticker}")
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
    
    time.sleep(2)
    
    
    
#need to transition to Tiingo, then start messing with data. can either start with coorelation or RRG

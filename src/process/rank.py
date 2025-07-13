import pandas as pd
from typing import List, Optional
from src.process.relative_strength import get_relative_strength
from src.process.rs_momentum import get_relative_strength_momentum
from sklearn.linear_model import LinearRegression
from config.helper import get_sector_config

config = get_sector_config()

def rank_relative_strength(tickers: List[str] = config['sector_etfs'], benchmark: str = config['benchmark'], lookback_days: int = 30, normalize: bool = True, display: bool = True) -> pd.DataFrame:
    rs_values = {}

    for ticker in tickers:
        if ticker == benchmark:
            continue
        rs_series = get_relative_strength(ticker, benchmark, lookback_days=lookback_days, normalize=normalize)
        rs_values[ticker] = rs_series.iloc[-1]

    rs_df = pd.DataFrame.from_dict(rs_values, orient='index', columns=['RelativeStrength'])
    rs_df.sort_values(by='RelativeStrength', ascending=False, inplace=True)
    rs_df['Rank'] = range(1, len(rs_df) + 1)

    if display:
        print("\nSector Relative Strength Rankings:")
        print(rs_df.round(4).to_string())

    return rs_df


def rank_relative_strength_momentum(tickers: List[str] = config['sector_etfs'], benchmark: str = config['benchmark'], lookback_days: int = 30, momentum_window: int = 5, normalize: bool = True, display: bool = True) -> pd.DataFrame:
    momentum_values = {}

    for ticker in tickers:
        if ticker == benchmark:
            continue
        try:
            slope = get_relative_strength_momentum(
                target=ticker,
                benchmark=benchmark,
                lookback_days=lookback_days,
                momentum_window=momentum_window,
                normalize=normalize
            )
            momentum_values[ticker] = slope
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

    df = pd.DataFrame.from_dict(momentum_values, orient='index', columns=['RSMomentum'])
    df.sort_values(by='RSMomentum', ascending=False, inplace=True)
    df['Rank'] = range(1, len(df) + 1)

    if display:
        print("\nSector RS Momentum Rankings:")
        print(df.round(4).to_string())

    return df

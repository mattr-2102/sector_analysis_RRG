import pandas as pd
from typing import List, Optional
from src.process.relative_strength import get_relative_strength
from src.process.rs_momentum import get_relative_strength_momentum
from config.helper import get_sector_config
from src.process.volatility import get_volatility_data

config = get_sector_config()

def rank_relative_strength(
    tickers: List[str] = config['sector_etfs'],
    benchmark: str = config['benchmark'],
    lookback_days: int = 30,
    normalize: bool = True,
    display: bool = True,
    timeframe: str = 'daily'
) -> pd.DataFrame:
    rs_values = {}

    for ticker in tickers:
        if ticker == benchmark:
            continue

        rs_series = get_relative_strength(ticker, benchmark, lookback_days=lookback_days, normalize=normalize, timeframe=timeframe)

        rs_values[ticker] = rs_series.iloc[-1]

    rs_df = pd.DataFrame.from_dict(rs_values, orient='index', columns=['RelativeStrength'])
    rs_df.sort_values(by='RelativeStrength', ascending=False, inplace=True)
    rs_df['Rank'] = range(1, len(rs_df) + 1)

    if display:
        print("\nSector Relative Strength Rankings:")
        print(rs_df.round(4).to_string())

    return rs_df


def rank_relative_strength_momentum(
    tickers: List[str] = config['sector_etfs'],
    benchmark: str = config['benchmark'],
    lookback_days: int = 30,
    momentum_window: int = 5,
    normalize: bool = True,
    display: bool = True,
    timeframe: str = 'daily'
) -> pd.DataFrame:
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
                normalize=normalize,
                timeframe=timeframe
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


def rank_volatility(
    tickers: Optional[List[str]] = config['sector_etfs'],
    window: int = 20,
    display: bool = True
) -> dict:
    """
    Rank sectors by volatility across daily, weekly, and monthly timeframes.
    Args:
        tickers: List of ticker symbols (defaults to sector_etfs from config)
        window: Rolling window for volatility calculation (default: 20)
        display: Whether to print rankings to console (default: True)
    Returns:
        Dictionary containing rankings for each timeframe
    """
    vol_df = get_volatility_data(tickers=tickers, window=window)
    timeframes = ['DailyZVol', 'WeeklyZVol', 'MonthlyZVol']
    rankings = {}
    for tf in timeframes:
        if tf not in vol_df.columns:
            continue
        tf_data = vol_df[tf].dropna()
        tf_df = tf_data.to_frame(name='Volatility_ZScore')
        tf_df['Ticker'] = tf_df.index
        # Most volatile (highest z-score)
        most_volatile_df = tf_df.sort_values(by='Volatility_ZScore', ascending=False).reset_index(drop=True)
        most_volatile_df['Rank'] = range(1, len(most_volatile_df) + 1)
        # Most stable (lowest z-score)
        most_stable_df = tf_df.sort_values(by='Volatility_ZScore', ascending=True).reset_index(drop=True)
        most_stable_df['Rank'] = range(1, len(most_stable_df) + 1)
        timeframe_name = tf.replace('ZVol', '')
        rankings[timeframe_name] = {
            'Most_Volatile': most_volatile_df[['Ticker', 'Volatility_ZScore', 'Rank']],
            'Most_Stable': most_stable_df[['Ticker', 'Volatility_ZScore', 'Rank']]
        }
        if display:
            print(f"\n{timeframe_name} Timeframe Rankings:")
            print(f"Most Volatile Sectors:")
            print(most_volatile_df[['Ticker', 'Volatility_ZScore', 'Rank']].round(4).to_string(index=False))
            print(f"Most Stable Sectors:")
            print(most_stable_df[['Ticker', 'Volatility_ZScore', 'Rank']].round(4).to_string(index=False))
            print("-" * 50)
    return rankings
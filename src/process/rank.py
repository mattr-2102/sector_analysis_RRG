import pandas as pd
from typing import List, Optional
from src.process.relative_strength import get_relative_strength
from src.process.rs_momentum import get_relative_strength_momentum
from config.helper import get_sector_config
from src.process.volatility import get_volatility_data
from src.fetch.update_data import update_data

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
        update_data(ticker)
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
        update_data(ticker)
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
    display: bool = True,
    raw_volatility: bool = False
) -> dict:
    """
    Rank sectors by volatility across daily, weekly, and monthly timeframes.
    Args:
        tickers: List of ticker symbols (defaults to sector_etfs from config)
        window: Rolling window for volatility calculation (default: 20)
        display: Whether to print rankings to console (default: True)
        raw_volatility: If True, use raw annualized volatility; if False, use z-scores (default: False)
    Returns:
        Dictionary containing rankings for each timeframe
    """
    for ticker in tickers:
        update_data(ticker)
    vol_df = get_volatility_data(tickers=tickers, window=window, raw_volatility=raw_volatility)
    
    # Choose column names based on raw_volatility parameter
    if raw_volatility:
        timeframes = ['DailyVol', 'WeeklyVol', 'MonthlyVol']
        value_label = 'Volatility'
    else:
        timeframes = ['DailyZVol', 'WeeklyZVol', 'MonthlyZVol']
        value_label = 'Volatility_ZScore'
    
    rankings = {}
    for tf in timeframes:
        if tf not in vol_df.columns:
            continue
        tf_data = vol_df[tf].dropna()
        tf_df = tf_data.to_frame(name=value_label)
        tf_df['Ticker'] = tf_df.index
        # Most volatile (highest value)
        most_volatile_df = tf_df.sort_values(by=value_label, ascending=False).reset_index(drop=True)
        most_volatile_df['Rank'] = range(1, len(most_volatile_df) + 1)
        # Most stable (lowest value)
        most_stable_df = tf_df.sort_values(by=value_label, ascending=True).reset_index(drop=True)
        most_stable_df['Rank'] = range(1, len(most_stable_df) + 1)
        timeframe_name = tf.replace('ZVol', '').replace('Vol', '')
        rankings[timeframe_name] = {
            'Most_Volatile': most_volatile_df[['Ticker', value_label, 'Rank']],
            'Most_Stable': most_stable_df[['Ticker', value_label, 'Rank']]
        }
        if display:
            vol_type = "Raw Volatility" if raw_volatility else "Z-Score"
            print(f"\n{timeframe_name} Timeframe Rankings ({vol_type}):")
            print(f"Most Volatile Sectors:")
            print(most_volatile_df[['Ticker', value_label, 'Rank']].round(4).to_string(index=False))
            print(f"Most Stable Sectors:")
            print(most_stable_df[['Ticker', value_label, 'Rank']].round(4).to_string(index=False))
            print("-" * 50)
    return rankings
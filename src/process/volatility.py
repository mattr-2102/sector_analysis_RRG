import pandas as pd
from typing import Optional, List
from src.process.returns import get_cumulative_returns
from src.fetch.update_data import update_data

def compute_volatility_for_timeframe(ticker: str, timeframe: str = 'daily', window: int = 20, raw_volatility: bool = False) -> Optional[float]:
    """
    Compute volatility for a single timeframe.
    Args:
        ticker: Stock/sector ticker symbol
        timeframe: 'daily', 'weekly', or 'monthly'
        window: Rolling window for volatility calculation (default: 20)
        raw_volatility: If True, return raw annualized volatility; if False, return z-score
    Returns:
        Single volatility value (float) or None on error
    """
    try:
        update_data(ticker)
        cum_returns = get_cumulative_returns(ticker, timeframe=timeframe)
        returns = cum_returns.pct_change().dropna()

        rolling_vol = returns.rolling(window).std()

        if raw_volatility:
            periods_per_year = {'daily': 252, 'weekly': 52, 'monthly': 12}[timeframe]
            annualized_vol = rolling_vol * (periods_per_year ** 0.5)
            latest_vol = annualized_vol.iloc[-1]
            if isinstance(latest_vol, pd.Series):
                latest_vol = latest_vol.iloc[0]
            return latest_vol
        else:
            zscore_vol = (rolling_vol - rolling_vol.mean()) / rolling_vol.std()
            latest_z = zscore_vol.iloc[-1]
            if isinstance(latest_z, pd.Series):
                latest_z = latest_z.iloc[0]
            return latest_z

    except Exception as e:
        print(f"Error processing {ticker} for {timeframe}: {e}")
        return None

def get_volatility_data(tickers: Optional[List[str]] = None, timeframe: str = 'daily', window: int = 20, raw_volatility: bool = False) -> pd.DataFrame:
    """
    Calculate volatility for a list of tickers for a specific timeframe.
    Args:
        tickers: List of ticker symbols (if None, uses sector ETFs from config)
        timeframe: 'daily', 'weekly', or 'monthly'
        window: Rolling window for volatility calculation (default: 20)
        raw_volatility: If True, return raw annualized volatility; if False, return z-scores
    Returns:
        DataFrame with ticker and its volatility for the given timeframe
    """
    from config.helper import get_sector_config

    config = get_sector_config()
    if tickers is None:
        tickers = config['sector_etfs']
    if not tickers:
        raise ValueError("No tickers provided and no sector_etfs found in config")

    records = []
    for ticker in tickers:
        vol = compute_volatility_for_timeframe(ticker, timeframe, window, raw_volatility)
        col_name = f"{timeframe.capitalize()}Vol" if raw_volatility else f"{timeframe.capitalize()}ZVol"
        records.append({'Ticker': ticker, col_name: vol})

    df = pd.DataFrame(records)
    df.set_index('Ticker', inplace=True)
    return df

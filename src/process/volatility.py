import pandas as pd
from typing import Optional, List
from src.process.returns import get_cumulative_returns

def compute_volatility_across_timeframes(ticker: str, window: int = 20) -> dict:
    """
    Compute normalized volatility z-scores across daily, weekly, and monthly timeframes.
    Args:
        ticker: Stock/sector ticker symbol
        window: Rolling window for volatility calculation (default: 20)
    Returns:
        Dictionary with volatility z-scores for each timeframe
    """
    vol_data = {}
    for tf in ['daily', 'weekly', 'monthly']:
        try:
            cum_returns = get_cumulative_returns(ticker, timeframe=tf)
            returns = cum_returns.pct_change().dropna()
            
            # Calculate rolling volatility
            rolling_vol = returns.rolling(window).std()
            
            # Normalize volatility using z-score for comparability across sectors
            zscore_vol = (rolling_vol - rolling_vol.mean()) / rolling_vol.std()
            
            # Get the latest z-score value
            latest_z = zscore_vol.iloc[-1]
            if isinstance(latest_z, pd.Series):
                latest_z = latest_z.iloc[0]

            vol_data[tf] = latest_z
        except Exception as e:
            print(f"Error processing {ticker} for {tf}: {e}")
            vol_data[tf] = None
    
    return vol_data

def get_volatility_data(tickers: Optional[List[str]] = None, window: int = 20) -> pd.DataFrame:
    """
    Calculate normalized volatility for a list of tickers across daily, weekly, and monthly timeframes.
    Args:
        tickers: List of ticker symbols (if None, uses sector ETFs from config)
        window: Rolling window for volatility calculation (default: 20)
    Returns:
        DataFrame with volatility z-scores for each ticker and timeframe
    """
    from config.helper import get_sector_config
    
    config = get_sector_config()
    if tickers is None:
        tickers = config['sector_etfs']
    if not tickers:
        raise ValueError("No tickers provided and no sector_etfs found in config")
    
    records = []
    for ticker in tickers:
        tf_vols = compute_volatility_across_timeframes(ticker, window)
        record = {
            'Ticker': ticker,
            'DailyZVol': tf_vols['daily'],
            'WeeklyZVol': tf_vols['weekly'],
            'MonthlyZVol': tf_vols['monthly']
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    df.set_index('Ticker', inplace=True)
    return df 
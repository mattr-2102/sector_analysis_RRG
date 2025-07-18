import pandas as pd
from typing import Optional, List
from src.process.returns import get_cumulative_returns
from src.fetch.update_data import update_data

def compute_volatility_across_timeframes(ticker: str, window: int = 20, raw_volatility: bool = False) -> dict:
    """
    Compute volatility across daily, weekly, and monthly timeframes.
    Args:
        ticker: Stock/sector ticker symbol
        window: Rolling window for volatility calculation (default: 20)
        raw_volatility: If True, return raw annualized volatility; if False, return z-scores (default: False)
    Returns:
        Dictionary with volatility values for each timeframe
    """
    update_data(ticker)
    vol_data = {}
    for tf in ['daily', 'weekly', 'monthly']:
        try:
            cum_returns = get_cumulative_returns(ticker, timeframe=tf)
            returns = cum_returns.pct_change().dropna()
            
            # Calculate rolling volatility
            rolling_vol = returns.rolling(window).std()
            
            if raw_volatility:
                # Return raw annualized volatility
                periods_per_year = {'daily': 252, 'weekly': 52, 'monthly': 12}[tf]
                annualized_vol = rolling_vol * (periods_per_year ** 0.5)
                latest_vol = annualized_vol.iloc[-1]
                if isinstance(latest_vol, pd.Series):
                    latest_vol = latest_vol.iloc[0]
                vol_data[tf] = latest_vol
            else:
                # Return z-scores (normalized against ticker's own history)
                zscore_vol = (rolling_vol - rolling_vol.mean()) / rolling_vol.std()
                latest_z = zscore_vol.iloc[-1]
                if isinstance(latest_z, pd.Series):
                    latest_z = latest_z.iloc[0]
                vol_data[tf] = latest_z
                
        except Exception as e:
            print(f"Error processing {ticker} for {tf}: {e}")
            vol_data[tf] = None
    
    return vol_data

def get_volatility_data(tickers: Optional[List[str]] = None, window: int = 20, raw_volatility: bool = False) -> pd.DataFrame:
    """
    Calculate volatility for a list of tickers across daily, weekly, and monthly timeframes.
    Args:
        tickers: List of ticker symbols (if None, uses sector ETFs from config)
        window: Rolling window for volatility calculation (default: 20)
        raw_volatility: If True, return raw annualized volatility; if False, return z-scores (default: False)
    Returns:
        DataFrame with volatility values for each ticker and timeframe
    """
    from config.helper import get_sector_config
    
    config = get_sector_config()
    if tickers is None:
        tickers = config['sector_etfs']
    if not tickers:
        raise ValueError("No tickers provided and no sector_etfs found in config")
    
    records = []
    for ticker in tickers:
        update_data(ticker)
        tf_vols = compute_volatility_across_timeframes(ticker, window, raw_volatility)
        
        if raw_volatility:
            record = {
                'Ticker': ticker,
                'DailyVol': tf_vols['daily'],
                'WeeklyVol': tf_vols['weekly'],
                'MonthlyVol': tf_vols['monthly']
            }
        else:
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
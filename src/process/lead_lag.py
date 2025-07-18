import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from config.helper import get_sector_config
from src.process.returns import get_cumulative_returns
from statsmodels.tsa.stattools import grangercausalitytests
from src.fetch.update_data import update_data

config = get_sector_config()
sector_etfs = config['sector_etfs']
benchmark = config['benchmark']

def cross_correlation_lead_lag(series1: pd.Series, series2: pd.Series, max_lag: int = 10) -> Tuple[int, float]:
    """
    Compute the lag (in periods) where series1 leads/lags series2 the most.
    Returns (best_lag, max_correlation).
    Positive lag: series1 leads series2.
    Negative lag: series1 lags series2.
    """
    lags = range(-max_lag, max_lag + 1)
    correlations = []
    for lag in lags:
        if lag < 0:
            corr = series1.iloc[:lag].corr(series2.iloc[-lag:])
        elif lag > 0:
            corr = series1.iloc[lag:].corr(series2.iloc[:-lag])
        else:
            corr = series1.corr(series2)
        correlations.append(corr)
    best_idx = int(np.nanargmax(np.abs(correlations)))
    return lags[best_idx], correlations[best_idx]

def sector_lead_lag_matrix(
    sectors: List[str] = sector_etfs,
    timeframe: str = 'daily',
    max_lag: int = 10
) -> pd.DataFrame:
    """
    Compute lead-lag matrix for all sector pairs.
    Returns a DataFrame: rows=leaders, cols=laggards, values=best lag (positive: row leads col).
    """
    idx = pd.Index(sectors)
    results = pd.DataFrame(index=idx, columns=idx)
    returns = {}
    for sector in sectors:
        update_data(sector)
        # Use returns, not cumulative, for lead-lag
        df = get_cumulative_returns(sector, timeframe)
        returns[sector] = df.iloc[:, 0].pct_change().dropna()
    for leader in sectors:
        for laggard in sectors:
            if leader == laggard:
                results.loc[leader, laggard] = 0
            else:
                lag, corr = cross_correlation_lead_lag(returns[leader], returns[laggard], max_lag)
                results.loc[leader, laggard] = lag
    return results

def granger_lead_lag_matrix(
    sectors: List[str] = sector_etfs,
    timeframe: str = 'daily',
    max_lag: int = 10,
    test: str = 'ssr_chi2test'
) -> pd.DataFrame:
    """
    Returns a DataFrame: rows=leaders, cols=laggards, values=(min_pvalue, best_lag)
    """
    idx = pd.Index(sectors)
    results = pd.DataFrame(index=idx, columns=idx, dtype=object)
    for sector in sectors:
        update_data(sector)
    returns = {sector: get_cumulative_returns(sector, timeframe).iloc[:, 0].pct_change().dropna() for sector in sectors}
    for leader in sectors:
        for laggard in sectors:
            if leader == laggard:
                results.loc[leader, laggard] = (np.nan, 0)
                continue
            # Align series
            df = pd.concat([returns[laggard], returns[leader]], axis=1, join='inner')
            df.columns = ['laggard', 'leader']
            try:
                test_result = grangercausalitytests(df, maxlag=max_lag)
                # Find lag with minimum p-value
                min_p = 1.0
                best_lag = 0
                for lag in range(1, max_lag+1):
                    pval = test_result[lag][0][test][1]
                    if pval < min_p:
                        min_p = pval
                        best_lag = lag
                results.loc[leader, laggard] = (min_p, best_lag)
            except Exception as e:
                results.loc[leader, laggard] = (np.nan, 0)
    return results

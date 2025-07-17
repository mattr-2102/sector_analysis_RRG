import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.process.returns import get_cumulative_returns
from src.fetch.price_data import fetch
from src.process.relative_strength import get_relative_strength
from src.process.rs_momentum import get_relative_strength_momentum
from src.process.rank import rank_relative_strength, rank_relative_strength_momentum
from src.graphing.graphs import plot_volatility_heatmap, plot_granger_lead_lag_matrix, plot_sector_lead_lag_matrix, plot_relative_strength, plot_sector_relative_strength, plot_relative_strength_momentum, plot_sector_relative_strength_momentum, plot_rrg
from config.helper import get_sector_config, get_sector_tickers
from src.process.rank import rank_volatility
from src.process.lead_lag import cross_correlation_lead_lag, sector_lead_lag_matrix

config = get_sector_config()
sector = 'XLU'
numgrab = 10
sector_holdings = get_sector_tickers(sector=sector, limit=numgrab)

def main():
    # print("Beginning to fetch data...")
    # fetch()
    # print("Data fetch processes complete.")
    
    # print(get_relative_strength(target='XLK', benchmark='SPY', lookback_days=30))
    # print(get_relative_strength(target='XLK', benchmark='SPY', lookback_days=30, timeframe='weekly'))
    # print(get_cumulative_returns(ticker='AAPL', timeframe='weekly', lookback_days=20))

    # plot_relative_strength(target='NVDA', benchmark='SPY', timeframe='daily')
    # rank_relative_strength(lookback_days=30)
    plot_sector_relative_strength(tickers= sector_holdings, benchmark=sector, lookback_days=30, timeframe='daily')
    #print(get_relative_strength_momentum(target='XLK', benchmark='SPY', lookback_days=30))
    
    # rank_relative_strength_momentum(lookback_days=30)
    # plot_relative_strength_momentum(target='XLK')
    plot_sector_relative_strength_momentum(tickers= sector_holdings, benchmark=sector, lookback_days=30, timeframe='daily')
    
    lookback = 30
    momentum = 5
    timeframe = 'daily'
    plot_rrg(lookback_days=lookback, momentum_window=momentum, timeframe=timeframe)    
    plot_rrg(tickers=sector_holdings, benchmark=sector, lookback_days=lookback, momentum_window=momentum, timeframe=timeframe)    
    plot_volatility_heatmap(tickers=sector_holdings)
    
    # plot_rrg(lookback_days=30, momentum_window=momentum, timeframe=timeframe)
    # plot_rrg(lookback_days=10, momentum_window=momentum, timeframe=timeframe)
    # rank_relative_strength(lookback_days=lookback, timeframe=timeframe)
    # rank_relative_strength_momentum(lookback_days=lookback, momentum_window=momentum, timeframe=timeframe)
    
    # plot_sector_lead_lag_matrix(timeframe='weekly', max_lag=3, show=True)
    # plot_granger_lead_lag_matrix(show=True, timeframe='daily', max_lag=8)
    # plot_granger_lead_lag_matrix(show=True, timeframe='weekly', max_lag=3)
    
    # df = rank_volatility()
    # plot_volatility_heatmap()
    # fetch("AAPL")
    
    
    
    
    
    

if __name__ == "__main__":
    main()
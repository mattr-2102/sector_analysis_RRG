import pandas as pd
from typing import Optional
from src.process.returns import get_cumulative_returns
from src.fetch.update_data import update_data

def get_relative_strength(target: str, benchmark: str, lookback_days: Optional[int] = None, normalize: bool = True, timeframe: str = 'daily') -> pd.Series:
    update_data(target)
    update_data(benchmark)
    target_cum = get_cumulative_returns(target, timeframe)
    benchmark_cum = get_cumulative_returns(benchmark, timeframe)

    # Ensure both series have proper names for identification
    target_cum.name = f"{target}_target"
    benchmark_cum.name = f"{benchmark}_benchmark"
    
    # Use concat with outer join to preserve all dates, then forward fill to handle missing values
    # This ensures we don't lose data due to different trading calendars
    aligned = pd.concat([target_cum, benchmark_cum], axis=1, join='outer')
    
    # Forward fill any missing values (this handles cases where one ticker trades on a day the other doesn't)
    aligned = aligned.ffill()
    
    # Drop any rows where we still have NaN values (should be minimal after forward fill)
    aligned = aligned.dropna()
    
    # Validate that we have data and benchmark values are non-zero
    if aligned.empty:
        raise ValueError(f"No aligned data available for {target} vs {benchmark}")
    
    if (aligned.iloc[:, 1] <= 0).any():
        raise ValueError(f"Benchmark {benchmark} contains zero or negative values, which would cause division errors")

    if lookback_days is not None:
        aligned = aligned.tail(lookback_days + 1)

    rs = aligned.iloc[:, 0] / aligned.iloc[:, 1]
    rs.name = f"{target}_vs_{benchmark}_RS"

    if normalize:
        rs = rs / rs.iloc[0]

    return rs

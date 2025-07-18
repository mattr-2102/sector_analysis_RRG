import pandas as pd
from typing import Optional
from src.process.relative_strength import get_relative_strength
from scipy.stats import linregress
from src.fetch.update_data import update_data


def get_relative_strength_momentum(target: str, benchmark: str, lookback_days: int = 30, momentum_window: Optional[int] = 5, normalize: bool = True, method: str = "slope", return_series: bool = False, timeframe: str = 'daily') -> float:
    update_data(target)
    update_data(benchmark)
    rs_series = get_relative_strength(
        target=target,
        benchmark=benchmark,
        lookback_days=lookback_days,
        normalize=normalize,
        timeframe=timeframe
    )

    if rs_series.empty or len(rs_series) < momentum_window:
        raise ValueError(f"Insufficient RS data for {target} vs {benchmark}")

    # Select the momentum window (tail)
    if momentum_window is not None:
        if len(rs_series) < momentum_window:
            raise ValueError("Momentum window exceeds available RS data")
        
    if method == "slope":
        if return_series:
            # Compute rolling slope for each tail segment
            momentum_vals = []
            for t in range(len(rs_series) - momentum_window + 1):
                window = rs_series.iloc[t:t + momentum_window]
                x = list(range(momentum_window))
                y = window.values
                slope, *_ = linregress(x, y)
                momentum_vals.append(slope)
            return momentum_vals

        else:
            x = range(momentum_window)
            y = rs_series.tail(momentum_window).values
            slope, *_ = linregress(x, y)
            return slope

    elif method == "pct_change":
        if return_series:
            raise NotImplementedError("Rolling percent change not yet implemented for series mode.")
        return (rs_series.iloc[-1] / rs_series.iloc[0]) - 1

    else:
        raise ValueError(f"Unsupported method '{method}'. Use 'slope' or 'pct_change'.")

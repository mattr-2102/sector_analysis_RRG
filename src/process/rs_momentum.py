import pandas as pd
from typing import Optional
from src.process.relative_strength import get_relative_strength
from scipy.stats import linregress


def get_relative_strength_momentum(target: str, benchmark: str, lookback_days: int = 30, momentum_window: Optional[int] = None, normalize: bool = True, method: str = "slope") -> float:
    rs_series = get_relative_strength(
        target=target,
        benchmark=benchmark,
        lookback_days=lookback_days,
        normalize=normalize
    )

    if rs_series.empty or len(rs_series) < 2:
        raise ValueError(f"Insufficient RS data for {target} vs {benchmark}")

    # Select the momentum window (tail)
    if momentum_window is not None:
        if momentum_window >= len(rs_series):
            raise ValueError("Momentum window exceeds available RS data")
        rs_series = rs_series.tail(momentum_window)
        
    if method == "slope":
        # Use linear regression slope
        x = range(len(rs_series))
        y = rs_series.values
        slope, _, _, _, _ = linregress(x, y)
        return slope

    elif method == "pct_change":
        # Use percent change over lookback window
        return (rs_series.iloc[-1] / rs_series.iloc[0]) - 1

    else:
        raise ValueError(f"Unsupported method '{method}'. Use 'slope' or 'pct_change'.")

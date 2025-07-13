import pandas as pd
from typing import Optional
from src.process.returns import get_cumulative_returns

def get_relative_strength(target: str, benchmark: str, lookback_days: Optional[int] = None, normalize: bool = True) -> pd.Series:
    target_cum = get_cumulative_returns(target)
    benchmark_cum = get_cumulative_returns(benchmark)

    aligned = target_cum.join(benchmark_cum, lsuffix='_target', rsuffix='_benchmark', how='inner')

    if lookback_days is not None:
        aligned = aligned.tail(lookback_days + 1)

    rs = aligned.iloc[:, 0] / aligned.iloc[:, 1]
    rs.name = f"{target}_vs_{benchmark}_RS"

    if normalize:
        rs = rs / rs.iloc[0]

    return rs

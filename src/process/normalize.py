import pandas as pd
from typing import Optional

def get_cumulative_returns(daily_pct_change_df: pd.DataFrame, lookback_days: Optional[int] = None) -> pd.DataFrame:

    # Validate input
    if not isinstance(daily_pct_change_df, pd.DataFrame):
        raise ValueError("Input must be a pandas DataFrame")

    df = daily_pct_change_df.copy()

    # Apply cumulative product
    cumulative = (1 + df).cumprod()

    if lookback_days is not None:
        if lookback_days >= len(cumulative):
            raise ValueError("Lookback period exceeds available data length.")

        # Determine the rebase point (N days before most recent date)
        rebased_start = cumulative.iloc[-lookback_days - 1]
        cumulative = cumulative.divide(rebased_start, axis=1)

    return cumulative
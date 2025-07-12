import sys
import os
import pandas as pd

from config.helper import get_data_file

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.fetch.price_data import fetch
from src.process.normalize import get_cumulative_returns

def main():
    print("Beginning to fetch data...")
    fetch()
    print("Data fetch processes complete.")
    # SPY = pd.read_csv(get_data_file("XLC_daily.csv"), index_col=0, parse_dates=True)
    # print(get_cumulative_returns(SPY).head())

if __name__ == "__main__":
    main()
import pandas as pd

def main():
    df = pd.read_parquet('data/XLC_real_raw.parquet')
    print(df.tail())

if __name__ == '__main__':
    main()
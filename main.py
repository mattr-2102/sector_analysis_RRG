import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.fetch.price_data import fetch

def main():
    print("Beginning to fetch data...")
    fetch()
    print("Data fetch processes complete.")

if __name__ == "__main__":
    main()
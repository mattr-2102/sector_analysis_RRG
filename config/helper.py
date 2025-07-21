import os
import yaml
from pathlib import Path
from typing import Optional

# dynamic resolve the project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_data_dir() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "data"

def get_financial_dir() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "data" / "financialdata"

def key(source: str) -> str | None:
    try:
        project_root = Path(__file__).resolve().parents[1]
        config_path = project_root / "config" / "api_keys.yaml"

        with config_path.open("r") as f:
            api_keys = yaml.safe_load(f) or {}

        return api_keys.get(source)
    except:
        print("Error retrieving api key.")

    return None

def get_data_file(filename: str) -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "data" / filename

def get_financial_file(filename: str) -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "data" / "financialdata" / filename

def get_sector_config() -> dict:
    config_path = Path(__file__).resolve().parent / "sectors.yaml"
    with config_path.open("r") as f:
        config = yaml.safe_load(f)
    return config

def get_sector_tickers(sector: str, limit: Optional[int] = None) -> list:
    """
    Get tickers for a specific sector with optional limit
    
    Args:
        sector (str): Sector code (e.g., 'XLE', 'XLF', 'XLK')
        limit (int, optional): Number of first tickers to return. If None, returns all tickers.
    
    Returns:
        list: List of ticker symbols for the sector (limited if specified)
    
    Examples:
        get_sector_tickers('XLE')  # Returns all XLE tickers
        get_sector_tickers('XLE', 3)  # Returns ['XOM', 'CVX', 'COP']
        get_sector_tickers('XLK', 8)  # Returns first 8 XLK tickers
    """
    config = get_sector_config()
    sector_data = config['sector_holdings'].get(sector, [])
    
    # Handle the case where tickers are stored as a comma-separated string
    if isinstance(sector_data, list) and len(sector_data) == 1 and isinstance(sector_data[0], str):
        # Split the comma-separated string and strip whitespace
        tickers = [ticker.strip() for ticker in sector_data[0].split(',')]
    elif isinstance(sector_data, list):
        # If it's already a proper list
        tickers = sector_data
    else:
        tickers = []
    
    if limit is not None:
        return tickers[:limit]
    return tickers

def get_resource(filename: str) -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / "resources" / filename
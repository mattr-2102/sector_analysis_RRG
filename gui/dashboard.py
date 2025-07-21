import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config.helper import get_sector_config, get_data_file
from src.fetch.update_data import update_data

class Dashboard:
    
    def __init__(self):
        self.config = get_sector_config()
        self.benchmark = self.config['benchmark']  # SPY
        self.sectors = self.config['sector_etfs']  # 11 sectors
        self.all_tickers = [self.benchmark] + self.sectors
        
    def get_sector_name(self, ticker: str) -> str:
        """Get the full name for a sector ticker"""
        sector_names = self.config['sector_names']
        return sector_names.get(ticker, ticker)
    
    def get_daily_changes_data(self) -> Tuple[Optional[Dict], str]:
        data = {}
        errors = []
        
        for ticker in self.all_tickers:
            try:
                update_data(ticker)
                # Get the daily data file path
                if ticker in (self.config['synthetic_etfs']):
                    file_path_percent = get_data_file(f"{ticker}_real_raw.parquet")
                    file_path_raw = get_data_file(f"{ticker}_daily.parquet")
                else:
                    file_path_percent = get_data_file(f"{ticker}_daily.parquet")
                    file_path_raw = get_data_file(f"{ticker}_daily_raw.parquet")
                
                # Read the parquet file
                df_percent = pd.read_parquet(file_path_percent)
                df_raw = pd.read_parquet(file_path_raw)
                df_percent = df_percent.sort_values('date')
                df_raw = df_raw.sort_values('date')
                
                if len(df_percent) < 2:
                    errors.append(f"Insufficient data for {ticker}")
                    continue
                
                if len(df_raw) < 2:
                    errors.append(f"Insufficient data for {ticker}")
                    continue
                
                # Get last two days of data
                last_two = df_raw.tail(2)
                current = last_two.iloc[-1]
                previous = last_two.iloc[-2]
                
                # Calculate changes
                change_dollar = current['close'] - previous['close']
                
                data[ticker] = {
                    'last_close': current['close'],
                    'prev_close': previous['close'],
                    'change_dollar': change_dollar,
                    'change_percent': df_percent.tail(1).iloc[-1][f'{ticker}'],
                    'volume': current.get('volume', 0),
                    'name': self.get_sector_name(ticker)
                }
                
            except Exception as e:
                errors.append(f"Error processing {ticker}: {str(e)}")
                continue
        
        # Create status message
        if errors:
            status = f"Errors: {'; '.join(errors[:3])}"  # Show first 3 errors
            if len(errors) > 3:
                status += f" and {len(errors) - 3} more..."
        else:
            status = f"Data loaded successfully - {len(data)} tickers"
            
        return data if data else None, status
    
    def get_table_data(self) -> Tuple[List[List], List[str], str]:
        data, status = self.get_daily_changes_data()
        
        if data is None:
            return [], [], status
        
        # Define headers
        headers = ["Ticker", "Name", "Last Close", "Prev Close", "Change ($)", "Change (%)", "Volume"]
        
        # Create table data
        table_data = []
        for ticker in self.all_tickers:
            if ticker not in data:
                continue
                
            ticker_data = data[ticker]
            
            # Format the row data
            row = [
                ticker,  # Ticker
                ticker_data['name'],  # Name
                f"${ticker_data['last_close']:.2f}",  # Last Close
                f"${ticker_data['prev_close']:.2f}",  # Prev Close
                f"${ticker_data['change_dollar']:+.2f}",  # Change ($)
                f"{ticker_data['change_percent']:+.2f}%",  # Change (%)
                f"{ticker_data['volume']:,}" if ticker_data['volume'] > 0 else "N/A"  # Volume
            ]
            
            table_data.append(row)
        
        return table_data, headers, status
    
    def get_color_data(self) -> Dict[str, Dict[str, str]]:
        data, _ = self.get_daily_changes_data()
        
        if data is None:
            return {}
        
        color_data = {}
        
        for ticker in self.all_tickers:
            if ticker not in data:
                continue
                
            ticker_data = data[ticker]
            
            # Determine colors based on changes
            change_dollar = ticker_data['change_dollar']
            change_percent = ticker_data['change_percent']
            
            # Color codes: 'green', 'red', 'black'
            dollar_color = 'green' if change_dollar > 0 else 'red' if change_dollar < 0 else 'black'
            percent_color = 'green' if change_percent > 0 else 'red' if change_percent < 0 else 'black'
            
            # Special formatting for SPY
            is_spy = ticker == self.benchmark
            
            color_data[ticker] = {
                'dollar_color': dollar_color,
                'percent_color': percent_color,
                'is_spy': is_spy,
                'row_background': 'darkblue' if is_spy else 'normal'
            }
        
        return color_data
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config.helper import get_sector_config, get_financial_file
from src.process.financials import finRatios

class IndividualFinancials:
    def __init__(self):
        self.config = get_sector_config()
    
    def get_financial_ratios(self) -> Tuple[Optional[Dict], str]:
        data = {}
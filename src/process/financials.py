import requests
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from src.fetch.financialdata import fetchfinancials
from config.helper import key, get_financial_file

poly_api_key = key('polygon')
marketcapendpoint = 'https://api.polygon.io/v3/reference/tickers/'
closeendpoint = 'https://api.polygon.io/v2/aggs/ticker/'
    
def finRatios(ticker) -> pd.DataFrame:
    currentdate = datetime.now().date()
    olddate = currentdate - timedelta(days=4)
    tickermcapend =  f"{marketcapendpoint}{ticker}?apiKey={poly_api_key}"
    tickercloseend = f"{closeendpoint}{ticker}/range/1/day/{olddate}/{currentdate}?adjusted=false&sort=desc&apiKey={poly_api_key}"
    
    fetchfinancials(ticker=ticker)
    finpath = get_financial_file(f"{ticker}_financials_raw.parquet")
    rawfindata = pd.read_parquet(finpath)
    
    raw = requests.get(tickermcapend)
    jraw = raw.json()
    
    if jraw.get('status') not in ['OK', 'DELAYED']:
        print(f"Error: API returned status {jraw.get('status')} for {ticker}")
    
    marketcap = jraw['results']['market_cap']
    
    raw = requests.get(tickercloseend)
    jraw = raw.json()
    
    if jraw.get('status') not in ['OK', 'DELAYED']:
        print(f"Error: API returned status {jraw.get('status')} for {ticker}")    
        
    close = jraw['results'][0]['c']
    
    
    # Use the most recent financial record
    fin = rawfindata.iloc[0]

    # Extract values safely
    ni = fin.get('income_statement_net_income_loss')
    rev = fin.get('income_statement_revenues')
    gp = fin.get('income_statement_gross_profit')
    op_inc = fin.get('income_statement_operating_income_loss')
    eq = fin.get('balance_sheet_equity')
    ta = fin.get('balance_sheet_assets')
    tl = fin.get('balance_sheet_liabilities')
    ca = fin.get('balance_sheet_current_assets')
    cl = fin.get('balance_sheet_current_liabilities')
    inv = fin.get('balance_sheet_inventory')
    ldebt = fin.get('balance_sheet_long_term_debt')
    cf = fin.get('cash_flow_statement_net_cash_flow_from_operating_activities_continuing')
    shares = fin.get('income_statement_diluted_average_shares')
    eps = fin.get('income_statement_diluted_earnings_per_share')
    
    print(cf)
    print(shares)

    # Compute ratios
    ratios = {
        'ROE': ni / eq if ni and eq else None,
        'ROA': ni / ta if ni and ta else None,
        'Net Margin': ni / rev if ni and rev else None,
        'Gross Margin': gp / rev if gp and rev else None,
        'Operating Margin': op_inc / rev if op_inc and rev else None,
        'Debt/Equity': tl / eq if tl and eq else None,
        'Current Ratio': ca / cl if ca and cl else None,
        'Quick Ratio': (ca - inv) / cl if ca and inv and cl else None,
        'Long-Term Debt/Equity': ldebt / eq if ldebt and eq else None,
        'Cash Flow / Share': cf / shares if cf and shares else None,
        'EPS (from filing)': eps,
        'Market Cap': marketcap,
        'Price': close,
        'P/E': close / eps if close and eps else None,
        'P/B': marketcap / eq if marketcap and eq else None,
        'P/S': marketcap / rev if marketcap and rev else None,
    }

    df = pd.DataFrame([ratios])
    return df
    
def plot_table(df, title="Financial Ratios"):
    fig, ax = plt.subplots(figsize=(12, 0.5 * len(df.columns)))
    ax.axis('off')
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    ax.set_title(title, fontweight='bold')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    ticker = 'NVDA'
    
    df1 = finRatios(ticker)
    plot_table(df1)

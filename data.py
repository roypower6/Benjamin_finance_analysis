import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from io import StringIO

@st.cache_data
def load_dow_tickers():
    """
    Wikipedia에서 Dow Jones Industrial Average (DJIA) 종목 리스트를 가져옵니다.
    """
    url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        # Use simple requests to avoid some blocking, passed to read_html or direct
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        
        # Find table with 'Symbol' or 'Ticker'
        for df in tables:
            if 'Symbol' in df.columns and 'Company' in df.columns:
                return df, None
            if 'Ticker' in df.columns:
                df = df.rename(columns={'Ticker': 'Symbol'})
                return df, None
                
        return None, "Table not found"
    except Exception as e:
        return None, str(e)

@st.cache_data
def load_nasdaq_tickers():
    """
    Wikipedia에서 NASDAQ-100 종목 리스트를 가져옵니다.
    """
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        
        for df in tables:
            # Check for 'Ticker' or 'Symbol'
            if 'Ticker' in df.columns:
                 df = df.rename(columns={'Ticker': 'Symbol'})
                 return df, None
            if 'Symbol' in df.columns:
                 return df, None
                 
        return None, "Table not found"
    except Exception as e:
        return None, str(e)

@st.cache_data
def load_sp500_tickers():
    """
    Wikipedia에서 S&P 500 종목 리스트를 가져옵니다.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]
        return df, None
    except Exception as e:
        return None, str(e)

@st.cache_data
def load_stock_data(symbol, period, interval):
    """
    yfinance를 사용하여 주식 데이터와 정보를 가져옵니다.
    """
    try:
        ticker = yf.Ticker(symbol)
        history = ticker.history(period=period, interval=interval)
        info = ticker.info
        financials = ticker.financials
        quarterly_financials = ticker.quarterly_financials
        balance_sheet = ticker.balance_sheet
        quarterly_balance_sheet = ticker.quarterly_balance_sheet
        cashflow = ticker.cashflow
        quarterly_cashflow = ticker.quarterly_cashflow
        return history, info, financials, quarterly_financials, balance_sheet, quarterly_balance_sheet, cashflow, quarterly_cashflow
    except Exception as e:
        return None, None, None, None, None, None, None, None



@st.cache_data
def load_market_data(tickers):
    """
    S&P 500 종목들의 현재가 정보를 일괄 다운로드하여 등락률과 거래량을 계산합니다.
    """
    try:
        # 500개 이상이므로 배치 처리는 생략하고 한 번에 시도
        data = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False)
        
        market_data = []
        for ticker in tickers:
            try:
                hist = data[ticker]
                if not hist.empty and len(hist) >= 2:
                    current_close = hist['Close'].iloc[-1]
                    prev_close = hist['Close'].iloc[-2]
                    volume = hist['Volume'].iloc[-1]
                    traded_value = current_close * volume
                    
                    pct_change = ((current_close - prev_close) / prev_close) * 100
                    
                    market_data.append({
                        'Symbol': ticker,
                        'Price': current_close,
                        'PctChange': pct_change,
                        'Volume': volume,
                        'TradedValue': traded_value
                    })
            except Exception:
                continue
                
        return pd.DataFrame(market_data)
    except Exception as e:
        return None

@st.cache_data(ttl=3600) # Cache for 1 hour
def load_indices_data():
    """
    주요 시장 지수 (DOW, NASDAQ, S&P 500, Russell 2000) 데이터를 가져옵니다.
    """
    indices = {
        "DOW": "^DJI",
        "NASDAQ": "^IXIC",
        "S&P 500": "^GSPC",
        "RUSSELL 2000": "^RUT"
    }
    
    results = {}
    
    try:
        # Batch download attempt (5d to ensure we have previous close)
        tickers = list(indices.values())
        data = yf.download(tickers, period="5d", interval="1d", group_by='ticker', progress=False)
        
        for name, symbol in indices.items():
            try:
                if len(tickers) > 1:
                    hist = data[symbol]
                else:
                    hist = data
                
                if not hist.empty:
                    # Clean up
                    hist = hist.dropna()
                    
                    if len(hist) >= 2:
                        last_close = hist['Close'].iloc[-1]
                        prev_close = hist['Close'].iloc[-2]
                        change = last_close - prev_close
                        pct_change = (change / prev_close) * 100
                        
                        results[name] = {
                            "symbol": symbol,
                            "price": last_close,
                            "change": change,
                            "pct_change": pct_change
                        }
            except Exception:
                continue
                
        return results
    except Exception as e:
        return {}

import requests

def fetch_fear_and_greed_index():
    """
    Fetches the Fear and Greed Index from CNN (or alternative).
    Returns a dictionary with 'score', 'rating', and 'timestamp'.
    """
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Structure: {'fear_and_greed': {...}, 'market_momentum_sp500': {...}, ...}
        fg_data = data.get('fear_and_greed', {})
        
        result = {
            'score': fg_data.get('score'),
            'rating': fg_data.get('rating'),
            'timestamp': fg_data.get('timestamp'),
            'previous_close': fg_data.get('previous_close'),
            'previous_1_week': fg_data.get('previous_1_week'),
            'previous_1_month': fg_data.get('previous_1_month'),
            'previous_1_year': fg_data.get('previous_1_year'),
            # Sub-indicators
            'market_momentum': data.get('market_momentum_sp500', {}),
            'stock_price_strength': data.get('stock_price_strength', {}),
            'stock_price_breadth': data.get('stock_price_breadth', {}),
            'put_call_options': data.get('put_call_options', {}),
            'market_volatility': data.get('market_volatility_vix', {}),
            'safe_haven_demand': data.get('safe_haven_demand', {}),
            'junk_bond_demand': data.get('junk_bond_demand', {})
        }
        return result
    except Exception as e:
        return None

@st.cache_data
def get_all_tickers_dict():
    """
    S&P 500, DOW, NASDAQ 100 종목을 통합하여 Dictionary로 반환합니다.
    Key: "Ticker | Company Name" (검색용)
    Value: Ticker (실제 데이터 로드용)
    """
    tickers_map = {}
    
    # helper to process df
    def process(df, source):
        if df is not None:
            for _, row in df.iterrows():
                symbol = row.get('Symbol')
                name = row.get('Security') or row.get('Company') or row.get('Name') or symbol
                
                if symbol and name:
                    # Clean symbol
                    symbol = str(symbol).replace('.', '-')
                    search_key = f"{symbol} | {name}"
                    tickers_map[search_key] = symbol

    sp500, _ = load_sp500_tickers()
    process(sp500, "S&P 500")
    
    dow, _ = load_dow_tickers()
    process(dow, "DOW")
    
    nasdaq, _ = load_nasdaq_tickers()
    process(nasdaq, "NASDAQ")
    
    return tickers_map

@st.cache_data(ttl=3600) # Cache for 1 hr
def load_insider_trading(symbol):
    """
    Fetch insider trading data using yfinance.
    """
    try:
        ticker = yf.Ticker(symbol)
        insider = ticker.insider_transactions
        if insider is not None and not insider.empty:
            # Sort by Date usually comes sorted but just in case
            return insider
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=300) # Cache for 5 mins
@st.cache_data(ttl=300) # Cache for 5 mins
def load_market_ticker_data():
    """
    Fetch data for Market Ticker Marquee.
    Refined: Crypto, Commodities (Gold, Silver, WTI), Treasury Yields (5, 10, 30Y).
    Note: Yahoo ^TNX value 40.0 = 4.0%.
    """
    # Define Tickers and their types
    # Type: 'crypto' (24h logic roughly), 'commodity' (Price), 'yield' (Index value/10 = %)
    # Note: 2Y Yield is hard to get reliably on Yahoo (^IRX is 3mo). We will use 5, 10, 30.
    ticker_config = [
        {'symbol': 'BTC-USD', 'name': 'Bitcoin', 'type': 'crypto'},
        {'symbol': 'ETH-USD', 'name': 'Ethereum', 'type': 'crypto'},
        {'symbol': 'GC=F',    'name': 'Gold',    'type': 'commodity'},
        {'symbol': 'SI=F',    'name': 'Silver',  'type': 'commodity'},
        {'symbol': 'CL=F',    'name': 'WTI Crude', 'type': 'commodity'},
        {'symbol': '^FVX',    'name': 'US 5Y Yield', 'type': 'yield'},
        {'symbol': '^TNX',    'name': 'US 10Y Yield', 'type': 'yield'},
        {'symbol': '^TYX',    'name': 'US 30Y Yield', 'type': 'yield'},
    ]
    
    symbols = [t['symbol'] for t in ticker_config]
    results = []
    
    try:
        # Batch download
        data = yf.download(symbols, period="2d", progress=False)
        
        if data is None or data.empty:
            return []
            
        for conf in ticker_config:
            symbol = conf['symbol']
            try:
                # Extract Data
                if isinstance(data.columns, pd.MultiIndex):
                     df_sym = data.xs(symbol, level=1, axis=1)
                else:
                     if symbol in data.columns:
                         df_sym = data[[symbol]] # Wrong if single level has open/close... 
                         # Actually if single ticker, columns are Open, Low..
                         # If multi ticker, columns are (Price, Ticker). 
                         # However, if we download multiple, it's (Price, Ticker).
                         # If one fails, it might be tricky.
                         pass
                     else:
                         # Fallback for single or weird structure
                         df_sym = data
                
                if df_sym.empty: continue
                
                closes = df_sym['Close'].dropna()
                if len(closes) >= 1:
                    price = closes.iloc[-1]
                    prev_price = closes.iloc[-2] if len(closes) >= 2 else price
                    
                    change = price - prev_price
                    change_pct = (change / prev_price) * 100 if prev_price != 0 else 0
                    
                    # Special Handling for Yields
                    # Yahoo Yield Indices like ^TNX are in basis points/10 (e.g. 42.5 = 4.25%)
                    # So 'Price' for display should be divided by 10.
                    # Change is also in basis points.
                    
                    display_price = price
                    suffix = ""
                    prefix = "$"
                    
                    if conf['type'] == 'yield':
                        # Special Handling for Yields
                        # Yahoo Indexes (e.g. ^TNX) traditionally are 10x (e.g. 42.0 = 4.2%)
                        # BUT sometimes might be raw.
                        # Heuristic: If value > 15 (unlikely to be 15% yield soon), divide by 10.
                        # If value <= 15, assume it is already percentage (e.g. 4.17)
                        
                        if price > 15:
                             display_price = price / 10.0
                        else:
                             display_price = price
                             
                        prefix = ""
                        suffix = "%"
                        
                    elif conf['type'] == 'crypto':
                        # Crypto behaves like normal price
                        pass
                        
                    results.append({
                        'symbol': symbol,
                        'name': conf['name'],
                        'price': display_price,
                        'change': change,
                        'change_pct': change_pct,
                        'type': conf['type'],
                        'prefix': prefix,
                        'suffix': suffix
                    })
            except Exception as e:
                continue
                
        return results
    except Exception as e:
        return []

@st.cache_data(ttl=3600)
def load_ownership_data(symbol):
    """
    Fetch ownership data: Major Holders and Institutional Holders.
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # 1. Major Holders (Breakdown)
        # Returns DataFrame with 0 (Percent), 1 (Description) usually
        major = ticker.major_holders
        
        # 2. Institutional Holders (Top Holders)
        inst = ticker.institutional_holders
        
        return {
            'major': major,
            'institutional': inst
        }
    except Exception as e:
        return None

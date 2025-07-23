import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

def get_market_symbol(symbol, market='USA'):
    """Convert symbol to market-specific format"""
    if market == 'USA':
        return symbol
    elif market == 'India':
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            return f"{symbol}.NS"  # NSE by default
        return symbol
    return symbol

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_info(symbol, market='USA'):
    """Get detailed stock information"""
    try:
        market_symbol = get_market_symbol(symbol, market)
        ticker = yf.Ticker(market_symbol)
        info = ticker.info
        
        return {
            'symbol': symbol,
            'market_symbol': market_symbol,
            'name': info.get('longName', symbol),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'market_cap': info.get('marketCap', 0),
            'price': info.get('currentPrice', 0),
            'previous_close': info.get('previousClose', 0),
            'day_change': info.get('currentPrice', 0) - info.get('previousClose', 0),
            'day_change_percent': ((info.get('currentPrice', 0) - info.get('previousClose', 0)) / info.get('previousClose', 1)) * 100,
            'volume': info.get('volume', 0),
            'avg_volume': info.get('averageVolume', 0),
            '52_week_high': info.get('fiftyTwoWeekHigh', 0),
            '52_week_low': info.get('fiftyTwoWeekLow', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 0),
            'country': info.get('country', 'Unknown'),
            'currency': info.get('currency', 'USD'),
            'market': market
        }
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_stock_price(symbol, market='USA'):
    """Get current stock price"""
    try:
        market_symbol = get_market_symbol(symbol, market)
        ticker = yf.Ticker(market_symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_history(symbol, period="1y", market='USA'):
    """Get stock price history"""
    try:
        market_symbol = get_market_symbol(symbol, market)
        ticker = yf.Ticker(market_symbol)
        hist = ticker.history(period=period)
        return hist
    except Exception as e:
        st.error(f"Error fetching history for {symbol}: {str(e)}")
        return pd.DataFrame()

def get_market_data():
    """Get major market indices data"""
    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "DOW": "^DJI",
        "Russell 2000": "^RUT"
    }
    
    market_data = {}
    for name, symbol in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                change = current - previous
                change_pct = (change / previous) * 100
                
                market_data[name] = {
                    'symbol': symbol,
                    'current': current,
                    'change': change,
                    'change_percent': change_pct
                }
        except Exception as e:
            continue
    
    return market_data

def categorize_stock(stock_info):
    """Categorize stock based on market cap and other factors"""
    if not stock_info or 'market_cap' not in stock_info:
        return 'Unknown'
    
    market_cap = stock_info['market_cap']
    
    if market_cap >= 200_000_000_000:  # $200B+
        return 'Mega Cap'
    elif market_cap >= 10_000_000_000:  # $10B - $200B
        return 'Large Cap'
    elif market_cap >= 2_000_000_000:   # $2B - $10B
        return 'Mid Cap'
    elif market_cap >= 300_000_000:     # $300M - $2B
        return 'Small Cap'
    elif market_cap >= 50_000_000:      # $50M - $300M
        return 'Micro Cap'
    else:
        return 'Nano Cap'

def get_sector_performance():
    """Get sector performance data"""
    sector_etfs = {
        'Technology': 'XLK',
        'Healthcare': 'XLV',
        'Financials': 'XLF',
        'Consumer Discretionary': 'XLY',
        'Consumer Staples': 'XLP',
        'Energy': 'XLE',
        'Industrials': 'XLI',
        'Materials': 'XLB',
        'Real Estate': 'XLRE',
        'Utilities': 'XLU',
        'Communication': 'XLC'
    }
    
    sector_data = {}
    for sector, etf in sector_etfs.items():
        try:
            ticker = yf.Ticker(etf)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                change_pct = ((current - previous) / previous) * 100
                
                sector_data[sector] = {
                    'etf': etf,
                    'change_percent': change_pct
                }
        except Exception as e:
            continue
    
    return sector_data

def search_stocks(query, limit=10):
    """Search for stocks based on query"""
    # This is a simple implementation - in a real app you might use a more sophisticated search
    common_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'DIS', 'BABA',
        'V', 'JPM', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'BAC', 'ADBE', 'CRM', 'PYPL',
        'INTC', 'VZ', 'KO', 'PFE', 'PEP', 'T', 'CSCO', 'XOM', 'ABT', 'TMO', 'ACN', 'CVX',
        'DHR', 'COST', 'TXN', 'AVGO', 'LLY', 'NEE', 'MDT', 'BMY', 'QCOM', 'PM', 'LOW'
    ]
    
    query = query.upper()
    matching_stocks = [stock for stock in common_stocks if query in stock]
    
    results = []
    for symbol in matching_stocks[:limit]:
        try:
            info = get_stock_info(symbol)
            if info:
                results.append(info)
        except:
            continue
    
    return results

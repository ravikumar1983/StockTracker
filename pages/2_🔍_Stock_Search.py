import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
from utils.stock_data import get_stock_info, get_stock_history, get_market_symbol
from utils.data_persistence import save_watchlist

st.set_page_config(page_title="Stock Search", page_icon="🔍", layout="wide")

def main():
    # Market selection in top right corner
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col1:
        st.title("🔍 Stock Search & Analysis")
    
    with col3:
        # Initialize market selection in session state
        if 'selected_market' not in st.session_state:
            st.session_state.selected_market = 'USA'
        
        market = st.selectbox(
            "Market",
            options=['USA', 'India'],
            index=['USA', 'India'].index(st.session_state.selected_market),
            key='search_market_selector'
        )
        
        # Update session state if market changed
        if market != st.session_state.selected_market:
            st.session_state.selected_market = market
            st.rerun()
    
    # Initialize session state
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []
    
    # Search section
    st.subheader("Search Stocks")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Show market-specific placeholder
        if st.session_state.selected_market == 'USA':
            placeholder = "AAPL, Apple, Tesla, TSLA"
        else:
            placeholder = "RELIANCE, TCS, HDFC, ITC"
        
        st.info(f"Selected Market: **{st.session_state.selected_market}**")
        search_query = st.text_input("Enter stock symbol or company name", placeholder=placeholder)
    
    with col2:
        search_type = st.selectbox("Search Type", ["Symbol"])
    
    # Search results
    if search_query:
        # Direct symbol lookup using selected market
        symbol = search_query.upper().strip()
        stock_info = get_stock_info(symbol, st.session_state.selected_market)
        
        if stock_info:
            display_stock_details(stock_info)
        else:
            st.error(f"Stock symbol '{symbol}' not found in {st.session_state.selected_market} market")
    
    # Market overview
    st.markdown("---")
    st.subheader("📊 Market Overview")
    
    # Sector performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Major Indices**")
        
        indices = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "DOW": "^DJI",
            "Russell 2000": "^RUT"
        }
        
        index_data = []
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2]
                    change = current - previous
                    change_pct = (change / previous) * 100
                    
                    index_data.append({
                        "Index": name,
                        "Value": f"{current:.2f}",
                        "Change": f"{change:+.2f}",
                        "Change %": f"{change_pct:+.2f}%"
                    })
            except:
                continue
        
        if index_data:
            df_indices = pd.DataFrame(index_data)
            st.dataframe(df_indices, use_container_width=True, hide_index=True)
    
    with col2:
        st.write("**Popular Stocks**")
        
        # Market-specific popular stocks
        if st.session_state.selected_market == 'USA':
            popular_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META']
        else:
            popular_stocks = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ITC', 'HDFC']
        
        popular_data = []
        
        for symbol in popular_stocks:
            try:
                stock_info = get_stock_info(symbol, st.session_state.selected_market)
                if stock_info:
                    popular_data.append({
                        "Symbol": symbol,
                        "Price": f"${stock_info['price']:.2f}",
                        "Change %": f"{stock_info['day_change_percent']:+.2f}%"
                    })
            except:
                continue
        
        if popular_data:
            df_popular = pd.DataFrame(popular_data)
            st.dataframe(df_popular, use_container_width=True, hide_index=True)

def display_stock_details(stock_info):
    """Display detailed stock information"""
    symbol = stock_info['symbol']
    
    # Header with basic info
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"{stock_info['name']} ({symbol})")
        st.write(f"**Sector:** {stock_info['sector']}")
        st.write(f"**Industry:** {stock_info['industry']}")
        st.write(f"**Country:** {stock_info['country']}")
    
    with col2:
        # Add to watchlist button
        if st.button(f"Add {symbol} to Watchlist"):
            if symbol not in st.session_state.watchlist:
                st.session_state.watchlist.append(symbol)
                save_watchlist(st.session_state.watchlist)
                st.success(f"Added {symbol} to watchlist")
            else:
                st.info(f"{symbol} already in watchlist")
    
    with col3:
        # Determine market cap category
        market_cap = stock_info.get('market_cap', 0)
        if market_cap >= 200_000_000_000:
            category = 'Mega Cap'
        elif market_cap >= 10_000_000_000:
            category = 'Large Cap'
        elif market_cap >= 2_000_000_000:
            category = 'Mid Cap'
        elif market_cap >= 300_000_000:
            category = 'Small Cap'
        else:
            category = 'Micro Cap'
        st.metric("Category", category)
    
    # Key metrics
    st.subheader("Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Price", 
            f"${stock_info['price']:.2f}",
            f"{stock_info['day_change']:+.2f} ({stock_info['day_change_percent']:+.2f}%)"
        )
    
    with col2:
        st.metric("Market Cap", f"${stock_info['market_cap']:,.0f}")
    
    with col3:
        st.metric("Volume", f"{stock_info['volume']:,}")
        st.metric("Avg Volume", f"{stock_info['avg_volume']:,}")
    
    with col4:
        st.metric("52W High", f"${stock_info['52_week_high']:.2f}")
        st.metric("52W Low", f"${stock_info['52_week_low']:.2f}")
    
    # Additional metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if stock_info['pe_ratio']:
            st.metric("P/E Ratio", f"{stock_info['pe_ratio']:.2f}")
        else:
            st.metric("P/E Ratio", "N/A")
    
    with col2:
        if stock_info['dividend_yield']:
            st.metric("Dividend Yield", f"{stock_info['dividend_yield']:.2f}%")
        else:
            st.metric("Dividend Yield", "N/A")
    
    with col3:
        if stock_info['beta']:
            st.metric("Beta", f"{stock_info['beta']:.2f}")
        else:
            st.metric("Beta", "N/A")
    
    with col4:
        st.metric("Currency", stock_info['currency'])
    
    # Price chart
    st.subheader("Price Chart")
    
    chart_period = st.selectbox(
        "Select Time Period", 
        ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"],
        index=4  # Default to 6mo
    )
    
    hist_data = get_stock_history(symbol, period=chart_period, market=st.session_state.selected_market)
    
    if not hist_data.empty:
        # Create candlestick chart
        fig = go.Figure(data=go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name=symbol
        ))
        
        fig.update_layout(
            title=f"{symbol} Stock Price",
            yaxis_title="Price ($)",
            xaxis_title="Date",
            height=500,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Volume chart
        fig_volume = go.Figure()
        fig_volume.add_trace(go.Bar(
            x=hist_data.index,
            y=hist_data['Volume'],
            name='Volume',
            marker_color='lightblue'
        ))
        
        fig_volume.update_layout(
            title=f"{symbol} Trading Volume",
            yaxis_title="Volume",
            xaxis_title="Date",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig_volume, use_container_width=True)
    else:
        st.error("Unable to fetch price history")
    
    # Performance analysis
    st.subheader("Performance Analysis")
    
    if not hist_data.empty and len(hist_data) > 1:
        # Calculate performance metrics
        returns = hist_data['Close'].pct_change().dropna()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            period_return = ((hist_data['Close'].iloc[-1] / hist_data['Close'].iloc[0]) - 1) * 100
            st.metric(f"{chart_period.upper()} Return", f"{period_return:+.2f}%")
        
        with col2:
            volatility = returns.std() * (252 ** 0.5) * 100  # Annualized volatility
            st.metric("Volatility (Annual)", f"{volatility:.2f}%")
        
        with col3:
            avg_volume = hist_data['Volume'].mean()
            st.metric("Avg Volume", f"{avg_volume:,.0f}")
        
        # Returns distribution
        st.subheader("Daily Returns Distribution")
        
        fig_hist = px.histogram(
            returns, 
            title=f"{symbol} Daily Returns Distribution",
            labels={'value': 'Daily Return', 'count': 'Frequency'}
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)

if __name__ == "__main__":
    main()

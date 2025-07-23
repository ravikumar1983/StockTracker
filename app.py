import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
from utils.stock_data import get_stock_info, get_stock_price, get_market_data
from utils.portfolio import calculate_portfolio_value, get_portfolio_performance
from utils.data_persistence import load_portfolio, load_watchlist, load_transactions
from utils.trading_rules import check_trading_rules

# Page configuration
st.set_page_config(
    page_title="Stock Trading Automation Tool",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = load_portfolio()
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_watchlist()
if 'transactions' not in st.session_state:
    st.session_state.transactions = load_transactions()
if 'trading_rules' not in st.session_state:
    st.session_state.trading_rules = []

def main():
    st.title("📈 Stock Trading Automation & Portfolio Management")
    
    # Initialize market selection
    if 'selected_market' not in st.session_state:
        st.session_state.selected_market = 'USA'
    
    st.markdown("---")
    
    # Sidebar for quick navigation
    with st.sidebar:
        st.header("Quick Actions")
        
        # Quick portfolio stats
        if st.session_state.portfolio:
            total_value = calculate_portfolio_value(st.session_state.portfolio, st.session_state.selected_market)
            st.metric("Portfolio Value", f"${total_value:,.2f}")
            
            # Today's change
            change = get_portfolio_performance(st.session_state.portfolio, period='1d', market=st.session_state.selected_market)
            if change:
                st.metric("Today's Change", f"${change['change']:,.2f}", f"{change['change_percent']:.2f}%")
        
        st.markdown("---")
        
        # Quick stock lookup
        st.subheader("Quick Stock Lookup")
        placeholder = "AAPL" if st.session_state.selected_market == 'USA' else "RELIANCE"
        quick_symbol = st.text_input("Enter Symbol", placeholder=placeholder, key="quick_lookup")
        if quick_symbol:
            try:
                price = get_stock_price(quick_symbol.upper(), st.session_state.selected_market)
                if price:
                    st.success(f"{quick_symbol.upper()}: ${price:.2f} ({st.session_state.selected_market})")
                else:
                    st.error(f"Invalid symbol for {st.session_state.selected_market} market")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Main dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        portfolio_count = len(st.session_state.portfolio) if st.session_state.portfolio else 0
        st.metric("Stocks Owned", portfolio_count)
    
    with col2:
        watchlist_count = len(st.session_state.watchlist) if st.session_state.watchlist else 0
        st.metric("Watchlist", watchlist_count)
    
    with col3:
        transaction_count = len(st.session_state.transactions) if st.session_state.transactions else 0
        st.metric("Transactions", transaction_count)
    
    with col4:
        active_rules = len(st.session_state.trading_rules) if st.session_state.trading_rules else 0
        st.metric("Active Rules", active_rules)
    
    st.markdown("---")
    
    # Recent activity and alerts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Market Overview")
        
        # Major indices
        try:
            indices = {
                "S&P 500": "^GSPC",
                "NASDAQ": "^IXIC",
                "DOW": "^DJI"
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
            else:
                st.info("Unable to fetch market data at the moment")
                
        except Exception as e:
            st.error(f"Error fetching market data: {str(e)}")
    
    with col2:
        st.subheader("🚨 Trading Alerts")
        
        # Check trading rules and display alerts
        alerts = []
        if st.session_state.trading_rules and st.session_state.portfolio:
            for rule in st.session_state.trading_rules:
                try:
                    alert = check_trading_rules(rule, st.session_state.portfolio)
                    if alert:
                        alerts.append(alert)
                except Exception as e:
                    continue
        
        if alerts:
            for alert in alerts[-5:]:  # Show last 5 alerts
                if alert['type'] == 'warning':
                    st.warning(f"⚠️ {alert['message']}")
                elif alert['type'] == 'success':
                    st.success(f"✅ {alert['message']}")
                else:
                    st.info(f"ℹ️ {alert['message']}")
        else:
            st.info("No active alerts")
    
    st.markdown("---")
    
    # Portfolio performance chart
    if st.session_state.portfolio and st.session_state.transactions:
        st.subheader("📈 Portfolio Performance")
        
        try:
            # Calculate portfolio value over time
            df_transactions = pd.DataFrame(st.session_state.transactions)
            df_transactions['date'] = pd.to_datetime(df_transactions['date'])
            
            # Get date range
            start_date = df_transactions['date'].min()
            end_date = datetime.now()
            
            # Create daily portfolio values
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            portfolio_values = []
            
            for date in date_range:
                # Calculate portfolio value at this date
                current_portfolio = {}
                for _, transaction in df_transactions[df_transactions['date'] <= date].iterrows():
                    symbol = transaction['symbol']
                    if symbol not in current_portfolio:
                        current_portfolio[symbol] = 0
                    
                    if transaction['type'] == 'buy':
                        current_portfolio[symbol] += transaction['quantity']
                    else:  # sell
                        current_portfolio[symbol] -= transaction['quantity']
                
                # Remove zero positions
                current_portfolio = {k: v for k, v in current_portfolio.items() if v > 0}
                
                # Calculate value
                total_value = 0
                for symbol, quantity in current_portfolio.items():
                    try:
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(start=date, end=date + timedelta(days=1))
                        if not hist.empty:
                            price = hist['Close'].iloc[0]
                            total_value += price * quantity
                    except:
                        continue
                
                portfolio_values.append({
                    'date': date,
                    'value': total_value
                })
            
            if portfolio_values:
                df_values = pd.DataFrame(portfolio_values)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_values['date'],
                    y=df_values['value'],
                    mode='lines',
                    name='Portfolio Value',
                    line=dict(color='#1f77b4', width=2)
                ))
                
                fig.update_layout(
                    title='Portfolio Value Over Time',
                    xaxis_title='Date',
                    yaxis_title='Value ($)',
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Insufficient data for portfolio performance chart")
                
        except Exception as e:
            st.error(f"Error generating portfolio chart: {str(e)}")
    else:
        st.info("Start by adding stocks to your portfolio to see performance charts")
    
    # Navigation instructions
    st.markdown("---")
    st.info("💡 Use the sidebar navigation to access different features: Portfolio management, Stock search, Watchlist, Trading rules, and Analytics.")

if __name__ == "__main__":
    main()

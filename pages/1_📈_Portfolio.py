import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils.stock_data import get_stock_info, get_stock_price, get_market_symbol
from utils.portfolio import (
    calculate_portfolio_value, 
    get_portfolio_breakdown, 
    get_position_details,
    calculate_portfolio_metrics
)
from utils.data_persistence import add_transaction, save_portfolio, export_portfolio_csv

st.set_page_config(page_title="Portfolio", page_icon="📈", layout="wide")

def main():
    # Market selection in top right corner
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col1:
        st.title("📈 Portfolio Management")
    
    with col3:
        # Initialize market selection in session state
        if 'selected_market' not in st.session_state:
            st.session_state.selected_market = 'USA'
        
        market = st.selectbox(
            "Market",
            options=['USA', 'India'],
            index=['USA', 'India'].index(st.session_state.selected_market),
            key='market_selector'
        )
        
        # Update session state if market changed
        if market != st.session_state.selected_market:
            st.session_state.selected_market = market
            st.rerun()
    
    # Initialize session state
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {}
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    
    # Sidebar for portfolio actions
    with st.sidebar:
        st.header("Portfolio Actions")
        
        # Add new position
        with st.expander("Add New Position", expanded=False):
            # Show market-specific placeholder
            placeholder = "AAPL" if st.session_state.selected_market == 'USA' else "RELIANCE"
            st.info(f"Selected Market: **{st.session_state.selected_market}**")
            
            symbol = st.text_input("Stock Symbol", placeholder=placeholder).upper()
            quantity = st.number_input("Quantity", min_value=1, value=1)
            price = st.number_input("Purchase Price", min_value=0.01, value=100.00, step=0.01)
            
            if st.button("Add to Portfolio"):
                if symbol and quantity > 0 and price > 0:
                    # Verify symbol exists using selected market
                    stock_info = get_stock_info(symbol, st.session_state.selected_market)
                    if stock_info:
                        if add_transaction(symbol, 'buy', quantity, price):
                            st.success(f"Added {quantity} shares of {symbol} at ${price:.2f} ({st.session_state.selected_market})")
                            st.rerun()
                        else:
                            st.error("Failed to add position")
                    else:
                        st.error(f"Invalid stock symbol for {st.session_state.selected_market} market")
                else:
                    st.error("Please fill all fields with valid values")
        
        # Sell position
        with st.expander("Sell Position", expanded=False):
            if st.session_state.portfolio:
                sell_symbol = st.selectbox("Select Stock to Sell", list(st.session_state.portfolio.keys()))
                max_quantity = st.session_state.portfolio.get(sell_symbol, 0)
                sell_quantity = st.number_input("Quantity to Sell", min_value=1, max_value=max_quantity, value=min(1, max_quantity))
                sell_price = st.number_input("Sell Price", min_value=0.01, value=100.00, step=0.01)
                
                if st.button("Sell Position"):
                    if sell_quantity > 0 and sell_price > 0:
                        if add_transaction(sell_symbol, 'sell', sell_quantity, sell_price):
                            st.success(f"Sold {sell_quantity} shares of {sell_symbol} at ${sell_price:.2f}")
                            st.rerun()
                        else:
                            st.error("Failed to sell position")
                    else:
                        st.error("Please enter valid values")
            else:
                st.info("No positions to sell")
        
        st.markdown("---")
        
        # Export options
        st.subheader("Export Options")
        if st.button("Export Portfolio CSV"):
            csv_data = export_portfolio_csv()
            if csv_data:
                st.download_button(
                    label="Download Portfolio CSV",
                    data=csv_data,
                    file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    # Main portfolio view
    if not st.session_state.portfolio:
        st.info("Your portfolio is empty. Add some stocks using the sidebar!")
        return
    
    # Portfolio overview metrics
    st.subheader("Portfolio Overview")
    
    total_value = calculate_portfolio_value(st.session_state.portfolio, st.session_state.selected_market)
    portfolio_metrics = calculate_portfolio_metrics(st.session_state.portfolio, st.session_state.transactions, st.session_state.selected_market)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Value", f"${total_value:,.2f}")
    
    with col2:
        total_return = portfolio_metrics.get('total_return', 0)
        total_return_pct = portfolio_metrics.get('total_return_percent', 0)
        st.metric("Total Return", f"${total_return:,.2f}", f"{total_return_pct:+.2f}%")
    
    with col3:
        realized_gains = portfolio_metrics.get('realized_gains', 0)
        st.metric("Realized Gains", f"${realized_gains:,.2f}")
    
    with col4:
        unrealized_gains = portfolio_metrics.get('unrealized_gains', 0)
        st.metric("Unrealized Gains", f"${unrealized_gains:,.2f}")
    
    st.markdown("---")
    
    # Portfolio breakdown charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Portfolio Allocation")
        breakdown = get_portfolio_breakdown(st.session_state.portfolio, st.session_state.selected_market)
        
        if breakdown['by_value']:
            # Create pie chart for portfolio allocation
            symbols = list(breakdown['by_value'].keys())
            values = [breakdown['by_value'][symbol]['value'] for symbol in symbols]
            
            fig = px.pie(
                values=values, 
                names=symbols, 
                title="Portfolio Allocation by Value"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Sector Allocation")
        
        if breakdown['by_sector']:
            sectors = list(breakdown['by_sector'].keys())
            sector_values = list(breakdown['by_sector'].values())
            
            fig = px.pie(
                values=sector_values, 
                names=sectors, 
                title="Portfolio Allocation by Sector"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed positions table
    st.subheader("Portfolio Positions")
    
    positions_data = []
    for symbol in st.session_state.portfolio:
        position_details = get_position_details(symbol, st.session_state.portfolio, st.session_state.transactions, st.session_state.selected_market)
        if position_details:
            positions_data.append({
                'Symbol': position_details['symbol'],
                'Name': position_details['name'][:30] + '...' if len(position_details['name']) > 30 else position_details['name'],
                'Quantity': position_details['quantity'],
                'Avg Cost': f"${position_details['avg_cost']:.2f}",
                'Current Price': f"${position_details['current_price']:.2f}",
                'Current Value': f"${position_details['current_value']:,.2f}",
                'Unrealized P&L': f"${position_details['unrealized_gain']:,.2f}",
                'Unrealized P&L %': f"{position_details['unrealized_gain_percent']:+.2f}%",
                'Day Change': f"{position_details['day_change_percent']:+.2f}%",
                'Sector': position_details['sector']
            })
    
    if positions_data:
        df_positions = pd.DataFrame(positions_data)
        
        # Style the dataframe
        def color_negative_red(val):
            if isinstance(val, str) and (val.startswith('-') or val.startswith('$-')):
                return 'color: red'
            elif isinstance(val, str) and (val.startswith('+') or (val.startswith('$') and not val.startswith('$-'))):
                return 'color: green'
            return ''
        
        styled_df = df_positions.style.applymap(color_negative_red, subset=['Unrealized P&L', 'Unrealized P&L %', 'Day Change'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Position details expander
        st.subheader("Position Details")
        selected_symbol = st.selectbox("Select position for details", list(st.session_state.portfolio.keys()))
        
        if selected_symbol:
            position_details = get_position_details(selected_symbol, st.session_state.portfolio, st.session_state.transactions, st.session_state.selected_market)
            if position_details:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", f"${position_details['current_price']:.2f}")
                    st.metric("Average Cost", f"${position_details['avg_cost']:.2f}")
                
                with col2:
                    st.metric("Quantity Owned", position_details['quantity'])
                    st.metric("Current Value", f"${position_details['current_value']:,.2f}")
                
                with col3:
                    st.metric(
                        "Unrealized P&L", 
                        f"${position_details['unrealized_gain']:,.2f}",
                        f"{position_details['unrealized_gain_percent']:+.2f}%"
                    )
                    st.metric("Sector", position_details['sector'])
    else:
        st.info("No position data available")
    
    st.markdown("---")
    
    # Recent transactions
    st.subheader("Recent Transactions")
    
    if st.session_state.transactions:
        df_transactions = pd.DataFrame(st.session_state.transactions)
        df_transactions = df_transactions.sort_values('date', ascending=False).head(10)
        
        # Format the dataframe for display
        display_transactions = df_transactions.copy()
        display_transactions['Date'] = pd.to_datetime(display_transactions['date']).dt.strftime('%Y-%m-%d %H:%M')
        display_transactions['Type'] = display_transactions['type'].str.title()
        display_transactions['Symbol'] = display_transactions['symbol']
        display_transactions['Quantity'] = display_transactions['quantity']
        display_transactions['Price'] = display_transactions['price'].apply(lambda x: f"${x:.2f}")
        display_transactions['Total'] = display_transactions['total'].apply(lambda x: f"${x:,.2f}")
        
        display_df = display_transactions[['Date', 'Type', 'Symbol', 'Quantity', 'Price', 'Total']]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet")

if __name__ == "__main__":
    main()

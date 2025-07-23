import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils.stock_data import get_stock_info, get_stock_price
from utils.data_persistence import save_watchlist, add_transaction

st.set_page_config(page_title="Watchlist", page_icon="👀", layout="wide")

def main():
    st.title("👀 Watchlist")
    
    # Initialize session state
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = []
    
    # Sidebar for watchlist management
    with st.sidebar:
        st.header("Watchlist Management")
        
        # Add stock to watchlist
        st.subheader("Add Stock")
        new_symbol = st.text_input("Stock Symbol", placeholder="AAPL").upper()
        
        if st.button("Add to Watchlist"):
            if new_symbol:
                # Verify symbol exists
                stock_info = get_stock_info(new_symbol)
                if stock_info:
                    if new_symbol not in st.session_state.watchlist:
                        st.session_state.watchlist.append(new_symbol)
                        save_watchlist(st.session_state.watchlist)
                        st.success(f"Added {new_symbol} to watchlist")
                        st.rerun()
                    else:
                        st.warning(f"{new_symbol} already in watchlist")
                else:
                    st.error("Invalid stock symbol")
            else:
                st.error("Please enter a stock symbol")
        
        st.markdown("---")
        
        # Remove stock from watchlist
        if st.session_state.watchlist:
            st.subheader("Remove Stock")
            symbol_to_remove = st.selectbox("Select stock to remove", st.session_state.watchlist)
            
            if st.button("Remove from Watchlist"):
                st.session_state.watchlist.remove(symbol_to_remove)
                save_watchlist(st.session_state.watchlist)
                st.success(f"Removed {symbol_to_remove} from watchlist")
                st.rerun()
        
        st.markdown("---")
        
        # Quick actions
        st.subheader("Quick Actions")
        if st.button("Clear All"):
            st.session_state.watchlist = []
            save_watchlist(st.session_state.watchlist)
            st.success("Watchlist cleared")
            st.rerun()
    
    # Main watchlist display
    if not st.session_state.watchlist:
        st.info("Your watchlist is empty. Add some stocks using the sidebar!")
        
        # Suggest popular stocks
        st.subheader("Popular Stocks to Watch")
        popular_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
        
        cols = st.columns(4)
        for i, symbol in enumerate(popular_stocks):
            with cols[i % 4]:
                try:
                    stock_info = get_stock_info(symbol)
                    if stock_info:
                        st.write(f"**{symbol}**")
                        st.write(f"${stock_info['price']:.2f}")
                        st.write(f"{stock_info['day_change_percent']:+.2f}%")
                        
                        if st.button(f"Add {symbol}", key=f"add_{symbol}"):
                            st.session_state.watchlist.append(symbol)
                            save_watchlist(st.session_state.watchlist)
                            st.rerun()
                except:
                    continue
        
        return
    
    # Display watchlist overview
    st.subheader(f"Your Watchlist ({len(st.session_state.watchlist)} stocks)")
    
    # Fetch data for all watchlist stocks
    watchlist_data = []
    for symbol in st.session_state.watchlist:
        try:
            stock_info = get_stock_info(symbol)
            if stock_info:
                watchlist_data.append({
                    'Symbol': symbol,
                    'Name': stock_info['name'][:30] + '...' if len(stock_info['name']) > 30 else stock_info['name'],
                    'Price': stock_info['price'],
                    'Change': stock_info['day_change'],
                    'Change %': stock_info['day_change_percent'],
                    'Volume': stock_info['volume'],
                    'Market Cap': stock_info['market_cap'],
                    'Sector': stock_info['sector'],
                    'PE Ratio': stock_info['pe_ratio'] if stock_info['pe_ratio'] else 0
                })
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
    
    if watchlist_data:
        df_watchlist = pd.DataFrame(watchlist_data)
        
        # Display options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            sort_by = st.selectbox("Sort by", ["Symbol", "Price", "Change %", "Volume", "Market Cap"])
        
        with col2:
            sort_order = st.selectbox("Order", ["Ascending", "Descending"])
        
        with col3:
            view_mode = st.selectbox("View", ["Table", "Cards"])
        
        # Sort data
        ascending = sort_order == "Ascending"
        if sort_by in df_watchlist.columns:
            df_sorted = df_watchlist.sort_values(sort_by, ascending=ascending)
        else:
            df_sorted = df_watchlist
        
        # Display data
        if view_mode == "Table":
            # Format data for display
            display_df = df_sorted.copy()
            display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:.2f}")
            display_df['Change'] = display_df['Change'].apply(lambda x: f"${x:+.2f}")
            display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:+.2f}%")
            display_df['Volume'] = display_df['Volume'].apply(lambda x: f"{x:,}")
            display_df['Market Cap'] = display_df['Market Cap'].apply(lambda x: f"${x:,.0f}" if x > 0 else "N/A")
            display_df['PE Ratio'] = display_df['PE Ratio'].apply(lambda x: f"{x:.2f}" if x > 0 else "N/A")
            
            # Color negative/positive changes
            def color_changes(val):
                if isinstance(val, str) and val.startswith('-'):
                    return 'color: red'
                elif isinstance(val, str) and val.startswith('+'):
                    return 'color: green'
                return ''
            
            styled_df = display_df.style.applymap(color_changes, subset=['Change', 'Change %'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        else:  # Cards view
            cols = st.columns(3)
            for i, row in df_sorted.iterrows():
                with cols[i % 3]:
                    with st.container():
                        # Color for change
                        change_color = "🔴" if row['Change %'] < 0 else "🟢" if row['Change %'] > 0 else "⚪"
                        
                        st.markdown(f"""
                        **{row['Symbol']}** {change_color}
                        
                        {row['Name']}
                        
                        **${row['Price']:.2f}** ({row['Change %']:+.2f}%)
                        
                        Volume: {row['Volume']:,}
                        
                        Sector: {row['Sector']}
                        """)
                        
                        # Quick buy button
                        if st.button(f"Quick Buy", key=f"buy_{row['Symbol']}"):
                            st.session_state.quick_buy_symbol = row['Symbol']
                            st.session_state.quick_buy_price = row['Price']
        
        # Quick buy dialog
        if hasattr(st.session_state, 'quick_buy_symbol'):
            st.markdown("---")
            st.subheader(f"Quick Buy: {st.session_state.quick_buy_symbol}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                buy_quantity = st.number_input("Quantity", min_value=1, value=1, key="quick_buy_qty")
            
            with col2:
                buy_price = st.number_input("Price", value=st.session_state.quick_buy_price, step=0.01, key="quick_buy_price_input")
            
            with col3:
                st.write(f"Total: ${buy_quantity * buy_price:,.2f}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Confirm Purchase"):
                    if add_transaction(st.session_state.quick_buy_symbol, 'buy', buy_quantity, buy_price):
                        st.success(f"Bought {buy_quantity} shares of {st.session_state.quick_buy_symbol}")
                        del st.session_state.quick_buy_symbol
                        del st.session_state.quick_buy_price
                        st.rerun()
                    else:
                        st.error("Failed to add transaction")
            
            with col2:
                if st.button("Cancel"):
                    del st.session_state.quick_buy_symbol
                    del st.session_state.quick_buy_price
                    st.rerun()
        
        st.markdown("---")
        
        # Watchlist analytics
        st.subheader("Watchlist Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sector distribution
            sector_counts = df_watchlist['Sector'].value_counts()
            
            fig_sectors = px.pie(
                values=sector_counts.values, 
                names=sector_counts.index, 
                title="Watchlist by Sector"
            )
            st.plotly_chart(fig_sectors, use_container_width=True)
        
        with col2:
            # Performance today
            fig_performance = px.bar(
                df_sorted, 
                x='Symbol', 
                y='Change %',
                title="Today's Performance",
                color='Change %',
                color_continuous_scale='RdYlGn'
            )
            fig_performance.update_layout(showlegend=False)
            st.plotly_chart(fig_performance, use_container_width=True)
        
        # Market cap distribution
        st.subheader("Market Cap Distribution")
        
        # Categorize by market cap
        def categorize_market_cap(market_cap):
            if market_cap >= 200_000_000_000:
                return 'Mega Cap (>$200B)'
            elif market_cap >= 10_000_000_000:
                return 'Large Cap ($10B-$200B)'
            elif market_cap >= 2_000_000_000:
                return 'Mid Cap ($2B-$10B)'
            elif market_cap >= 300_000_000:
                return 'Small Cap ($300M-$2B)'
            else:
                return 'Micro Cap (<$300M)'
        
        df_watchlist['Market Cap Category'] = df_watchlist['Market Cap'].apply(categorize_market_cap)
        cap_counts = df_watchlist['Market Cap Category'].value_counts()
        
        fig_caps = px.bar(
            x=cap_counts.index, 
            y=cap_counts.values,
            title="Watchlist by Market Capitalization",
            labels={'x': 'Market Cap Category', 'y': 'Number of Stocks'}
        )
        st.plotly_chart(fig_caps, use_container_width=True)
        
        # Summary statistics
        st.subheader("Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_change = df_watchlist['Change %'].mean()
            st.metric("Avg Change Today", f"{avg_change:+.2f}%")
        
        with col2:
            positive_stocks = len(df_watchlist[df_watchlist['Change %'] > 0])
            st.metric("Stocks Up Today", f"{positive_stocks}/{len(df_watchlist)}")
        
        with col3:
            total_volume = df_watchlist['Volume'].sum()
            st.metric("Total Volume", f"{total_volume:,.0f}")
        
        with col4:
            avg_pe = df_watchlist[df_watchlist['PE Ratio'] > 0]['PE Ratio'].mean()
            st.metric("Avg P/E Ratio", f"{avg_pe:.2f}" if not pd.isna(avg_pe) else "N/A")
    
    else:
        st.error("Unable to fetch data for watchlist stocks")

if __name__ == "__main__":
    main()

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from utils.portfolio import calculate_portfolio_metrics, get_portfolio_breakdown, calculate_portfolio_value
from utils.stock_data import get_stock_info, get_sector_performance
from utils.data_persistence import export_transactions_csv

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")


def main():
    st.title("📊 Portfolio Analytics & Performance")

    # Initialize session state
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {}
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []

    if not st.session_state.portfolio and not st.session_state.transactions:
        st.info(
            "No portfolio data available. Add some stocks to your portfolio to see analytics!"
        )
        return

    # Portfolio overview metrics
    st.subheader("📈 Performance Overview")

    portfolio_metrics = calculate_portfolio_metrics(
        st.session_state.portfolio, st.session_state.transactions)
    current_value = calculate_portfolio_value(st.session_state.portfolio)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Current Value", f"${current_value:,.2f}")

    with col2:
        total_invested = portfolio_metrics.get('total_invested', 0)
        st.metric("Total Invested", f"${total_invested:,.2f}")

    with col3:
        total_return = portfolio_metrics.get('total_return', 0)
        total_return_pct = portfolio_metrics.get('total_return_percent', 0)
        st.metric("Total Return", f"${total_return:,.2f}",
                  f"{total_return_pct:+.2f}%")

    with col4:
        win_rate = portfolio_metrics.get('win_rate', 0)
        st.metric("Number of Trades",
                  portfolio_metrics.get('number_of_trades', 0))

    st.markdown("---")

    # Portfolio allocation analysis
    st.subheader("🥧 Portfolio Allocation Analysis")

    breakdown = get_portfolio_breakdown(st.session_state.portfolio)

    if breakdown['by_value']:
        col1, col2 = st.columns(2)

        with col1:
            # Position allocation pie chart
            symbols = list(breakdown['by_value'].keys())
            values = [
                breakdown['by_value'][symbol]['value'] for symbol in symbols
            ]
            weights = [
                breakdown['by_value'][symbol]['weight'] for symbol in symbols
            ]

            fig_allocation = px.pie(
                values=values,
                names=symbols,
                title="Portfolio Allocation by Value",
                hover_data={'values': [f'${v:,.2f}' for v in values]})
            fig_allocation.update_traces(textposition='inside',
                                         textinfo='percent+label')
            st.plotly_chart(fig_allocation, use_container_width=True)

        with col2:
            # Sector allocation pie chart
            if breakdown['by_sector']:
                sector_names = list(breakdown['by_sector'].keys())
                sector_values = list(breakdown['by_sector'].values())

                fig_sectors = px.pie(values=sector_values,
                                     names=sector_names,
                                     title="Portfolio Allocation by Sector")
                fig_sectors.update_traces(textposition='inside',
                                          textinfo='percent+label')
                st.plotly_chart(fig_sectors, use_container_width=True)

    # Diversification metrics
    st.subheader("📊 Diversification Analysis")

    if breakdown['by_value']:
        col1, col2, col3 = st.columns(3)

        with col1:
            # Concentration risk
            weights = [
                breakdown['by_value'][symbol]['weight']
                for symbol in breakdown['by_value']
            ]
            max_weight = max(weights)
            concentration_risk = "High" if max_weight > 30 else "Medium" if max_weight > 20 else "Low"
            st.metric("Concentration Risk", concentration_risk,
                      f"Max position: {max_weight:.1f}%")

        with col2:
            # Number of sectors
            num_sectors = len(breakdown['by_sector'])
            diversification = "Good" if num_sectors >= 5 else "Fair" if num_sectors >= 3 else "Poor"
            st.metric("Sector Diversification", diversification,
                      f"{num_sectors} sectors")

        with col3:
            # Portfolio size
            num_positions = len(breakdown['by_value'])
            size_category = "Large" if num_positions >= 20 else "Medium" if num_positions >= 10 else "Small"
            st.metric("Portfolio Size", size_category,
                      f"{num_positions} positions")

    st.markdown("---")

    # Performance tracking over time
    if st.session_state.transactions:
        st.subheader("📈 Portfolio Performance Over Time")

        # Calculate portfolio value over time
        df_transactions = pd.DataFrame(st.session_state.transactions)
        df_transactions['date'] = pd.to_datetime(df_transactions['date'])

        # Get date range
        start_date = df_transactions['date'].min()
        end_date = datetime.now()

        # Calculate daily portfolio values
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        portfolio_history = []

        progress_bar = st.progress(0)
        total_dates = len(date_range)

        for i, date in enumerate(date_range):
            # Update progress
            progress_bar.progress((i + 1) / total_dates)

            # Calculate portfolio at this date
            current_portfolio = {}
            total_invested_at_date = 0

            for _, transaction in df_transactions[df_transactions['date'] <=
                                                  date].iterrows():
                symbol = transaction['symbol']
                if symbol not in current_portfolio:
                    current_portfolio[symbol] = {
                        'quantity': 0,
                        'total_cost': 0
                    }

                if transaction['type'] == 'buy':
                    current_portfolio[symbol]['quantity'] += transaction[
                        'quantity']
                    current_portfolio[symbol]['total_cost'] += transaction[
                        'total']
                    total_invested_at_date += transaction['total']
                else:  # sell
                    # Calculate average cost for this symbol
                    if current_portfolio[symbol]['quantity'] > 0:
                        avg_cost = current_portfolio[symbol][
                            'total_cost'] / current_portfolio[symbol][
                                'quantity']
                        cost_reduction = avg_cost * transaction['quantity']
                        current_portfolio[symbol][
                            'total_cost'] -= cost_reduction
                        total_invested_at_date -= cost_reduction

                    current_portfolio[symbol]['quantity'] -= transaction[
                        'quantity']

            # Remove zero positions
            current_portfolio = {
                k: v
                for k, v in current_portfolio.items() if v['quantity'] > 0
            }

            # Calculate market value
            total_market_value = 0
            for symbol, position in current_portfolio.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=date,
                                          end=date + timedelta(days=1))
                    if not hist.empty:
                        price = hist['Close'].iloc[0]
                        total_market_value += price * position['quantity']
                except:
                    continue

            portfolio_history.append({
                'date':
                date,
                'invested':
                total_invested_at_date,
                'market_value':
                total_market_value,
                'return':
                total_market_value - total_invested_at_date,
                'return_pct': ((total_market_value - total_invested_at_date) /
                               total_invested_at_date *
                               100) if total_invested_at_date > 0 else 0
            })

        progress_bar.empty()

        if portfolio_history:
            df_history = pd.DataFrame(portfolio_history)

            # Portfolio value chart
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(x=df_history['date'],
                           y=df_history['market_value'],
                           mode='lines',
                           name='Market Value',
                           line=dict(color='blue', width=2)))

            fig.add_trace(
                go.Scatter(x=df_history['date'],
                           y=df_history['invested'],
                           mode='lines',
                           name='Total Invested',
                           line=dict(color='red', width=2)))

            fig.update_layout(title='Portfolio Value vs. Total Invested',
                              xaxis_title='Date',
                              yaxis_title='Value ($)',
                              height=500,
                              hovermode='x unified')

            st.plotly_chart(fig, use_container_width=True)

            # Return percentage chart
            fig_return = go.Figure()

            fig_return.add_trace(
                go.Scatter(x=df_history['date'],
                           y=df_history['return_pct'],
                           mode='lines',
                           name='Return %',
                           line=dict(color='green', width=2),
                           fill='tonexty'))

            fig_return.update_layout(
                title='Portfolio Return Percentage Over Time',
                xaxis_title='Date',
                yaxis_title='Return (%)',
                height=400)

            st.plotly_chart(fig_return, use_container_width=True)

    st.markdown("---")

    # Transaction analysis
    if st.session_state.transactions:
        st.subheader("💰 Transaction Analysis")

        df_transactions = pd.DataFrame(st.session_state.transactions)
        df_transactions['date'] = pd.to_datetime(df_transactions['date'])

        col1, col2 = st.columns(2)

        with col1:
            # Transaction volume by month
            df_transactions['month'] = df_transactions['date'].dt.to_period(
                'M')
            monthly_volume = df_transactions.groupby(
                ['month', 'type'])['total'].sum().reset_index()

            fig_volume = px.bar(monthly_volume,
                                x='month',
                                y='total',
                                color='type',
                                title='Transaction Volume by Month',
                                labels={
                                    'total': 'Amount ($)',
                                    'month': 'Month'
                                })
            st.plotly_chart(fig_volume, use_container_width=True)

        with col2:
            # Most traded stocks
            symbol_trades = df_transactions['symbol'].value_counts().head(10)

            fig_trades = px.bar(x=symbol_trades.values,
                                y=symbol_trades.index,
                                orientation='h',
                                title='Most Traded Stocks',
                                labels={
                                    'x': 'Number of Trades',
                                    'y': 'Symbol'
                                })
            st.plotly_chart(fig_trades, use_container_width=True)

        # Transaction statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_trade_size = df_transactions['total'].mean()
            st.metric("Avg Trade Size", f"${avg_trade_size:,.2f}")

        with col2:
            buy_trades = len(df_transactions[df_transactions['type'] == 'buy'])
            sell_trades = len(
                df_transactions[df_transactions['type'] == 'sell'])
            st.metric("Buy/Sell Ratio", f"{buy_trades}/{sell_trades}")

        with col3:
            total_volume = df_transactions['total'].sum()
            st.metric("Total Volume", f"${total_volume:,.2f}")

        with col4:
            unique_symbols = df_transactions['symbol'].nunique()
            st.metric("Unique Symbols", unique_symbols)

    st.markdown("---")

    # Market comparison
    st.subheader("📊 Market Comparison")

    if st.session_state.portfolio:
        # Compare portfolio sectors with market
        sector_performance = get_sector_performance()

        if sector_performance and breakdown['by_sector']:
            portfolio_sectors = breakdown['by_sector']

            comparison_data = []
            for sector, portfolio_value in portfolio_sectors.items():
                portfolio_weight = (portfolio_value /
                                    breakdown['total_value']) * 100
                market_change = sector_performance.get(sector, {}).get(
                    'change_percent', 0)

                comparison_data.append({
                    'Sector': sector,
                    'Portfolio Weight': portfolio_weight,
                    'Market Performance': market_change
                })

            if comparison_data:
                df_comparison = pd.DataFrame(comparison_data)

                fig_comparison = px.scatter(
                    df_comparison,
                    x='Portfolio Weight',
                    y='Market Performance',
                    text='Sector',
                    title='Portfolio Sector Allocation vs Market Performance',
                    labels={
                        'Portfolio Weight': 'Portfolio Weight (%)',
                        'Market Performance': 'Market Performance (%)'
                    })
                fig_comparison.update_traces(textposition="top center")
                st.plotly_chart(fig_comparison, use_container_width=True)

    # Risk metrics
    st.subheader("⚠️ Risk Analysis")

    if breakdown['by_value']:
        col1, col2, col3 = st.columns(3)

        with col1:
            # Calculate portfolio beta (simplified)
            portfolio_beta = 0
            total_weight = 0

            for symbol, position in breakdown['by_value'].items():
                try:
                    stock_info = get_stock_info(symbol)
                    if stock_info and stock_info.get('beta'):
                        weight = position['weight'] / 100
                        portfolio_beta += stock_info['beta'] * weight
                        total_weight += weight
                except:
                    continue

            if total_weight > 0:
                portfolio_beta = portfolio_beta / total_weight
                risk_level = "High" if portfolio_beta > 1.3 else "Medium" if portfolio_beta > 0.8 else "Low"
                st.metric("Portfolio Beta", f"{portfolio_beta:.2f}",
                          risk_level)
            else:
                st.metric("Portfolio Beta", "N/A")

        with col2:
            # Largest position risk
            max_position = max(
                [pos['weight'] for pos in breakdown['by_value'].values()])
            position_risk = "High" if max_position > 25 else "Medium" if max_position > 15 else "Low"
            st.metric("Single Position Risk", position_risk,
                      f"{max_position:.1f}% max")

        with col3:
            # Sector concentration
            if breakdown['by_sector']:
                max_sector = max(breakdown['by_sector'].values())
                max_sector_pct = (max_sector / breakdown['total_value']) * 100
                sector_risk = "High" if max_sector_pct > 40 else "Medium" if max_sector_pct > 25 else "Low"
                st.metric("Sector Risk", sector_risk,
                          f"{max_sector_pct:.1f}% max")

    # Export options
    st.markdown("---")
    st.subheader("📁 Export Data")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Export Transaction History"):
            csv_data = export_transactions_csv()
            if csv_data:
                st.download_button(
                    label="Download Transactions CSV",
                    data=csv_data,
                    file_name=
                    f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv")

    with col2:
        if st.button("Export Portfolio Report"):
            # Create a comprehensive portfolio report
            report_data = {
                'Portfolio Summary': {
                    'Current Value':
                    f"${current_value:,.2f}",
                    'Total Invested':
                    f"${portfolio_metrics.get('total_invested', 0):,.2f}",
                    'Total Return':
                    f"${portfolio_metrics.get('total_return', 0):,.2f}",
                    'Return %':
                    f"{portfolio_metrics.get('total_return_percent', 0):+.2f}%",
                    'Number of Positions':
                    len(breakdown['by_value']) if breakdown['by_value'] else 0,
                    'Number of Sectors':
                    len(breakdown['by_sector'])
                    if breakdown['by_sector'] else 0
                }
            }

            import json
            report_json = json.dumps(report_data, indent=2)

            st.download_button(
                label="Download Portfolio Report",
                data=report_json,
                file_name=
                f"portfolio_report_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json")


if __name__ == "__main__":
    main()

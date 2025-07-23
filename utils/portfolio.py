import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
from utils.stock_data import get_stock_price, get_stock_info, get_market_symbol

def calculate_portfolio_value(portfolio, market='USA'):
    """Calculate current portfolio value"""
    total_value = 0
    
    for symbol, quantity in portfolio.items():
        try:
            current_price = get_stock_price(symbol, market)
            if current_price:
                total_value += current_price * quantity
        except Exception as e:
            continue
    
    return total_value

def get_portfolio_performance(portfolio, period='1d', market='USA'):
    """Calculate portfolio performance over a period"""
    if not portfolio:
        return None
    
    try:
        current_value = 0
        previous_value = 0
        
        # Get period offset
        if period == '1d':
            days_back = 1
        elif period == '1w':
            days_back = 7
        elif period == '1m':
            days_back = 30
        elif period == '3m':
            days_back = 90
        elif period == '1y':
            days_back = 365
        else:
            days_back = 1
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back + 5)  # Extra days for market closure
        
        for symbol, quantity in portfolio.items():
            try:
                market_symbol = get_market_symbol(symbol, market)
                ticker = yf.Ticker(market_symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                if len(hist) >= 2:
                    current_price = hist['Close'].iloc[-1]
                    previous_price = hist['Close'].iloc[-(days_back + 1)] if len(hist) > days_back else hist['Close'].iloc[0]
                    
                    current_value += current_price * quantity
                    previous_value += previous_price * quantity
            except Exception as e:
                continue
        
        if previous_value > 0:
            change = current_value - previous_value
            change_percent = (change / previous_value) * 100
            
            return {
                'current_value': current_value,
                'previous_value': previous_value,
                'change': change,
                'change_percent': change_percent
            }
        
        return None
        
    except Exception as e:
        return None

def get_portfolio_breakdown(portfolio, market='USA'):
    """Get portfolio breakdown by sector, market cap, etc."""
    breakdown = {
        'by_sector': {},
        'by_market_cap': {},
        'by_value': {},
        'total_value': 0
    }
    
    for symbol, quantity in portfolio.items():
        try:
            stock_info = get_stock_info(symbol, market)
            current_price = get_stock_price(symbol, market)
            
            if stock_info and current_price:
                position_value = current_price * quantity
                breakdown['total_value'] += position_value
                
                # By sector
                sector = stock_info.get('sector', 'Unknown')
                if sector not in breakdown['by_sector']:
                    breakdown['by_sector'][sector] = 0
                breakdown['by_sector'][sector] += position_value
                
                # By market cap category
                market_cap = stock_info.get('market_cap', 0)
                if market_cap >= 10_000_000_000:
                    cap_category = 'Large Cap'
                elif market_cap >= 2_000_000_000:
                    cap_category = 'Mid Cap'
                elif market_cap >= 300_000_000:
                    cap_category = 'Small Cap'
                else:
                    cap_category = 'Micro Cap'
                
                if cap_category not in breakdown['by_market_cap']:
                    breakdown['by_market_cap'][cap_category] = 0
                breakdown['by_market_cap'][cap_category] += position_value
                
                # By individual position
                breakdown['by_value'][symbol] = {
                    'quantity': quantity,
                    'price': current_price,
                    'value': position_value,
                    'weight': 0  # Will be calculated after total is known
                }
        
        except Exception as e:
            continue
    
    # Calculate weights
    if breakdown['total_value'] > 0:
        for symbol in breakdown['by_value']:
            breakdown['by_value'][symbol]['weight'] = (
                breakdown['by_value'][symbol]['value'] / breakdown['total_value']
            ) * 100
    
    return breakdown

def calculate_portfolio_metrics(portfolio, transactions, market='USA'):
    """Calculate portfolio metrics like total return, win rate, etc."""
    if not transactions:
        return {}
    
    df_transactions = pd.DataFrame(transactions)
    df_transactions['date'] = pd.to_datetime(df_transactions['date'])
    
    metrics = {
        'total_invested': 0,
        'total_current_value': 0,
        'total_return': 0,
        'total_return_percent': 0,
        'realized_gains': 0,
        'unrealized_gains': 0,
        'win_rate': 0,
        'number_of_trades': len(df_transactions),
        'average_holding_period': 0
    }
    
    # Calculate total invested
    buy_transactions = df_transactions[df_transactions['type'] == 'buy']
    metrics['total_invested'] = (buy_transactions['quantity'] * buy_transactions['price']).sum()
    
    # Calculate current value
    metrics['total_current_value'] = calculate_portfolio_value(portfolio, market)
    
    # Calculate realized gains from sell transactions
    sell_transactions = df_transactions[df_transactions['type'] == 'sell']
    for symbol in sell_transactions['symbol'].unique():
        symbol_sells = sell_transactions[sell_transactions['symbol'] == symbol]
        symbol_buys = buy_transactions[buy_transactions['symbol'] == symbol]
        
        if not symbol_buys.empty:
            avg_buy_price = (symbol_buys['quantity'] * symbol_buys['price']).sum() / symbol_buys['quantity'].sum()
            for _, sell in symbol_sells.iterrows():
                realized_gain = (sell['price'] - avg_buy_price) * sell['quantity']
                metrics['realized_gains'] += realized_gain
    
    # Calculate unrealized gains
    metrics['unrealized_gains'] = metrics['total_current_value'] - metrics['total_invested'] + metrics['realized_gains']
    
    # Calculate total return
    metrics['total_return'] = metrics['realized_gains'] + metrics['unrealized_gains']
    if metrics['total_invested'] > 0:
        metrics['total_return_percent'] = (metrics['total_return'] / metrics['total_invested']) * 100
    
    return metrics

def get_position_details(symbol, portfolio, transactions, market='USA'):
    """Get detailed information about a specific position"""
    if symbol not in portfolio:
        return None
    
    quantity = portfolio[symbol]
    current_price = get_stock_price(symbol, market)
    stock_info = get_stock_info(symbol, market)
    
    if not current_price or not stock_info:
        return None
    
    # Get transaction history for this symbol
    df_transactions = pd.DataFrame(transactions) if transactions else pd.DataFrame()
    symbol_transactions = df_transactions[df_transactions['symbol'] == symbol] if not df_transactions.empty else pd.DataFrame()
    
    # Calculate average cost basis
    avg_cost = 0
    total_shares_bought = 0
    total_cost = 0
    
    if not symbol_transactions.empty:
        buy_transactions = symbol_transactions[symbol_transactions['type'] == 'buy']
        if not buy_transactions.empty:
            total_cost = (buy_transactions['quantity'] * buy_transactions['price']).sum()
            total_shares_bought = buy_transactions['quantity'].sum()
            if total_shares_bought > 0:
                avg_cost = total_cost / total_shares_bought
    
    current_value = current_price * quantity
    unrealized_gain = (current_price - avg_cost) * quantity if avg_cost > 0 else 0
    unrealized_gain_percent = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0
    
    return {
        'symbol': symbol,
        'name': stock_info.get('name', symbol),
        'quantity': quantity,
        'current_price': current_price,
        'avg_cost': avg_cost,
        'current_value': current_value,
        'total_cost': avg_cost * quantity if avg_cost > 0 else 0,
        'unrealized_gain': unrealized_gain,
        'unrealized_gain_percent': unrealized_gain_percent,
        'day_change': stock_info.get('day_change', 0),
        'day_change_percent': stock_info.get('day_change_percent', 0),
        'sector': stock_info.get('sector', 'Unknown'),
        'market_cap_category': categorize_by_market_cap(stock_info.get('market_cap', 0))
    }

def categorize_by_market_cap(market_cap):
    """Categorize stock by market cap"""
    if market_cap >= 200_000_000_000:
        return 'Mega Cap'
    elif market_cap >= 10_000_000_000:
        return 'Large Cap'
    elif market_cap >= 2_000_000_000:
        return 'Mid Cap'
    elif market_cap >= 300_000_000:
        return 'Small Cap'
    elif market_cap >= 50_000_000:
        return 'Micro Cap'
    else:
        return 'Nano Cap'

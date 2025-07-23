import json
import csv
import pandas as pd
import streamlit as st
from datetime import datetime
import os
from utils.database import (
    init_database, 
    save_portfolio_to_db, 
    load_portfolio_from_db,
    add_transaction_to_db,
    load_transactions_from_db,
    save_watchlist_to_db,
    load_watchlist_from_db,
    save_trading_rules_to_db,
    load_trading_rules_from_db,
    clear_all_data_from_db,
    backup_database,
    get_database_stats,
    DATABASE_URL
)

# Initialize database on import
@st.cache_resource
def initialize_database():
    """Initialize database tables"""
    return init_database()

# Try to initialize database
try:
    db_initialized = initialize_database()
    if not db_initialized:
        st.error("Failed to initialize database. Using fallback file storage.")
        USE_DATABASE = False
    else:
        USE_DATABASE = True
except Exception as e:
    st.error(f"Database initialization error: {str(e)}. Using fallback file storage.")
    USE_DATABASE = False

# File paths for fallback file persistence
PORTFOLIO_FILE = "data/portfolio.json"
WATCHLIST_FILE = "data/watchlist.json"
TRANSACTIONS_FILE = "data/transactions.csv"
TRADING_RULES_FILE = "data/trading_rules.json"

def ensure_data_directory():
    """Ensure data directory exists"""
    if not os.path.exists("data"):
        os.makedirs("data")

# Portfolio functions
def save_portfolio(portfolio):
    """Save portfolio"""
    if USE_DATABASE:
        return save_portfolio_to_db(portfolio)
    else:
        # Fallback to file storage
        ensure_data_directory()
        try:
            with open(PORTFOLIO_FILE, 'w') as f:
                json.dump(portfolio, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving portfolio: {str(e)}")
            return False

def load_portfolio():
    """Load portfolio"""
    if USE_DATABASE:
        return load_portfolio_from_db()
    else:
        # Fallback to file storage
        try:
            if os.path.exists(PORTFOLIO_FILE):
                with open(PORTFOLIO_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.error(f"Error loading portfolio: {str(e)}")
        return {}

# Watchlist functions
def save_watchlist(watchlist):
    """Save watchlist"""
    if USE_DATABASE:
        return save_watchlist_to_db(watchlist)
    else:
        # Fallback to file storage
        ensure_data_directory()
        try:
            with open(WATCHLIST_FILE, 'w') as f:
                json.dump(watchlist, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving watchlist: {str(e)}")
            return False

def load_watchlist():
    """Load watchlist"""
    if USE_DATABASE:
        return load_watchlist_from_db()
    else:
        # Fallback to file storage
        try:
            if os.path.exists(WATCHLIST_FILE):
                with open(WATCHLIST_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.error(f"Error loading watchlist: {str(e)}")
        return []

# Transaction functions
def save_transactions(transactions):
    """Save transactions (only used for file fallback)"""
    if USE_DATABASE:
        return True  # Transactions are saved individually in database mode
    else:
        # Fallback to file storage
        ensure_data_directory()
        try:
            df = pd.DataFrame(transactions)
            df.to_csv(TRANSACTIONS_FILE, index=False)
            return True
        except Exception as e:
            st.error(f"Error saving transactions: {str(e)}")
            return False

def load_transactions():
    """Load transactions"""
    if USE_DATABASE:
        return load_transactions_from_db()
    else:
        # Fallback to file storage
        try:
            if os.path.exists(TRANSACTIONS_FILE):
                df = pd.read_csv(TRANSACTIONS_FILE)
                return df.to_dict('records')
        except Exception as e:
            st.error(f"Error loading transactions: {str(e)}")
        return []

def add_transaction(symbol, transaction_type, quantity, price, date=None):
    """Add a new transaction"""
    if USE_DATABASE:
        success = add_transaction_to_db(symbol, transaction_type, quantity, price, date)
        if success:
            # Update session state
            st.session_state.transactions = load_transactions()
            st.session_state.portfolio = load_portfolio()
        return success
    else:
        # Fallback to file storage
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        transaction = {
            'symbol': symbol.upper(),
            'type': transaction_type,
            'quantity': quantity,
            'price': price,
            'date': date,
            'total': quantity * price
        }
        
        # Load existing transactions
        transactions = load_transactions()
        transactions.append(transaction)
        
        # Save updated transactions
        if save_transactions(transactions):
            # Update session state
            st.session_state.transactions = transactions
            
            # Update portfolio
            portfolio = load_portfolio()
            
            if transaction_type == 'buy':
                if symbol in portfolio:
                    portfolio[symbol] += quantity
                else:
                    portfolio[symbol] = quantity
            elif transaction_type == 'sell':
                if symbol in portfolio:
                    portfolio[symbol] -= quantity
                    if portfolio[symbol] <= 0:
                        del portfolio[symbol]
            
            save_portfolio(portfolio)
            st.session_state.portfolio = portfolio
            
            return True
        
        return False

# Trading rules functions
def save_trading_rules(trading_rules):
    """Save trading rules"""
    if USE_DATABASE:
        return save_trading_rules_to_db(trading_rules)
    else:
        # Fallback to file storage
        ensure_data_directory()
        try:
            # Convert datetime objects to strings for JSON serialization
            rules_to_save = []
            for rule in trading_rules:
                rule_copy = rule.copy()
                if 'created_at' in rule_copy and hasattr(rule_copy['created_at'], 'isoformat'):
                    rule_copy['created_at'] = rule_copy['created_at'].isoformat()
                rules_to_save.append(rule_copy)
            
            with open(TRADING_RULES_FILE, 'w') as f:
                json.dump(rules_to_save, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving trading rules: {str(e)}")
            return False

def load_trading_rules():
    """Load trading rules"""
    if USE_DATABASE:
        return load_trading_rules_from_db()
    else:
        # Fallback to file storage
        try:
            if os.path.exists(TRADING_RULES_FILE):
                with open(TRADING_RULES_FILE, 'r') as f:
                    rules = json.load(f)
                    
                    # Convert string dates back to datetime objects
                    for rule in rules:
                        if 'created_at' in rule and isinstance(rule['created_at'], str):
                            try:
                                rule['created_at'] = datetime.fromisoformat(rule['created_at'])
                            except:
                                rule['created_at'] = datetime.now()
                    
                    return rules
        except Exception as e:
            st.error(f"Error loading trading rules: {str(e)}")
        return []

def export_transactions_csv():
    """Export transactions to CSV for download"""
    transactions = load_transactions()
    if transactions:
        df = pd.DataFrame(transactions)
        return df.to_csv(index=False)
    return None

def export_portfolio_csv():
    """Export current portfolio to CSV for download"""
    portfolio = load_portfolio()
    if portfolio:
        portfolio_data = []
        for symbol, quantity in portfolio.items():
            portfolio_data.append({
                'Symbol': symbol,
                'Quantity': quantity
            })
        
        df = pd.DataFrame(portfolio_data)
        return df.to_csv(index=False)
    return None

def clear_all_data():
    """Clear all saved data"""
    if USE_DATABASE:
        success = clear_all_data_from_db()
        if success:
            # Clear session state
            st.session_state.portfolio = {}
            st.session_state.watchlist = []
            st.session_state.transactions = []
            st.session_state.trading_rules = []
            st.success("All data cleared successfully!")
        return success
    else:
        # Fallback to file storage
        files_to_remove = [PORTFOLIO_FILE, WATCHLIST_FILE, TRANSACTIONS_FILE, TRADING_RULES_FILE]
        
        for file_path in files_to_remove:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                st.error(f"Error removing {file_path}: {str(e)}")
        
        # Clear session state
        st.session_state.portfolio = {}
        st.session_state.watchlist = []
        st.session_state.transactions = []
        st.session_state.trading_rules = []
        
        st.success("All data cleared successfully!")
        return True

def backup_data():
    """Create a backup of all data"""
    if USE_DATABASE:
        backup_data_dict = backup_database()
        if backup_data_dict:
            ensure_data_directory()
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            try:
                with open(f"data/{backup_filename}", 'w') as f:
                    json.dump(backup_data_dict, f, indent=2, default=str)
                return backup_filename
            except Exception as e:
                st.error(f"Error creating backup file: {str(e)}")
                return None
        return None
    else:
        # Fallback to file storage
        ensure_data_directory()
        backup_data_dict = {
            'portfolio': load_portfolio(),
            'watchlist': load_watchlist(),
            'transactions': load_transactions(),
            'trading_rules': load_trading_rules(),
            'backup_date': datetime.now().isoformat()
        }
        
        # Convert datetime objects to strings for JSON serialization
        if 'trading_rules' in backup_data_dict:
            for rule in backup_data_dict['trading_rules']:
                if 'created_at' in rule and hasattr(rule['created_at'], 'isoformat'):
                    rule['created_at'] = rule['created_at'].isoformat()
        
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(f"data/{backup_filename}", 'w') as f:
                json.dump(backup_data_dict, f, indent=2)
            return backup_filename
        except Exception as e:
            st.error(f"Error creating backup: {str(e)}")
            return None

def get_storage_info():
    """Get information about current storage method and statistics"""
    if USE_DATABASE:
        stats = get_database_stats()
        return {
            'storage_type': 'Database (PostgreSQL/SQLite)',
            'database_url': 'PostgreSQL' if 'postgresql' in str(DATABASE_URL).lower() else 'SQLite',
            'stats': stats
        }
    else:
        return {
            'storage_type': 'File Storage',
            'database_url': 'Not connected',
            'stats': {
                'portfolio_count': len(load_portfolio()),
                'transaction_count': len(load_transactions()),
                'watchlist_count': len(load_watchlist()),
                'trading_rules_count': len(load_trading_rules())
            }
        }

def export_transactions_csv():
    """Export transactions to CSV for download"""
    transactions = load_transactions()
    if transactions:
        df = pd.DataFrame(transactions)
        return df.to_csv(index=False)
    return None

def export_portfolio_csv():
    """Export current portfolio to CSV for download"""
    portfolio = load_portfolio()
    if portfolio:
        portfolio_data = []
        for symbol, quantity in portfolio.items():
            portfolio_data.append({
                'Symbol': symbol,
                'Quantity': quantity
            })
        
        df = pd.DataFrame(portfolio_data)
        return df.to_csv(index=False)
    return None

def clear_all_data():
    """Clear all saved data"""
    files_to_remove = [PORTFOLIO_FILE, WATCHLIST_FILE, TRANSACTIONS_FILE, TRADING_RULES_FILE]
    
    for file_path in files_to_remove:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            st.error(f"Error removing {file_path}: {str(e)}")
    
    # Clear session state
    st.session_state.portfolio = {}
    st.session_state.watchlist = []
    st.session_state.transactions = []
    st.session_state.trading_rules = []
    
    st.success("All data cleared successfully!")

def backup_data():
    """Create a backup of all data"""
    ensure_data_directory()
    backup_data = {
        'portfolio': load_portfolio(),
        'watchlist': load_watchlist(),
        'transactions': load_transactions(),
        'trading_rules': load_trading_rules(),
        'backup_date': datetime.now().isoformat()
    }
    
    # Convert datetime objects to strings for JSON serialization
    if 'trading_rules' in backup_data:
        for rule in backup_data['trading_rules']:
            if 'created_at' in rule and hasattr(rule['created_at'], 'isoformat'):
                rule['created_at'] = rule['created_at'].isoformat()
    
    backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(f"data/{backup_filename}", 'w') as f:
            json.dump(backup_data, f, indent=2)
        return backup_filename
    except Exception as e:
        st.error(f"Error creating backup: {str(e)}")
        return None

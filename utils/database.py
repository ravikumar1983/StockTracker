import os
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# Database setup - Use SQLite for local development, PostgreSQL for deployment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    # Fallback to SQLite for local development
    if not os.path.exists('data'):
        os.makedirs('data')
    DATABASE_URL = 'sqlite:///data/trading_app.db'

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Portfolio(Base):
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    quantity = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    type = Column(String)  # 'buy' or 'sell'
    quantity = Column(Float)
    price = Column(Float)
    total = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Watchlist(Base):
    __tablename__ = "watchlist"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True)
    added_at = Column(DateTime, default=datetime.utcnow)

class TradingRule(Base):
    __tablename__ = "trading_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(String, unique=True, index=True)
    symbol = Column(String, index=True)
    type = Column(String)  # 'price_alert', 'stop_loss', etc.
    target_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    alert_type = Column(String, nullable=True)  # 'above', 'below'
    percentage_threshold = Column(Float, nullable=True)
    direction = Column(String, nullable=True)  # 'up', 'down'
    volume_threshold = Column(Float, nullable=True)
    comparison = Column(String, nullable=True)  # 'above', 'below'
    quantity = Column(Float, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    rule_data = Column(Text)  # JSON string for additional rule data

def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        st.error(f"Error initializing database: {str(e)}")
        return False

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

def close_db(db):
    """Close database session"""
    if db:
        db.close()

# Portfolio operations
def save_portfolio_to_db(portfolio_dict):
    """Save portfolio to database"""
    db = get_db()
    if not db:
        return False
    
    try:
        # Clear existing portfolio
        db.query(Portfolio).delete()
        
        # Add new portfolio data
        for symbol, quantity in portfolio_dict.items():
            portfolio_item = Portfolio(symbol=symbol, quantity=quantity)
            db.add(portfolio_item)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Error saving portfolio: {str(e)}")
        return False
    finally:
        close_db(db)

def load_portfolio_from_db():
    """Load portfolio from database"""
    db = get_db()
    if not db:
        return {}
    
    try:
        portfolio_items = db.query(Portfolio).all()
        portfolio = {item.symbol: item.quantity for item in portfolio_items}
        return portfolio
    except Exception as e:
        st.error(f"Error loading portfolio: {str(e)}")
        return {}
    finally:
        close_db(db)

# Transaction operations
def add_transaction_to_db(symbol, transaction_type, quantity, price, date=None):
    """Add transaction to database"""
    db = get_db()
    if not db:
        return False
    
    try:
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        
        total = quantity * price
        
        transaction = Transaction(
            symbol=symbol.upper(),
            type=transaction_type,
            quantity=quantity,
            price=price,
            total=total,
            date=date
        )
        
        db.add(transaction)
        db.commit()
        
        # Update portfolio
        portfolio = load_portfolio_from_db()
        
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
        
        save_portfolio_to_db(portfolio)
        return True
        
    except Exception as e:
        db.rollback()
        st.error(f"Error adding transaction: {str(e)}")
        return False
    finally:
        close_db(db)

def load_transactions_from_db():
    """Load transactions from database"""
    db = get_db()
    if not db:
        return []
    
    try:
        transactions = db.query(Transaction).order_by(Transaction.date.desc()).all()
        transaction_list = []
        
        for trans in transactions:
            transaction_list.append({
                'symbol': trans.symbol,
                'type': trans.type,
                'quantity': trans.quantity,
                'price': trans.price,
                'total': trans.total,
                'date': trans.date.isoformat()
            })
        
        return transaction_list
    except Exception as e:
        st.error(f"Error loading transactions: {str(e)}")
        return []
    finally:
        close_db(db)

# Watchlist operations
def save_watchlist_to_db(watchlist_symbols):
    """Save watchlist to database"""
    db = get_db()
    if not db:
        return False
    
    try:
        # Clear existing watchlist
        db.query(Watchlist).delete()
        
        # Add new watchlist items
        for symbol in watchlist_symbols:
            watchlist_item = Watchlist(symbol=symbol)
            db.add(watchlist_item)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Error saving watchlist: {str(e)}")
        return False
    finally:
        close_db(db)

def load_watchlist_from_db():
    """Load watchlist from database"""
    db = get_db()
    if not db:
        return []
    
    try:
        watchlist_items = db.query(Watchlist).order_by(Watchlist.added_at).all()
        watchlist = [item.symbol for item in watchlist_items]
        return watchlist
    except Exception as e:
        st.error(f"Error loading watchlist: {str(e)}")
        return []
    finally:
        close_db(db)

# Trading rules operations
def save_trading_rules_to_db(trading_rules):
    """Save trading rules to database"""
    db = get_db()
    if not db:
        return False
    
    try:
        # Clear existing rules
        db.query(TradingRule).delete()
        
        # Add new rules
        for rule in trading_rules:
            # Convert datetime to string if needed
            created_at = rule.get('created_at')
            if hasattr(created_at, 'isoformat'):
                created_at = created_at
            elif isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except:
                    created_at = datetime.now()
            else:
                created_at = datetime.now()
            
            trading_rule = TradingRule(
                rule_id=rule.get('id'),
                symbol=rule.get('symbol'),
                type=rule.get('type'),
                target_price=rule.get('target_price'),
                stop_price=rule.get('stop_price'),
                alert_type=rule.get('alert_type'),
                percentage_threshold=rule.get('percentage_threshold'),
                direction=rule.get('direction'),
                volume_threshold=rule.get('volume_threshold'),
                comparison=rule.get('comparison'),
                quantity=rule.get('quantity'),
                active=rule.get('active', True),
                created_at=created_at,
                rule_data=json.dumps(rule)  # Store complete rule as JSON
            )
            
            db.add(trading_rule)
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Error saving trading rules: {str(e)}")
        return False
    finally:
        close_db(db)

def load_trading_rules_from_db():
    """Load trading rules from database"""
    db = get_db()
    if not db:
        return []
    
    try:
        rule_items = db.query(TradingRule).order_by(TradingRule.created_at).all()
        rules = []
        
        for rule_item in rule_items:
            try:
                # Try to load from JSON data first
                if rule_item.rule_data is not None:
                    rule = json.loads(rule_item.rule_data)
                    # Ensure created_at is datetime object
                    if isinstance(rule.get('created_at'), str):
                        rule['created_at'] = datetime.fromisoformat(rule['created_at'])
                else:
                    # Fallback to individual columns
                    rule = {
                        'id': rule_item.rule_id,
                        'symbol': rule_item.symbol,
                        'type': rule_item.type,
                        'active': rule_item.active,
                        'created_at': rule_item.created_at
                    }
                    
                    # Add type-specific fields
                    if rule_item.target_price is not None:
                        rule['target_price'] = rule_item.target_price
                    if rule_item.stop_price is not None:
                        rule['stop_price'] = rule_item.stop_price
                    if rule_item.alert_type is not None:
                        rule['alert_type'] = rule_item.alert_type
                    if rule_item.percentage_threshold is not None:
                        rule['percentage_threshold'] = rule_item.percentage_threshold
                    if rule_item.direction is not None:
                        rule['direction'] = rule_item.direction
                    if rule_item.volume_threshold is not None:
                        rule['volume_threshold'] = rule_item.volume_threshold
                    if rule_item.comparison is not None:
                        rule['comparison'] = rule_item.comparison
                    if rule_item.quantity is not None:
                        rule['quantity'] = rule_item.quantity
                
                rules.append(rule)
            except Exception as e:
                continue
        
        return rules
    except Exception as e:
        st.error(f"Error loading trading rules: {str(e)}")
        return []
    finally:
        close_db(db)

# Database utility functions
def clear_all_data_from_db():
    """Clear all data from database"""
    db = get_db()
    if not db:
        return False
    
    try:
        db.query(Portfolio).delete()
        db.query(Transaction).delete()
        db.query(Watchlist).delete()
        db.query(TradingRule).delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        st.error(f"Error clearing database: {str(e)}")
        return False
    finally:
        close_db(db)

def backup_database():
    """Create a backup of all database data"""
    try:
        backup_data = {
            'portfolio': load_portfolio_from_db(),
            'watchlist': load_watchlist_from_db(),
            'transactions': load_transactions_from_db(),
            'trading_rules': load_trading_rules_from_db(),
            'backup_date': datetime.now().isoformat()
        }
        return backup_data
    except Exception as e:
        st.error(f"Error creating backup: {str(e)}")
        return None

def get_database_stats():
    """Get database statistics"""
    db = get_db()
    if not db:
        return {}
    
    try:
        stats = {
            'portfolio_count': db.query(Portfolio).count(),
            'transaction_count': db.query(Transaction).count(),
            'watchlist_count': db.query(Watchlist).count(),
            'trading_rules_count': db.query(TradingRule).count()
        }
        return stats
    except Exception as e:
        st.error(f"Error getting database stats: {str(e)}")
        return {}
    finally:
        close_db(db)
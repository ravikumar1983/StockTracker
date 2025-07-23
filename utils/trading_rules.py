from datetime import datetime
import yfinance as yf
from utils.stock_data import get_stock_price, get_stock_info

def create_price_alert(symbol, target_price, alert_type='above'):
    """Create a price alert rule"""
    return {
        'id': f"price_alert_{symbol}_{datetime.now().timestamp()}",
        'type': 'price_alert',
        'symbol': symbol,
        'target_price': target_price,
        'alert_type': alert_type,  # 'above' or 'below'
        'created_at': datetime.now(),
        'active': True
    }

def create_stop_loss(symbol, stop_price, portfolio_quantity):
    """Create a stop loss rule"""
    return {
        'id': f"stop_loss_{symbol}_{datetime.now().timestamp()}",
        'type': 'stop_loss',
        'symbol': symbol,
        'stop_price': stop_price,
        'quantity': portfolio_quantity,
        'created_at': datetime.now(),
        'active': True
    }

def create_take_profit(symbol, target_price, portfolio_quantity):
    """Create a take profit rule"""
    return {
        'id': f"take_profit_{symbol}_{datetime.now().timestamp()}",
        'type': 'take_profit',
        'symbol': symbol,
        'target_price': target_price,
        'quantity': portfolio_quantity,
        'created_at': datetime.now(),
        'active': True
    }

def create_percentage_change_alert(symbol, percentage_threshold, direction='up'):
    """Create a percentage change alert"""
    return {
        'id': f"pct_change_{symbol}_{datetime.now().timestamp()}",
        'type': 'percentage_change',
        'symbol': symbol,
        'percentage_threshold': percentage_threshold,
        'direction': direction,  # 'up' or 'down'
        'created_at': datetime.now(),
        'active': True
    }

def create_volume_alert(symbol, volume_threshold, comparison='above'):
    """Create a volume alert"""
    return {
        'id': f"volume_{symbol}_{datetime.now().timestamp()}",
        'type': 'volume_alert',
        'symbol': symbol,
        'volume_threshold': volume_threshold,
        'comparison': comparison,  # 'above' or 'below'
        'created_at': datetime.now(),
        'active': True
    }

def check_trading_rules(rule, portfolio=None):
    """Check if a trading rule condition is met"""
    if not rule.get('active', False):
        return None
    
    symbol = rule['symbol']
    rule_type = rule['type']
    
    try:
        current_price = get_stock_price(symbol)
        if not current_price:
            return None
        
        stock_info = get_stock_info(symbol)
        if not stock_info:
            return None
        
        alert = None
        
        if rule_type == 'price_alert':
            target_price = rule['target_price']
            alert_type = rule['alert_type']
            
            if alert_type == 'above' and current_price >= target_price:
                alert = {
                    'type': 'warning',
                    'message': f"{symbol} has reached target price ${target_price:.2f} (Current: ${current_price:.2f})",
                    'rule_id': rule['id'],
                    'symbol': symbol,
                    'timestamp': datetime.now()
                }
            elif alert_type == 'below' and current_price <= target_price:
                alert = {
                    'type': 'warning',
                    'message': f"{symbol} has dropped to ${target_price:.2f} (Current: ${current_price:.2f})",
                    'rule_id': rule['id'],
                    'symbol': symbol,
                    'timestamp': datetime.now()
                }
        
        elif rule_type == 'stop_loss':
            stop_price = rule['stop_price']
            
            if current_price <= stop_price:
                alert = {
                    'type': 'warning',
                    'message': f"🚨 STOP LOSS TRIGGERED: {symbol} at ${current_price:.2f} (Stop: ${stop_price:.2f})",
                    'rule_id': rule['id'],
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'action_suggested': f"Consider selling {rule.get('quantity', 0)} shares"
                }
        
        elif rule_type == 'take_profit':
            target_price = rule['target_price']
            
            if current_price >= target_price:
                alert = {
                    'type': 'success',
                    'message': f"🎯 TAKE PROFIT: {symbol} reached ${target_price:.2f} (Current: ${current_price:.2f})",
                    'rule_id': rule['id'],
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'action_suggested': f"Consider selling {rule.get('quantity', 0)} shares"
                }
        
        elif rule_type == 'percentage_change':
            day_change_percent = stock_info.get('day_change_percent', 0)
            percentage_threshold = rule['percentage_threshold']
            direction = rule['direction']
            
            if direction == 'up' and day_change_percent >= percentage_threshold:
                alert = {
                    'type': 'info',
                    'message': f"📈 {symbol} up {day_change_percent:.2f}% today (Threshold: {percentage_threshold:.2f}%)",
                    'rule_id': rule['id'],
                    'symbol': symbol,
                    'timestamp': datetime.now()
                }
            elif direction == 'down' and day_change_percent <= -percentage_threshold:
                alert = {
                    'type': 'warning',
                    'message': f"📉 {symbol} down {abs(day_change_percent):.2f}% today (Threshold: {percentage_threshold:.2f}%)",
                    'rule_id': rule['id'],
                    'symbol': symbol,
                    'timestamp': datetime.now()
                }
        
        elif rule_type == 'volume_alert':
            current_volume = stock_info.get('volume', 0)
            avg_volume = stock_info.get('avg_volume', 0)
            volume_threshold = rule['volume_threshold']
            comparison = rule['comparison']
            
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            if comparison == 'above' and volume_ratio >= volume_threshold:
                alert = {
                    'type': 'info',
                    'message': f"📊 {symbol} volume {volume_ratio:.1f}x average (Threshold: {volume_threshold:.1f}x)",
                    'rule_id': rule['id'],
                    'symbol': symbol,
                    'timestamp': datetime.now()
                }
            elif comparison == 'below' and volume_ratio <= volume_threshold:
                alert = {
                    'type': 'info',
                    'message': f"📊 {symbol} low volume {volume_ratio:.1f}x average (Threshold: {volume_threshold:.1f}x)",
                    'rule_id': rule['id'],
                    'symbol': symbol,
                    'timestamp': datetime.now()
                }
        
        return alert
        
    except Exception as e:
        return {
            'type': 'error',
            'message': f"Error checking rule for {symbol}: {str(e)}",
            'rule_id': rule['id'],
            'symbol': symbol,
            'timestamp': datetime.now()
        }

def get_rule_summary(rule):
    """Get a human-readable summary of a trading rule"""
    rule_type = rule['type']
    symbol = rule['symbol']
    
    if rule_type == 'price_alert':
        direction = "above" if rule['alert_type'] == 'above' else "below"
        return f"Alert when {symbol} goes {direction} ${rule['target_price']:.2f}"
    
    elif rule_type == 'stop_loss':
        return f"Stop loss for {symbol} at ${rule['stop_price']:.2f}"
    
    elif rule_type == 'take_profit':
        return f"Take profit for {symbol} at ${rule['target_price']:.2f}"
    
    elif rule_type == 'percentage_change':
        direction = "up" if rule['direction'] == 'up' else "down"
        return f"Alert when {symbol} moves {direction} {rule['percentage_threshold']:.1f}%"
    
    elif rule_type == 'volume_alert':
        comparison = "above" if rule['comparison'] == 'above' else "below"
        return f"Alert when {symbol} volume is {comparison} {rule['volume_threshold']:.1f}x average"
    
    return f"Unknown rule type for {symbol}"

def validate_rule(rule, portfolio=None):
    """Validate a trading rule"""
    errors = []
    
    if not rule.get('symbol'):
        errors.append("Symbol is required")
    
    if not rule.get('type'):
        errors.append("Rule type is required")
    
    rule_type = rule.get('type')
    
    if rule_type in ['price_alert', 'stop_loss', 'take_profit']:
        price_field = 'target_price' if rule_type != 'stop_loss' else 'stop_price'
        if not rule.get(price_field) or rule.get(price_field) <= 0:
            errors.append(f"{price_field.replace('_', ' ').title()} must be greater than 0")
    
    elif rule_type == 'percentage_change':
        if not rule.get('percentage_threshold') or rule.get('percentage_threshold') <= 0:
            errors.append("Percentage threshold must be greater than 0")
        
        if rule.get('direction') not in ['up', 'down']:
            errors.append("Direction must be 'up' or 'down'")
    
    elif rule_type == 'volume_alert':
        if not rule.get('volume_threshold') or rule.get('volume_threshold') <= 0:
            errors.append("Volume threshold must be greater than 0")
        
        if rule.get('comparison') not in ['above', 'below']:
            errors.append("Comparison must be 'above' or 'below'")
    
    # Check if symbol is valid (optional - you might want to skip this for performance)
    if rule.get('symbol') and len(errors) == 0:
        try:
            stock_info = get_stock_info(rule['symbol'])
            if not stock_info:
                errors.append(f"Invalid symbol: {rule['symbol']}")
        except:
            errors.append(f"Could not validate symbol: {rule['symbol']}")
    
    return errors

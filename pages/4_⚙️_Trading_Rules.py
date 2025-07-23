import streamlit as st
import pandas as pd
from datetime import datetime
from utils.trading_rules import (
    create_price_alert, 
    create_stop_loss, 
    create_take_profit,
    create_percentage_change_alert,
    create_volume_alert,
    check_trading_rules,
    get_rule_summary,
    validate_rule
)
from utils.data_persistence import save_trading_rules, load_trading_rules
from utils.stock_data import get_stock_info

st.set_page_config(page_title="Trading Rules", page_icon="⚙️", layout="wide")

def main():
    st.title("⚙️ Trading Rules & Alerts")
    
    # Initialize session state
    if 'trading_rules' not in st.session_state:
        st.session_state.trading_rules = load_trading_rules()
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = {}
    
    # Sidebar for creating new rules
    with st.sidebar:
        st.header("Create New Rule")
        
        rule_type = st.selectbox("Rule Type", [
            "Price Alert",
            "Stop Loss",
            "Take Profit", 
            "Percentage Change Alert",
            "Volume Alert"
        ])
        
        symbol = st.text_input("Stock Symbol", placeholder="AAPL").upper()
        
        # Validate symbol
        if symbol:
            try:
                stock_info = get_stock_info(symbol)
                if stock_info:
                    st.success(f"✓ {symbol}: ${stock_info['price']:.2f}")
                    current_price = stock_info['price']
                else:
                    st.error("Invalid symbol")
                    symbol = None
            except:
                st.error("Error validating symbol")
                symbol = None
        
        if symbol and stock_info:
            # Rule-specific inputs
            if rule_type == "Price Alert":
                st.subheader("Price Alert Settings")
                target_price = st.number_input("Target Price", value=current_price, step=0.01)
                alert_type = st.selectbox("Alert Type", ["Above", "Below"])
                
                if st.button("Create Price Alert"):
                    rule = create_price_alert(symbol, target_price, alert_type.lower())
                    errors = validate_rule(rule)
                    
                    if not errors:
                        st.session_state.trading_rules.append(rule)
                        save_trading_rules(st.session_state.trading_rules)
                        st.success("Price alert created!")
                        st.rerun()
                    else:
                        for error in errors:
                            st.error(error)
            
            elif rule_type == "Stop Loss":
                st.subheader("Stop Loss Settings")
                
                if symbol in st.session_state.portfolio:
                    quantity = st.session_state.portfolio[symbol]
                    st.info(f"You own {quantity} shares of {symbol}")
                    
                    stop_price = st.number_input("Stop Loss Price", value=current_price * 0.9, step=0.01)
                    loss_amount = (current_price - stop_price) * quantity
                    loss_percent = ((current_price - stop_price) / current_price) * 100
                    
                    st.write(f"Potential loss: ${loss_amount:.2f} ({loss_percent:.1f}%)")
                    
                    if st.button("Create Stop Loss"):
                        rule = create_stop_loss(symbol, stop_price, quantity)
                        errors = validate_rule(rule, st.session_state.portfolio)
                        
                        if not errors:
                            st.session_state.trading_rules.append(rule)
                            save_trading_rules(st.session_state.trading_rules)
                            st.success("Stop loss created!")
                            st.rerun()
                        else:
                            for error in errors:
                                st.error(error)
                else:
                    st.warning(f"You don't own any {symbol} shares")
                    stop_price = st.number_input("Stop Loss Price", value=current_price * 0.9, step=0.01)
                    
                    if st.button("Create Stop Loss (Hypothetical)"):
                        rule = create_stop_loss(symbol, stop_price, 0)
                        errors = validate_rule(rule)
                        
                        if not errors:
                            st.session_state.trading_rules.append(rule)
                            save_trading_rules(st.session_state.trading_rules)
                            st.success("Stop loss created!")
                            st.rerun()
                        else:
                            for error in errors:
                                st.error(error)
            
            elif rule_type == "Take Profit":
                st.subheader("Take Profit Settings")
                
                if symbol in st.session_state.portfolio:
                    quantity = st.session_state.portfolio[symbol]
                    st.info(f"You own {quantity} shares of {symbol}")
                    
                    target_price = st.number_input("Take Profit Price", value=current_price * 1.1, step=0.01)
                    profit_amount = (target_price - current_price) * quantity
                    profit_percent = ((target_price - current_price) / current_price) * 100
                    
                    st.write(f"Potential profit: ${profit_amount:.2f} ({profit_percent:.1f}%)")
                    
                    if st.button("Create Take Profit"):
                        rule = create_take_profit(symbol, target_price, quantity)
                        errors = validate_rule(rule, st.session_state.portfolio)
                        
                        if not errors:
                            st.session_state.trading_rules.append(rule)
                            save_trading_rules(st.session_state.trading_rules)
                            st.success("Take profit created!")
                            st.rerun()
                        else:
                            for error in errors:
                                st.error(error)
                else:
                    st.warning(f"You don't own any {symbol} shares")
                    target_price = st.number_input("Take Profit Price", value=current_price * 1.1, step=0.01)
                    
                    if st.button("Create Take Profit (Hypothetical)"):
                        rule = create_take_profit(symbol, target_price, 0)
                        errors = validate_rule(rule)
                        
                        if not errors:
                            st.session_state.trading_rules.append(rule)
                            save_trading_rules(st.session_state.trading_rules)
                            st.success("Take profit created!")
                            st.rerun()
                        else:
                            for error in errors:
                                st.error(error)
            
            elif rule_type == "Percentage Change Alert":
                st.subheader("Percentage Change Alert")
                
                percentage_threshold = st.number_input("Percentage Threshold", value=5.0, step=0.1)
                direction = st.selectbox("Direction", ["Up", "Down"])
                
                if st.button("Create Percentage Alert"):
                    rule = create_percentage_change_alert(symbol, percentage_threshold, direction.lower())
                    errors = validate_rule(rule)
                    
                    if not errors:
                        st.session_state.trading_rules.append(rule)
                        save_trading_rules(st.session_state.trading_rules)
                        st.success("Percentage change alert created!")
                        st.rerun()
                    else:
                        for error in errors:
                            st.error(error)
            
            elif rule_type == "Volume Alert":
                st.subheader("Volume Alert")
                
                avg_volume = stock_info.get('avg_volume', 0)
                current_volume = stock_info.get('volume', 0)
                
                if avg_volume > 0:
                    current_ratio = current_volume / avg_volume
                    st.info(f"Current volume: {current_volume:,} ({current_ratio:.1f}x average)")
                
                volume_threshold = st.number_input("Volume Threshold (x average)", value=2.0, step=0.1)
                comparison = st.selectbox("Comparison", ["Above", "Below"])
                
                if st.button("Create Volume Alert"):
                    rule = create_volume_alert(symbol, volume_threshold, comparison.lower())
                    errors = validate_rule(rule)
                    
                    if not errors:
                        st.session_state.trading_rules.append(rule)
                        save_trading_rules(st.session_state.trading_rules)
                        st.success("Volume alert created!")
                        st.rerun()
                    else:
                        for error in errors:
                            st.error(error)
    
    # Main content area
    if not st.session_state.trading_rules:
        st.info("No trading rules created yet. Use the sidebar to create your first rule!")
        
        # Show rule examples
        st.subheader("Example Trading Rules")
        
        examples = [
            "**Price Alert**: Get notified when AAPL goes above $200",
            "**Stop Loss**: Automatically sell TSLA if it drops to $180",
            "**Take Profit**: Get alerted when MSFT reaches your target of $400",
            "**Percentage Alert**: Know when NVDA moves up or down 5% in a day",
            "**Volume Alert**: Get notified when unusual volume occurs (2x average)"
        ]
        
        for example in examples:
            st.write(f"• {example}")
        
        return
    
    # Display existing rules
    st.subheader(f"Active Trading Rules ({len(st.session_state.trading_rules)})")
    
    # Filter and sort options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        rule_filter = st.selectbox("Filter by Type", ["All"] + list(set([rule['type'] for rule in st.session_state.trading_rules])))
    
    with col2:
        symbol_filter = st.selectbox("Filter by Symbol", ["All"] + list(set([rule['symbol'] for rule in st.session_state.trading_rules])))
    
    with col3:
        status_filter = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
    
    # Apply filters
    filtered_rules = st.session_state.trading_rules.copy()
    
    if rule_filter != "All":
        filtered_rules = [rule for rule in filtered_rules if rule['type'] == rule_filter]
    
    if symbol_filter != "All":
        filtered_rules = [rule for rule in filtered_rules if rule['symbol'] == symbol_filter]
    
    if status_filter != "All":
        active_status = status_filter == "Active"
        filtered_rules = [rule for rule in filtered_rules if rule.get('active', True) == active_status]
    
    # Display rules
    if filtered_rules:
        rules_data = []
        
        for i, rule in enumerate(filtered_rules):
            # Check if rule is triggered
            alert = check_trading_rules(rule, st.session_state.portfolio)
            status = "🔴 Triggered" if alert else "🟢 Active" if rule.get('active', True) else "⚪ Inactive"
            
            rules_data.append({
                'Index': i,
                'Symbol': rule['symbol'],
                'Type': rule['type'].replace('_', ' ').title(),
                'Description': get_rule_summary(rule),
                'Status': status,
                'Created': rule['created_at'].strftime('%Y-%m-%d %H:%M') if isinstance(rule['created_at'], datetime) else rule['created_at']
            })
        
        df_rules = pd.DataFrame(rules_data)
        
        # Display in cards format
        for i, row in df_rules.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.write(f"**{row['Symbol']} - {row['Type']}**")
                    st.write(row['Description'])
                
                with col2:
                    st.write(f"Created: {row['Created']}")
                    st.write(row['Status'])
                
                with col3:
                    rule_index = next(j for j, r in enumerate(st.session_state.trading_rules) if r['id'] == filtered_rules[row['Index']]['id'])
                    
                    if st.button("Toggle", key=f"toggle_{rule_index}"):
                        st.session_state.trading_rules[rule_index]['active'] = not st.session_state.trading_rules[rule_index].get('active', True)
                        save_trading_rules(st.session_state.trading_rules)
                        st.rerun()
                
                with col4:
                    if st.button("Delete", key=f"delete_{rule_index}"):
                        st.session_state.trading_rules.pop(rule_index)
                        save_trading_rules(st.session_state.trading_rules)
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("No rules match the current filters")
    
    # Check all rules and show alerts
    st.subheader("🚨 Active Alerts")
    
    alerts = []
    for rule in st.session_state.trading_rules:
        if rule.get('active', True):
            try:
                alert = check_trading_rules(rule, st.session_state.portfolio)
                if alert:
                    alerts.append(alert)
            except Exception as e:
                continue
    
    if alerts:
        for alert in alerts[-10:]:  # Show last 10 alerts
            if alert['type'] == 'warning':
                st.warning(f"⚠️ {alert['message']}")
            elif alert['type'] == 'success':
                st.success(f"✅ {alert['message']}")
            elif alert['type'] == 'error':
                st.error(f"❌ {alert['message']}")
            else:
                st.info(f"ℹ️ {alert['message']}")
            
            # Show suggested action if available
            if 'action_suggested' in alert:
                st.write(f"💡 Suggested action: {alert['action_suggested']}")
    else:
        st.info("No active alerts at this time")
    
    # Rule statistics
    st.markdown("---")
    st.subheader("📊 Rule Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_rules = len(st.session_state.trading_rules)
        st.metric("Total Rules", total_rules)
    
    with col2:
        active_rules = len([rule for rule in st.session_state.trading_rules if rule.get('active', True)])
        st.metric("Active Rules", active_rules)
    
    with col3:
        triggered_rules = len(alerts)
        st.metric("Triggered Today", triggered_rules)
    
    with col4:
        unique_symbols = len(set([rule['symbol'] for rule in st.session_state.trading_rules]))
        st.metric("Symbols Monitored", unique_symbols)
    
    # Rule type distribution
    if st.session_state.trading_rules:
        rule_types = [rule['type'] for rule in st.session_state.trading_rules]
        type_counts = pd.Series(rule_types).value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Rules by Type")
            for rule_type, count in type_counts.items():
                st.write(f"• {rule_type.replace('_', ' ').title()}: {count}")
        
        with col2:
            st.subheader("Rules by Symbol")
            symbol_counts = pd.Series([rule['symbol'] for rule in st.session_state.trading_rules]).value_counts().head(5)
            for symbol, count in symbol_counts.items():
                st.write(f"• {symbol}: {count}")

if __name__ == "__main__":
    main()

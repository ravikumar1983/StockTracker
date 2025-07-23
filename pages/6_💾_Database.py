import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_persistence import get_storage_info, backup_data, clear_all_data

st.set_page_config(page_title="Database", page_icon="💾", layout="wide")

def main():
    st.title("💾 Database Management")
    
    # Get storage information
    storage_info = get_storage_info()
    
    # Display current storage configuration
    st.subheader("📊 Storage Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Storage Type:** {storage_info['storage_type']}")
        st.info(f"**Database:** {storage_info['database_url']}")
    
    with col2:
        st.write("**Current Data Counts:**")
        stats = storage_info['stats']
        for key, value in stats.items():
            st.write(f"• {key.replace('_', ' ').title()}: {value}")
    
    st.markdown("---")
    
    # Storage type explanation
    st.subheader("🏗️ Database Architecture")
    
    if "SQLite" in storage_info['database_url']:
        st.success("**SQLite Database** - Perfect for local development")
        st.write("""
        ✅ **Advantages:**
        - Lightweight and fast
        - No server setup required
        - Single file storage (data/trading_app.db)
        - Perfect for personal use
        - Zero configuration
        
        📁 **Database Location:** `data/trading_app.db`
        """)
    elif "PostgreSQL" in storage_info['database_url']:
        st.success("**PostgreSQL Database** - Production ready")
        st.write("""
        ✅ **Advantages:**
        - Scalable and robust
        - Concurrent user support
        - Advanced features
        - Production ready
        - Data integrity and ACID compliance
        """)
    else:
        st.warning("**File Storage** - Fallback mode")
        st.write("""
        ⚠️ **Note:** Using file-based storage as fallback
        - Data stored in JSON/CSV files
        - Good for testing and development
        - Consider setting up a database for better performance
        """)
    
    st.markdown("---")
    
    # Database operations
    st.subheader("🔧 Database Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Backup Data**")
        st.write("Create a backup of all your trading data")
        
        if st.button("Create Backup", type="primary"):
            with st.spinner("Creating backup..."):
                backup_filename = backup_data()
                if backup_filename:
                    st.success(f"Backup created: {backup_filename}")
                else:
                    st.error("Failed to create backup")
    
    with col2:
        st.write("**Clear All Data**")
        st.write("⚠️ This will permanently delete all data")
        
        if st.button("Clear All Data", type="secondary"):
            st.warning("Are you sure? This action cannot be undone!")
            if st.button("Yes, Clear Everything", type="secondary"):
                with st.spinner("Clearing all data..."):
                    success = clear_all_data()
                    if success:
                        st.rerun()
    
    with col3:
        st.write("**Refresh Data**")
        st.write("Reload data from storage")
        
        if st.button("Refresh", type="secondary"):
            # Clear session state to force reload
            for key in ['portfolio', 'watchlist', 'transactions', 'trading_rules']:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Data refreshed!")
            st.rerun()
    
    st.markdown("---")
    
    # Local setup instructions
    st.subheader("🏠 Local Setup Instructions")
    
    st.write("**For Local Development (SQLite):**")
    st.code("""
# The app automatically creates a SQLite database
# No setup required - just run the app!

# Database file location: data/trading_app.db
# Backup files location: data/backup_*.json
    """, language="bash")
    
    st.write("**For Production (PostgreSQL):**")
    st.code("""
# Set the DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:password@localhost/trading_app"

# Or in your .env file:
DATABASE_URL=postgresql://user:password@localhost/trading_app
    """, language="bash")
    
    st.markdown("---")
    
    # Performance tips
    st.subheader("⚡ Performance Tips")
    
    tips = [
        "**SQLite** is perfect for individual use with up to 10,000 transactions",
        "**PostgreSQL** recommended for multiple users or heavy trading activity",
        "Regular backups are automatically created with timestamps",
        "Database connections are pooled for optimal performance",
        "All data is cached in session for fast page navigation"
    ]
    
    for tip in tips:
        st.write(f"• {tip}")
    
    # Data migration info
    st.markdown("---")
    st.subheader("🔄 Data Migration")
    
    st.info("""
    **Switching Storage Methods:**
    
    The app automatically detects your storage method:
    1. If DATABASE_URL is set → Uses PostgreSQL/SQLite database
    2. If no DATABASE_URL → Falls back to file storage
    3. Backup files work with both methods for easy migration
    """)

if __name__ == "__main__":
    main()
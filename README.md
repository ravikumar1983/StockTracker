# Stock Trading Automation Tool

## Overview

This is a comprehensive stock trading automation and portfolio management application built with Streamlit. The application provides real-time stock data, portfolio tracking, watchlist management, trading rules automation, and performance analytics. It's designed as a multi-page web application that allows users to manage their stock investments with automated trading rules and detailed portfolio analytics.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a modular architecture with a main Streamlit app and multiple page modules, supported by utility libraries for core functionality.

### Frontend Architecture
- **Framework**: Streamlit for web UI
- **Visualization**: Plotly for interactive charts and graphs
- **Layout**: Multi-page application with sidebar navigation
- **State Management**: Streamlit session state for maintaining user data across pages

### Backend Architecture
- **Data Source**: Yahoo Finance API (via yfinance library) for real-time stock data
- **Data Processing**: Pandas for data manipulation and analysis
- **Caching**: Streamlit's @st.cache_data decorator for API response caching

### Data Storage
- **Database Integration**: Added PostgreSQL/SQLite database support with file-based fallback
- **Dual Storage Architecture**: 
  - **Primary**: SQLite database for local development (data/trading_app.db)
  - **Production**: PostgreSQL for deployment with DATABASE_URL environment variable
  - **Fallback**: JSON/CSV files when database unavailable
- **Data Structure**: 
  - Portfolio, transactions, watchlist, and trading rules stored in structured database tables
  - Automatic migration between storage methods
  - Database backup functionality with JSON export

## Key Components

### 1. Main Application (app.py)
- Entry point with dashboard overview
- Quick portfolio metrics display
- Navigation to other pages
- Real-time portfolio value calculations

### 2. Portfolio Management (pages/1_📈_Portfolio.py)
- Add/remove stock positions
- Portfolio value tracking
- Position details and metrics
- Transaction management
- Portfolio export functionality

### 3. Stock Search & Analysis (pages/2_🔍_Stock_Search.py)
- Stock symbol lookup and validation
- Company information display
- Stock categorization and analysis
- Integration with watchlist

### 4. Watchlist Management (pages/3_👀_Watchlist.py)
- Add/remove stocks from watchlist
- Real-time price monitoring
- Quick buy actions from watchlist
- Watchlist persistence

### 5. Trading Rules Engine (pages/4_⚙️_Trading_Rules.py)
- Price alerts (above/below thresholds)
- Stop loss automation
- Take profit rules
- Percentage change alerts
- Volume-based alerts
- Rule validation and management

### 6. Analytics Dashboard (pages/5_📊_Analytics.py)
- Portfolio performance metrics
- Return calculations
- Trading statistics
- Sector analysis
- Performance visualizations

### 7. Database Management (pages/6_💾_Database.py)
- Database configuration and status
- Data backup and restore functionality
- Clear all data operations
- Storage architecture information
- Performance monitoring

## Market Selection Feature
- **Multi-Market Support**: USA and Indian market selection in top right corner of Portfolio and Stock Search pages
- **Market-Specific Symbols**: Automatic symbol conversion (.NS suffix for Indian stocks)
- **Regional Data**: Market-appropriate stock suggestions and popular stocks list
- **Unified Interface**: Consistent market selection across all portfolio operations

### 7. Utility Modules
- **stock_data.py**: Yahoo Finance API integration, stock information retrieval
- **portfolio.py**: Portfolio calculations, performance metrics
- **data_persistence.py**: File I/O operations for data storage
- **trading_rules.py**: Trading rule creation and validation logic

## Data Flow

1. **Data Ingestion**: Real-time stock data fetched from Yahoo Finance API
2. **Caching Layer**: Streamlit caching reduces API calls and improves performance
3. **State Management**: Session state maintains user data during app usage
4. **Persistence**: User data saved to local JSON/CSV files
5. **Analytics Pipeline**: Portfolio and transaction data processed for metrics and visualizations

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **yfinance**: Yahoo Finance API client for stock data
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive data visualization
- **numpy**: Numerical computations

### Data Sources
- **Yahoo Finance**: Primary source for stock prices, company information, and historical data
- **No external database**: All data stored locally

### File Storage Structure
```
data/
├── portfolio.json          # User's stock holdings
├── watchlist.json         # Watchlisted stocks
├── transactions.csv       # Trading history
└── trading_rules.json     # Automated trading rules
```

## Deployment Strategy

### Local Development
- **Environment**: Python 3.7+ required
- **Dependencies**: Install via requirements.txt (implied)
- **Data Directory**: Automatically created on first run
- **Port**: Default Streamlit port (8501)

### Replit Deployment
- **Platform**: Optimized for Replit environment
- **Storage**: Uses Replit's file system for persistence
- **Configuration**: Streamlit page config optimized for wide layout
- **Caching**: TTL-based caching for API responses (60-300 seconds)

### Key Architectural Decisions

1. **File-based Storage**: Chosen for simplicity and ease of deployment without external database dependencies
2. **Streamlit Framework**: Selected for rapid development and built-in UI components
3. **Yahoo Finance API**: Free, reliable source for stock data with comprehensive coverage
4. **Modular Page Structure**: Enables clear separation of concerns and maintainable code
5. **Session State Management**: Provides seamless user experience across page navigation
6. **Caching Strategy**: Balances data freshness with API rate limiting

### Security Considerations
- **No Authentication**: Currently designed for single-user local deployment
- **API Rate Limiting**: Implemented through caching to respect Yahoo Finance limits
- **Data Privacy**: All data stored locally, no external data transmission except API calls

### Scalability Considerations
- **File Storage Limitation**: Current approach suitable for single user; would need database for multi-user
- **API Dependencies**: Relies on Yahoo Finance API availability
- **Memory Usage**: Session state and caching may impact memory with large portfolios

# System Architecture

The AI crypto trading bot is designed as a modular, event-driven system that combines technical analysis, AI-powered market insights, and robust risk management.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │  Core Trading   │    │   Outputs &     │
│                 │    │     Engine      │    │  Monitoring     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Coinbase API    │───▶│ Strategy Manager│───▶│ Web Dashboard   │
│ Market Data     │    │ Risk Manager    │    │ Daily Reports   │
│ Price Feeds     │    │ Portfolio Mgmt  │    │ Trade Execution │
│ Volume Data     │    │ AI Analyzer     │    │ Notifications   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Data Storage   │
                    ├─────────────────┤
                    │ Portfolio State │
                    │ Trade History   │
                    │ Performance     │
                    │ Configurations  │
                    └─────────────────┘
```

## Core Components

### 1. Main Trading Loop (`main.py`)

**Purpose**: Orchestrates the entire trading process
**Frequency**: Configurable (default: 60 minutes)

```python
def main_trading_loop():
    while True:
        try:
            # 1. Collect market data
            market_data = data_collector.collect_all_data()
            
            # 2. Update portfolio from exchange
            portfolio.update_from_exchange()
            
            # 3. Analyze with strategies + AI
            decision = strategy_manager.get_combined_signal(market_data)
            
            # 4. Apply risk management
            safe_decision = risk_manager.evaluate_decision(decision)
            
            # 5. Execute trades if approved
            if safe_decision['action'] != 'HOLD':
                execute_trade(safe_decision)
            
            # 6. Update performance tracking
            performance_tracker.take_snapshot()
            
            # 7. Sync dashboard
            dashboard_sync.update_dashboard()
            
        except Exception as e:
            logger.error(f"Trading loop error: {e}")
        
        time.sleep(DECISION_INTERVAL_MINUTES * 60)
```

### 2. Data Collection Layer

#### Data Collector (`data_collector.py`)
- **Market Data**: Real-time price, volume, order book data
- **Technical Indicators**: RSI, MACD, Bollinger Bands, moving averages
- **Data Validation**: Ensures data quality and freshness
- **Caching**: Reduces API calls and improves performance

```python
class DataCollector:
    def collect_all_data(self):
        return {
            'market_data': self.get_market_data(),
            'technical_indicators': self.calculate_indicators(),
            'portfolio_data': self.get_portfolio_state(),
            'timestamp': datetime.utcnow()
        }
```

#### Coinbase Client (`coinbase_client.py`)
- **API Integration**: Coinbase Advanced Trade API
- **Rate Limiting**: Respects API limits (10 req/sec)
- **Error Handling**: Retry logic with exponential backoff
- **Authentication**: EC private key authentication

### 3. Strategy Layer

#### Strategy Manager (`strategies/strategy_manager.py`)
- **Multi-Strategy Coordination**: Combines three strategies
- **Market Regime Detection**: Bull/Bear/Sideways identification
- **Dynamic Weight Adjustment**: Adapts to market conditions
- **Signal Combination**: Weighted decision making

#### Individual Strategies
- **Trend Following** (`strategies/trend_following_strategy.py`)
- **Mean Reversion** (`strategies/mean_reversion_strategy.py`)
- **Momentum** (`strategies/momentum_strategy.py`)

Each strategy implements:
```python
class BaseStrategy:
    def analyze(self, indicators, portfolio):
        return {
            'signal': 'BUY|SELL|HOLD',
            'confidence': 0-100,
            'reasoning': 'explanation',
            'position_multiplier': 0.5-1.5
        }
```

### 4. AI Analysis Layer

#### LLM Analyzer (`llm_analyzer.py`)
- **Model**: Google Gemini 3 Flash (primary), Gemini 3 Pro (fallback)
- **Library**: New `google-genai` unified SDK
- **Authentication**: Service account with Vertex AI
- **Location**: Global (required for preview models)

```python
class LLMAnalyzer:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=GOOGLE_CLOUD_PROJECT,
            location='global',
            credentials=credentials
        )
    
    def analyze_market(self, market_data, technical_signals):
        # Combines technical analysis with AI insights
        # Provides confidence adjustment and reasoning
        # Identifies market anomalies and news impacts
```

### 5. Risk Management Layer

#### Risk Manager (integrated in portfolio and strategies)
- **Position Sizing**: Based on risk level and portfolio size
- **Allocation Limits**: Maximum position sizes per asset
- **Stop Conditions**: Emergency stops and safety mechanisms
- **Validation**: Pre-trade risk checks

```python
class RiskManager:
    def evaluate_decision(self, decision, portfolio):
        # Check position limits
        # Validate trade size
        # Apply risk multipliers
        # Ensure EUR reserves
        return validated_decision
```

### 6. Portfolio Management

#### Portfolio (`portfolio.py`)
- **State Management**: Current holdings and values
- **Trade Execution**: Buy/sell order placement
- **Synchronization**: Exchange state updates
- **Persistence**: JSON-based state storage

```python
class Portfolio:
    def execute_trade(self, action, asset, amount):
        # Validate trade parameters
        # Place market order via Coinbase
        # Update local state
        # Log trade execution
```

### 7. Performance Tracking

#### Performance Tracker (`utils/performance_tracker.py`)
- **Snapshot System**: Regular portfolio snapshots
- **Metrics Calculation**: Returns, Sharpe ratio, drawdown
- **Historical Data**: Trade history and performance
- **Reset Capability**: Performance period management

#### Performance Calculator (`utils/performance_calculator.py`)
- **Return Calculations**: Total, annualized, CAGR
- **Risk Metrics**: Volatility, Sharpe ratio, Sortino ratio
- **Trading Performance**: Win rate, profit factor
- **Benchmarking**: Market vs trading performance

### 8. Monitoring & Reporting

#### Web Dashboard (`dashboard/`)
- **Real-time Data**: Portfolio status, recent trades
- **Performance Charts**: Historical performance visualization
- **AI Insights**: Latest analysis and reasoning
- **System Health**: Bot status and uptime

#### Daily Reports (`daily_report.py`)
- **Email Delivery**: Automated daily summaries
- **AI-Generated**: Comprehensive analysis using Gemini
- **Performance Summary**: 24-hour activity and insights
- **Error Reporting**: Issues and recommendations

### 9. Configuration Management

#### Config (`config.py`)
- **Environment Variables**: Centralized configuration
- **Type Safety**: Validation and type conversion
- **Defaults**: Sensible fallback values
- **Security**: Credential management

## Data Flow

### 1. Data Collection Flow
```
Coinbase API → Data Collector → Technical Indicators → Strategy Manager
     ↓
Market Data Validation → Caching → Error Handling
```

### 2. Decision Making Flow
```
Technical Indicators → Individual Strategies → Strategy Manager
                                                      ↓
Market Regime Detection → Weight Adjustment → Signal Combination
                                                      ↓
AI Analysis → LLM Analyzer → Confidence Adjustment → Final Decision
```

### 3. Risk Management Flow
```
Trading Decision → Risk Validation → Position Sizing → Trade Execution
                        ↓
Portfolio Limits → EUR Reserves → Safety Checks → Order Placement
```

### 4. Monitoring Flow
```
Portfolio State → Performance Tracker → Metrics Calculation
                        ↓
Dashboard Update → Daily Reports → Email Delivery
```

## Storage Architecture

### File-Based Storage
```
data/
├── portfolio.json          # Current portfolio state
├── performance_config.json # Performance tracking config
├── performance_data.json   # Historical snapshots
└── trades.json            # Trade history

logs/
├── supervisor.log         # Main application logs
├── daily_report.log       # Daily report generation
└── daily_report_*.txt     # Generated reports
```

### Data Persistence Strategy
- **Portfolio State**: JSON files with atomic writes
- **Performance Data**: Append-only with periodic cleanup
- **Trade History**: Immutable log with timestamps
- **Configuration**: Environment variables + file overrides

## Deployment Architecture

### Local Development
```
Python Virtual Environment
├── Main Application (main.py)
├── Dependencies (requirements.txt)
├── Configuration (.env)
└── Data Storage (data/, logs/)
```

### Cloud Deployment (GCP)
```
Compute Engine VM
├── Supervisor Process Manager
│   └── Python Application
├── Apache Web Server
│   └── Dashboard Files
├── Cron Jobs
│   └── Daily Reports
└── Persistent Storage
    ├── Application Data
    └── Log Files
```

### Service Management
- **Supervisor**: Process management and auto-restart
- **Systemd**: Service integration (optional)
- **Cron**: Scheduled tasks (daily reports)
- **Apache**: Web dashboard serving

## Security Architecture

### API Security
- **Coinbase**: EC private key authentication
- **Google Cloud**: Service account with minimal permissions
- **Rate Limiting**: Respect API limits and implement backoff

### Data Security
- **Credentials**: Environment variables only
- **Logs**: Sanitized (no sensitive data)
- **File Permissions**: Restricted access
- **Network**: HTTPS only for external communications

### Operational Security
- **Error Handling**: Graceful degradation
- **Input Validation**: All external data validated
- **Resource Limits**: Memory and CPU monitoring
- **Backup Strategy**: Configuration and data backups

## Scalability Considerations

### Performance Optimization
- **Caching**: Market data and indicator calculations
- **Async Operations**: Non-blocking API calls where possible
- **Batch Processing**: Multiple operations combined
- **Resource Management**: Memory and connection pooling

### Monitoring & Alerting
- **Health Checks**: System component monitoring
- **Performance Metrics**: Response times and success rates
- **Error Tracking**: Exception monitoring and alerting
- **Resource Usage**: CPU, memory, disk monitoring

### Future Enhancements
- **Database Integration**: Replace file-based storage
- **Microservices**: Split components into separate services
- **Load Balancing**: Multiple instance support
- **Real-time Streaming**: WebSocket data feeds

## Error Handling Strategy

### Graceful Degradation
1. **API Failures**: Use cached data, reduce trading frequency
2. **AI Failures**: Fall back to technical analysis only
3. **Exchange Issues**: Hold positions, retry with backoff
4. **System Errors**: Log, alert, continue with safe defaults

### Recovery Mechanisms
- **Automatic Restart**: Supervisor handles process crashes
- **State Recovery**: Portfolio state restored from files
- **Data Validation**: Corrupted data detection and repair
- **Manual Override**: Emergency stop and manual control

This architecture ensures robust, scalable, and maintainable cryptocurrency trading operations while prioritizing safety and risk management.
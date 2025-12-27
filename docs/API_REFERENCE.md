# API Reference

This document provides a comprehensive reference for the AI crypto trading bot's internal APIs, classes, and methods.

## Core Classes

### Config

Central configuration management class.

```python
from config import Config

config = Config()
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `COINBASE_API_KEY` | str | Coinbase API key |
| `COINBASE_API_SECRET` | str | Coinbase private key |
| `GOOGLE_CLOUD_PROJECT` | str | Google Cloud project ID |
| `TRADING_PAIRS` | List[str] | List of trading pairs |
| `RISK_LEVEL` | str | Risk level (LOW, MEDIUM, HIGH) |
| `SIMULATION_MODE` | bool | Whether to run in simulation mode |

#### Methods

```python
def validate_all() -> Dict[str, bool]:
    """Validate all configuration settings"""
    
def get_strategy_weights() -> Dict[str, float]:
    """Get current strategy weights"""
    
def update_strategy_weights(weights: Dict[str, float]) -> None:
    """Update strategy weights"""
```

### Portfolio

Portfolio management and state tracking.

```python
from portfolio import Portfolio

portfolio = Portfolio()
```

#### Methods

```python
def calculate_total_value() -> float:
    """Calculate total portfolio value in EUR"""
    
def execute_trade(action: str, asset: str, amount: float) -> Dict:
    """Execute a trade (BUY/SELL)"""
    
def update_from_exchange() -> None:
    """Sync portfolio state with exchange"""
    
def get_asset_allocation() -> Dict[str, float]:
    """Get current asset allocation percentages"""
    
def to_dict() -> Dict:
    """Convert portfolio to dictionary representation"""
```

### CoinbaseClient

Coinbase API integration.

```python
from coinbase_client import CoinbaseClient

client = CoinbaseClient()
```

#### Methods

```python
def get_accounts() -> List[Dict]:
    """Get all account balances"""
    
def get_product_ticker(product_id: str) -> Dict:
    """Get current price for a product"""
    
def create_market_order(product_id: str, side: str, amount: float) -> Dict:
    """Create a market order"""
    
def get_order(order_id: str) -> Dict:
    """Get order details by ID"""
    
def list_orders(product_id: str = None) -> List[Dict]:
    """List recent orders"""
```

### LLMAnalyzer

AI-powered market analysis using Google Gemini.

```python
from llm_analyzer import LLMAnalyzer

analyzer = LLMAnalyzer()
```

#### Methods

```python
def analyze_market(market_data: Dict, technical_indicators: Dict) -> Dict:
    """Analyze market conditions with AI"""
    
def analyze_with_llm(prompt: str) -> Dict:
    """Generic LLM analysis with custom prompt"""
    
def prepare_market_summary(market_data: Dict, indicators: Dict) -> str:
    """Prepare market data summary for analysis"""
```

## Strategy Classes

### Base Strategy Interface

All strategies implement this interface:

```python
from strategies.base_strategy import BaseStrategy

class CustomStrategy(BaseStrategy):
    def analyze(self, indicators: Dict, portfolio: Portfolio) -> Dict:
        """Analyze market and return trading signal"""
        return {
            'signal': 'BUY|SELL|HOLD',
            'confidence': 0-100,
            'reasoning': 'explanation',
            'position_multiplier': 0.5-1.5
        }
    
    def get_market_regime_suitability(self, regime: str) -> float:
        """Return suitability score (0-1) for market regime"""
        pass
```

### TrendFollowingStrategy

```python
from strategies.trend_following_strategy import TrendFollowingStrategy

strategy = TrendFollowingStrategy()
```

#### Methods

```python
def calculate_trend_strength(indicators: Dict) -> float:
    """Calculate trend strength (0-100)"""
    
def determine_trend_direction(indicators: Dict) -> str:
    """Determine trend direction (UP/DOWN/SIDEWAYS)"""
    
def analyze(indicators: Dict, portfolio: Portfolio) -> Dict:
    """Analyze with trend following logic"""
```

### MeanReversionStrategy

```python
from strategies.mean_reversion_strategy import MeanReversionStrategy

strategy = MeanReversionStrategy()
```

#### Methods

```python
def analyze_rsi_signals(rsi: float) -> Dict:
    """Analyze RSI for mean reversion signals"""
    
def analyze_bollinger_bands(indicators: Dict) -> Dict:
    """Analyze Bollinger Bands for mean reversion"""
    
def combine_signals(rsi_signal: Dict, bb_signal: Dict) -> Dict:
    """Combine RSI and Bollinger Band signals"""
```

### MomentumStrategy

```python
from strategies.momentum_strategy import MomentumStrategy

strategy = MomentumStrategy()
```

#### Methods

```python
def calculate_price_momentum(indicators: Dict) -> float:
    """Calculate price momentum score"""
    
def calculate_volume_momentum(indicators: Dict) -> float:
    """Calculate volume momentum score"""
    
def calculate_technical_momentum(indicators: Dict) -> float:
    """Calculate technical indicator momentum"""
```

### StrategyManager

Coordinates multiple strategies.

```python
from strategies.strategy_manager import StrategyManager

manager = StrategyManager()
```

#### Methods

```python
def get_combined_signal(market_data: Dict, technical_indicators: Dict) -> Dict:
    """Get combined signal from all strategies"""
    
def detect_market_regime(indicators: Dict) -> str:
    """Detect current market regime (BULL/BEAR/SIDEWAYS)"""
    
def adjust_strategy_weights(regime: str) -> None:
    """Adjust strategy weights based on market regime"""
    
def get_strategy_performance() -> Dict[str, Dict]:
    """Get performance metrics for each strategy"""
```

## Utility Classes

### DataCollector

Market data collection and processing.

```python
from data_collector import DataCollector

collector = DataCollector()
```

#### Methods

```python
def collect_all_data() -> Dict:
    """Collect all market data and indicators"""
    
def get_market_data(product_id: str) -> Dict:
    """Get current market data for a product"""
    
def calculate_technical_indicators(price_data: List[float]) -> Dict:
    """Calculate technical indicators from price data"""
    
def validate_data_quality(data: Dict) -> bool:
    """Validate data quality and freshness"""
```

### PerformanceTracker

Performance tracking and analysis.

```python
from utils.performance_tracker import PerformanceTracker

tracker = PerformanceTracker()
```

#### Methods

```python
def take_portfolio_snapshot(portfolio: Portfolio) -> None:
    """Take a portfolio snapshot"""
    
def get_performance_summary(period: str = 'all') -> Dict:
    """Get performance summary for period"""
    
def reset_performance_tracking(reason: str = None) -> None:
    """Reset performance tracking"""
    
def is_tracking_enabled() -> bool:
    """Check if performance tracking is enabled"""
```

### PerformanceCalculator

Performance metrics calculation.

```python
from utils.performance_calculator import PerformanceCalculator

calculator = PerformanceCalculator()
```

#### Methods

```python
def calculate_returns(snapshots: List[Dict], period: str = None) -> Dict:
    """Calculate return metrics"""
    
def calculate_risk_metrics(snapshots: List[Dict]) -> Dict:
    """Calculate risk metrics (Sharpe, Sortino, etc.)"""
    
def analyze_trading_performance(trades: List[Dict]) -> Dict:
    """Analyze trading performance metrics"""
    
def calculate_drawdown(values: List[float]) -> float:
    """Calculate maximum drawdown"""
```

## Data Structures

### Market Data Format

```python
market_data = {
    'BTC-EUR': {
        'price': 45000.0,
        'volume': 1234.56,
        'bid': 44995.0,
        'ask': 45005.0,
        'timestamp': '2024-01-01T12:00:00Z'
    },
    'ETH-EUR': {
        'price': 3000.0,
        'volume': 5678.90,
        'bid': 2998.0,
        'ask': 3002.0,
        'timestamp': '2024-01-01T12:00:00Z'
    }
}
```

### Technical Indicators Format

```python
technical_indicators = {
    'rsi': 65.5,
    'macd': {
        'macd': 123.45,
        'signal': 120.30,
        'histogram': 3.15
    },
    'bollinger_bands': {
        'upper': 46000.0,
        'middle': 45000.0,
        'lower': 44000.0
    },
    'moving_averages': {
        'sma_20': 44800.0,
        'sma_50': 44500.0,
        'ema_12': 45100.0,
        'ema_26': 44900.0
    },
    'volume_sma': 1000.0,
    'timestamp': '2024-01-01T12:00:00Z'
}
```

### Trading Signal Format

```python
trading_signal = {
    'action': 'BUY',  # BUY, SELL, HOLD
    'asset': 'BTC-EUR',
    'confidence': 75,  # 0-100
    'amount': 100.0,   # EUR amount
    'reasoning': 'Strong upward trend with high momentum',
    'strategy_contributions': {
        'trend_following': {'signal': 'BUY', 'confidence': 80, 'weight': 0.4},
        'mean_reversion': {'signal': 'HOLD', 'confidence': 50, 'weight': 0.3},
        'momentum': {'signal': 'BUY', 'confidence': 85, 'weight': 0.3}
    },
    'risk_assessment': 'MEDIUM',
    'position_multiplier': 1.1,
    'timestamp': '2024-01-01T12:00:00Z'
}
```

### Portfolio State Format

```python
portfolio_state = {
    'assets': {
        'EUR': {
            'amount': 500.0,
            'value_eur': 500.0,
            'allocation_percent': 50.0
        },
        'BTC': {
            'amount': 0.01,
            'value_eur': 450.0,
            'allocation_percent': 45.0,
            'price_eur': 45000.0
        },
        'ETH': {
            'amount': 0.0167,
            'value_eur': 50.0,
            'allocation_percent': 5.0,
            'price_eur': 3000.0
        }
    },
    'total_value_eur': 1000.0,
    'last_updated': '2024-01-01T12:00:00Z'
}
```

### Trade Record Format

```python
trade_record = {
    'id': 'trade_20240101_120000',
    'timestamp': '2024-01-01T12:00:00Z',
    'action': 'BUY',
    'asset': 'BTC-EUR',
    'amount': 0.002,  # Asset amount
    'price': 45000.0,
    'value_eur': 90.0,
    'fees': 0.09,  # 0.1% fee
    'strategy': 'combined',
    'confidence': 75,
    'reasoning': 'Strong bullish signals',
    'order_id': 'coinbase_order_123',
    'status': 'FILLED',
    'pnl': None  # Calculated later for sells
}
```

## Error Handling

### Custom Exceptions

```python
class TradingBotError(Exception):
    """Base exception for trading bot errors"""
    pass

class ConfigurationError(TradingBotError):
    """Configuration-related errors"""
    pass

class APIError(TradingBotError):
    """API communication errors"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code

class InsufficientBalanceError(TradingBotError):
    """Insufficient balance for trade"""
    pass

class RiskManagementError(TradingBotError):
    """Risk management constraint violation"""
    pass
```

### Error Response Format

```python
error_response = {
    'success': False,
    'error': {
        'type': 'APIError',
        'message': 'Failed to connect to Coinbase API',
        'code': 'CONNECTION_ERROR',
        'details': {
            'status_code': 503,
            'retry_after': 60
        }
    },
    'timestamp': '2024-01-01T12:00:00Z'
}
```

## Configuration Reference

### Environment Variables

See [Configuration Guide](CONFIGURATION.md) for complete reference.

### Runtime Configuration

```python
# Update configuration at runtime
config.update_strategy_weights({
    'TREND_FOLLOWING_WEIGHT': 0.5,
    'MEAN_REVERSION_WEIGHT': 0.3,
    'MOMENTUM_WEIGHT': 0.2
})

# Get current configuration
current_config = {
    'trading_pairs': config.TRADING_PAIRS,
    'risk_level': config.RISK_LEVEL,
    'simulation_mode': config.SIMULATION_MODE,
    'strategy_weights': config.get_strategy_weights()
}
```

## Event System

### Event Types

```python
from enum import Enum

class EventType(Enum):
    TRADE_EXECUTED = "trade_executed"
    PORTFOLIO_UPDATED = "portfolio_updated"
    MARKET_DATA_RECEIVED = "market_data_received"
    STRATEGY_SIGNAL = "strategy_signal"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_SNAPSHOT = "performance_snapshot"
```

### Event Handler Registration

```python
from utils.event_system import EventSystem

event_system = EventSystem()

@event_system.on(EventType.TRADE_EXECUTED)
def handle_trade_executed(event_data):
    """Handle trade execution event"""
    trade = event_data['trade']
    print(f"Trade executed: {trade['action']} {trade['amount']} {trade['asset']}")

# Emit event
event_system.emit(EventType.TRADE_EXECUTED, {'trade': trade_record})
```

## Logging

### Logger Configuration

```python
import logging

# Get logger for specific module
logger = logging.getLogger(__name__)

# Log levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")
```

### Structured Logging

```python
import json

def log_trade(trade_data):
    """Log trade with structured data"""
    logger.info("Trade executed", extra={
        'trade_id': trade_data['id'],
        'action': trade_data['action'],
        'asset': trade_data['asset'],
        'amount': trade_data['amount'],
        'value_eur': trade_data['value_eur']
    })
```

This API reference provides comprehensive documentation for integrating with and extending the AI crypto trading bot.
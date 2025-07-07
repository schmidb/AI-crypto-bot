# Migration to Multi-Strategy Framework

## Issue Identified
The production bot is currently using the old `trading_strategy.py` which has a Bollinger Band data access issue. The new multi-strategy framework in `/strategies/` correctly handles all technical indicators and has 100% test coverage with 162 comprehensive tests.

## Current State
- **Production**: Uses `TradingStrategy` from `trading_strategy.py` (old, has Bollinger Band issue)
- **New Framework**: Uses `StrategyManager` from `strategies/strategy_manager.py` (tested, working correctly)

## Bollinger Band Issue Details
**Old Strategy Problem:**
```python
# trading_strategy.py line 1023
bb_data = technical_indicators.get('bollinger_bands', {})  # ❌ Wrong key
```

**New Strategy Solution:**
```python
# strategies/mean_reversion.py lines 54-58
bollinger = {
    'upper': technical_indicators.get('bb_upper', 0),      # ✅ Correct keys
    'lower': technical_indicators.get('bb_lower', 0),
    'middle': technical_indicators.get('bb_middle', 0)
}
```

## Migration Steps

### 1. Update main.py imports
**Current:**
```python
from trading_strategy import TradingStrategy
```

**New:**
```python
from strategies.strategy_manager import StrategyManager
```

### 2. Update TradingStrategy initialization
**Current:**
```python
self.trading_strategy = TradingStrategy(self.config, self.llm_analyzer, self.data_collector)
```

**New:**
```python
self.strategy_manager = StrategyManager(self.config)
```

### 3. Update strategy execution calls
**Current:**
```python
decision_result = self.trading_strategy.execute_strategy(product_id)
```

**New:**
```python
# Get market data and technical indicators from data collector
market_data = self.data_collector.get_market_data(product_id)
technical_indicators = self.data_collector.get_technical_indicators(product_id)
portfolio = self.portfolio_manager.get_portfolio()

# Get combined signal from all strategies
decision_result = self.strategy_manager.get_combined_signal(
    market_data, technical_indicators, portfolio
)
```

### 4. Update portfolio management
The new framework separates concerns:
- **StrategyManager**: Handles trading decisions
- **PortfolioManager**: Handles portfolio operations (needs to be extracted from old TradingStrategy)

### 5. Benefits of Migration
- ✅ **Fixes Bollinger Band data access issue**
- ✅ **100% test coverage with 162 comprehensive tests**
- ✅ **Multi-strategy approach** (trend following, mean reversion, momentum)
- ✅ **Better separation of concerns**
- ✅ **More robust error handling**
- ✅ **Improved position sizing with strategy-specific multipliers**

## Test Coverage Comparison
- **Old Strategy**: Limited test coverage, known Bollinger Band issue
- **New Framework**: 
  - Mean Reversion: 32 tests ✅
  - Trend Following: 39 tests ✅  
  - Momentum: 54 tests ✅
  - Strategy Manager: 37 tests ✅
  - **Total: 162 tests with 100% coverage**

## Risk Assessment
- **Low Risk**: New framework is thoroughly tested
- **High Reward**: Fixes dashboard issue and improves trading logic
- **Rollback Plan**: Keep old `trading_strategy.py` as backup

## Implementation Priority
**HIGH PRIORITY** - This migration will:
1. Fix the dashboard Bollinger Band display issue
2. Improve trading decision quality with multi-strategy approach
3. Provide better test coverage and maintainability

## Next Steps
1. Create portfolio manager extraction from old TradingStrategy
2. Update main.py to use new framework
3. Test in simulation mode
4. Deploy to production

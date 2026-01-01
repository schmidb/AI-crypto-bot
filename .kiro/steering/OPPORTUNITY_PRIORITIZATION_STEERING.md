---
inclusion: always
---

# Opportunity Prioritization Steering Document

## Phase 1 Multi-Coin Prioritization System

### Overview
The AI crypto bot now uses an intelligent opportunity prioritization system that analyzes all trading pairs simultaneously, ranks them by opportunity strength, and allocates capital dynamically based on signal quality.

### Core Components

#### OpportunityManager Class
- **Location**: `utils/trading/opportunity_manager.py`
- **Purpose**: Handles opportunity scoring and dynamic capital allocation
- **Integration**: Automatically used in main trading cycle

#### Three-Phase Trading Cycle
1. **Phase 1: Analysis** - Analyze all trading pairs simultaneously
2. **Phase 2: Prioritization** - Rank opportunities and allocate capital
3. **Phase 3: Execution** - Execute trades in priority order

### Opportunity Scoring Algorithm

#### Scoring Factors (0-100+ scale):
1. **Base Confidence** (0-100): From multi-strategy analysis
2. **Action Bonus** (+20%): BUY/SELL signals get priority over HOLD
3. **Momentum Bonus** (up to +10): Strong 24h price movements (>3%)
4. **Consensus Bonus** (up to +15): When multiple strategies agree
5. **Regime Alignment** (up to +5): Action appropriate for market conditions

#### Example Scoring:
```
BTC-EUR Analysis:
- Base confidence: 75.5%
- Action: BUY (+20% bonus = 90.6%)
- 24h change: 5.2% (+5 momentum bonus = 95.6%)
- 3/4 strategies agree (+15 consensus bonus = 110.6%)
- BUY in trending market (+5 regime bonus = 115.6%)
= Final opportunity score: 100.0 (capped at 100)
```

### Dynamic Capital Allocation

#### Allocation Logic:
- **Reserve Management**: 20% EUR kept in reserve
- **Weighted Distribution**: Higher opportunity scores get more capital
- **Constraints**: Min €50 per trade, max 60% to single trade
- **Power Factor**: 1.2x amplifies score differences for more pronounced allocation

#### Example Allocation:
```
Available: €1000
Trading Capital: €800 (€200 reserve)

Opportunities:
- BTC-EUR: 100.0 score → €409.20 (40.9%)
- ETH-EUR: 96.2 score → €390.80 (39.1%)
- Reserve: €200.00 (20.0%)
```

### Configuration Parameters

#### Adjustable Settings:
```python
# In OpportunityManager.__init__()
min_actionable_confidence = 50      # Min confidence for actionable signals
consensus_bonus_threshold = 2       # Strategies needed for consensus bonus
momentum_threshold = 3.0            # 24h change threshold for momentum bonus
capital_reserve_ratio = 0.2         # 20% EUR reserve
min_trade_allocation = 50.0         # Min €50 per trade
max_single_trade_ratio = 0.6        # Max 60% to single trade
```

### Integration with Existing Systems

#### Backward Compatibility:
- All existing strategies work unchanged
- Fallback to legacy sequential processing if needed
- All configuration options preserved
- Dashboard compatibility maintained

#### Enhanced Logging:
```
🔍 Phase 1: Analyzing all trading opportunities...
🎯 Phase 2: Ranking opportunities and allocating capital...
💰 Phase 2: Capital allocation results
⚡ Phase 3: Executing prioritized trades...
📈 Execution Summary: X trades executed, €Y capital deployed
```

### Multi-Coin Scaling

#### Adding New Trading Pairs:
```env
# Simply add more pairs - system handles them automatically
TRADING_PAIRS=BTC-EUR,ETH-EUR,SOL-EUR,ADA-EUR,DOT-EUR
```

#### Automatic Handling:
- Each new coin gets analyzed independently
- Scored for opportunity strength
- Allocated capital based on signal quality
- Executed in priority order

### Testing and Validation

#### Test Script:
```bash
# Test the opportunity manager with sample data
python test_opportunity_manager.py
```

#### Expected Results:
- Opportunity scoring with multiple factors
- Intelligent ranking by opportunity strength
- Dynamic capital allocation based on signals
- Reserve management (20% kept in reserve)
- Minimum trade size enforcement

### Best Practices

#### Development Guidelines:
- Always test new configurations with `test_opportunity_manager.py`
- Monitor the enhanced logging to understand prioritization decisions
- Start with simulation mode when adding new trading pairs
- Adjust scoring parameters based on backtesting results

#### Production Guidelines:
- Monitor opportunity scores and allocation patterns
- Ensure adequate EUR reserves for trading opportunities
- Review execution summaries for capital deployment efficiency
- Track performance across different market regimes

### Future Enhancements (Phase 2)

#### Planned Improvements:
1. **Market Regime Priorities**: Different coin preferences for bull/bear/sideways markets
2. **Cross-Asset Rebalancing**: "Sell weak to buy strong" logic
3. **Correlation Analysis**: Avoid over-concentration in correlated assets
4. **Performance Learning**: Adjust scoring based on historical success rates

### Error Handling

#### Fallback Mechanisms:
- Automatic fallback to legacy sequential processing if opportunity manager fails
- Graceful degradation with detailed error logging
- Maintains trading capability even if prioritization fails

#### Common Issues:
- Insufficient EUR balance for allocated trades
- Network issues during multi-pair analysis
- Configuration parameter validation errors

### Performance Impact

#### Efficiency Gains:
- Better capital utilization through intelligent allocation
- Reduced missed opportunities through prioritization
- Scalable architecture for any number of trading pairs
- Enhanced decision transparency through detailed logging

This opportunity prioritization system transforms the bot from a simple sequential processor into an intelligent multi-coin trading system that maximizes capital efficiency and opportunity capture.
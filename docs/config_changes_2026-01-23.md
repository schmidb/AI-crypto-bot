# Configuration Changes - 2026-01-23 10:50 UTC

## Changes Applied

### Confidence Thresholds
```env
CONFIDENCE_THRESHOLD_BUY=70      # Changed from 65
CONFIDENCE_THRESHOLD_SELL=55     # Unchanged
```

### EUR Capital Management
```env
TARGET_EUR_ALLOCATION=25         # Changed from 12
MIN_EUR_RESERVE=25.0            # Changed from 15.0
REBALANCE_TARGET_EUR_PERCENT=25  # Changed from 12
```

## Rationale

### Problem Identified
Analysis of last 48 hours showed:
- Low EUR balance (€49.77, only €39.81 tradeable)
- 15 trading signals skipped due to insufficient capital
- LLM strategy showing 3:1 BUY bias
- Algorithm generating BUY signals but unable to execute due to capital depletion

### Solution
1. **Increase BUY threshold** (65→70): Makes BUY signals harder to trigger
2. **Maintain SELL threshold** (55): Creates 15-point gap favoring SELL
3. **Increase EUR targets** (12→25): Forces more SELL activity to reach target
4. **Increase reserves** (15→25): Ensures minimum capital for trading

### Expected Impact
- More SELL signals will pass the 55% threshold
- Fewer BUY signals will pass the 70% threshold
- Bot will prioritize replenishing EUR balance
- Better capital management for sustained trading

## Deployment
- **Applied**: 2026-01-23 10:50:39 UTC
- **Bot Status**: Restarted and running
- **Verification**: Configuration loaded correctly

## Monitoring
Watch for:
- Increased SELL execution rate
- EUR balance trending toward €85 (25% of €339 portfolio)
- BUY/SELL ratio moving toward 1:2 or 1:3 temporarily
- Capital availability for trading opportunities

## Related Documents
- `analysis_sell_activity_48h.md` - Full 48-hour analysis
- `.env` - Configuration file (not in git)

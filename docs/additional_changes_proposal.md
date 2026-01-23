# Additional Recommended Changes - Root Causes 2 & 4

## Current Status
✅ **Already Applied** (2026-01-23 10:50):
- Confidence thresholds adjusted (BUY: 70, SELL: 55)
- EUR targets increased (25%)

## Remaining Issues

### Root Cause 2: LLM Strategy BUY Bias (3:1 ratio)
**Problem**: LLM strategy generates 3 BUY signals for every 1 SELL signal
**Impact**: Dominates decision-making with BUY preference

**Proposed Solutions**:

#### Option A: Add EUR Balance Context to LLM Prompt (RECOMMENDED)
Modify `llm_analyzer.py` to include portfolio balance in the prompt:
```python
# Add to LLM prompt
portfolio_context = f"""
Current Portfolio Balance:
- EUR Available: €{eur_balance:.2f}
- EUR Target: {config.TARGET_EUR_ALLOCATION}%
- Current EUR %: {current_eur_pct:.1f}%

IMPORTANT: If EUR balance is below target, STRONGLY PREFER SELL signals to replenish reserves.
"""
```

**Pros**: 
- Makes LLM aware of capital constraints
- Natural language instruction easy to understand
- No code complexity

**Cons**: 
- Relies on LLM following instructions
- May not be deterministic

#### Option B: Reduce LLM Strategy Weight When EUR Low
Modify `strategies/strategy_manager.py`:
```python
def _adjust_weights_for_market_regime(self, ...):
    # Existing code...
    
    # NEW: Reduce LLM weight when EUR is low
    eur_balance = portfolio.get('EUR', {}).get('amount', 0)
    portfolio_value = portfolio.get('portfolio_value_eur', {}).get('amount', 1)
    eur_pct = (eur_balance / portfolio_value) * 100
    
    if eur_pct < config.TARGET_EUR_ALLOCATION:
        # Reduce LLM weight, increase trend_following (which generates SELL)
        adjusted_weights['llm_strategy'] *= 0.7
        adjusted_weights['trend_following'] *= 1.3
        logger.info(f"⚖️  Adjusted weights for low EUR ({eur_pct:.1f}%): LLM↓ TrendFollow↑")
```

**Pros**: 
- Deterministic behavior
- Automatically shifts to SELL-generating strategies

**Cons**: 
- Requires passing portfolio data to strategy manager
- More code changes

---

### Root Cause 4: No Dynamic Threshold Adjustment
**Problem**: Thresholds are static regardless of portfolio state
**Impact**: Bot doesn't adapt to capital constraints

**Proposed Solution**: Dynamic Threshold Adjustment

Add to `utils/trading/opportunity_manager.py`:
```python
def get_dynamic_thresholds(self, eur_balance: float, portfolio_value: float) -> Tuple[float, float]:
    """
    Adjust confidence thresholds based on EUR balance
    
    Returns: (buy_threshold, sell_threshold)
    """
    eur_pct = (eur_balance / portfolio_value) * 100
    target_pct = self.config.TARGET_EUR_ALLOCATION
    
    # Base thresholds from config
    base_buy = self.config.CONFIDENCE_THRESHOLD_BUY
    base_sell = self.config.CONFIDENCE_THRESHOLD_SELL
    
    # Dynamic adjustment based on EUR balance
    if eur_pct < target_pct * 0.6:  # EUR < 60% of target (critical low)
        buy_threshold = base_buy + 15  # Much harder to BUY
        sell_threshold = base_sell - 10  # Much easier to SELL
        self.logger.info(f"🔴 Critical low EUR ({eur_pct:.1f}%): BUY={buy_threshold}, SELL={sell_threshold}")
        
    elif eur_pct < target_pct:  # EUR below target
        buy_threshold = base_buy + 5  # Harder to BUY
        sell_threshold = base_sell - 5  # Easier to SELL
        self.logger.info(f"🟡 Low EUR ({eur_pct:.1f}%): BUY={buy_threshold}, SELL={sell_threshold}")
        
    elif eur_pct > target_pct * 1.5:  # EUR > 150% of target (too much cash)
        buy_threshold = base_buy - 10  # Easier to BUY
        sell_threshold = base_sell + 5  # Harder to SELL
        self.logger.info(f"🟢 High EUR ({eur_pct:.1f}%): BUY={buy_threshold}, SELL={sell_threshold}")
        
    else:  # EUR in healthy range
        buy_threshold = base_buy
        sell_threshold = base_sell
        self.logger.debug(f"✅ Healthy EUR ({eur_pct:.1f}%): Using base thresholds")
    
    return buy_threshold, sell_threshold
```

**Usage in main trading loop**:
```python
# Get dynamic thresholds
buy_threshold, sell_threshold = opportunity_manager.get_dynamic_thresholds(
    eur_balance=portfolio['EUR']['amount'],
    portfolio_value=portfolio['portfolio_value_eur']['amount']
)

# Use these instead of config values when filtering signals
```

---

## Recommendation Priority

### Immediate (Do Now):
1. **Option A: Add EUR context to LLM prompt** - Quick win, low risk
2. **Dynamic Threshold Adjustment** - Addresses root cause 4 directly

### Short-term (Next Week):
3. **Option B: Adjust strategy weights** - More robust but requires testing

### Why This Order:
- LLM prompt change is fastest and safest
- Dynamic thresholds provide automatic adaptation
- Strategy weight changes need more testing to avoid unintended consequences

---

## Implementation Estimate

**Option A (LLM Prompt)**: 15 minutes
- Modify `llm_analyzer.py` prompt generation
- Add portfolio balance to context
- Test with one cycle

**Dynamic Thresholds**: 30 minutes
- Add method to `opportunity_manager.py`
- Integrate into main trading loop
- Test threshold calculations

**Option B (Strategy Weights)**: 1-2 hours
- Modify `strategy_manager.py`
- Pass portfolio data through call chain
- Test weight adjustments
- Verify no side effects

---

## Testing Plan

1. **Monitor next 24 hours** with current changes (BUY=70, SELL=55)
2. **If still seeing BUY bias**: Implement Option A (LLM prompt)
3. **If EUR not recovering**: Implement Dynamic Thresholds
4. **If both above fail**: Implement Option B (Strategy weights)

---

## Decision

**Should we implement these now?**

**My recommendation**: 
- ✅ **YES** to Option A (LLM prompt) - Quick, safe, addresses root cause 2
- ⏸️ **WAIT** on Dynamic Thresholds - Let's see if current changes + LLM prompt are sufficient
- ⏸️ **WAIT** on Option B - More complex, save as backup plan

**Rationale**: 
- Current threshold changes (BUY=70, SELL=55) already create 15-point gap
- Adding EUR context to LLM is low-risk enhancement
- Let's observe for 12-24 hours before more aggressive changes
- Avoid over-engineering if simpler solution works

**What do you think?**

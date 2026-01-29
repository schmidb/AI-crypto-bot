# Configuration Changes - January 23, 2026

## Overview
Configuration adjustments to address excessive BUY signals and EUR capital depletion.

## Changes Made

### Confidence Thresholds
- **BUY Threshold**: Increased from 65 to **70** (harder to trigger BUY)
- **SELL Threshold**: Remains at **55** (easier to trigger SELL)
- **Gap**: 15-point difference favors SELL signals over BUY

### EUR Reserve Management
- **Target EUR Allocation**: Increased from 12% to **25%**
- **Minimum EUR Reserve**: Increased from €15 to **€25**
- **Rebalance Target**: Updated to match 25% EUR allocation

## Rationale

### Problem
- Bot was generating too many BUY signals
- EUR balance depleted to critical levels (€49.77, ~14.7%)
- Insufficient capital for future trading opportunities

### Solution
1. **Higher BUY threshold** reduces frequency of BUY signals
2. **Lower SELL threshold** encourages selling to rebuild EUR reserves
3. **Higher EUR targets** maintain adequate trading capital

## Expected Behavior

### Signal Generation
- 60% confidence signal:
  - ❌ Will NOT trigger BUY (needs 70%)
  - ✅ Will trigger SELL (needs 55%)

### Portfolio Management
- Critical EUR threshold: 15% (60% of 25% target)
- High EUR threshold: 37.5% (150% of 25% target)
- Current EUR (14.7%) triggers critical warning

## Implementation
- Updated `.env` configuration file
- Changes take effect immediately on bot restart
- No code changes required

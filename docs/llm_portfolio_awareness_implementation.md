# LLM Portfolio Awareness Implementation

## Overview
Enhanced LLM analyzer to include portfolio state in trading decisions, enabling context-aware recommendations.

## Implementation Details

### Portfolio Data Integration

#### Data Structure
```python
portfolio_data = {
    'EUR': {'amount': 49.77},
    'BTC': {'amount': 0.00385, 'last_price_eur': 75000},
    'portfolio_value_eur': {'amount': 339.42}
}
```

#### EUR Percentage Calculation
```python
eur_balance = portfolio['EUR']['amount']
portfolio_value = portfolio['portfolio_value_eur']['amount']
eur_percentage = (eur_balance / portfolio_value) * 100
```

### LLM Prompt Enhancement

#### Portfolio Context Added
The LLM now receives:
- Current EUR balance and percentage
- Target EUR allocation (25%)
- Critical thresholds (15% low, 37.5% high)
- Portfolio composition

#### Decision Guidance
```
EUR Status: €49.77 (14.7% of portfolio)
Target: 25% EUR allocation
Status: CRITICAL - Below 15% threshold

Guidance:
- Prefer SELL signals to rebuild EUR reserves
- Avoid BUY signals unless extremely strong
- Consider portfolio rebalancing needs
```

### Threshold Integration

#### Dynamic Thresholds
- **Critical Low** (< 15%): Strong SELL preference
- **Below Target** (15-25%): Moderate SELL preference
- **At Target** (25-37.5%): Balanced decisions
- **Above Target** (> 37.5%): BUY preference

### JSON Parsing Improvements

#### Common LLM Errors Handled
1. **Missing Commas**: Auto-insert after arrays
2. **Markdown Blocks**: Strip ```json``` wrappers
3. **Trailing Commas**: Remove invalid trailing commas
4. **Whitespace Issues**: Normalize spacing

#### Regex Fixes Applied
```python
# Add missing commas after arrays
fixed = re.sub(r'(\])\s*\n\s*"', r'\1,\n  "', response)

# Remove markdown code blocks
fixed = re.sub(r'```json\s*', '', fixed)
fixed = re.sub(r'```\s*', '', fixed)
```

## Testing

### Unit Tests
- Portfolio percentage calculation
- Threshold detection logic
- JSON parsing error handling

### Integration Tests
- Portfolio data acceptance in analyze_market
- EUR status influence on decisions
- Configuration threshold validation

## Expected Behavior

### Current State (EUR at 14.7%)
- ✅ SELL signals encouraged (rebuild reserves)
- ❌ BUY signals discouraged (preserve capital)
- ⚠️ Critical warning displayed

### Future State (EUR at 25%+)
- ✅ Balanced BUY/SELL decisions
- ✅ Normal trading operations
- ✅ Adequate capital for opportunities

## Benefits
1. **Context-Aware Decisions**: LLM considers portfolio state
2. **Capital Preservation**: Prevents EUR depletion
3. **Adaptive Strategy**: Adjusts to portfolio needs
4. **Improved Reliability**: Better JSON parsing

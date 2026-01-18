# Test Coverage Improvement Plan

## Current Status
- **Overall Coverage**: 60% (19,390 statements, 7,669 not covered)
- **Passing Tests**: 755
- **Failing Tests**: 20
- **Skipped Tests**: 31

## Critical Failing Tests Analysis

### 1. Mock Comparison Errors (12 tests)
**Issue**: TypeError when comparing Mock objects with numbers

#### Opportunity Manager Tests (7 failures)
- `test_allocate_trading_capital_basic`
- `test_allocate_trading_capital_insufficient_funds`
- `test_calculate_weighted_allocations`
- `test_get_opportunity_summary_basic`
- `test_get_opportunity_summary_calculations`
- `test_full_opportunity_workflow`
- `test_multiple_asset_scenario`

**Root Cause**: Mock objects being compared with `>=`, `<=`, `<` operators
**Fix**: Ensure mocks return proper numeric values, not Mock objects

#### Strategy Manager Tests (4 failures)
- `test_combine_all_buy_signals`
- `test_combine_all_sell_signals`
- `test_combine_with_high_confidence_boost`
- `test_position_multiplier_bounds`

**Root Cause**: Same - Mock comparison issues
**Fix**: Configure mocks to return actual numbers

### 2. Configuration Tests (1 failure)
- `test_module_level_config_instance`

**Issue**: `isinstance(<Mock>, Config)` returns False
**Fix**: Use actual Config instance or adjust test expectations

### 3. LLM Analyzer Tests (3 failures)
- `test_llm_analyzer_market_analysis_basic`
- `test_llm_analyzer_uses_correct_models`
- `test_llm_analyzer_uses_global_location`

**Issue**: Mock objects not properly configured
**Fix**: Return proper dict/string values from mocks

### 4. Main Module Tests (3 failures)
- `test_execute_buy_order_simulation_mode`
- `test_update_local_dashboard`
- `test_save_result_with_market_data`

**Issue**: Assertion mismatches and mock call counts
**Fix**: Adjust test expectations or fix implementation

### 5. Security Test (1 failure)
- `test_configuration_validation`

**Issue**: Mock comparison in validation logic
**Fix**: Use real values in validation tests

## Low Coverage Areas (Priority Order)

### 🔴 Critical (< 40% coverage)
1. **performance_dashboard_updater.py** - 8% coverage (260 statements)
2. **trade_cooldown.py** - 37% coverage (41 statements)
3. **strategy_vectorizer.py** - 0% coverage (2 statements)

### 🟡 Medium (40-70% coverage)
4. **opportunity_manager.py** - 66% coverage (198 statements)
5. **trade_logger.py** - 65% coverage (94 statements)

### 🟢 Good (70-90% coverage)
6. **performance_tracker.py** - 79% coverage (198 statements)
7. **tax_report.py** - 80% coverage (15 statements)
8. **performance_manager.py** - 84% coverage (352 statements)
9. **portfolio.py** - 88% coverage (333 statements)

### ✅ Excellent (> 90% coverage)
10. **volatility_analyzer.py** - 92% coverage
11. **capital_manager.py** - 96% coverage

## Recommended Action Plan

### Phase 1: Fix Failing Tests (Immediate)
1. Fix Mock comparison errors in opportunity_manager tests
2. Fix Mock comparison errors in strategy_manager tests
3. Fix LLM analyzer mock configurations
4. Fix main module test assertions
5. Fix security validation test

**Expected Impact**: 20 tests fixed → 775 passing tests

### Phase 2: Improve Critical Coverage (High Priority)
1. Add tests for `performance_dashboard_updater.py` (8% → 80%)
2. Add tests for `trade_cooldown.py` (37% → 80%)
3. Add tests for `strategy_vectorizer.py` (0% → 80%)

**Expected Impact**: +15% overall coverage

### Phase 3: Improve Medium Coverage (Medium Priority)
4. Add tests for `opportunity_manager.py` (66% → 85%)
5. Add tests for `trade_logger.py` (65% → 85%)

**Expected Impact**: +5% overall coverage

### Target: 80% Overall Coverage
- Current: 60%
- After Phase 1: 60% (tests fixed, no new coverage)
- After Phase 2: 75%
- After Phase 3: 80%

## Quick Wins

### Easiest Fixes (< 30 min each)
1. ✅ **daily_report.py** - Already at 100% (completed)
2. **strategy_vectorizer.py** - Only 2 statements
3. **tax_report.py** - Only 15 statements, already 80%
4. **trade_cooldown.py** - Only 41 statements

### High Impact Fixes (1-2 hours each)
1. **performance_dashboard_updater.py** - 260 statements at 8%
2. **opportunity_manager.py** - 198 statements at 66%
3. **trade_logger.py** - 94 statements at 65%

## Next Steps

Would you like me to:
1. **Fix all 20 failing tests** (recommended first step)
2. **Focus on critical low-coverage files** (performance_dashboard_updater, trade_cooldown)
3. **Both** - fix tests then improve coverage

The failing tests are likely causing the low coverage numbers in some areas, so fixing them first is recommended.

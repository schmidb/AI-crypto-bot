# Quick Coverage Improvement Plan

## Target: 65% Coverage (Current: 60%)

### Phase 1: Add Simple Integration Tests for main.py (570 lines potential)

**Strategy**: Add integration tests that exercise main.py workflows without mocking everything

Files to create:
1. `tests/integration/test_main_workflows.py` - Test actual trading cycles
2. `tests/integration/test_main_initialization.py` - Test bot startup paths

**Estimated gain**: +200 lines (33% of main.py gaps)

### Phase 2: Add Coinbase Client Tests (326 lines potential)

**Strategy**: Mock API responses and test all client methods

File to enhance:
- `tests/unit/test_coinbase_client.py` (currently 39% coverage)

**Estimated gain**: +150 lines (46% of coinbase_client.py gaps)

### Phase 3: Add Data Collector Tests (171 lines potential)

**Strategy**: Test historical data fetching and indicator calculations

File to enhance:
- `tests/unit/test_data_collector.py` (currently 87% coverage)

**Estimated gain**: +50 lines (29% of data_collector.py gaps)

---

**Total Expected Gain**: ~400 lines
**New Coverage**: 60% + (400/19120)*100 = **62%**

To reach 65%, need 955 more lines.
To reach 80%, need 3824 more lines.

## Recommendation:
Focus on main.py integration tests first - highest ROI with minimal complexity.

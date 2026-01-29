#!/bin/bash
# Phase 1: Remove unused code (0% coverage modules)

echo "🗑️  Phase 1: Removing unused code..."

# 1. Remove entire backtest utils directory (2,392 lines)
echo "Removing utils/backtest/ directory..."
rm -rf utils/backtest/

# 2. Remove unused strategy modules (280 lines)
echo "Removing unused strategy modules..."
rm -f strategies/aggressive_strategy_manager.py
rm -f strategies/decision_logic_manager.py

# 3. Remove unused monitoring modules (620 lines)
echo "Removing unused monitoring/dashboard modules..."
rm -f utils/monitoring/data_quality_monitor.py
rm -f utils/monitoring/parameter_monitor.py
rm -f utils/decision_mode_controller.py

# 4. Remove old test scripts from root (201 lines)
echo "Removing old test scripts..."
rm -f test_live_performance_tracker.py
rm -f test_llm_parser.py
rm -f test_outcome_tracking.py

# 5. Remove unused utilities (508 lines)
echo "Removing unused utility modules..."
rm -f utils/log_reader.py
rm -f utils/ensure_eur_data.py
rm -f utils/indicator_factory.py
rm -f utils/strategy_vectorizer.py
rm -f utils/backtest_suite.py
rm -f utils/performance/analyze_performance.py
rm -f utils/performance/indicator_factory.py

# 6. Remove deployment scripts (57 lines)
echo "Removing manual deployment scripts..."
rm -f deploy_dashboard.py
rm -f generate_live_performance_report.py

echo "✅ Phase 1 cleanup complete!"
echo ""
echo "Summary:"
echo "  - Removed ~3,500 lines of unused code"
echo "  - Codebase reduced by ~17%"
echo ""
echo "Next: Run tests to ensure nothing broke"

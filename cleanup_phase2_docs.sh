#!/bin/bash
# Phase 2: Remove outdated documentation and testing artifacts

echo "🗑️  Phase 2: Removing outdated documentation..."

# Root-level old status documents
rm -f 100_PERCENT_TESTS_READY.md
rm -f ADAPTIVE_SYSTEM_DEEP_ANALYSIS.md
rm -f ADAPTIVE_SYSTEM_STATUS.md
rm -f ANTI_OVERTRADING_IMPROVEMENTS.md
rm -f CHANGES_APPLIED_2026-01-27.md
rm -f CI_CD_READINESS.md
rm -f FIXES_APPLIED.md
rm -f IMPLEMENTATION_SUMMARY.md
rm -f IMPLEMENTATION_SUMMARY_LLM_FIX.md
rm -f LIVE_PERFORMANCE_INTEGRATION.md
rm -f LLM_JSON_PARSING_IMPROVEMENTS.md
rm -f MARKET_REGIME_ADAPTATION_ANALYSIS.md
rm -f MARKET_REVIEW_2026-01-27.md
rm -f OPTIMIZATION_SUMMARY.md
rm -f OUTCOME_TRACKING_FIX.md
rm -f PERFORMANCE_REVIEW_2026-01-27_AFTERNOON.md
rm -f QUICK_REFERENCE_LLM_FIX.md
rm -f RECOMMENDATIONS_IMPLEMENTATION_COMPLETE.md
rm -f TEST_COVERAGE_SUMMARY.md
rm -f TEST_ERROR_ANALYSIS.md
rm -f TEST_FIXES_FINAL.md
rm -f TEST_FIXES_SUMMARY.md
rm -f analysis_sell_activity_48h.md
rm -f quick_coverage_plan.md

# Docs subdirectory cleanup
rm -f docs/DAILY_REPORT_TEST_COVERAGE.md
rm -f docs/LLM_JSON_PARSING_FIX.md
rm -f docs/LLM_PARSING_FIX.md
rm -f docs/TEST_COVERAGE_IMPROVEMENT_PLAN.md
rm -f docs/TEST_COVERAGE_LLM_PARSING.md
rm -f docs/TEST_FIXING_SUMMARY.md
rm -f docs/additional_changes_proposal.md
rm -f docs/config_changes_2026-01-23.md
rm -f docs/llm_portfolio_awareness_implementation.md
rm -f docs/test_coverage_summary.md
rm -f tests/unit/TEST_LLM_PARSING_COVERAGE.md

# Old log files
rm -f logs/daily_report_2025-12-27_*.txt

echo "✅ Phase 2 documentation cleanup complete!"
echo ""
echo "Summary:"
echo "  - Removed ~35 outdated documentation files"
echo "  - Kept essential docs (README, guides, steering)"
echo "  - Documentation structure is now cleaner"

#!/bin/bash

# AI Crypto Trading Bot - Test Execution Script
# Runs comprehensive tests for all core functionality

echo "🧪 AI Crypto Trading Bot - Test Suite"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the AI-crypto-bot directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not detected"
    echo "   Consider activating your virtual environment first:"
    echo "   source venv/bin/activate"
    echo ""
fi

# Check if required dependencies are installed
echo "🔍 Checking dependencies..."
python3 -c "import unittest, json, datetime" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: Required Python modules not available"
    echo "   Please install dependencies: pip install -r requirements.txt"
    exit 1
fi

echo "✅ Dependencies check passed"
echo ""

# Run the test suite
echo "🚀 Starting test execution..."
echo ""

# Option 1: Run all tests
if [ "$1" = "" ]; then
    echo "Running all tests..."
    python3 tests/test_runner.py
    exit_code=$?
    
# Option 2: Run specific test module
elif [ "$1" != "" ]; then
    echo "Running specific test: $1"
    python3 tests/test_runner.py "$1"
    exit_code=$?
fi

echo ""
echo "📊 Test Execution Summary"
echo "========================="

if [ $exit_code -eq 0 ]; then
    echo "✅ All tests passed successfully!"
    echo ""
    echo "🎯 Next Steps:"
    echo "• Your bot is ready for deployment"
    echo "• Consider running tests regularly during development"
    echo "• Add new tests when implementing new features"
else
    echo "❌ Some tests failed"
    echo ""
    echo "🔧 Recommended Actions:"
    echo "• Review the test output above for specific failures"
    echo "• Fix any failing tests before deploying to production"
    echo "• Check error messages and update code accordingly"
fi

echo ""
echo "📚 Available Test Modules:"
echo "• test_main_bot - Main bot orchestration"
echo "• test_llm_analyzer - LLM analysis functionality"
echo "• test_portfolio - Portfolio management"
echo "• test_dashboard - Dashboard updates"
echo "• test_strategy - Trading strategy"
echo "• test_data_collector - Data collection"
echo "• test_coinbase - Coinbase API client"
echo "• test_backtesting - Backtesting functionality"
echo "• test_config - Configuration management"
echo "• test_error_handling - Error handling and edge cases"
echo ""
echo "Usage: ./run_tests.sh [test_module_name]"
echo "Example: ./run_tests.sh test_portfolio"

exit $exit_code

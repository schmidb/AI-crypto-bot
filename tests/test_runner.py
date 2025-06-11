#!/usr/bin/env python3
"""
Comprehensive test runner for AI Crypto Trading Bot
Runs all tests and provides detailed coverage report
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_suite():
    """Run the complete test suite"""
    
    print("🧪 AI Crypto Trading Bot - Test Suite")
    print("=" * 50)
    print()
    
    # Discover and load all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Count total tests
    total_tests = suite.countTestCases()
    print(f"📊 Found {total_tests} test cases")
    print()
    
    # Run tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        buffer=True,
        failfast=False
    )
    
    print("🚀 Running tests...")
    start_time = time.time()
    
    result = runner.run(suite)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Print results
    print()
    print("📋 Test Results Summary")
    print("-" * 30)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Duration: {duration:.2f} seconds")
    print()
    
    # Print detailed output
    output = stream.getvalue()
    if output:
        print("📝 Detailed Test Output:")
        print("-" * 30)
        print(output)
    
    # Print failures and errors
    if result.failures:
        print("❌ Test Failures:")
        print("-" * 20)
        for test, traceback in result.failures:
            print(f"FAIL: {test}")
            print(traceback)
            print()
    
    if result.errors:
        print("💥 Test Errors:")
        print("-" * 20)
        for test, traceback in result.errors:
            print(f"ERROR: {test}")
            print(traceback)
            print()
    
    # Success rate
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    
    print(f"✅ Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 All tests passed!")
    elif success_rate >= 90:
        print("✨ Most tests passed - minor issues to address")
    elif success_rate >= 70:
        print("⚠️  Some tests failed - review needed")
    else:
        print("🚨 Many tests failed - significant issues detected")
    
    print()
    print("🔍 Test Coverage by Component:")
    print("-" * 35)
    
    # Analyze test coverage by component
    test_modules = [
        ('Main Bot Orchestration', 'test_main_bot'),
        ('LLM Analyzer', 'test_llm_analyzer'),
        ('Portfolio Management', 'test_portfolio'),
        ('Dashboard Updates', 'test_dashboard'),
        ('Trading Strategy', 'test_strategy'),
        ('Data Collection', 'test_data_collector'),
        ('Coinbase Client', 'test_coinbase'),
        ('Backtesting', 'test_backtesting')
    ]
    
    for component, module in test_modules:
        try:
            module_suite = loader.loadTestsFromName(module)
            test_count = module_suite.countTestCases()
            print(f"  {component}: {test_count} tests")
        except Exception:
            print(f"  {component}: Module not found or error loading")
    
    print()
    print("🎯 Recommendations:")
    print("-" * 20)
    
    if success_rate < 100:
        print("• Fix failing tests before deploying to production")
        print("• Review error messages and update code accordingly")
    
    if total_tests < 50:
        print("• Consider adding more edge case tests")
        print("• Add integration tests for complex workflows")
    
    print("• Run tests regularly during development")
    print("• Add new tests when adding new features")
    print("• Mock external dependencies for reliable testing")
    
    return result.wasSuccessful()

def run_specific_test(test_name):
    """Run a specific test module"""
    print(f"🧪 Running specific test: {test_name}")
    print("=" * 40)
    
    loader = unittest.TestLoader()
    
    try:
        suite = loader.loadTestsFromName(test_name)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    except Exception as e:
        print(f"❌ Error running test {test_name}: {e}")
        return False

def main():
    """Main test runner function"""
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # Run all tests
        success = run_test_suite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

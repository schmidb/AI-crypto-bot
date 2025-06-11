# AI Crypto Trading Bot - Test Suite

This directory contains comprehensive tests for all core functionality of the AI Crypto Trading Bot.

## 🧪 Test Overview

The test suite covers all critical components with unit tests, integration tests, and edge case testing:

### Core Component Tests

| Test Module | Component | Coverage |
|-------------|-----------|----------|
| `test_main_bot.py` | Main Bot Orchestration | Bot initialization, trading cycles, shutdown handling |
| `test_llm_analyzer.py` | LLM Analysis | Market analysis, decision making, response parsing |
| `test_portfolio.py` | Portfolio Management | Balance tracking, trade execution, performance calculation |
| `test_dashboard.py` | Dashboard Updates | Data visualization, chart generation, real-time updates |
| `test_strategy.py` | Trading Strategy | Risk management, position sizing, trade validation |
| `test_data_collector.py` | Data Collection | Market data fetching, technical indicators, data processing |
| `test_coinbase.py` | Coinbase API Client | API communication, authentication, error handling |
| `test_backtesting.py` | Backtesting Engine | Strategy evaluation, historical analysis, performance metrics |

### Additional Test Modules

| Test Module | Purpose | Coverage |
|-------------|---------|----------|
| `test_config.py` | Configuration Management | Environment variables, defaults, validation |
| `test_error_handling.py` | Error Handling & Edge Cases | API failures, malformed data, resource limits |

## 🚀 Running Tests

### Run All Tests
```bash
# From the project root directory
./run_tests.sh
```

### Run Specific Test Module
```bash
# Run specific component tests
./run_tests.sh test_portfolio
./run_tests.sh test_llm_analyzer
```

### Run Individual Test Cases
```bash
# Run specific test class
python3 -m unittest tests.test_portfolio.TestPortfolio -v

# Run specific test method
python3 -m unittest tests.test_portfolio.TestPortfolio.test_execute_buy_trade -v
```

### Advanced Test Runner
```bash
# Use the comprehensive test runner
python3 tests/test_runner.py

# Run specific module with detailed output
python3 tests/test_runner.py test_main_bot
```

## 📊 Test Categories

### 1. Unit Tests
- **Purpose**: Test individual functions and methods in isolation
- **Coverage**: All core functions with mocked dependencies
- **Examples**: Portfolio balance updates, LLM response parsing, configuration loading

### 2. Integration Tests
- **Purpose**: Test component interactions and data flow
- **Coverage**: Multi-component workflows and realistic scenarios
- **Examples**: Complete trading cycles, dashboard updates with real data

### 3. Error Handling Tests
- **Purpose**: Verify graceful handling of failures and edge cases
- **Coverage**: API failures, malformed data, resource constraints
- **Examples**: Network timeouts, corrupted files, invalid configurations

### 4. Edge Case Tests
- **Purpose**: Test boundary conditions and extreme scenarios
- **Coverage**: Zero values, very large numbers, invalid inputs
- **Examples**: Insufficient funds, extreme market conditions, malformed responses

## 🎯 Test Features

### Comprehensive Mocking
- **External APIs**: Coinbase API, Google Vertex AI
- **File Operations**: JSON files, configuration files
- **System Resources**: Network, file system, memory

### Realistic Test Data
- **Market Data**: Realistic price movements, volume data, technical indicators
- **Portfolio States**: Various balance combinations, trade histories
- **AI Decisions**: Buy/sell/hold decisions with confidence levels

### Error Simulation
- **API Failures**: Connection errors, rate limiting, invalid responses
- **Data Corruption**: Malformed JSON, missing files, permission errors
- **Resource Limits**: Memory constraints, disk space, network timeouts

## 📈 Test Metrics

### Coverage Goals
- **Unit Test Coverage**: >90% of core functions
- **Integration Coverage**: All major workflows tested
- **Error Handling**: All failure modes covered
- **Edge Cases**: Boundary conditions validated

### Performance Benchmarks
- **Test Execution Time**: <30 seconds for full suite
- **Memory Usage**: Minimal memory footprint during testing
- **Reliability**: 100% test pass rate in clean environment

## 🔧 Test Configuration

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install -r requirements.txt

# Set test environment variables (optional)
export TESTING=true
export SIMULATION_MODE=true
```

### Mock Configuration
Tests use comprehensive mocking to avoid:
- Real API calls to Coinbase or Google Cloud
- Actual file system modifications
- Network dependencies
- External service requirements

### Test Data
- **Fixtures**: Predefined test data in realistic formats
- **Factories**: Dynamic test data generation
- **Scenarios**: Common and edge case scenarios

## 🛠️ Adding New Tests

### Test Structure
```python
import unittest
from unittest.mock import patch, MagicMock

class TestNewComponent(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        pass
    
    def tearDown(self):
        """Clean up after tests"""
        pass
    
    def test_specific_functionality(self):
        """Test specific functionality"""
        # Arrange
        # Act
        # Assert
        pass
```

### Best Practices
1. **Descriptive Names**: Use clear, descriptive test method names
2. **Arrange-Act-Assert**: Structure tests with clear phases
3. **Mock External Dependencies**: Avoid real API calls or file operations
4. **Test Edge Cases**: Include boundary conditions and error scenarios
5. **Realistic Data**: Use realistic test data that matches production scenarios

### Test Categories to Include
- **Happy Path**: Normal operation scenarios
- **Error Conditions**: Various failure modes
- **Edge Cases**: Boundary values and extreme conditions
- **Integration**: Component interaction testing

## 📋 Test Checklist

Before deploying new features, ensure:

- [ ] Unit tests for all new functions
- [ ] Integration tests for new workflows
- [ ] Error handling tests for failure modes
- [ ] Edge case tests for boundary conditions
- [ ] All tests pass consistently
- [ ] No external dependencies in tests
- [ ] Realistic test data used
- [ ] Performance impact assessed

## 🎉 Test Results Interpretation

### Success Indicators
- **100% Pass Rate**: All tests pass consistently
- **Fast Execution**: Test suite completes quickly
- **Clear Output**: Easy to understand test results
- **Good Coverage**: All critical paths tested

### Failure Analysis
- **Review Error Messages**: Understand specific failures
- **Check Mock Configuration**: Ensure mocks are properly set up
- **Validate Test Data**: Confirm test data is realistic
- **Update Tests**: Modify tests when code changes

## 🔍 Debugging Tests

### Common Issues
1. **Import Errors**: Check Python path and module imports
2. **Mock Failures**: Verify mock setup and patch decorators
3. **Data Issues**: Ensure test data matches expected formats
4. **Environment**: Check virtual environment and dependencies

### Debugging Commands
```bash
# Run with verbose output
python3 -m unittest tests.test_module -v

# Run single test with debugging
python3 -m unittest tests.test_module.TestClass.test_method -v

# Check test discovery
python3 -m unittest discover tests -v
```

## 📚 Additional Resources

- **Python unittest**: [Official Documentation](https://docs.python.org/3/library/unittest.html)
- **Mock Library**: [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- **Testing Best Practices**: Industry standards for Python testing
- **CI/CD Integration**: Automated testing in deployment pipelines

---

**Note**: Always run the full test suite before deploying to production. Tests are designed to catch issues early and ensure reliable bot operation.

"""
Example: Integrating Data Quality Validation into Trading System

This example shows how to integrate the data quality validation framework
into your existing trading bot to prevent data quality issues from affecting trades.
"""

import logging
from datetime import datetime
from utils.data_quality_monitor import DataQualityMonitor, validate_data_quality, DataQualityError
from strategies.strategy_manager import StrategyManager
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SafeTradingBot:
    """
    Example trading bot with integrated data quality validation.
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = logger
        self.strategy_manager = StrategyManager(config)
        self.data_quality_monitor = DataQualityMonitor(logger)
        
        # Track data quality metrics
        self.data_quality_stats = {
            'total_validations': 0,
            'failed_validations': 0,
            'warnings': 0,
            'last_validation_time': None
        }
    
    def analyze_with_data_quality_check(self, market_data, technical_indicators, portfolio):
        """
        Analyze market with comprehensive data quality validation.
        """
        self.data_quality_stats['total_validations'] += 1
        self.data_quality_stats['last_validation_time'] = datetime.utcnow()
        
        # Validate data quality first
        is_valid, errors = self.data_quality_monitor.validate_all(
            market_data, technical_indicators, portfolio
        )
        
        if not is_valid:
            self.data_quality_stats['failed_validations'] += 1
            error_msg = f"Data quality validation failed: {errors}"
            self.logger.error(error_msg)
            
            # Return safe HOLD signal instead of risking bad data
            from strategies.base_strategy import TradingSignal
            return TradingSignal(
                action="HOLD",
                confidence=0,
                reasoning=f"Data quality issues detected: {list(errors.keys())}"
            )
        
        # Log warnings if any
        if self.data_quality_monitor.warnings:
            self.data_quality_stats['warnings'] += len(self.data_quality_monitor.warnings)
            self.logger.warning(f"Data quality warnings: {self.data_quality_monitor.warnings}")
        
        # Data is good, proceed with normal analysis
        try:
            return self.strategy_manager.get_combined_signal(
                market_data, technical_indicators, portfolio
            )
        except Exception as e:
            self.logger.error(f"Strategy analysis failed: {e}")
            from strategies.base_strategy import TradingSignal
            return TradingSignal(
                action="HOLD",
                confidence=0,
                reasoning=f"Strategy analysis error: {str(e)}"
            )
    
    @validate_data_quality(logger)
    def analyze_with_decorator(self, market_data, technical_indicators, portfolio):
        """
        Example using the decorator approach for automatic validation.
        """
        return self.strategy_manager.get_combined_signal(
            market_data, technical_indicators, portfolio
        )
    
    def get_data_quality_report(self):
        """
        Get data quality statistics report.
        """
        if self.data_quality_stats['total_validations'] > 0:
            failure_rate = (self.data_quality_stats['failed_validations'] / 
                          self.data_quality_stats['total_validations']) * 100
        else:
            failure_rate = 0
        
        return {
            'total_validations': self.data_quality_stats['total_validations'],
            'failed_validations': self.data_quality_stats['failed_validations'],
            'failure_rate_percent': round(failure_rate, 2),
            'warnings': self.data_quality_stats['warnings'],
            'last_validation': self.data_quality_stats['last_validation_time'],
            'status': 'HEALTHY' if failure_rate < 5 else 'DEGRADED' if failure_rate < 20 else 'CRITICAL'
        }


def example_usage():
    """
    Example of how to use the data quality validation in practice.
    """
    config = Config()
    bot = SafeTradingBot(config)
    
    # Example 1: Good data
    print("=== Example 1: Good Data ===")
    good_market_data = {
        'price': 50000.0,
        'volume': {'current': 1500000, 'average': 1200000},
        'price_changes': {'1h': 2.0, '4h': 3.0, '24h': 5.0, '5d': 8.0},
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    good_technical_indicators = {
        'rsi': 65,
        'macd': {'macd': 0.3, 'signal': 0.2, 'histogram': 0.1},
        'bb_upper': 52000,
        'bb_lower': 48000,
        'bb_middle': 50000,
        'current_price': 50000.0
    }
    
    good_portfolio = {
        'EUR': {'amount': 1000.0, 'price': 1.0},
        'BTC': {'amount': 0.1, 'price': 50000.0}
    }
    
    try:
        signal = bot.analyze_with_data_quality_check(
            good_market_data, good_technical_indicators, good_portfolio
        )
        print(f"Good data result: {signal.action} (confidence: {signal.confidence}%)")
    except Exception as e:
        print(f"Error with good data: {e}")
    
    # Example 2: Bad data
    print("\n=== Example 2: Bad Data ===")
    bad_market_data = {
        'price': -100,  # Invalid negative price
        'volume': {'current': 'invalid', 'average': 1200000},  # Invalid volume type
        'price_changes': {'1h': float('nan'), '4h': 3.0, '24h': 5.0, '5d': 8.0}  # NaN price change
    }
    
    try:
        signal = bot.analyze_with_data_quality_check(
            bad_market_data, good_technical_indicators, good_portfolio
        )
        print(f"Bad data result: {signal.action} (confidence: {signal.confidence}%)")
        print(f"Reasoning: {signal.reasoning}")
    except Exception as e:
        print(f"Error with bad data: {e}")
    
    # Example 3: Using decorator approach
    print("\n=== Example 3: Decorator Approach ===")
    try:
        signal = bot.analyze_with_decorator(
            good_market_data, good_technical_indicators, good_portfolio
        )
        print(f"Decorator result: {signal.action} (confidence: {signal.confidence}%)")
    except DataQualityError as e:
        print(f"Data quality error caught by decorator: {e}")
    except Exception as e:
        print(f"Other error: {e}")
    
    # Example 4: Data quality report
    print("\n=== Example 4: Data Quality Report ===")
    report = bot.get_data_quality_report()
    print(f"Data Quality Status: {report['status']}")
    print(f"Total Validations: {report['total_validations']}")
    print(f"Failed Validations: {report['failed_validations']}")
    print(f"Failure Rate: {report['failure_rate_percent']}%")
    print(f"Warnings: {report['warnings']}")


def integration_checklist():
    """
    Checklist for integrating data quality validation into existing systems.
    """
    checklist = """
    DATA QUALITY INTEGRATION CHECKLIST:
    
    ✅ 1. Import the data quality monitor:
       from utils.data_quality_monitor import DataQualityMonitor, validate_data_quality
    
    ✅ 2. Choose integration approach:
       Option A: Manual validation before analysis
       Option B: Decorator-based automatic validation
       Option C: Middleware validation in data pipeline
    
    ✅ 3. Handle validation failures gracefully:
       - Return safe HOLD signals instead of risky trades
       - Log detailed error information for debugging
       - Implement fallback mechanisms
    
    ✅ 4. Monitor data quality metrics:
       - Track validation success/failure rates
       - Set up alerts for high failure rates
       - Log warnings for degraded data quality
    
    ✅ 5. Test with various data scenarios:
       - Valid data (should pass)
       - Invalid data (should be caught)
       - Edge cases (boundary conditions)
       - Missing data (should handle gracefully)
    
    ✅ 6. Configure appropriate thresholds:
       - Price ranges for your trading pairs
       - Volume thresholds for your markets
       - Staleness limits for your use case
    
    ✅ 7. Set up monitoring and alerting:
       - Dashboard for data quality metrics
       - Alerts for validation failures
       - Regular data quality reports
    
    ✅ 8. Document data quality requirements:
       - Expected data formats and ranges
       - Validation rules and thresholds
       - Error handling procedures
    """
    print(checklist)


if __name__ == "__main__":
    print("Data Quality Integration Example")
    print("=" * 40)
    
    example_usage()
    
    print("\n" + "=" * 40)
    integration_checklist()

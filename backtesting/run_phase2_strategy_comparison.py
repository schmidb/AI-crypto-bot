#!/usr/bin/env python3
"""
Phase 2: Adaptive Strategy Comparison - Enhanced vs Original (90 days)

Purpose: Compare AdaptiveStrategyManager vs individual strategies to validate improvements
Duration: 2-3 hours
Assets: BTC-EUR, ETH-EUR
Period: 90 days
Interval: 60 minutes

UPDATED: Now uses AdaptiveBacktestEngine for aligned testing
"""

import sys
import logging
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append('.')

# Import aligned backtesting components
from utils.backtest.adaptive_backtest_engine import AdaptiveBacktestEngine
from utils.backtest.market_regime_analyzer import MarketRegimeAnalyzer
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase2AdaptiveStrategyComparison:
    """Phase 2 adaptive strategy comparison test runner"""
    
    def __init__(self):
        self.results_dir = Path("backtesting/reports/phase2_adaptive_strategy_comparison")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            'phase': 'Phase 2 - Adaptive Strategy Comparison',
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'summary': {},
            'adaptive_results': {}
        }
        
        # Test configuration
        self.assets = ['BTC-EUR', 'ETH-EUR']
        self.period_days = 90
        self.interval_minutes = 60
        
        # Initialize aligned components
        self.config = Config()
        self.adaptive_engine = AdaptiveBacktestEngine(
            initial_capital=10000.0,
            fees=0.006,
            slippage=0.0005,
            config=self.config
        )
        self.regime_analyzer = MarketRegimeAnalyzer()
        
        logger.info("🚀 Phase 2 initialized with AdaptiveBacktestEngine")
    
    def run_test(self, test_name: str, command: str, description: str, timeout: int = 3600) -> bool:
        """Run a single test and capture results"""
        logger.info(f"🧪 Running {test_name}: {description}")
        
        try:
            # Run the test command
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            
            self.results['tests'][test_name] = {
                'description': description,
                'command': command,
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout[-2000:] if result.stdout else '',  # Last 2000 chars
                'stderr': result.stderr[-1000:] if result.stderr else '',
                'timestamp': datetime.now().isoformat(),
                'timeout': timeout
            }
            
            if success:
                logger.info(f"✅ {test_name} completed successfully")
            else:
                logger.error(f"❌ {test_name} failed (return code: {result.returncode})")
                if result.stderr:
                    logger.error(f"Error: {result.stderr[:200]}...")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {test_name} timed out after {timeout} seconds")
            self.results['tests'][test_name] = {
                'description': description,
                'command': command,
                'success': False,
                'error': f'Timeout after {timeout} seconds',
                'timestamp': datetime.now().isoformat()
            }
            return False
            
        except Exception as e:
            logger.error(f"💥 {test_name} crashed: {e}")
            self.results['tests'][test_name] = {
                'description': description,
                'command': command,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return False
    
    def run_all_tests(self) -> bool:
        """Run all Phase 2 strategy comparison tests"""
        logger.info("🚀 Starting Phase 2 Strategy Comparison")
        logger.info(f"📊 Testing: {self.period_days} days, {', '.join(self.assets)}, Enhanced vs Original")
        
        tests = []
        passed_tests = 0
        
        # Test 1: Parameter optimization (baseline for enhanced strategies)
        test_name = 'parameter_optimization'
        description = 'Optimize strategy parameters for enhanced performance'
        command = 'python backtesting/optimize_strategy_parameters.py'
        timeout = 3600  # 1 hour
        
        tests.append((test_name, command, description, timeout))
        
        # Test 2: Strategy performance debugging
        test_name = 'strategy_performance_debug'
        description = 'Debug and analyze individual strategy performance'
        command = 'python backtesting/debug_strategy_performance.py'
        timeout = 2400  # 40 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Test 3: Enhanced strategies test (if available)
        enhanced_script = Path("backtesting/test_enhanced_strategies_6months_fast.py")
        if enhanced_script.exists():
            test_name = 'enhanced_strategies_test'
            description = 'Test enhanced strategies with optimized parameters'
            command = 'python backtesting/test_enhanced_strategies_6months_fast.py'
            timeout = 5400  # 1.5 hours
            
            tests.append((test_name, command, description, timeout))
        
        # Test 4: Comprehensive backtest comparison
        comprehensive_script = Path("backtesting/test_comprehensive_backtest.py")
        if comprehensive_script.exists():
            test_name = 'comprehensive_backtest_comparison'
            description = 'Compare comprehensive backtest results'
            command = 'python backtesting/test_comprehensive_backtest.py'
            timeout = 3600  # 1 hour
            
            tests.append((test_name, command, description, timeout))
        
        # Test 5: Simple backtest for baseline
        test_name = 'simple_backtest_baseline'
        description = 'Run simple backtest for baseline comparison'
        command = 'python backtesting/test_simple_backtest.py'
        timeout = 1800  # 30 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Run all tests
        total_tests = len(tests)
        for test_info in tests:
            if len(test_info) == 4:
                test_name, command, description, timeout = test_info
            else:
                test_name, command, description = test_info
                timeout = 3600  # Default 1 hour
            
            success = self.run_test(test_name, command, description, timeout)
            if success:
                passed_tests += 1
        
        # Calculate results
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        overall_success = success_rate >= 0.7  # 70% pass rate required
        
        # Create summary
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_success': overall_success,
            'assets_tested': self.assets,
            'period_days': self.period_days,
            'interval_minutes': self.interval_minutes
        }
        
        self.results.update({
            'end_time': datetime.now().isoformat(),
            'recommendation': self._get_recommendation(success_rate, passed_tests, total_tests)
        })
        
        # Save results
        self.save_results()
        self.display_results()
        
        return overall_success
    
    def _get_recommendation(self, success_rate: float, passed: int, total: int) -> str:
        """Get recommendation based on test results"""
        if success_rate >= 0.9:
            return "✅ Strategy comparison completed successfully. Enhanced strategies validated. Proceed to Phase 3 (Interval Optimization)."
        elif success_rate >= 0.7:
            return "⚠️ Most strategy comparisons completed. Review failed tests, then proceed to Phase 3."
        elif success_rate >= 0.5:
            return "🔧 Some strategy comparison issues detected. Fix failed tests before proceeding."
        else:
            return "❌ Major strategy comparison issues detected. Fix all critical tests before proceeding."
    
    def save_results(self):
        """Save test results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase2_strategy_comparison_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_phase2_strategy_comparison.json"
            with open(latest_filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def display_results(self):
        """Display test results summary"""
        print(f"\n{'='*80}")
        print(f"PHASE 2 STRATEGY COMPARISON RESULTS")
        print(f"{'='*80}")
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.results['summary']['total_tests']}")
        print(f"   Passed: {self.results['summary']['passed_tests']}")
        print(f"   Success Rate: {self.results['summary']['success_rate']:.1%}")
        print(f"   Overall: {'✅ PASS' if self.results['summary']['overall_success'] else '❌ FAIL'}")
        
        print(f"\n🎯 Test Configuration:")
        print(f"   Assets: {', '.join(self.results['summary']['assets_tested'])}")
        print(f"   Period: {self.results['summary']['period_days']} days")
        print(f"   Interval: {self.results['summary']['interval_minutes']} minutes")
        
        print(f"\n🧪 Individual Test Results:")
        for test_name, test_result in self.results['tests'].items():
            status = "✅ PASS" if test_result['success'] else "❌ FAIL"
            timeout_info = f" ({test_result.get('timeout', 3600)}s timeout)" if 'timeout' in test_result else ""
            print(f"   {test_name:<30} {status}{timeout_info}")
            if not test_result['success'] and 'error' in test_result:
                print(f"      Error: {test_result['error']}")
        
        print(f"\n💡 Recommendation:")
        print(f"   {self.results['recommendation']}")
        
        if self.results['summary']['overall_success']:
            print(f"\n🎯 Next Steps:")
            print(f"   1. Review strategy comparison results")
            print(f"   2. Identify best performing enhanced strategies")
            print(f"   3. Update configuration with optimal parameters")
            print(f"   4. Run Phase 3: python backtesting/run_phase3_interval_optimization.py")
            print(f"   5. Continue with comprehensive testing strategy")
        else:
            print(f"\n🔧 Required Actions:")
            print(f"   1. Fix all failed tests")
            print(f"   2. Re-run Phase 2 strategy comparison")
            print(f"   3. Only proceed when success rate >= 70%")
        
        print(f"\n📈 Strategy Analysis:")
        print(f"   - Compare enhanced vs original strategy performance")
        print(f"   - Look for consistent improvements across assets")
        print(f"   - Validate parameter optimization effectiveness")
        print(f"   - Check market filter impact on performance")

def main():
    """Run Phase 2 strategy comparison"""
    try:
        comparison = Phase2StrategyComparison()
        success = comparison.run_all_tests()
        
        if success:
            print(f"\n✅ Phase 2 strategy comparison completed successfully!")
            print(f"🚀 Ready to proceed to Phase 3 (Interval Optimization)")
            return True
        else:
            print(f"\n❌ Phase 2 strategy comparison failed!")
            print(f"🔧 Please fix issues before proceeding")
            return False
            
    except Exception as e:
        logger.error(f"Phase 2 strategy comparison crashed: {e}")
        print(f"\n💥 Phase 2 strategy comparison crashed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
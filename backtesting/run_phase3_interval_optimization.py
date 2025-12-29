#!/usr/bin/env python3
"""
Phase 3: Interval Optimization - Find Optimal Trading Frequency (90 days)

Purpose: Test different time intervals to find optimal trading frequency
Duration: 3-4 hours
Assets: BTC-EUR, ETH-EUR
Period: 90 days
Intervals: 15, 30, 60, 120 minutes

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

class Phase3IntervalOptimization:
    """Phase 3 interval optimization test runner"""
    
    def __init__(self):
        self.results_dir = Path("backtesting/reports/phase3_interval_optimization")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            'phase': 'Phase 3 - Interval Optimization',
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'summary': {},
            'adaptive_results': {}
        }
        
        # Test configuration
        self.intervals = [15, 30, 60, 120]  # minutes
        self.assets = ['BTC-EUR', 'ETH-EUR']
        self.period_days = 90
        
        # Initialize aligned components
        self.config = Config()
        self.adaptive_engine = AdaptiveBacktestEngine(
            initial_capital=10000.0,
            fees=0.006,
            slippage=0.0005,
            config=self.config
        )
        self.regime_analyzer = MarketRegimeAnalyzer()
        
        logger.info("🚀 Phase 3 initialized with AdaptiveBacktestEngine")
    
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
        """Run all Phase 3 interval optimization tests"""
        logger.info("🚀 Starting Phase 3 Interval Optimization")
        logger.info(f"📊 Testing: {self.period_days} days, {', '.join(self.assets)}, intervals: {self.intervals} minutes")
        
        tests = []
        passed_tests = 0
        
        # Test 1: Adaptive interval optimization (primary test)
        test_name = 'adaptive_interval_optimization'
        description = 'Test AdaptiveStrategyManager across different intervals'
        command = 'python backtesting/test_interval_optimization_adaptive.py'
        timeout = 5400  # 1.5 hours
        
        tests.append((test_name, command, description, timeout))
        
        # Test 2: Basic interval optimization (legacy comparison)
        test_name = 'basic_interval_optimization'
        description = f'Test basic interval optimization across {self.intervals} minute intervals'
        command = 'python backtesting/interval_optimization.py'
        timeout = 3600  # 1 hour
        
        tests.append((test_name, command, description, timeout))
        
        # Test 3: Enhanced strategies interval test (if available)
        enhanced_6m_script = Path("backtesting/test_enhanced_strategies_6months_fast.py")
        if enhanced_6m_script.exists():
            test_name = 'enhanced_strategies_interval_test'
            description = 'Test enhanced strategies with different intervals (fast version)'
            command = 'python backtesting/test_enhanced_strategies_6months_fast.py'
            timeout = 7200  # 2 hours
            
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
            'intervals_tested': self.intervals,
            'assets_tested': self.assets,
            'period_days': self.period_days
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
            return "✅ Interval optimization completed successfully. Proceed to Phase 4 (Comprehensive Analysis)."
        elif success_rate >= 0.7:
            return "⚠️ Most interval tests completed. Review failed tests, then proceed to Phase 4."
        elif success_rate >= 0.5:
            return "🔧 Some interval optimization issues detected. Fix failed tests before proceeding."
        else:
            return "❌ Major interval optimization issues detected. Fix all critical tests before proceeding."
    
    def save_results(self):
        """Save test results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase3_interval_optimization_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_phase3_interval_optimization.json"
            with open(latest_filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def display_results(self):
        """Display test results summary"""
        print(f"\n{'='*80}")
        print(f"PHASE 3 INTERVAL OPTIMIZATION RESULTS")
        print(f"{'='*80}")
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.results['summary']['total_tests']}")
        print(f"   Passed: {self.results['summary']['passed_tests']}")
        print(f"   Success Rate: {self.results['summary']['success_rate']:.1%}")
        print(f"   Overall: {'✅ PASS' if self.results['summary']['overall_success'] else '❌ FAIL'}")
        
        print(f"\n🎯 Test Configuration:")
        print(f"   Intervals: {', '.join(map(str, self.results['summary']['intervals_tested']))} minutes")
        print(f"   Assets: {', '.join(self.results['summary']['assets_tested'])}")
        print(f"   Period: {self.results['summary']['period_days']} days")
        
        print(f"\n🧪 Individual Test Results:")
        for test_name, test_result in self.results['tests'].items():
            status = "✅ PASS" if test_result['success'] else "❌ FAIL"
            print(f"   {test_name:<30} {status}")
            if not test_result['success'] and 'error' in test_result:
                print(f"      Error: {test_result['error']}")
        
        print(f"\n💡 Recommendation:")
        print(f"   {self.results['recommendation']}")
        
        if self.results['summary']['overall_success']:
            print(f"\n🎯 Next Steps:")
            print(f"   1. Review interval optimization results")
            print(f"   2. Update DECISION_INTERVAL_MINUTES in configuration if needed")
            print(f"   3. Run Phase 4: python backtesting/run_phase4_comprehensive_analysis.py")
            print(f"   4. Continue with comprehensive testing strategy")
        else:
            print(f"\n🔧 Required Actions:")
            print(f"   1. Fix all failed tests")
            print(f"   2. Re-run Phase 3 interval optimization")
            print(f"   3. Only proceed when success rate >= 70%")

def main():
    """Run Phase 3 interval optimization"""
    try:
        optimizer = Phase3IntervalOptimization()
        success = optimizer.run_all_tests()
        
        if success:
            print(f"\n✅ Phase 3 interval optimization completed successfully!")
            print(f"🚀 Ready to proceed to Phase 4 (Comprehensive Analysis)")
            return True
        else:
            print(f"\n❌ Phase 3 interval optimization failed!")
            print(f"🔧 Please fix issues before proceeding")
            return False
            
    except Exception as e:
        logger.error(f"Phase 3 interval optimization crashed: {e}")
        print(f"\n💥 Phase 3 interval optimization crashed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
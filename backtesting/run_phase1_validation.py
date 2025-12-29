#!/usr/bin/env python3
"""
Phase 1: Foundation Tests - Quick Validation (30 days)

Purpose: Ensure all systems work correctly before comprehensive testing
Duration: 1-2 hours
Assets: BTC-USD
Period: 30 days
Interval: 60 minutes
"""

import sys
import logging
import json
from datetime import datetime
from pathlib import Path
import subprocess

# Add project root to path
sys.path.append('.')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase1Validator:
    """Phase 1 validation test runner"""
    
    def __init__(self):
        self.results_dir = Path("backtesting/reports/phase1_validation")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            'phase': 'Phase 1 - Foundation Tests',
            'start_time': datetime.now().isoformat(),
            'tests': {}
        }
    
    def run_test(self, test_name: str, command: str, description: str) -> bool:
        """Run a single test and capture results"""
        logger.info(f"🧪 Running {test_name}: {description}")
        
        try:
            # Run the test command
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            
            self.results['tests'][test_name] = {
                'description': description,
                'command': command,
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout[-1000:] if result.stdout else '',  # Last 1000 chars
                'stderr': result.stderr[-1000:] if result.stderr else '',
                'timestamp': datetime.now().isoformat()
            }
            
            if success:
                logger.info(f"✅ {test_name} passed")
            else:
                logger.error(f"❌ {test_name} failed (return code: {result.returncode})")
                if result.stderr:
                    logger.error(f"Error: {result.stderr[:200]}...")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {test_name} timed out after 5 minutes")
            self.results['tests'][test_name] = {
                'description': description,
                'command': command,
                'success': False,
                'error': 'Timeout after 5 minutes',
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
        """Run all Phase 1 validation tests"""
        logger.info("🚀 Starting Phase 1 Foundation Tests")
        logger.info("📊 Testing: 30 days, BTC-USD, 60min interval")
        
        tests = [
            # System validation tests
            {
                'name': 'backtest_engine',
                'command': 'python backtesting/test_backtest_engine.py',
                'description': 'Test backtest engine functionality'
            },
            {
                'name': 'strategy_vectorization',
                'command': 'python backtesting/test_strategy_vectorization_quick.py',
                'description': 'Test strategy vectorization (quick version)'
            },
            {
                'name': 'indicators',
                'command': 'python backtesting/test_indicators.py',
                'description': 'Test technical indicator calculations'
            },
            
            # Basic strategy tests
            {
                'name': 'simple_backtest',
                'command': 'python backtesting/test_simple_backtest.py',
                'description': 'Test basic strategy backtesting'
            },
            {
                'name': 'strategy_debug',
                'command': 'python backtesting/debug_simple_strategy.py',
                'description': 'Debug individual strategy performance'
            },
            
            # Data and integration tests
            {
                'name': 'backtest_setup',
                'command': 'python backtesting/test_backtest_setup.py',
                'description': 'Test backtest setup and data loading'
            }
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            success = self.run_test(
                test['name'],
                test['command'],
                test['description']
            )
            if success:
                passed_tests += 1
        
        # Calculate results
        success_rate = passed_tests / total_tests
        overall_success = success_rate >= 0.8  # 80% pass rate required
        
        self.results.update({
            'end_time': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_success': overall_success,
            'recommendation': self._get_recommendation(success_rate, passed_tests, total_tests)
        })
        
        # Save results
        self.save_results()
        self.display_results()
        
        return overall_success
    
    def _get_recommendation(self, success_rate: float, passed: int, total: int) -> str:
        """Get recommendation based on test results"""
        if success_rate >= 0.9:
            return "✅ All systems healthy. Proceed to Phase 2 (Strategy Comparison)."
        elif success_rate >= 0.8:
            return "⚠️ Most systems healthy. Review failed tests, then proceed to Phase 2."
        elif success_rate >= 0.6:
            return "🔧 Some issues detected. Fix failed tests before proceeding."
        else:
            return "❌ Major issues detected. Fix all critical systems before proceeding."
    
    def save_results(self):
        """Save test results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase1_validation_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_phase1_validation.json"
            with open(latest_filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def display_results(self):
        """Display test results summary"""
        print(f"\n{'='*80}")
        print(f"PHASE 1 VALIDATION RESULTS")
        print(f"{'='*80}")
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.results['total_tests']}")
        print(f"   Passed: {self.results['passed_tests']}")
        print(f"   Success Rate: {self.results['success_rate']:.1%}")
        print(f"   Overall: {'✅ PASS' if self.results['overall_success'] else '❌ FAIL'}")
        
        print(f"\n🧪 Individual Test Results:")
        for test_name, test_result in self.results['tests'].items():
            status = "✅ PASS" if test_result['success'] else "❌ FAIL"
            print(f"   {test_name:<25} {status}")
            if not test_result['success'] and 'error' in test_result:
                print(f"      Error: {test_result['error']}")
        
        print(f"\n💡 Recommendation:")
        print(f"   {self.results['recommendation']}")
        
        if self.results['overall_success']:
            print(f"\n🎯 Next Steps:")
            print(f"   1. Review any failed tests (if any)")
            print(f"   2. Run Phase 2: python backtesting/run_phase2_strategy_comparison.py")
            print(f"   3. Continue with comprehensive testing strategy")
        else:
            print(f"\n🔧 Required Actions:")
            print(f"   1. Fix all failed tests")
            print(f"   2. Re-run Phase 1 validation")
            print(f"   3. Only proceed when success rate >= 80%")

def main():
    """Run Phase 1 validation"""
    try:
        validator = Phase1Validator()
        success = validator.run_all_tests()
        
        if success:
            print(f"\n✅ Phase 1 validation completed successfully!")
            print(f"🚀 Ready to proceed to Phase 2 (Strategy Comparison)")
            return True
        else:
            print(f"\n❌ Phase 1 validation failed!")
            print(f"🔧 Please fix issues before proceeding")
            return False
            
    except Exception as e:
        logger.error(f"Phase 1 validation crashed: {e}")
        print(f"\n💥 Phase 1 validation crashed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
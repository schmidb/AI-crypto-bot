#!/usr/bin/env python3
"""
Phase 4: Comprehensive Analysis - Full Strategy Validation (180 days)

Purpose: Full strategy validation across market cycles
Duration: 4-6 hours (or use VM upgrade)
Assets: BTC-USD, ETH-USD
Period: 180 days (6 months)
Focus: Enhanced strategies with optimal settings
"""

import sys
import logging
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append('.')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase4ComprehensiveAnalysis:
    """Phase 4 comprehensive analysis test runner"""
    
    def __init__(self):
        self.results_dir = Path("backtesting/reports/phase4_comprehensive_analysis")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            'phase': 'Phase 4 - Comprehensive Analysis',
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'summary': {}
        }
        
        # Test configuration
        self.assets = ['BTC-USD', 'ETH-USD']
        self.period_days = 180
        self.use_fast_version = True  # Use fast version by default to avoid 12+ hour runs
    
    def run_test(self, test_name: str, command: str, description: str, timeout: int = 7200) -> bool:
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
                'stdout': result.stdout[-3000:] if result.stdout else '',  # Last 3000 chars
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
        """Run all Phase 4 comprehensive analysis tests"""
        logger.info("🚀 Starting Phase 4 Comprehensive Analysis")
        logger.info(f"📊 Testing: {self.period_days} days, {', '.join(self.assets)}")
        logger.info(f"⚡ Using fast version: {self.use_fast_version}")
        
        tests = []
        passed_tests = 0
        
        # Test 1: Enhanced strategies 6-month test
        if self.use_fast_version:
            test_name = 'enhanced_strategies_6months_fast'
            description = '6-month enhanced strategy test (fast version)'
            command = 'python backtesting/test_enhanced_strategies_6months_fast.py'
            timeout = 7200  # 2 hours
        else:
            test_name = 'enhanced_strategies_6months_full'
            description = '6-month enhanced strategy test (full version)'
            command = 'python backtesting/test_enhanced_strategies_6months.py'
            timeout = 21600  # 6 hours
        
        tests.append((test_name, command, description, timeout))
        
        # Test 2: Market period analysis
        test_name = 'market_period_analysis'
        description = 'Analyze different market periods and regimes'
        command = 'python backtesting/analyze_market_period.py'
        timeout = 3600  # 1 hour
        
        tests.append((test_name, command, description, timeout))
        
        # Test 3: Comprehensive backtest (if available)
        comprehensive_script = Path("backtesting/test_comprehensive_backtest.py")
        if comprehensive_script.exists():
            test_name = 'comprehensive_backtest'
            description = 'Run comprehensive backtest with all strategies'
            command = 'python backtesting/test_comprehensive_backtest.py'
            timeout = 5400  # 1.5 hours
            
            tests.append((test_name, command, description, timeout))
        
        # Test 4: Strategy performance debugging
        test_name = 'strategy_performance_debug'
        description = 'Debug and analyze strategy performance in detail'
        command = 'python backtesting/debug_strategy_performance.py'
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
        overall_success = success_rate >= 0.75  # 75% pass rate required for comprehensive analysis
        
        # Create summary
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_success': overall_success,
            'assets_tested': self.assets,
            'period_days': self.period_days,
            'fast_version_used': self.use_fast_version
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
            return "✅ Comprehensive analysis completed successfully. Proceed to Phase 5 (Production Readiness)."
        elif success_rate >= 0.75:
            return "⚠️ Most comprehensive tests completed. Review failed tests, then proceed to Phase 5."
        elif success_rate >= 0.5:
            return "🔧 Some comprehensive analysis issues detected. Fix failed tests before proceeding."
        else:
            return "❌ Major comprehensive analysis issues detected. Fix all critical tests before proceeding."
    
    def save_results(self):
        """Save test results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase4_comprehensive_analysis_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_phase4_comprehensive_analysis.json"
            with open(latest_filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def display_results(self):
        """Display test results summary"""
        print(f"\n{'='*80}")
        print(f"PHASE 4 COMPREHENSIVE ANALYSIS RESULTS")
        print(f"{'='*80}")
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.results['summary']['total_tests']}")
        print(f"   Passed: {self.results['summary']['passed_tests']}")
        print(f"   Success Rate: {self.results['summary']['success_rate']:.1%}")
        print(f"   Overall: {'✅ PASS' if self.results['summary']['overall_success'] else '❌ FAIL'}")
        
        print(f"\n🎯 Test Configuration:")
        print(f"   Assets: {', '.join(self.results['summary']['assets_tested'])}")
        print(f"   Period: {self.results['summary']['period_days']} days")
        print(f"   Fast Version: {'Yes' if self.results['summary']['fast_version_used'] else 'No'}")
        
        print(f"\n🧪 Individual Test Results:")
        for test_name, test_result in self.results['tests'].items():
            status = "✅ PASS" if test_result['success'] else "❌ FAIL"
            timeout_info = f" ({test_result.get('timeout', 3600)}s timeout)" if 'timeout' in test_result else ""
            print(f"   {test_name:<35} {status}{timeout_info}")
            if not test_result['success'] and 'error' in test_result:
                print(f"      Error: {test_result['error']}")
        
        print(f"\n💡 Recommendation:")
        print(f"   {self.results['recommendation']}")
        
        if self.results['summary']['overall_success']:
            print(f"\n🎯 Next Steps:")
            print(f"   1. Review comprehensive analysis results")
            print(f"   2. Analyze risk-adjusted returns and drawdowns")
            print(f"   3. Run Phase 5: python backtesting/run_phase5_production_readiness.py")
            print(f"   4. Prepare for production deployment")
        else:
            print(f"\n🔧 Required Actions:")
            print(f"   1. Fix all failed tests")
            print(f"   2. Consider scaling up VM for better performance")
            print(f"   3. Re-run Phase 4 comprehensive analysis")
            print(f"   4. Only proceed when success rate >= 75%")
        
        print(f"\n⚡ Performance Notes:")
        if self.results['summary']['fast_version_used']:
            print(f"   - Used fast version for quicker testing")
            print(f"   - For full analysis, set use_fast_version=False")
        print(f"   - Consider VM scaling for better performance")
        print(f"   - Use ./scripts/vm_scale_up.sh for faster execution")

def main():
    """Run Phase 4 comprehensive analysis"""
    try:
        analyzer = Phase4ComprehensiveAnalysis()
        success = analyzer.run_all_tests()
        
        if success:
            print(f"\n✅ Phase 4 comprehensive analysis completed successfully!")
            print(f"🚀 Ready to proceed to Phase 5 (Production Readiness)")
            return True
        else:
            print(f"\n❌ Phase 4 comprehensive analysis failed!")
            print(f"🔧 Please fix issues before proceeding")
            return False
            
    except Exception as e:
        logger.error(f"Phase 4 comprehensive analysis crashed: {e}")
        print(f"\n💥 Phase 4 comprehensive analysis crashed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
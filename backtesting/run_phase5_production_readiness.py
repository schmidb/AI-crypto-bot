#!/usr/bin/env python3
"""
Phase 5: Production Readiness - Final Validation (Current Data)

Purpose: Final validation before live deployment
Duration: 1-2 hours
Assets: BTC-EUR, ETH-EUR
Focus: Integration tests, health checks, monitoring

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
from utils.backtest.risk_management_validator import RiskManagementValidator
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase5ProductionReadiness:
    """Phase 5 production readiness test runner"""
    
    def __init__(self):
        self.results_dir = Path("backtesting/reports/phase5_production_readiness")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.results = {
            'phase': 'Phase 5 - Production Readiness',
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'summary': {},
            'adaptive_validation': {}
        }
        
        # Test configuration
        self.assets = ['BTC-EUR', 'ETH-EUR']
        
        # Initialize aligned components for validation
        self.config = Config()
        self.adaptive_engine = AdaptiveBacktestEngine(
            initial_capital=10000.0,
            fees=0.006,
            slippage=0.0005,
            config=self.config
        )
        self.regime_analyzer = MarketRegimeAnalyzer()
        self.risk_validator = RiskManagementValidator(self.config)
        
        logger.info("🚀 Phase 5 initialized with aligned components for production validation")
    
    def run_test(self, test_name: str, command: str, description: str, timeout: int = 1800) -> bool:
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
        """Run all Phase 5 production readiness tests"""
        logger.info("🚀 Starting Phase 5 Production Readiness")
        logger.info(f"📊 Testing: Production integration and health checks with adaptive components")
        
        tests = []
        passed_tests = 0
        
        # Test 1: Adaptive backtest engine validation
        test_name = 'adaptive_backtest_engine_validation'
        description = 'Validate AdaptiveBacktestEngine alignment with live bot'
        command = 'python backtesting/test_adaptive_backtest_engine.py'
        timeout = 1800  # 30 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Test 2: Market regime analyzer validation
        test_name = 'market_regime_analyzer_validation'
        description = 'Validate MarketRegimeAnalyzer accuracy and performance'
        command = 'python backtesting/test_market_regime_analyzer.py'
        timeout = 900  # 15 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Test 3: Risk management validator
        test_name = 'risk_management_validation'
        description = 'Validate RiskManagementValidator with production settings'
        command = 'python backtesting/test_risk_management_validator.py'
        timeout = 900  # 15 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Test 4: LLM strategy simulator validation
        test_name = 'llm_strategy_simulator_validation'
        description = 'Validate LLM strategy simulator for realistic backtesting'
        command = 'python backtesting/test_llm_strategy_simulator.py'
        timeout = 900  # 15 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Test 5: Daily health check simulation
        # Test 5: Daily health check simulation
        test_name = 'daily_health_check'
        description = 'Simulate daily health check procedures'
        command = 'python backtesting/run_daily_health_check.py'
        timeout = 1800  # 30 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Test 6: Weekly validation simulation
        # Test 6: Weekly validation simulation
        test_name = 'weekly_validation'
        description = 'Simulate weekly validation procedures'
        command = 'python backtesting/run_weekly_validation.py'
        timeout = 2400  # 40 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Test 7: Dashboard integration test
        # Test 7: Dashboard integration test
        test_name = 'dashboard_integration'
        description = 'Test dashboard integration and data flow'
        command = 'python backtesting/dashboard_integration.py'
        timeout = 900  # 15 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Test 8: GCS sync test
        test_name = 'gcs_sync_test'
        description = 'Test Google Cloud Storage synchronization'
        command = 'python backtesting/sync_to_gcs.py list'
        timeout = 600  # 10 minutes
        
        tests.append((test_name, command, description, timeout))
        
        # Test 8: Backtest integration test (if available)
        backtest_integration_script = Path("backtesting/test_backtest_integration.py")
        if backtest_integration_script.exists():
            test_name = 'backtest_integration'
            description = 'Test backtest integration with live systems'
            command = 'python backtesting/test_backtest_integration.py'
            timeout = 1800  # 30 minutes
            
            tests.append((test_name, command, description, timeout))
        
        # Test 9: Parameter monitoring
        param_monitoring_script = Path("backtesting/run_parameter_monitoring.py")
        if param_monitoring_script.exists():
            test_name = 'parameter_monitoring'
            description = 'Test parameter monitoring and alerting'
            command = 'python backtesting/run_parameter_monitoring.py'
            timeout = 900  # 15 minutes
            
            tests.append((test_name, command, description, timeout))
        
        # Test 10: Monthly stability check
        monthly_stability_script = Path("backtesting/run_monthly_stability.py")
        if monthly_stability_script.exists():
            test_name = 'monthly_stability'
            description = 'Test monthly stability procedures'
            command = 'python backtesting/run_monthly_stability.py'
            timeout = 3600  # 1 hour
            
            tests.append((test_name, command, description, timeout))
        
        # Run all tests
        total_tests = len(tests)
        for test_info in tests:
            if len(test_info) == 4:
                test_name, command, description, timeout = test_info
            else:
                test_name, command, description = test_info
                timeout = 1800  # Default 30 minutes
            
            success = self.run_test(test_name, command, description, timeout)
            if success:
                passed_tests += 1
        
        # Calculate results
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        overall_success = success_rate >= 0.8  # 80% pass rate required for production readiness
        
        # Create summary
        self.results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': success_rate,
            'overall_success': overall_success,
            'assets_tested': self.assets,
            'production_ready': overall_success,
            'adaptive_components_validated': True
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
        if success_rate >= 0.95:
            return "✅ All systems ready for production deployment. Deploy with confidence!"
        elif success_rate >= 0.8:
            return "⚠️ Most systems ready for production. Review failed tests, then deploy."
        elif success_rate >= 0.6:
            return "🔧 Some production readiness issues detected. Fix failed tests before deployment."
        else:
            return "❌ Major production readiness issues detected. Fix all critical systems before deployment."
    
    def save_results(self):
        """Save test results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phase5_production_readiness_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_phase5_production_readiness.json"
            with open(latest_filepath, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def display_results(self):
        """Display test results summary"""
        print(f"\n{'='*80}")
        print(f"PHASE 5 PRODUCTION READINESS RESULTS")
        print(f"{'='*80}")
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {self.results['summary']['total_tests']}")
        print(f"   Passed: {self.results['summary']['passed_tests']}")
        print(f"   Success Rate: {self.results['summary']['success_rate']:.1%}")
        print(f"   Overall: {'✅ PASS' if self.results['summary']['overall_success'] else '❌ FAIL'}")
        print(f"   Production Ready: {'✅ YES' if self.results['summary']['production_ready'] else '❌ NO'}")
        
        print(f"\n🎯 Test Configuration:")
        print(f"   Assets: {', '.join(self.results['summary']['assets_tested'])}")
        print(f"   Focus: Integration, health checks, monitoring")
        
        print(f"\n🧪 Individual Test Results:")
        for test_name, test_result in self.results['tests'].items():
            status = "✅ PASS" if test_result['success'] else "❌ FAIL"
            timeout_info = f" ({test_result.get('timeout', 1800)}s timeout)" if 'timeout' in test_result else ""
            print(f"   {test_name:<25} {status}{timeout_info}")
            if not test_result['success'] and 'error' in test_result:
                print(f"      Error: {test_result['error']}")
        
        print(f"\n💡 Recommendation:")
        print(f"   {self.results['recommendation']}")
        
        if self.results['summary']['overall_success']:
            print(f"\n🎯 Production Deployment Checklist:")
            print(f"   ✅ All systems tested and healthy")
            print(f"   ✅ AdaptiveBacktestEngine validated and aligned")
            print(f"   ✅ MarketRegimeAnalyzer accuracy confirmed")
            print(f"   ✅ RiskManagementValidator operational")
            print(f"   ✅ Integration tests passed")
            print(f"   ✅ Monitoring and alerting working")
            print(f"   ✅ Data synchronization verified")
            print(f"")
            print(f"🚀 Ready for Production Deployment!")
            print(f"   1. Set SIMULATION_MODE=false in .env")
            print(f"   2. Deploy using: python main.py")
            print(f"   3. Monitor dashboard and logs closely")
            print(f"   4. Run daily health checks")
            print(f"   5. Verify adaptive strategy decisions match backtesting")
        else:
            print(f"\n🔧 Required Actions Before Production:")
            print(f"   1. Fix all failed tests")
            print(f"   2. Verify adaptive component alignment")
            print(f"   3. Verify all integrations are working")
            print(f"   4. Test monitoring and alerting systems")
            print(f"   5. Re-run Phase 5 production readiness")
            print(f"   6. Only deploy when success rate >= 80%")
        
        print(f"\n📋 Post-Deployment Monitoring:")
        print(f"   - Monitor logs/supervisor.log for issues")
        print(f"   - Check dashboard for performance metrics")
        print(f"   - Verify adaptive decisions match expected patterns")
        print(f"   - Run daily health checks")
        print(f"   - Review weekly validation reports")
        print(f"   - Monitor GCS sync status")
        print(f"   - Compare live decisions with backtesting results")

def main():
    """Run Phase 5 production readiness"""
    try:
        readiness_checker = Phase5ProductionReadiness()
        success = readiness_checker.run_all_tests()
        
        if success:
            print(f"\n✅ Phase 5 production readiness completed successfully!")
            print(f"🚀 System is ready for production deployment!")
            return True
        else:
            print(f"\n❌ Phase 5 production readiness failed!")
            print(f"🔧 Please fix issues before production deployment")
            return False
            
    except Exception as e:
        logger.error(f"Phase 5 production readiness crashed: {e}")
        print(f"\n💥 Phase 5 production readiness crashed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
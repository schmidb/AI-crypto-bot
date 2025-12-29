#!/usr/bin/env python3
"""
Backtesting Alignment Validation Script

This script validates that the backtesting system is properly aligned with the live bot
by running comprehensive tests on all aligned components.
"""

import sys
import os
import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.append('.')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BacktestingAlignmentValidator:
    """
    Comprehensive validator for backtesting alignment with live bot
    """
    
    def __init__(self):
        """Initialize the alignment validator"""
        self.results_dir = Path("backtesting/reports/alignment_validation")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        self.validation_results = {
            'validation_start': datetime.now().isoformat(),
            'component_tests': {},
            'integration_tests': {},
            'summary': {},
            'recommendations': []
        }
        
        logger.info("🔍 BacktestingAlignmentValidator initialized")
    
    def run_component_test(self, test_name: str, test_script: str, description: str, 
                          timeout: int = 1800) -> Dict[str, Any]:
        """Run a single component test"""
        logger.info(f"🧪 Running {test_name}: {description}")
        
        try:
            # Set test environment
            env = os.environ.copy()
            env['TESTING'] = 'true'
            env['SIMULATION_MODE'] = 'true'
            
            # Run the test
            result = subprocess.run(
                ['python', test_script],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            
            success = result.returncode == 0
            
            test_result = {
                'test_name': test_name,
                'description': description,
                'script': test_script,
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout[-2000:] if result.stdout else '',
                'stderr': result.stderr[-1000:] if result.stderr else '',
                'timestamp': datetime.now().isoformat(),
                'timeout': timeout
            }
            
            if success:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED (return code: {result.returncode})")
                if result.stderr:
                    logger.error(f"Error: {result.stderr[:200]}...")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {test_name} timed out after {timeout} seconds")
            return {
                'test_name': test_name,
                'description': description,
                'script': test_script,
                'success': False,
                'error': f'Timeout after {timeout} seconds',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"💥 {test_name} crashed: {e}")
            return {
                'test_name': test_name,
                'description': description,
                'script': test_script,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def validate_aligned_components(self) -> Dict[str, Any]:
        """Validate all aligned components"""
        logger.info("🔍 Validating aligned components...")
        
        component_tests = [
            {
                'name': 'adaptive_backtest_engine',
                'script': 'backtesting/test_adaptive_backtest_engine.py',
                'description': 'Test AdaptiveBacktestEngine functionality and alignment',
                'timeout': 1800
            },
            {
                'name': 'market_regime_analyzer',
                'script': 'backtesting/test_market_regime_analyzer.py',
                'description': 'Test MarketRegimeAnalyzer accuracy and performance',
                'timeout': 900
            },
            {
                'name': 'risk_management_validator',
                'script': 'backtesting/test_risk_management_validator.py',
                'description': 'Test RiskManagementValidator alignment with live bot',
                'timeout': 900
            },
            {
                'name': 'llm_strategy_simulator',
                'script': 'backtesting/test_llm_strategy_simulator.py',
                'description': 'Test LLM strategy simulator for realistic backtesting decisions',
                'timeout': 900
            }
        ]
        
        component_results = {}
        passed_tests = 0
        
        for test_config in component_tests:
            # Check if test script exists
            if not Path(test_config['script']).exists():
                logger.warning(f"⚠️ Test script not found: {test_config['script']}")
                component_results[test_config['name']] = {
                    'success': False,
                    'error': 'Test script not found',
                    'description': test_config['description']
                }
                continue
            
            # Run the test
            result = self.run_component_test(
                test_config['name'],
                test_config['script'],
                test_config['description'],
                test_config.get('timeout', 1800)
            )
            
            component_results[test_config['name']] = result
            
            if result['success']:
                passed_tests += 1
        
        # Calculate component validation score
        total_tests = len(component_tests)
        component_score = passed_tests / total_tests if total_tests > 0 else 0
        
        self.validation_results['component_tests'] = {
            'results': component_results,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'component_score': component_score,
            'component_validation_passed': component_score >= 0.8  # 80% required
        }
        
        logger.info(f"📊 Component validation score: {component_score:.1%}")
        return self.validation_results['component_tests']
    
    def validate_integration(self) -> Dict[str, Any]:
        """Validate integration between components"""
        logger.info("🔗 Validating component integration...")
        
        integration_tests = [
            {
                'name': 'adaptive_integration',
                'script': 'backtesting/test_adaptive_integration.py',
                'description': 'Test integration between AdaptiveBacktestEngine and live bot',
                'timeout': 3600
            }
        ]
        
        integration_results = {}
        passed_tests = 0
        
        for test_config in integration_tests:
            # Check if test script exists
            if not Path(test_config['script']).exists():
                logger.warning(f"⚠️ Integration test script not found: {test_config['script']}")
                integration_results[test_config['name']] = {
                    'success': False,
                    'error': 'Test script not found',
                    'description': test_config['description']
                }
                continue
            
            # Run the test
            result = self.run_component_test(
                test_config['name'],
                test_config['script'],
                test_config['description'],
                test_config.get('timeout', 3600)
            )
            
            integration_results[test_config['name']] = result
            
            if result['success']:
                passed_tests += 1
        
        # Calculate integration validation score
        total_tests = len(integration_tests)
        integration_score = passed_tests / total_tests if total_tests > 0 else 0
        
        self.validation_results['integration_tests'] = {
            'results': integration_results,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'integration_score': integration_score,
            'integration_validation_passed': integration_score >= 0.9  # 90% required for integration
        }
        
        logger.info(f"📊 Integration validation score: {integration_score:.1%}")
        return self.validation_results['integration_tests']
    
    def analyze_alignment_quality(self) -> Dict[str, Any]:
        """Analyze the quality of alignment based on test results"""
        try:
            component_results = self.validation_results.get('component_tests', {})
            integration_results = self.validation_results.get('integration_tests', {})
            
            # Calculate overall alignment score
            component_score = component_results.get('component_score', 0)
            integration_score = integration_results.get('integration_score', 0)
            
            # Weighted average (integration is more important)
            overall_score = (component_score * 0.4) + (integration_score * 0.6)
            
            # Determine alignment quality
            if overall_score >= 0.95:
                quality_level = "EXCELLENT"
                quality_description = "Backtesting is excellently aligned with live bot"
            elif overall_score >= 0.85:
                quality_level = "GOOD"
                quality_description = "Backtesting is well aligned with live bot"
            elif overall_score >= 0.70:
                quality_level = "ACCEPTABLE"
                quality_description = "Backtesting has acceptable alignment with live bot"
            elif overall_score >= 0.50:
                quality_level = "POOR"
                quality_description = "Backtesting has poor alignment with live bot"
            else:
                quality_level = "CRITICAL"
                quality_description = "Backtesting has critical alignment issues"
            
            # Generate recommendations
            recommendations = []
            
            if component_score < 0.8:
                recommendations.append("Fix failing component tests before using backtesting")
            
            if integration_score < 0.9:
                recommendations.append("Address integration issues between backtesting and live bot")
            
            if overall_score < 0.85:
                recommendations.append("Do not rely on backtesting results until alignment improves")
            else:
                recommendations.append("Backtesting results should accurately represent live bot performance")
            
            if overall_score >= 0.95:
                recommendations.append("Backtesting system is production-ready")
            
            alignment_analysis = {
                'overall_alignment_score': overall_score,
                'component_score': component_score,
                'integration_score': integration_score,
                'quality_level': quality_level,
                'quality_description': quality_description,
                'alignment_acceptable': overall_score >= 0.85,
                'production_ready': overall_score >= 0.90,
                'recommendations': recommendations
            }
            
            return alignment_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing alignment quality: {e}")
            return {
                'overall_alignment_score': 0.0,
                'quality_level': 'ERROR',
                'quality_description': f'Error analyzing alignment: {str(e)}',
                'alignment_acceptable': False,
                'production_ready': False,
                'recommendations': ['Fix alignment analysis errors before proceeding']
            }
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive backtesting alignment validation"""
        try:
            logger.info("🚀 Starting comprehensive backtesting alignment validation...")
            
            # Step 1: Validate aligned components
            logger.info("📊 Step 1: Component Validation")
            component_results = self.validate_aligned_components()
            
            # Step 2: Validate integration
            logger.info("📊 Step 2: Integration Validation")
            integration_results = self.validate_integration()
            
            # Step 3: Analyze alignment quality
            logger.info("📊 Step 3: Alignment Quality Analysis")
            alignment_analysis = self.analyze_alignment_quality()
            
            # Create final summary
            self.validation_results['summary'] = {
                **alignment_analysis,
                'validation_end': datetime.now().isoformat(),
                'total_component_tests': component_results.get('total_tests', 0),
                'passed_component_tests': component_results.get('passed_tests', 0),
                'total_integration_tests': integration_results.get('total_tests', 0),
                'passed_integration_tests': integration_results.get('passed_tests', 0)
            }
            
            self.validation_results['recommendations'] = alignment_analysis.get('recommendations', [])
            
            # Save results
            self.save_validation_results()
            
            logger.info(f"✅ Validation completed: {alignment_analysis['overall_alignment_score']:.1%} alignment")
            return self.validation_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive validation: {e}")
            return {'error': str(e)}
    
    def save_validation_results(self):
        """Save validation results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtesting_alignment_validation_{timestamp}.json"
            filepath = self.results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(self.validation_results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = self.results_dir / "latest_backtesting_alignment_validation.json"
            with open(latest_filepath, 'w') as f:
                json.dump(self.validation_results, f, indent=2, default=str)
            
            logger.info(f"📁 Validation results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving validation results: {e}")
    
    def display_validation_results(self):
        """Display comprehensive validation results"""
        summary = self.validation_results.get('summary', {})
        
        print(f"\n{'='*80}")
        print(f"BACKTESTING ALIGNMENT VALIDATION RESULTS")
        print(f"{'='*80}")
        
        print(f"📊 Overall Alignment Score: {summary.get('overall_alignment_score', 0):.1%}")
        print(f"🏆 Quality Level: {summary.get('quality_level', 'UNKNOWN')}")
        print(f"📝 Quality Description: {summary.get('quality_description', 'No description available')}")
        
        print(f"\n📈 Component Scores:")
        print(f"   Component Tests: {summary.get('component_score', 0):.1%}")
        print(f"   Integration Tests: {summary.get('integration_score', 0):.1%}")
        
        print(f"\n📋 Test Summary:")
        print(f"   Component Tests: {summary.get('passed_component_tests', 0)}/{summary.get('total_component_tests', 0)}")
        print(f"   Integration Tests: {summary.get('passed_integration_tests', 0)}/{summary.get('total_integration_tests', 0)}")
        
        print(f"\n🎯 Validation Status:")
        print(f"   Alignment Acceptable: {'✅ YES' if summary.get('alignment_acceptable', False) else '❌ NO'}")
        print(f"   Production Ready: {'✅ YES' if summary.get('production_ready', False) else '❌ NO'}")
        
        print(f"\n💡 Recommendations:")
        recommendations = self.validation_results.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print(f"   No specific recommendations")
        
        # Component test details
        component_tests = self.validation_results.get('component_tests', {}).get('results', {})
        if component_tests:
            print(f"\n🧪 Component Test Details:")
            for test_name, result in component_tests.items():
                status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
                print(f"   {test_name:<30} {status}")
                if not result.get('success', False) and 'error' in result:
                    print(f"      Error: {result['error']}")
        
        # Integration test details
        integration_tests = self.validation_results.get('integration_tests', {}).get('results', {})
        if integration_tests:
            print(f"\n🔗 Integration Test Details:")
            for test_name, result in integration_tests.items():
                status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
                print(f"   {test_name:<30} {status}")
                if not result.get('success', False) and 'error' in result:
                    print(f"      Error: {result['error']}")
        
        # Final verdict
        if summary.get('production_ready', False):
            print(f"\n🎉 VALIDATION PASSED - PRODUCTION READY")
            print(f"   Backtesting system is properly aligned with live bot")
            print(f"   Backtesting results should accurately represent live performance")
            print(f"   Safe to proceed with backtesting phases")
        elif summary.get('alignment_acceptable', False):
            print(f"\n⚠️ VALIDATION PASSED - ACCEPTABLE ALIGNMENT")
            print(f"   Backtesting system has acceptable alignment")
            print(f"   Proceed with caution and monitor results closely")
        else:
            print(f"\n❌ VALIDATION FAILED - ALIGNMENT ISSUES")
            print(f"   Backtesting system has significant alignment issues")
            print(f"   Do not rely on backtesting results until issues are resolved")

def main():
    """Run the backtesting alignment validation"""
    try:
        # Set test environment
        os.environ['TESTING'] = 'true'
        os.environ['SIMULATION_MODE'] = 'true'
        
        # Run validation
        validator = BacktestingAlignmentValidator()
        results = validator.run_comprehensive_validation()
        
        # Display results
        validator.display_validation_results()
        
        # Return success status
        summary = results.get('summary', {})
        return summary.get('alignment_acceptable', False)
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"\n💥 Validation crashed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
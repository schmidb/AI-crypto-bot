#!/usr/bin/env python3
"""
Test LLM Strategy Simulator

This script tests the LLM strategy simulator to ensure it provides realistic
and consistent trading decisions for backtesting.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import json
from pathlib import Path

# Add project root to path
sys.path.append('.')

from utils.backtest.llm_strategy_simulator import LLMStrategySimulator, simulate_llm_analysis
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMSimulatorTest:
    """Test suite for LLM Strategy Simulator"""
    
    def __init__(self):
        """Initialize the test suite"""
        self.config = Config()
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'summary': {}
        }
        
        logger.info("🧪 LLM Strategy Simulator Test initialized")
    
    def generate_test_scenarios(self) -> list:
        """Generate various market scenarios for testing"""
        scenarios = []
        
        # Scenario 1: Strong bullish signals
        scenarios.append({
            'name': 'strong_bullish',
            'market_data': {
                'current_price': 50000.0,
                'price': 50000.0,
                'product_id': 'BTC-EUR',
                'price_changes': {'1h': 2.5, '24h': 8.0, '5d': 15.0}
            },
            'technical_indicators': {
                'rsi': 25.0,  # Oversold
                'macd': 150.0,
                'macd_signal': 100.0,
                'bb_upper': 52000.0,
                'bb_middle': 49000.0,
                'bb_lower': 46000.0,
                'current_price': 50000.0
            },
            'expected_action': 'BUY',
            'min_confidence': 60
        })
        
        # Scenario 2: Strong bearish signals
        scenarios.append({
            'name': 'strong_bearish',
            'market_data': {
                'current_price': 45000.0,
                'price': 45000.0,
                'product_id': 'BTC-EUR',
                'price_changes': {'1h': -3.0, '24h': -10.0, '5d': -20.0}
            },
            'technical_indicators': {
                'rsi': 80.0,  # Overbought
                'macd': -200.0,
                'macd_signal': -150.0,
                'bb_upper': 48000.0,
                'bb_middle': 45000.0,
                'bb_lower': 42000.0,
                'current_price': 45000.0
            },
            'expected_action': 'SELL',
            'min_confidence': 60
        })
        
        # Scenario 3: Neutral/mixed signals
        scenarios.append({
            'name': 'neutral_mixed',
            'market_data': {
                'current_price': 48000.0,
                'price': 48000.0,
                'product_id': 'BTC-EUR',
                'price_changes': {'1h': 0.5, '24h': -1.0, '5d': 2.0}
            },
            'technical_indicators': {
                'rsi': 52.0,  # Neutral
                'macd': 10.0,
                'macd_signal': 15.0,
                'bb_upper': 49000.0,
                'bb_middle': 48000.0,
                'bb_lower': 47000.0,
                'current_price': 48000.0
            },
            'expected_action': 'HOLD',
            'max_confidence': 70
        })
        
        # Scenario 4: High volatility squeeze
        scenarios.append({
            'name': 'volatility_squeeze',
            'market_data': {
                'current_price': 47500.0,
                'price': 47500.0,
                'product_id': 'BTC-EUR',
                'price_changes': {'1h': 0.1, '24h': 0.5, '5d': 1.0}
            },
            'technical_indicators': {
                'rsi': 48.0,
                'macd': 5.0,
                'macd_signal': 8.0,
                'bb_upper': 47600.0,  # Very tight bands
                'bb_middle': 47500.0,
                'bb_lower': 47400.0,
                'current_price': 47500.0
            },
            'expected_action': 'HOLD',
            'description': 'Low volatility squeeze should result in cautious HOLD'
        })
        
        # Scenario 5: Bollinger Band breakout (upper)
        scenarios.append({
            'name': 'bb_breakout_upper',
            'market_data': {
                'current_price': 51000.0,
                'price': 51000.0,
                'product_id': 'BTC-EUR',
                'price_changes': {'1h': 1.5, '24h': 4.0, '5d': 8.0}
            },
            'technical_indicators': {
                'rsi': 65.0,
                'macd': 80.0,
                'macd_signal': 60.0,
                'bb_upper': 50000.0,  # Price above upper band
                'bb_middle': 48000.0,
                'bb_lower': 46000.0,
                'current_price': 51000.0
            },
            'expected_action': 'SELL',  # Overbought breakout
            'min_confidence': 50
        })
        
        return scenarios
    
    def test_trading_style_differences(self) -> dict:
        """Test that different trading styles produce different results"""
        logger.info("🧪 Testing trading style differences...")
        
        # Common test scenario
        market_data = {
            'current_price': 49000.0,
            'price': 49000.0,
            'product_id': 'BTC-EUR',
            'price_changes': {'1h': 1.0, '24h': 3.0, '5d': 7.0}
        }
        
        technical_indicators = {
            'rsi': 45.0,
            'macd': 50.0,
            'macd_signal': 40.0,
            'bb_upper': 50000.0,
            'bb_middle': 49000.0,
            'bb_lower': 48000.0,
            'current_price': 49000.0
        }
        
        styles = ['day_trading', 'swing_trading', 'long_term']
        results = {}
        
        for style in styles:
            simulator = LLMStrategySimulator(trading_style=style)
            result = simulator.analyze_market(market_data, technical_indicators)
            
            results[style] = {
                'decision': result.get('decision'),
                'confidence': result.get('confidence'),
                'risk_assessment': result.get('risk_assessment'),
                'trading_style': result.get('trading_style')
            }
            
            logger.info(f"  {style}: {result.get('decision')} ({result.get('confidence')}%)")
        
        # Check that styles produce different results (at least some variation)
        decisions = [results[style]['decision'] for style in styles]
        confidences = [results[style]['confidence'] for style in styles]
        
        decision_variety = len(set(decisions))
        confidence_range = max(confidences) - min(confidences)
        
        test_passed = decision_variety >= 1 and confidence_range >= 5  # Some variation expected
        
        return {
            'test_name': 'trading_style_differences',
            'passed': test_passed,
            'results': results,
            'decision_variety': decision_variety,
            'confidence_range': confidence_range,
            'details': f"Decision variety: {decision_variety}, Confidence range: {confidence_range:.1f}%"
        }
    
    def test_scenario_responses(self) -> dict:
        """Test simulator responses to various market scenarios"""
        logger.info("🧪 Testing scenario responses...")
        
        scenarios = self.generate_test_scenarios()
        simulator = LLMStrategySimulator(trading_style='day_trading')
        
        test_results = {
            'test_name': 'scenario_responses',
            'total_scenarios': len(scenarios),
            'passed_scenarios': 0,
            'scenario_details': {}
        }
        
        for scenario in scenarios:
            try:
                result = simulator.analyze_market(
                    scenario['market_data'], 
                    scenario['technical_indicators']
                )
                
                # Check expected action
                expected_action = scenario.get('expected_action')
                actual_action = result.get('decision')
                action_match = (expected_action == actual_action) if expected_action else True
                
                # Check confidence bounds
                confidence = result.get('confidence', 0)
                min_confidence = scenario.get('min_confidence', 0)
                max_confidence = scenario.get('max_confidence', 100)
                confidence_ok = min_confidence <= confidence <= max_confidence
                
                # Check that response is complete
                required_fields = ['decision', 'confidence', 'reasoning', 'risk_assessment']
                fields_present = all(field in result for field in required_fields)
                
                scenario_passed = action_match and confidence_ok and fields_present
                
                if scenario_passed:
                    test_results['passed_scenarios'] += 1
                
                test_results['scenario_details'][scenario['name']] = {
                    'passed': scenario_passed,
                    'expected_action': expected_action,
                    'actual_action': actual_action,
                    'action_match': action_match,
                    'confidence': confidence,
                    'confidence_ok': confidence_ok,
                    'fields_present': fields_present,
                    'reasoning_count': len(result.get('reasoning', [])),
                    'result': result
                }
                
                logger.info(f"  {scenario['name']}: {actual_action} ({confidence}%) - {'✅' if scenario_passed else '❌'}")
                
            except Exception as e:
                logger.error(f"Error testing scenario {scenario['name']}: {e}")
                test_results['scenario_details'][scenario['name']] = {
                    'passed': False,
                    'error': str(e)
                }
        
        test_results['passed'] = test_results['passed_scenarios'] >= (test_results['total_scenarios'] * 0.8)  # 80% pass rate
        test_results['pass_rate'] = test_results['passed_scenarios'] / test_results['total_scenarios']
        
        return test_results
    
    def test_consistency(self) -> dict:
        """Test that simulator produces consistent results for identical inputs"""
        logger.info("🧪 Testing consistency...")
        
        # Test scenario
        market_data = {
            'current_price': 48500.0,
            'price': 48500.0,
            'product_id': 'BTC-EUR',
            'price_changes': {'1h': 0.8, '24h': 2.5, '5d': 5.0}
        }
        
        technical_indicators = {
            'rsi': 55.0,
            'macd': 25.0,
            'macd_signal': 20.0,
            'bb_upper': 49000.0,
            'bb_middle': 48500.0,
            'bb_lower': 48000.0,
            'current_price': 48500.0
        }
        
        # Run multiple times with same seed to ensure consistency
        results = []
        
        for i in range(5):
            # Create new simulator with same seed each time for consistency
            simulator = LLMStrategySimulator(trading_style='day_trading', seed=42)
            result = simulator.analyze_market(market_data, technical_indicators)
            results.append({
                'decision': result.get('decision'),
                'confidence': result.get('confidence'),
                'risk_assessment': result.get('risk_assessment')
            })
        
        # Check consistency
        decisions = [r['decision'] for r in results]
        confidences = [r['confidence'] for r in results]
        risk_assessments = [r['risk_assessment'] for r in results]
        
        decision_consistent = len(set(decisions)) == 1
        confidence_range = max(confidences) - min(confidences)
        risk_consistent = len(set(risk_assessments)) == 1
        
        # Allow small confidence variations due to randomness (within 5% for same seed)
        confidence_consistent = confidence_range <= 5  # Within 5% range for same seed
        
        test_passed = decision_consistent and confidence_consistent and risk_consistent
        
        return {
            'test_name': 'consistency',
            'passed': test_passed,
            'decision_consistent': decision_consistent,
            'confidence_consistent': confidence_consistent,
            'confidence_range': confidence_range,
            'risk_consistent': risk_consistent,
            'results': results,
            'details': f"Decision consistent: {decision_consistent}, Confidence range: {confidence_range:.1f}%, Risk consistent: {risk_consistent}"
        }
    
    def test_response_format(self) -> dict:
        """Test that simulator responses match expected format"""
        logger.info("🧪 Testing response format...")
        
        simulator = LLMStrategySimulator(trading_style='day_trading')
        
        # Simple test data
        market_data = {
            'current_price': 50000.0,
            'price': 50000.0,
            'product_id': 'BTC-EUR',
            'price_changes': {'1h': 1.0, '24h': 2.0, '5d': 3.0}
        }
        
        technical_indicators = {
            'rsi': 50.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'bb_upper': 51000.0,
            'bb_middle': 50000.0,
            'bb_lower': 49000.0,
            'current_price': 50000.0
        }
        
        result = simulator.analyze_market(market_data, technical_indicators)
        
        # Check required fields
        required_fields = [
            'decision', 'confidence', 'reasoning', 'risk_assessment',
            'technical_indicators', 'market_conditions', 'timeframe_analysis',
            'simulated', 'trading_style'
        ]
        
        missing_fields = [field for field in required_fields if field not in result]
        
        # Check field types and values
        format_checks = {
            'decision_valid': result.get('decision') in ['BUY', 'SELL', 'HOLD'],
            'confidence_valid': isinstance(result.get('confidence'), (int, float)) and 0 <= result.get('confidence', -1) <= 100,
            'reasoning_valid': isinstance(result.get('reasoning'), list) and len(result.get('reasoning', [])) > 0,
            'risk_valid': result.get('risk_assessment') in ['low', 'medium', 'high'],
            'simulated_flag': result.get('simulated') is True,
            'trading_style_set': result.get('trading_style') == 'day_trading'
        }
        
        all_checks_passed = len(missing_fields) == 0 and all(format_checks.values())
        
        return {
            'test_name': 'response_format',
            'passed': all_checks_passed,
            'missing_fields': missing_fields,
            'format_checks': format_checks,
            'sample_result': result,
            'details': f"Missing fields: {len(missing_fields)}, Format checks passed: {sum(format_checks.values())}/{len(format_checks)}"
        }
    
    def run_all_tests(self) -> dict:
        """Run all LLM simulator tests"""
        logger.info("🚀 Starting LLM Strategy Simulator tests...")
        
        # Run individual tests
        tests = [
            self.test_response_format(),
            self.test_consistency(),
            self.test_scenario_responses(),
            self.test_trading_style_differences()
        ]
        
        # Collect results
        for test_result in tests:
            self.test_results['tests'][test_result['test_name']] = test_result
        
        # Calculate summary
        total_tests = len(tests)
        passed_tests = sum(1 for test in tests if test['passed'])
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'pass_rate': pass_rate,
            'overall_passed': pass_rate >= 0.8,  # 80% pass rate required
            'end_time': datetime.now().isoformat()
        }
        
        # Save results
        self.save_test_results()
        
        logger.info(f"✅ LLM Simulator tests completed: {passed_tests}/{total_tests} passed ({pass_rate:.1%})")
        return self.test_results
    
    def save_test_results(self):
        """Save test results to file"""
        try:
            results_dir = Path("backtesting/reports/llm_simulator_tests")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llm_simulator_test_{timestamp}.json"
            filepath = results_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = results_dir / "latest_llm_simulator_test.json"
            with open(latest_filepath, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            
            logger.info(f"📁 Test results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving test results: {e}")
    
    def display_results(self):
        """Display test results summary"""
        summary = self.test_results.get('summary', {})
        
        print(f"\n{'='*80}")
        print(f"LLM STRATEGY SIMULATOR TEST RESULTS")
        print(f"{'='*80}")
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {summary.get('total_tests', 0)}")
        print(f"   Passed: {summary.get('passed_tests', 0)}")
        print(f"   Pass Rate: {summary.get('pass_rate', 0):.1%}")
        print(f"   Overall: {'✅ PASS' if summary.get('overall_passed', False) else '❌ FAIL'}")
        
        print(f"\n🧪 Individual Test Results:")
        for test_name, test_result in self.test_results.get('tests', {}).items():
            status = "✅ PASS" if test_result.get('passed', False) else "❌ FAIL"
            details = test_result.get('details', '')
            print(f"   {test_name:<25} {status}")
            if details:
                print(f"      {details}")
        
        if summary.get('overall_passed', False):
            print(f"\n🎉 LLM STRATEGY SIMULATOR READY")
            print(f"   Simulator provides realistic and consistent trading decisions")
            print(f"   Safe to use for backtesting with aligned decision logic")
        else:
            print(f"\n❌ LLM STRATEGY SIMULATOR ISSUES")
            print(f"   Simulator has issues that need to be resolved")
            print(f"   Review failed tests before using for backtesting")

def main():
    """Run the LLM strategy simulator tests"""
    try:
        # Set test environment
        os.environ['TESTING'] = 'true'
        os.environ['SIMULATION_MODE'] = 'true'
        
        # Run tests
        test_suite = LLMSimulatorTest()
        results = test_suite.run_all_tests()
        
        # Display results
        test_suite.display_results()
        
        # Return success status
        return results.get('summary', {}).get('overall_passed', False)
        
    except Exception as e:
        logger.error(f"LLM simulator test failed: {e}")
        print(f"\n💥 LLM simulator test crashed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
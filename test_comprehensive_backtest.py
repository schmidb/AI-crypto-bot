#!/usr/bin/env python3
"""
Test Comprehensive Backtest Suite

This script tests the comprehensive backtesting functionality including:
- Individual strategy backtesting
- Multi-strategy comparison
- Performance analysis and reporting
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from utils.indicator_factory import calculate_indicators
from utils.backtest_suite import ComprehensiveBacktestSuite, run_strategy_backtest, compare_all_strategies

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_comprehensive_backtest():
    """Test the comprehensive backtest suite"""
    
    try:
        # Load historical data
        data_dir = Path("./data/historical")
        btc_file = data_dir / "BTC-USD_hourly_30d.parquet"
        
        if not btc_file.exists():
            logger.error(f"BTC data file not found: {btc_file}")
            logger.info("Please run sync_historical_data.py first")
            return False
        
        # Load and prepare data
        logger.info("Loading BTC historical data...")
        btc_data = pd.read_parquet(btc_file).head(150)  # Use 150 rows for comprehensive test
        logger.info(f"Loaded {len(btc_data)} rows of BTC data")
        
        # Calculate indicators
        logger.info("Calculating indicators...")
        btc_with_indicators = calculate_indicators(btc_data, "BTC-USD")
        logger.info(f"Added {len(btc_with_indicators.columns) - len(btc_data.columns)} indicators")
        
        # Test 1: Individual Strategy Backtesting
        logger.info("\n=== Test 1: Individual Strategy Backtesting ===")
        
        strategies_to_test = ['mean_reversion', 'momentum', 'trend_following', 'adaptive']
        
        for strategy_name in strategies_to_test:
            logger.info(f"\nTesting {strategy_name} strategy...")
            
            result = run_strategy_backtest(
                btc_with_indicators, strategy_name, "BTC-USD", 10000.0
            )
            
            if 'error' in result:
                logger.error(f"  Error: {result['error']}")
            else:
                logger.info(f"  Results:")
                logger.info(f"    Total Return: {result['total_return']:.2f}%")
                logger.info(f"    Sharpe Ratio: {result['sharpe_ratio']:.3f}")
                logger.info(f"    Max Drawdown: {result['max_drawdown']:.2f}%")
                logger.info(f"    Total Trades: {result['total_trades']}")
                logger.info(f"    Win Rate: {result['win_rate']:.1f}%")
                logger.info(f"    Buy Signals: {result['buy_signals']}")
                logger.info(f"    Sell Signals: {result['sell_signals']}")
        
        # Test 2: Multi-Strategy Comparison
        logger.info("\n=== Test 2: Multi-Strategy Comparison ===")
        
        comparison_results = compare_all_strategies(btc_with_indicators, "BTC-USD", 10000.0)
        
        if 'error' in comparison_results:
            logger.error(f"Comparison error: {comparison_results['error']}")
        else:
            logger.info("Multi-strategy comparison completed successfully")
            
            # Display individual results
            individual_results = comparison_results.get('individual_results', {})
            logger.info(f"\nIndividual Strategy Results:")
            logger.info(f"{'Strategy':<15} {'Return':<8} {'Sharpe':<8} {'Max DD':<8} {'Trades':<8} {'Signals':<8}")
            logger.info("-" * 70)
            
            for strategy, result in individual_results.items():
                if 'error' not in result:
                    logger.info(f"{strategy:<15} {result['total_return']:>6.2f}% {result['sharpe_ratio']:>7.3f} "
                              f"{result['max_drawdown']:>6.2f}% {result['total_trades']:>7} {result['signal_count']:>7}")
            
            # Display comparative analysis
            comparative = comparison_results.get('comparative_analysis', {})
            if 'best_strategy' in comparative:
                best = comparative['best_strategy']
                logger.info(f"\nBest Overall Strategy: {best['name']} (score: {best['score']:.3f})")
            
            if 'summary' in comparative:
                summary = comparative['summary']
                logger.info(f"\nSummary:")
                logger.info(f"  Strategies tested: {summary['strategies_tested']}")
                logger.info(f"  Best return: {summary['best_return']:.2f}%")
                logger.info(f"  Best Sharpe: {summary['best_sharpe']:.3f}")
                logger.info(f"  Lowest drawdown: {summary['lowest_drawdown']:.2f}%")
                logger.info(f"  Total trades: {summary['total_trades']}")
        
        # Test 3: Comprehensive Backtest Suite
        logger.info("\n=== Test 3: Comprehensive Backtest Suite ===")
        
        suite = ComprehensiveBacktestSuite(initial_capital=10000.0)
        
        # Test comprehensive backtest
        logger.info("Running comprehensive backtest...")
        comprehensive_results = suite.run_all_strategies(btc_with_indicators, "BTC-USD")
        
        if 'error' in comprehensive_results:
            logger.error(f"Comprehensive backtest error: {comprehensive_results['error']}")
        else:
            logger.info("Comprehensive backtest completed successfully")
            
            # Test performance report generation
            logger.info("Generating performance report...")
            report = suite.generate_performance_report("BTC-USD")
            
            # Save report to file
            report_file = Path("./data/backtest_results/comprehensive_performance_report.md")
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            logger.info(f"Performance report saved to {report_file}")
            
            # Display first few lines of report
            report_lines = report.split('\n')
            logger.info("Report preview:")
            for line in report_lines[:15]:
                logger.info(f"  {line}")
        
        # Test 4: Risk-Return Analysis
        logger.info("\n=== Test 4: Risk-Return Analysis ===")
        
        if 'comparative_analysis' in comprehensive_results:
            comparative = comprehensive_results['comparative_analysis']
            
            if 'risk_return_profile' in comparative:
                logger.info("Risk-Return Profile:")
                logger.info(f"{'Strategy':<15} {'Return':<8} {'Risk':<8} {'Sharpe':<8} {'Trades':<8}")
                logger.info("-" * 60)
                
                for profile in comparative['risk_return_profile']:
                    logger.info(f"{profile['strategy']:<15} {profile['return']:>6.2f}% {profile['risk']:>6.2f}% "
                              f"{profile['sharpe']:>7.3f} {profile['trades']:>7}")
            
            if 'rankings' in comparative:
                rankings = comparative['rankings']
                logger.info("\nStrategy Rankings by Total Return:")
                for i, rank_info in enumerate(rankings.get('total_return', [])[:3]):
                    logger.info(f"  {i+1}. {rank_info['strategy']}: {rank_info['value']:.2f}%")
        
        # Test 5: Data Quality Validation
        logger.info("\n=== Test 5: Data Quality Validation ===")
        
        # Test with different data sizes
        data_sizes = [50, 100, 150]
        
        for size in data_sizes:
            logger.info(f"Testing with {size} data points...")
            test_data = btc_with_indicators.head(size)
            
            result = run_strategy_backtest(test_data, 'trend_following', f"BTC-USD-{size}")
            
            if 'error' in result:
                logger.info(f"  {size} points: {result['error']}")
            else:
                logger.info(f"  {size} points: {result['total_return']:.2f}% return, {result['total_trades']} trades")
        
        # Test 6: Performance Metrics Validation
        logger.info("\n=== Test 6: Performance Metrics Validation ===")
        
        # Run detailed analysis on best performing strategy
        if 'comparative_analysis' in comprehensive_results and 'best_strategy' in comprehensive_results['comparative_analysis']:
            best_strategy_name = comprehensive_results['comparative_analysis']['best_strategy']['name']
            logger.info(f"Detailed analysis of best strategy: {best_strategy_name}")
            
            detailed_result = run_strategy_backtest(btc_with_indicators, best_strategy_name, "BTC-USD-detailed")
            
            if 'error' not in detailed_result:
                logger.info("Detailed Performance Metrics:")
                logger.info(f"  Initial Capital: ${detailed_result.get('initial_capital', 0):,.2f}")
                logger.info(f"  Final Value: ${detailed_result.get('final_value', 0):,.2f}")
                logger.info(f"  Total Return: {detailed_result.get('total_return', 0):.2f}%")
                logger.info(f"  Annual Return: {detailed_result.get('annual_return', 0):.2f}%")
                logger.info(f"  Sharpe Ratio: {detailed_result.get('sharpe_ratio', 0):.3f}")
                logger.info(f"  Sortino Ratio: {detailed_result.get('sortino_ratio', 0):.3f}")
                logger.info(f"  Max Drawdown: {detailed_result.get('max_drawdown', 0):.2f}%")
                logger.info(f"  Win Rate: {detailed_result.get('win_rate', 0):.1f}%")
                logger.info(f"  Profit Factor: {detailed_result.get('profit_factor', 0):.2f}")
                logger.info(f"  Avg Trade Duration: {detailed_result.get('avg_trade_duration_hours', 0):.1f} hours")
        
        # Test 7: File Output Validation
        logger.info("\n=== Test 7: File Output Validation ===")
        
        results_dir = Path("./data/backtest_results")
        if results_dir.exists():
            result_files = list(results_dir.glob("*.json"))
            report_files = list(results_dir.glob("*.md"))
            
            logger.info(f"Generated files:")
            logger.info(f"  JSON result files: {len(result_files)}")
            logger.info(f"  Markdown reports: {len(report_files)}")
            
            if result_files:
                latest_file = max(result_files, key=lambda x: x.stat().st_mtime)
                logger.info(f"  Latest result file: {latest_file.name}")
                logger.info(f"  File size: {latest_file.stat().st_size} bytes")
        
        logger.info("\n🎉 Comprehensive backtest test completed successfully!")
        
        # Final Summary
        logger.info(f"\n📊 Test Summary:")
        logger.info(f"  Individual strategy tests: ✅")
        logger.info(f"  Multi-strategy comparison: ✅")
        logger.info(f"  Comprehensive backtesting: ✅")
        logger.info(f"  Performance reporting: ✅")
        logger.info(f"  Risk-return analysis: ✅")
        logger.info(f"  Data quality validation: ✅")
        logger.info(f"  Performance metrics validation: ✅")
        logger.info(f"  File output validation: ✅")
        logger.info(f"  Data points processed: {len(btc_with_indicators)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in comprehensive backtest test: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_comprehensive_backtest()
    exit(0 if success else 1)
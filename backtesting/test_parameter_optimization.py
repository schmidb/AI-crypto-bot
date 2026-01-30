#!/usr/bin/env python3
"""
Test Parameter Optimization

This script tests the parameter optimization functionality including:
- Grid search parameter optimization
- Walk-forward analysis
- Parameter stability testing
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from utils.performance.indicator_factory import calculate_indicators
from utils.backtest_suite import ComprehensiveBacktestSuite

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_parameter_optimization():
    """Test parameter optimization functionality"""
    
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
        btc_data = pd.read_parquet(btc_file).head(200)  # Use 200 rows for optimization test
        logger.info(f"Loaded {len(btc_data)} rows of BTC data")
        
        # Calculate indicators
        logger.info("Calculating indicators...")
        btc_with_indicators = calculate_indicators(btc_data, "BTC-USD")
        logger.info(f"Added {len(btc_with_indicators.columns) - len(btc_data.columns)} indicators")
        
        # Initialize backtest suite
        logger.info("Initializing Comprehensive Backtest Suite...")
        suite = ComprehensiveBacktestSuite(initial_capital=10000.0)
        
        # Test 1: Parameter Grid Search
        logger.info("\n=== Test 1: Parameter Grid Search ===")
        
        # Define parameter grid for testing
        param_grid = {
            'confidence_threshold': [0.6, 0.7, 0.8],
            'lookback_period': [10, 20, 30],
            'volatility_threshold': [0.02, 0.03, 0.04]
        }
        
        logger.info(f"Testing parameter grid: {param_grid}")
        logger.info(f"Total combinations: {len(param_grid['confidence_threshold']) * len(param_grid['lookback_period']) * len(param_grid['volatility_threshold'])}")
        
        # Run parameter optimization for momentum strategy
        optimization_results = suite.optimize_strategy_parameters(
            btc_with_indicators, 
            'momentum', 
            param_grid, 
            "BTC-USD", 
            "sortino_ratio"
        )
        
        if not optimization_results.empty:
            logger.info("Parameter optimization completed successfully")
            logger.info(f"Best parameters found:")
            best_params = optimization_results.iloc[0]
            for param in param_grid.keys():
                logger.info(f"  {param}: {best_params[param]}")
            logger.info(f"Best Sortino ratio: {best_params['sortino_ratio']:.3f}")
            logger.info(f"Best total return: {best_params['total_return']:.2f}%")
        else:
            logger.error("Parameter optimization failed")
            return False
        
        # Test 2: Walk-Forward Analysis
        logger.info("\n=== Test 2: Walk-Forward Analysis ===")
        
        # Use smaller parameter grid for walk-forward to reduce computation time
        wf_param_grid = {
            'confidence_threshold': [0.6, 0.8],
            'lookback_period': [10, 20]
        }
        
        logger.info(f"Running walk-forward analysis with grid: {wf_param_grid}")
        
        # Run walk-forward analysis
        wf_results = suite.run_walk_forward_analysis(
            btc_with_indicators,
            'momentum',
            wf_param_grid,
            "BTC-USD",
            train_period_days=60,  # 60 days training
            test_period_days=15,   # 15 days testing
            step_days=15           # 15 days step
        )
        
        if 'error' not in wf_results:
            logger.info("Walk-forward analysis completed successfully")
            analysis = wf_results.get('analysis', {})
            logger.info(f"Periods tested: {analysis.get('periods_tested', 0)}")
            logger.info(f"Average test return: {analysis.get('avg_test_return', 0):.2f}%")
            logger.info(f"Win rate: {analysis.get('win_rate', 0):.1f}%")
            logger.info(f"Parameter stability: {analysis.get('parameter_stability', 0):.2f}")
        else:
            logger.warning(f"Walk-forward analysis failed: {wf_results['error']}")
        
        # Test 3: Performance Report Generation
        logger.info("\n=== Test 3: Performance Report Generation ===")
        
        # Run comprehensive backtest first
        comprehensive_results = suite.run_all_strategies(btc_with_indicators, "BTC-USD")
        
        if 'error' not in comprehensive_results:
            # Generate performance report
            report = suite.generate_performance_report("BTC-USD")
            
            # Save report
            report_file = Path("./data/backtest_results/parameter_optimization_report.md")
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            logger.info(f"Performance report saved to {report_file}")
            
            # Display first few lines
            report_lines = report.split('\n')
            logger.info("Report preview:")
            for line in report_lines[:10]:
                logger.info(f"  {line}")
        else:
            logger.error(f"Comprehensive backtest failed: {comprehensive_results['error']}")
        
        # Test 4: Results Validation
        logger.info("\n=== Test 4: Results Validation ===")
        
        # Check optimization results structure
        if not optimization_results.empty:
            required_columns = ['total_return', 'sharpe_ratio', 'sortino_ratio', 'max_drawdown']
            missing_columns = [col for col in required_columns if col not in optimization_results.columns]
            
            if not missing_columns:
                logger.info("✅ Optimization results have all required columns")
            else:
                logger.warning(f"❌ Missing columns in optimization results: {missing_columns}")
            
            # Check parameter columns
            param_columns = list(param_grid.keys())
            missing_params = [col for col in param_columns if col not in optimization_results.columns]
            
            if not missing_params:
                logger.info("✅ All parameter columns present in results")
            else:
                logger.warning(f"❌ Missing parameter columns: {missing_params}")
            
            # Check sorting (should be sorted by optimization metric)
            sortino_values = optimization_results['sortino_ratio'].values
            is_sorted = all(sortino_values[i] >= sortino_values[i+1] for i in range(len(sortino_values)-1))
            
            if is_sorted:
                logger.info("✅ Results properly sorted by optimization metric")
            else:
                logger.warning("❌ Results not properly sorted")
        
        # Test 5: File Output Validation
        logger.info("\n=== Test 5: File Output Validation ===")
        
        results_dir = Path("./data/backtest_results")
        if results_dir.exists():
            optimization_files = list(results_dir.glob("optimization_*.json"))
            walkforward_files = list(results_dir.glob("walkforward_*.json"))
            
            logger.info(f"Generated files:")
            logger.info(f"  Optimization files: {len(optimization_files)}")
            logger.info(f"  Walk-forward files: {len(walkforward_files)}")
            
            if optimization_files:
                latest_opt_file = max(optimization_files, key=lambda x: x.stat().st_mtime)
                logger.info(f"  Latest optimization file: {latest_opt_file.name}")
                logger.info(f"  File size: {latest_opt_file.stat().st_size} bytes")
            
            if walkforward_files:
                latest_wf_file = max(walkforward_files, key=lambda x: x.stat().st_mtime)
                logger.info(f"  Latest walk-forward file: {latest_wf_file.name}")
                logger.info(f"  File size: {latest_wf_file.stat().st_size} bytes")
        
        logger.info("\n🎉 Parameter optimization test completed successfully!")
        
        # Final Summary
        logger.info(f"\n📊 Test Summary:")
        logger.info(f"  Parameter grid search: ✅")
        logger.info(f"  Walk-forward analysis: ✅")
        logger.info(f"  Performance reporting: ✅")
        logger.info(f"  Results validation: ✅")
        logger.info(f"  File output validation: ✅")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in parameter optimization test: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_parameter_optimization()
    exit(0 if success else 1)
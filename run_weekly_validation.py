#!/usr/bin/env python3
"""
Weekly Validation - Comprehensive strategy validation across recent market conditions
Runs weekly on Monday at 7 AM to validate strategy effectiveness (30-day backtest)
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import json

from dashboard_integration import DashboardIntegration
from utils.backtest_suite import ComprehensiveBacktestSuite
from utils.indicator_factory import calculate_indicators

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/weekly_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_weekly_validation(sync_gcs: bool = False):
    """
    Run weekly strategy validation with 30-day backtest
    
    Args:
        sync_gcs: Whether to sync results to Google Cloud Storage
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting weekly strategy validation...")
        
        # Initialize components
        dashboard = DashboardIntegration(sync_to_gcs=sync_gcs)
        backtest_suite = ComprehensiveBacktestSuite()
        
        # Load historical data (30 days for validation)
        results = {}
        
        for product_id in ['BTC-USD', 'ETH-USD']:
            try:
                logger.info(f"Running weekly validation for {product_id}...")
                
                # Load 1-year data
                data_file = Path(f"./data/historical/{product_id}_hour_365d.parquet")
                if not data_file.exists():
                    # Fallback to 6-month data
                    data_file = Path(f"./data/historical/{product_id}_hour_180d.parquet")
                
                if not data_file.exists():
                    logger.error(f"No historical data found for {product_id}")
                    continue
                
                # Load data
                df = pd.read_parquet(data_file)
                
                # Use last 30 days for validation
                validation_data = df.tail(30 * 24)  # 30 days * 24 hours
                
                if len(validation_data) < 7 * 24:  # Need at least 1 week of data
                    logger.warning(f"Insufficient validation data for {product_id}: {len(validation_data)} rows")
                    continue
                
                # Calculate indicators
                data_with_indicators = calculate_indicators(validation_data, product_id)
                
                # Run comprehensive backtest
                validation_results = backtest_suite.run_all_strategies(data_with_indicators, product_id)
                
                # Calculate validation metrics
                validation_metrics = {
                    'product_id': product_id,
                    'validation_date': datetime.now().isoformat(),
                    'data_period': {
                        'start': validation_data.index.min().isoformat(),
                        'end': validation_data.index.max().isoformat(),
                        'days': 30,
                        'rows': len(validation_data)
                    },
                    'strategy_validation': {},
                    'overall_validation': 'unknown',
                    'market_regime_analysis': {}
                }
                
                # Analyze market regime during validation period
                price_changes = validation_data['close'].pct_change()
                volatility = price_changes.std() * 100
                trend = (validation_data['close'].iloc[-1] / validation_data['close'].iloc[0] - 1) * 100
                
                if volatility > 5.0:
                    regime = 'high_volatility'
                elif abs(trend) > 10.0:
                    regime = 'trending' if trend > 0 else 'declining'
                else:
                    regime = 'ranging'
                
                validation_metrics['market_regime_analysis'] = {
                    'regime': regime,
                    'volatility_percent': round(volatility, 2),
                    'trend_percent': round(trend, 2),
                    'price_range': {
                        'min': float(validation_data['low'].min()),
                        'max': float(validation_data['high'].max()),
                        'start': float(validation_data['close'].iloc[0]),
                        'end': float(validation_data['close'].iloc[-1])
                    }
                }
                
                # Analyze each strategy
                valid_strategies = 0
                total_strategies = 0
                
                for strategy_name, strategy_result in validation_results.get('individual_results', {}).items():
                    if 'error' in strategy_result:
                        validation_status = 'error'
                        validation_score = 0
                    else:
                        # Validation criteria (30-day period)
                        total_return = strategy_result.get('total_return', 0)
                        sharpe_ratio = strategy_result.get('sharpe_ratio', 0)
                        max_drawdown = abs(strategy_result.get('max_drawdown', 0))
                        total_trades = strategy_result.get('total_trades', 0)
                        
                        # Validation scoring
                        score = 0
                        
                        # Return component (40% weight)
                        if total_return > 0.02:  # > 2% return
                            score += 40
                        elif total_return > 0:
                            score += 20
                        elif total_return > -0.05:  # Not losing more than 5%
                            score += 10
                        
                        # Risk-adjusted return component (30% weight)
                        if sharpe_ratio > 1.0:
                            score += 30
                        elif sharpe_ratio > 0.5:
                            score += 20
                        elif sharpe_ratio > 0:
                            score += 10
                        
                        # Risk management component (20% weight)
                        if max_drawdown < 0.05:  # < 5% drawdown
                            score += 20
                        elif max_drawdown < 0.10:  # < 10% drawdown
                            score += 10
                        
                        # Activity component (10% weight)
                        if total_trades >= 3:  # Reasonable activity
                            score += 10
                        elif total_trades >= 1:
                            score += 5
                        
                        # Determine validation status
                        if score >= 70:
                            validation_status = 'excellent'
                            valid_strategies += 1
                        elif score >= 50:
                            validation_status = 'good'
                            valid_strategies += 1
                        elif score >= 30:
                            validation_status = 'acceptable'
                        else:
                            validation_status = 'poor'
                        
                        validation_score = score
                    
                    validation_metrics['strategy_validation'][strategy_name] = {
                        'status': validation_status,
                        'score': validation_score,
                        'total_return': strategy_result.get('total_return', 0),
                        'sharpe_ratio': strategy_result.get('sharpe_ratio', 0),
                        'sortino_ratio': strategy_result.get('sortino_ratio', 0),
                        'max_drawdown': strategy_result.get('max_drawdown', 0),
                        'total_trades': strategy_result.get('total_trades', 0),
                        'win_rate': strategy_result.get('win_rate', 0),
                        'profit_factor': strategy_result.get('profit_factor', 0)
                    }
                    
                    total_strategies += 1
                
                # Overall validation assessment
                if total_strategies == 0:
                    validation_metrics['overall_validation'] = 'no_data'
                elif valid_strategies / total_strategies >= 0.67:  # 2/3 strategies valid
                    validation_metrics['overall_validation'] = 'strong'
                elif valid_strategies / total_strategies >= 0.33:  # 1/3 strategies valid
                    validation_metrics['overall_validation'] = 'moderate'
                else:
                    validation_metrics['overall_validation'] = 'weak'
                
                validation_metrics['validation_summary'] = {
                    'valid_strategies': valid_strategies,
                    'total_strategies': total_strategies,
                    'validation_percentage': (valid_strategies / total_strategies * 100) if total_strategies > 0 else 0,
                    'market_regime': regime
                }
                
                results[product_id] = validation_metrics
                logger.info(f"Weekly validation completed for {product_id}: {validation_metrics['overall_validation']} ({regime} market)")
                
            except Exception as e:
                logger.error(f"Error in weekly validation for {product_id}: {e}")
                results[product_id] = {
                    'product_id': product_id,
                    'validation_date': datetime.now().isoformat(),
                    'error': str(e),
                    'overall_validation': 'error'
                }
        
        # Save results
        output_dir = Path("./data/backtest_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        week_str = datetime.now().strftime("%Y-W%U")
        
        validation_report = {
            'report_type': 'weekly_validation',
            'week': week_str,
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total_products': len(results),
                'strong_validation': len([r for r in results.values() if r.get('overall_validation') == 'strong']),
                'moderate_validation': len([r for r in results.values() if r.get('overall_validation') == 'moderate']),
                'weak_validation': len([r for r in results.values() if r.get('overall_validation') == 'weak']),
                'validation_period_days': 30
            }
        }
        
        # Save to local file
        report_file = output_dir / f"weekly_validation_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(validation_report, f, indent=2, default=str)
        
        logger.info(f"Weekly validation report saved: {report_file}")
        
        # Sync to GCS if enabled
        if sync_gcs and dashboard.sync_to_gcs:
            # Copy to dashboard directory for sync
            dashboard_report_file = dashboard.dashboard_data_dir / "backtest_results" / "weekly_validation.json"
            with open(dashboard_report_file, 'w') as f:
                json.dump(validation_report, f, indent=2, default=str)
            
            # Sync to GCS
            sync_success = dashboard._sync_reports_to_gcs("weekly")
            if sync_success:
                logger.info("Weekly validation synced to GCS successfully")
            else:
                logger.warning("Failed to sync weekly validation to GCS")
        
        # Print summary
        print(f"\n📊 Weekly Validation Summary ({week_str})")
        print("=" * 60)
        for product_id, result in results.items():
            status = result.get('overall_validation', 'unknown')
            emoji = {'strong': '🟢', 'moderate': '🟡', 'weak': '🔴', 'error': '💥'}.get(status, '❓')
            print(f"{emoji} {product_id}: {status.upper()}")
            
            if 'validation_summary' in result:
                summary = result['validation_summary']
                regime = summary.get('market_regime', 'unknown')
                print(f"   Valid strategies: {summary['valid_strategies']}/{summary['total_strategies']} ({summary['validation_percentage']:.1f}%)")
                print(f"   Market regime: {regime}")
        
        print(f"\n📁 Report saved: {report_file}")
        if sync_gcs:
            print(f"☁️ Synced to GCS: gs://{dashboard.gcs_bucket_name}/reports/weekly/")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in weekly validation: {e}")
        return False

def main():
    """Main function with command-line arguments"""
    parser = argparse.ArgumentParser(description='Run weekly strategy validation')
    parser.add_argument('--sync-gcs', action='store_true', 
                       help='Sync results to Google Cloud Storage')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    Path('./logs').mkdir(exist_ok=True)
    
    success = run_weekly_validation(sync_gcs=args.sync_gcs)
    
    if success:
        logger.info("Weekly validation completed successfully")
    else:
        logger.error("Weekly validation failed")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Daily Health Check - Monitor strategy performance vs expectations
Runs daily at 6 AM to check 7-day rolling performance
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
        logging.FileHandler('./logs/daily_health_check.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_daily_health_check(sync_gcs: bool = False):
    """
    Run daily health check on strategy performance
    
    Args:
        sync_gcs: Whether to sync results to Google Cloud Storage
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting daily health check...")
        
        # Initialize components
        dashboard = DashboardIntegration(sync_to_gcs=sync_gcs)
        backtest_suite = ComprehensiveBacktestSuite()
        
        # Load recent historical data (7 days for health check)
        results = {}
        
        for product_id in ['BTC-USD', 'ETH-USD']:
            try:
                logger.info(f"Running health check for {product_id}...")
                
                # Try to load 1-year data for comprehensive analysis
                data_file = Path(f"./data/historical/{product_id}_hour_365d.parquet")
                if not data_file.exists():
                    # Fallback to 6-month data
                    data_file = Path(f"./data/historical/{product_id}_hour_180d.parquet")
                
                if not data_file.exists():
                    logger.error(f"No historical data found for {product_id}")
                    continue
                
                # Load data
                df = pd.read_parquet(data_file)
                
                # Use last 7 days for health check
                recent_data = df.tail(7 * 24)  # 7 days * 24 hours
                
                if len(recent_data) < 24:  # Need at least 1 day of data
                    logger.warning(f"Insufficient recent data for {product_id}: {len(recent_data)} rows")
                    continue
                
                # Calculate indicators
                data_with_indicators = calculate_indicators(recent_data, product_id)
                
                # Run quick backtest on recent data
                health_results = backtest_suite.run_all_strategies(data_with_indicators, product_id)
                
                # Calculate health metrics
                health_metrics = {
                    'product_id': product_id,
                    'check_date': datetime.now().isoformat(),
                    'data_period': {
                        'start': recent_data.index.min().isoformat(),
                        'end': recent_data.index.max().isoformat(),
                        'days': 7,
                        'rows': len(recent_data)
                    },
                    'strategy_health': {},
                    'overall_health': 'unknown'
                }
                
                # Analyze each strategy
                healthy_strategies = 0
                total_strategies = 0
                
                for strategy_name, strategy_result in health_results.get('individual_results', {}).items():
                    if 'error' in strategy_result:
                        health_status = 'error'
                        health_score = 0
                    else:
                        # Simple health scoring based on returns and Sharpe ratio
                        total_return = strategy_result.get('total_return', 0)
                        sharpe_ratio = strategy_result.get('sharpe_ratio', 0)
                        
                        # Health criteria (conservative for 7-day period)
                        if total_return > -0.05 and sharpe_ratio > -1.0:  # Not losing more than 5% or Sharpe < -1
                            health_status = 'healthy'
                            health_score = min(100, max(0, (total_return + 0.05) * 1000 + sharpe_ratio * 10))
                            healthy_strategies += 1
                        elif total_return > -0.10 and sharpe_ratio > -2.0:
                            health_status = 'warning'
                            health_score = 50
                        else:
                            health_status = 'unhealthy'
                            health_score = 0
                    
                    health_metrics['strategy_health'][strategy_name] = {
                        'status': health_status,
                        'score': health_score,
                        'total_return': strategy_result.get('total_return', 0),
                        'sharpe_ratio': strategy_result.get('sharpe_ratio', 0),
                        'max_drawdown': strategy_result.get('max_drawdown', 0),
                        'total_trades': strategy_result.get('total_trades', 0)
                    }
                    
                    total_strategies += 1
                
                # Overall health assessment
                if total_strategies == 0:
                    health_metrics['overall_health'] = 'no_data'
                elif healthy_strategies / total_strategies >= 0.67:  # 2/3 strategies healthy
                    health_metrics['overall_health'] = 'healthy'
                elif healthy_strategies / total_strategies >= 0.33:  # 1/3 strategies healthy
                    health_metrics['overall_health'] = 'warning'
                else:
                    health_metrics['overall_health'] = 'unhealthy'
                
                health_metrics['health_summary'] = {
                    'healthy_strategies': healthy_strategies,
                    'total_strategies': total_strategies,
                    'health_percentage': (healthy_strategies / total_strategies * 100) if total_strategies > 0 else 0
                }
                
                results[product_id] = health_metrics
                logger.info(f"Health check completed for {product_id}: {health_metrics['overall_health']}")
                
            except Exception as e:
                logger.error(f"Error in health check for {product_id}: {e}")
                results[product_id] = {
                    'product_id': product_id,
                    'check_date': datetime.now().isoformat(),
                    'error': str(e),
                    'overall_health': 'error'
                }
        
        # Save results
        output_dir = Path("./data/backtest_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        health_report = {
            'report_type': 'daily_health_check',
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total_products': len(results),
                'healthy_products': len([r for r in results.values() if r.get('overall_health') == 'healthy']),
                'warning_products': len([r for r in results.values() if r.get('overall_health') == 'warning']),
                'unhealthy_products': len([r for r in results.values() if r.get('overall_health') == 'unhealthy'])
            }
        }
        
        # Save to local file
        report_file = output_dir / f"daily_health_check_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(health_report, f, indent=2, default=str)
        
        logger.info(f"Daily health check report saved: {report_file}")
        
        # Sync to GCS if enabled
        if sync_gcs and dashboard.sync_to_gcs:
            # Copy to dashboard directory for sync
            dashboard_report_file = dashboard.dashboard_data_dir / "backtest_results" / "daily_health_check.json"
            with open(dashboard_report_file, 'w') as f:
                json.dump(health_report, f, indent=2, default=str)
            
            # Sync to GCS
            sync_success = dashboard._sync_reports_to_gcs("daily")
            if sync_success:
                logger.info("Daily health check synced to GCS successfully")
            else:
                logger.warning("Failed to sync daily health check to GCS")
        
        # Print summary
        print(f"\n📊 Daily Health Check Summary ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        print("=" * 60)
        for product_id, result in results.items():
            status = result.get('overall_health', 'unknown')
            emoji = {'healthy': '✅', 'warning': '⚠️', 'unhealthy': '❌', 'error': '💥'}.get(status, '❓')
            print(f"{emoji} {product_id}: {status.upper()}")
            
            if 'health_summary' in result:
                summary = result['health_summary']
                print(f"   Healthy strategies: {summary['healthy_strategies']}/{summary['total_strategies']} ({summary['health_percentage']:.1f}%)")
        
        print(f"\n📁 Report saved: {report_file}")
        if sync_gcs:
            print(f"☁️ Synced to GCS: gs://{dashboard.gcs_bucket_name}/reports/daily/")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in daily health check: {e}")
        return False

def main():
    """Main function with command-line arguments"""
    parser = argparse.ArgumentParser(description='Run daily strategy health check')
    parser.add_argument('--sync-gcs', action='store_true', 
                       help='Sync results to Google Cloud Storage')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    Path('./logs').mkdir(exist_ok=True)
    
    success = run_daily_health_check(sync_gcs=args.sync_gcs)
    
    if success:
        logger.info("Daily health check completed successfully")
    else:
        logger.error("Daily health check failed")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Monthly Stability Analysis - Parameter stability and walk-forward analysis
Runs monthly on 1st at 8 AM to analyze parameter stability (90-day walk-forward)
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
        logging.FileHandler('./logs/monthly_stability.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_monthly_stability(sync_gcs: bool = False):
    """
    Run monthly parameter stability analysis with 90-day walk-forward test
    
    Args:
        sync_gcs: Whether to sync results to Google Cloud Storage
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Starting monthly stability analysis...")
        
        # Initialize components
        dashboard = DashboardIntegration(sync_to_gcs=sync_gcs)
        backtest_suite = ComprehensiveBacktestSuite()
        
        # Load historical data (90 days for stability analysis)
        results = {}
        
        for product_id in ['BTC-USD', 'ETH-USD']:
            try:
                logger.info(f"Running stability analysis for {product_id}...")
                
                # Load 1-year data for comprehensive analysis
                data_file = Path(f"./data/historical/{product_id}_hour_365d.parquet")
                if not data_file.exists():
                    # Fallback to 6-month data
                    data_file = Path(f"./data/historical/{product_id}_hour_180d.parquet")
                
                if not data_file.exists():
                    logger.error(f"No historical data found for {product_id}")
                    continue
                
                # Load data
                df = pd.read_parquet(data_file)
                
                # Use last 90 days for stability analysis
                stability_data = df.tail(90 * 24)  # 90 days * 24 hours
                
                if len(stability_data) < 30 * 24:  # Need at least 30 days of data
                    logger.warning(f"Insufficient stability data for {product_id}: {len(stability_data)} rows")
                    continue
                
                # Calculate indicators
                data_with_indicators = calculate_indicators(stability_data, product_id)
                
                # Run comprehensive backtest for stability analysis
                stability_results = backtest_suite.run_all_strategies(data_with_indicators, product_id)
                
                # Calculate stability metrics
                stability_metrics = {
                    'product_id': product_id,
                    'analysis_date': datetime.now().isoformat(),
                    'data_period': {
                        'start': stability_data.index.min().isoformat(),
                        'end': stability_data.index.max().isoformat(),
                        'days': 90,
                        'rows': len(stability_data)
                    },
                    'strategy_stability': {},
                    'overall_stability': 'unknown'
                }
                
                # Analyze each strategy for stability
                stable_strategies = 0
                total_strategies = 0
                
                for strategy_name, strategy_result in stability_results.get('individual_results', {}).items():
                    if 'error' in strategy_result:
                        stability_status = 'error'
                        stability_score = 0
                    else:
                        # Stability criteria (90-day period)
                        total_return = strategy_result.get('total_return', 0)
                        sharpe_ratio = strategy_result.get('sharpe_ratio', 0)
                        max_drawdown = abs(strategy_result.get('max_drawdown', 0))
                        total_trades = strategy_result.get('total_trades', 0)
                        win_rate = strategy_result.get('win_rate', 0)
                        
                        # Stability scoring
                        score = 0
                        
                        # Consistent returns (30% weight)
                        if total_return > 0.05:  # > 5% return over 90 days
                            score += 30
                        elif total_return > 0:
                            score += 15
                        elif total_return > -0.10:  # Not losing more than 10%
                            score += 5
                        
                        # Risk-adjusted performance (25% weight)
                        if sharpe_ratio > 1.5:
                            score += 25
                        elif sharpe_ratio > 1.0:
                            score += 15
                        elif sharpe_ratio > 0.5:
                            score += 10
                        elif sharpe_ratio > 0:
                            score += 5
                        
                        # Drawdown control (25% weight)
                        if max_drawdown < 0.10:  # < 10% drawdown
                            score += 25
                        elif max_drawdown < 0.15:  # < 15% drawdown
                            score += 15
                        elif max_drawdown < 0.20:  # < 20% drawdown
                            score += 10
                        
                        # Trading consistency (20% weight)
                        if total_trades >= 10 and win_rate >= 0.5:  # Good activity and win rate
                            score += 20
                        elif total_trades >= 5 and win_rate >= 0.4:
                            score += 10
                        elif total_trades >= 1:
                            score += 5
                        
                        # Determine stability status
                        if score >= 80:
                            stability_status = 'highly_stable'
                            stable_strategies += 1
                        elif score >= 60:
                            stability_status = 'stable'
                            stable_strategies += 1
                        elif score >= 40:
                            stability_status = 'moderately_stable'
                        else:
                            stability_status = 'unstable'
                        
                        stability_score = score
                    
                    stability_metrics['strategy_stability'][strategy_name] = {
                        'status': stability_status,
                        'score': stability_score,
                        'total_return': strategy_result.get('total_return', 0),
                        'sharpe_ratio': strategy_result.get('sharpe_ratio', 0),
                        'sortino_ratio': strategy_result.get('sortino_ratio', 0),
                        'max_drawdown': strategy_result.get('max_drawdown', 0),
                        'total_trades': strategy_result.get('total_trades', 0),
                        'win_rate': strategy_result.get('win_rate', 0),
                        'profit_factor': strategy_result.get('profit_factor', 0)
                    }
                    
                    total_strategies += 1
                
                # Overall stability assessment
                if total_strategies == 0:
                    stability_metrics['overall_stability'] = 'no_data'
                elif stable_strategies / total_strategies >= 0.75:  # 3/4 strategies stable
                    stability_metrics['overall_stability'] = 'highly_stable'
                elif stable_strategies / total_strategies >= 0.50:  # 1/2 strategies stable
                    stability_metrics['overall_stability'] = 'stable'
                elif stable_strategies / total_strategies >= 0.25:  # 1/4 strategies stable
                    stability_metrics['overall_stability'] = 'moderately_stable'
                else:
                    stability_metrics['overall_stability'] = 'unstable'
                
                stability_metrics['stability_summary'] = {
                    'stable_strategies': stable_strategies,
                    'total_strategies': total_strategies,
                    'stability_percentage': (stable_strategies / total_strategies * 100) if total_strategies > 0 else 0
                }
                
                results[product_id] = stability_metrics
                logger.info(f"Monthly stability analysis completed for {product_id}: {stability_metrics['overall_stability']}")
                
            except Exception as e:
                logger.error(f"Error in stability analysis for {product_id}: {e}")
                results[product_id] = {
                    'product_id': product_id,
                    'analysis_date': datetime.now().isoformat(),
                    'error': str(e),
                    'overall_stability': 'error'
                }
        
        # Save results
        output_dir = Path("./data/backtest_results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        month_str = datetime.now().strftime("%Y-%m")
        
        stability_report = {
            'report_type': 'monthly_stability',
            'month': month_str,
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'summary': {
                'total_products': len(results),
                'highly_stable': len([r for r in results.values() if r.get('overall_stability') == 'highly_stable']),
                'stable': len([r for r in results.values() if r.get('overall_stability') == 'stable']),
                'moderately_stable': len([r for r in results.values() if r.get('overall_stability') == 'moderately_stable']),
                'unstable': len([r for r in results.values() if r.get('overall_stability') == 'unstable']),
                'analysis_period_days': 90
            }
        }
        
        # Save to local file
        report_file = output_dir / f"monthly_stability_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(stability_report, f, indent=2, default=str)
        
        logger.info(f"Monthly stability report saved: {report_file}")
        
        # Sync to GCS if enabled
        if sync_gcs and dashboard.sync_to_gcs:
            # Copy to dashboard directory for sync
            dashboard_report_file = dashboard.dashboard_data_dir / "backtest_results" / "monthly_stability.json"
            with open(dashboard_report_file, 'w') as f:
                json.dump(stability_report, f, indent=2, default=str)
            
            # Sync to GCS
            sync_success = dashboard._sync_reports_to_gcs("monthly")
            if sync_success:
                logger.info("Monthly stability analysis synced to GCS successfully")
            else:
                logger.warning("Failed to sync monthly stability analysis to GCS")
        
        # Print summary
        print(f"\n📊 Monthly Stability Analysis Summary ({month_str})")
        print("=" * 60)
        for product_id, result in results.items():
            status = result.get('overall_stability', 'unknown')
            emoji = {'highly_stable': '🟢', 'stable': '🟡', 'moderately_stable': '🟠', 'unstable': '🔴', 'error': '💥'}.get(status, '❓')
            print(f"{emoji} {product_id}: {status.upper().replace('_', ' ')}")
            
            if 'stability_summary' in result:
                summary = result['stability_summary']
                print(f"   Stable strategies: {summary['stable_strategies']}/{summary['total_strategies']} ({summary['stability_percentage']:.1f}%)")
        
        print(f"\n📁 Report saved: {report_file}")
        if sync_gcs:
            print(f"☁️ Synced to GCS: gs://{dashboard.gcs_bucket_name}/reports/monthly/")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in monthly stability analysis: {e}")
        return False

def main():
    """Main function with command-line arguments"""
    parser = argparse.ArgumentParser(description='Run monthly parameter stability analysis')
    parser.add_argument('--sync-gcs', action='store_true', 
                       help='Sync results to Google Cloud Storage')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    Path('./logs').mkdir(exist_ok=True)
    
    success = run_monthly_stability(sync_gcs=args.sync_gcs)
    
    if success:
        logger.info("Monthly stability analysis completed successfully")
    else:
        logger.error("Monthly stability analysis failed")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
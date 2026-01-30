#!/usr/bin/env python3
"""
Daily Health Check - Automated Server-Side Backtesting
Quick strategy health validation with 7-day rolling performance analysis
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

# Import our backtesting infrastructure
from utils.backtest_suite import ComprehensiveBacktestSuite
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_collector import DataCollector
from coinbase_client import CoinbaseClient
from backtesting.sync_to_gcs import GCSBacktestSync

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DailyHealthChecker:
    """Daily health check for trading strategies"""
    
    def __init__(self, sync_to_gcs: bool = False):
        """Initialize daily health checker"""
        self.sync_to_gcs = sync_to_gcs
        self.results_dir = Path("./reports/daily")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        try:
            coinbase_client = CoinbaseClient()
            self.data_collector = DataCollector(coinbase_client, gcs_bucket_name=None)
            self.backtest_suite = ComprehensiveBacktestSuite()
            
            if sync_to_gcs:
                self.gcs_sync = GCSBacktestSync()
            
            logger.info("Daily Health Checker initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def load_recent_data(self, days: int = 7) -> Dict[str, pd.DataFrame]:
        """Load recent historical data for health check"""
        try:
            # Ensure EUR data is available
            from utils.ensure_eur_data import ensure_eur_data_available
            ensure_eur_data_available(days)
            
            data = {}
            # Use EUR pairs to match bot configuration
            products = ['BTC-EUR', 'ETH-EUR']
            
            for product in products:
                # Try to load from existing files first
                data_files = [
                    f"data/historical/{product}_hour_180d.parquet",
                    f"data/historical/{product}_hour_30d.parquet", 
                    f"data/historical/{product}_hour_7d.parquet",
                    f"data/historical/{product}_hourly_30d.parquet"
                ]
                
                df = None
                for file_path in data_files:
                    if Path(file_path).exists():
                        df = pd.read_parquet(file_path)
                        break
                
                if df is None or len(df) < days * 24:
                    logger.warning(f"Insufficient data for {product}, fetching fresh data")
                    # Fetch fresh data if needed
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days + 1)  # Extra day for safety
                    
                    df = self.data_collector.fetch_bulk_historical_data(
                        product_id=product,
                        start_date=start_date,
                        end_date=end_date,
                        granularity='ONE_HOUR'
                    )
                
                # Get last N days
                if df is not None and not df.empty:
                    cutoff_date = datetime.now() - timedelta(days=days)
                    recent_df = df[df.index >= cutoff_date].copy()
                    data[product] = recent_df
                    logger.info(f"Loaded {len(recent_df)} hours of {product} data")
                else:
                    logger.error(f"Failed to load data for {product}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load recent data: {e}")
            return {}
    
    def run_strategy_health_check(self, data: pd.DataFrame, product: str, 
                                 strategy: str) -> Dict[str, Any]:
        """Run health check for a single strategy"""
        try:
            # Add indicators using DataCollector
            indicators = self.data_collector.calculate_indicators(data)
            
            # Combine data with indicators
            data_with_indicators = data.copy()
            for key, value in indicators.items():
                if isinstance(value, (int, float)):
                    data_with_indicators[key] = value
            
            # Run backtest
            result = self.backtest_suite.run_single_strategy(
                data_with_indicators=data_with_indicators,
                strategy_name=strategy,
                product_id=product
            )
            
            if 'error' in result:
                logger.error(f"Strategy {strategy} failed for {product}: {result['error']}")
                return {'error': result['error']}
            
            # Calculate health metrics
            health_metrics = self.calculate_health_metrics(result, data)
            
            return {
                'strategy': strategy,
                'product': product,
                'total_return': result.get('total_return', 0.0),
                'sharpe_ratio': result.get('performance', {}).get('sharpe_ratio', 0.0),
                'max_drawdown': result.get('performance', {}).get('max_drawdown', 0.0),
                'win_rate': result.get('performance', {}).get('win_rate', 0.0),
                'total_trades': result.get('signal_count', 0),
                'buy_signals': result.get('buy_signals', 0),
                'sell_signals': result.get('sell_signals', 0),
                'health_score': health_metrics['health_score'],
                'health_status': health_metrics['health_status'],
                'alerts': health_metrics['alerts'],
                'data_period_days': (data.index[-1] - data.index[0]).days,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed for {strategy} on {product}: {e}")
            return {'error': str(e)}
    
    def calculate_health_metrics(self, backtest_result: Dict[str, Any], 
                                data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate strategy health metrics and alerts"""
        try:
            alerts = []
            health_score = 100  # Start with perfect score
            
            # Get metrics
            total_return = backtest_result.get('total_return', 0.0)
            sharpe_ratio = backtest_result.get('performance', {}).get('sharpe_ratio', 0.0)
            max_drawdown = backtest_result.get('performance', {}).get('max_drawdown', 0.0)
            win_rate = backtest_result.get('performance', {}).get('win_rate', 0.0)
            total_trades = backtest_result.get('signal_count', 0)
            
            # Market return for comparison
            market_return = ((data['close'].iloc[-1] / data['close'].iloc[0]) - 1) * 100
            
            # Health checks
            
            # 1. Return vs Market
            if total_return < market_return - 5:  # Underperforming market by >5%
                health_score -= 20
                alerts.append(f"Underperforming market by {market_return - total_return:.1f}%")
            
            # 2. Negative returns
            if total_return < -10:
                health_score -= 25
                alerts.append(f"Large negative return: {total_return:.1f}%")
            elif total_return < -5:
                health_score -= 15
                alerts.append(f"Negative return: {total_return:.1f}%")
            
            # 3. Poor risk-adjusted returns
            if sharpe_ratio < 0:
                health_score -= 20
                alerts.append(f"Negative Sharpe ratio: {sharpe_ratio:.2f}")
            elif sharpe_ratio < 0.5:
                health_score -= 10
                alerts.append(f"Low Sharpe ratio: {sharpe_ratio:.2f}")
            
            # 4. High drawdown
            if abs(max_drawdown) > 20:
                health_score -= 25
                alerts.append(f"High drawdown: {max_drawdown:.1f}%")
            elif abs(max_drawdown) > 10:
                health_score -= 15
                alerts.append(f"Moderate drawdown: {max_drawdown:.1f}%")
            
            # 5. Low win rate
            if win_rate < 0.3:
                health_score -= 15
                alerts.append(f"Low win rate: {win_rate:.1%}")
            
            # 6. No trading activity
            if total_trades == 0:
                health_score -= 30
                alerts.append("No trading signals generated")
            elif total_trades < 3:  # Very few trades in 7 days
                health_score -= 10
                alerts.append(f"Low trading activity: {total_trades} trades")
            
            # Determine health status
            if health_score >= 80:
                health_status = "HEALTHY"
            elif health_score >= 60:
                health_status = "WARNING"
            elif health_score >= 40:
                health_status = "POOR"
            else:
                health_status = "CRITICAL"
            
            return {
                'health_score': max(0, health_score),
                'health_status': health_status,
                'alerts': alerts,
                'market_return': market_return,
                'relative_performance': total_return - market_return
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate health metrics: {e}")
            return {
                'health_score': 0,
                'health_status': 'ERROR',
                'alerts': [f"Health calculation failed: {str(e)}"],
                'market_return': 0.0,
                'relative_performance': 0.0
            }
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check for all strategies"""
        logger.info("🏥 Starting daily health check...")
        
        # Load recent data
        data = self.load_recent_data(days=7)
        
        if not data:
            logger.error("No data available for health check")
            return {'error': 'No data available'}
        
        # Strategies to check - TECHNICAL ONLY (LLM cannot be accurately backtested)
        strategies = ['momentum', 'mean_reversion', 'trend_following']
        
        logger.warning("⚠️  LLM strategy excluded from backtesting - cannot simulate neural network decisions")
        
        # Run health checks
        results = {
            'timestamp': datetime.now().isoformat(),
            'check_type': 'daily_health',
            'data_period_days': 7,
            'validation_scope': 'technical_strategies_only',
            'warnings': [
                "⚠️  LLM strategy excluded from backtesting",
                "⚠️  LLM uses Google Gemini API (neural network) - cannot be simulated with rules",
                "⚠️  Results represent technical strategies only, not actual bot behavior",
                "ℹ️  For actual bot performance, see live trading logs and performance tracking"
            ],
            'strategies': {},
            'summary': {
                'total_strategies': 0,
                'healthy_strategies': 0,
                'warning_strategies': 0,
                'poor_strategies': 0,
                'critical_strategies': 0,
                'overall_status': 'UNKNOWN'
            },
            'alerts': []
        }
        
        total_checks = len(strategies) * len(data)
        current_check = 0
        
        for strategy in strategies:
            results['strategies'][strategy] = {}
            
            for product, df in data.items():
                current_check += 1
                logger.info(f"Progress: {current_check}/{total_checks} - Checking {strategy} on {product}")
                
                health_result = self.run_strategy_health_check(df, product, strategy)
                results['strategies'][strategy][product] = health_result
                
                # Update summary
                if 'error' not in health_result:
                    results['summary']['total_strategies'] += 1
                    status = health_result.get('health_status', 'UNKNOWN')
                    
                    if status == 'HEALTHY':
                        results['summary']['healthy_strategies'] += 1
                    elif status == 'WARNING':
                        results['summary']['warning_strategies'] += 1
                    elif status == 'POOR':
                        results['summary']['poor_strategies'] += 1
                    elif status == 'CRITICAL':
                        results['summary']['critical_strategies'] += 1
                    
                    # Collect alerts
                    alerts = health_result.get('alerts', [])
                    for alert in alerts:
                        results['alerts'].append(f"{strategy}/{product}: {alert}")
        
        # Determine overall status
        total = results['summary']['total_strategies']
        if total > 0:
            healthy_pct = results['summary']['healthy_strategies'] / total
            warning_pct = results['summary']['warning_strategies'] / total
            critical_pct = results['summary']['critical_strategies'] / total
            
            if critical_pct > 0.5:
                results['summary']['overall_status'] = 'CRITICAL'
            elif critical_pct > 0.25 or warning_pct > 0.5:
                results['summary']['overall_status'] = 'WARNING'
            elif healthy_pct >= 0.7:
                results['summary']['overall_status'] = 'HEALTHY'
            else:
                results['summary']['overall_status'] = 'POOR'
        
        logger.info(f"Health check complete: {results['summary']['overall_status']}")
        return results
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """Save health check results"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_health_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Save timestamped results
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Save as latest
            latest_filepath = self.results_dir / "latest_daily_health.json"
            with open(latest_filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
            # Sync to GCS if enabled
            if self.sync_to_gcs and hasattr(self, 'gcs_sync'):
                try:
                    self.gcs_sync.upload_report(results, 'daily', 'latest_daily_health.json', 'server')
                    logger.info("Results synced to GCS")
                except Exception as e:
                    logger.error(f"Failed to sync to GCS: {e}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return ""

def run_daily_health_check(sync_gcs: bool = True) -> bool:
    """
    Run daily health check programmatically
    
    Args:
        sync_gcs: Whether to sync results to Google Cloud Storage
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize health checker
        health_checker = DailyHealthChecker(sync_to_gcs=sync_gcs)
        
        # Run health check
        logger.info("🚀 Starting daily health check...")
        results = health_checker.run_comprehensive_health_check()
        
        if 'error' in results:
            logger.error(f"Health check failed: {results['error']}")
            return False
        
        # Save results
        filepath = health_checker.save_results(results)
        logger.info(f"💾 Health check results saved to: {filepath}")
        
        if sync_gcs:
            logger.info("☁️  Results synced to GCS")
        
        return True
        
    except Exception as e:
        logger.error(f"Daily health check failed: {e}")
        return False

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description='Daily Strategy Health Check')
    
    parser.add_argument('--sync-gcs', action='store_true',
                       help='Sync results to Google Cloud Storage')
    
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days to analyze (default: 7)')
    
    args = parser.parse_args()
    
    try:
        # Initialize health checker
        health_checker = DailyHealthChecker(sync_to_gcs=args.sync_gcs)
        
        # Run health check
        logger.info("🚀 Starting daily health check...")
        results = health_checker.run_comprehensive_health_check()
        
        if 'error' in results:
            logger.error(f"Health check failed: {results['error']}")
            return False
        
        # Save results
        filepath = health_checker.save_results(results)
        
        # Display summary
        print("\n" + "="*80)
        print("🏥 DAILY HEALTH CHECK RESULTS")
        print("="*80)
        
        summary = results.get('summary', {})
        print(f"📊 Overall Status: {summary.get('overall_status', 'UNKNOWN')}")
        print(f"✅ Healthy: {summary.get('healthy_strategies', 0)}")
        print(f"⚠️  Warning: {summary.get('warning_strategies', 0)}")
        print(f"🔴 Poor: {summary.get('poor_strategies', 0)}")
        print(f"💥 Critical: {summary.get('critical_strategies', 0)}")
        
        alerts = results.get('alerts', [])
        if alerts:
            print(f"\n🚨 ALERTS ({len(alerts)}):")
            for alert in alerts[:10]:  # Show first 10 alerts
                print(f"   • {alert}")
            if len(alerts) > 10:
                print(f"   ... and {len(alerts) - 10} more alerts")
        
        print(f"\n💾 Results saved to: {filepath}")
        if args.sync_gcs:
            print("☁️  Results synced to GCS")
        
        print("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Daily health check failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
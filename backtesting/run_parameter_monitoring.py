#!/usr/bin/env python3
"""
Parameter Monitoring Service - Phase 4.4
Real-time parameter stability monitoring and alert generation
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import logging
from typing import Dict, List, Any

# Import our monitoring infrastructure
from utils.monitoring.parameter_monitor import ParameterStabilityMonitor, AlertLevel
from data_collector import DataCollector
from coinbase_client import CoinbaseClient
from backtesting.sync_to_gcs import GCSBacktestSync

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ParameterMonitoringService:
    """Real-time parameter monitoring service"""
    
    def __init__(self, sync_to_gcs: bool = False, monitoring_interval: int = 3600):
        """Initialize parameter monitoring service"""
        self.sync_to_gcs = sync_to_gcs
        self.monitoring_interval = monitoring_interval  # seconds
        self.results_dir = Path("./reports/parameter_monitoring")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        try:
            coinbase_client = CoinbaseClient()
            self.data_collector = DataCollector(coinbase_client, gcs_bucket_name=None)
            self.parameter_monitor = ParameterStabilityMonitor()
            
            if sync_to_gcs:
                self.gcs_sync = GCSBacktestSync()
            
            logger.info("Parameter Monitoring Service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def load_recent_market_data(self, hours: int = 48) -> Dict[str, pd.DataFrame]:
        """Load recent market data for monitoring"""
        try:
            data = {}
            products = ['BTC-USD', 'ETH-USD']
            
            for product in products:
                # Try to load from existing files first
                data_files = [
                    f"data/historical/{product}_hour_180d.parquet",
                    f"data/historical/{product}_hour_30d.parquet",
                    f"data/historical/{product}_hourly_30d.parquet"
                ]
                
                df = None
                for file_path in data_files:
                    if Path(file_path).exists():
                        df = pd.read_parquet(file_path)
                        break
                
                if df is None or len(df) < hours:
                    logger.warning(f"Insufficient data for {product}, fetching fresh data")
                    # Fetch fresh data if needed
                    end_date = datetime.now()
                    start_date = end_date - timedelta(hours=hours + 12)  # Extra hours for safety
                    
                    df = self.data_collector.fetch_bulk_historical_data(
                        product_id=product,
                        start_date=start_date,
                        end_date=end_date,
                        granularity='ONE_HOUR'
                    )
                
                # Get last N hours
                if df is not None and not df.empty:
                    cutoff_date = datetime.now() - timedelta(hours=hours)
                    recent_df = df[df.index >= cutoff_date].copy()
                    data[product] = recent_df
                    logger.info(f"Loaded {len(recent_df)} hours of {product} data")
                else:
                    logger.error(f"Failed to load data for {product}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load recent market data: {e}")
            return {}
    
    def load_recent_performance_data(self) -> Dict[str, Any]:
        """Load recent performance data from daily/weekly reports"""
        try:
            performance_data = {}
            
            # Load daily health check results
            daily_reports_dir = Path("./reports/daily")
            if daily_reports_dir.exists():
                latest_daily = daily_reports_dir / "latest_daily_health.json"
                if latest_daily.exists():
                    with open(latest_daily, 'r') as f:
                        daily_data = json.load(f)
                    
                    # Extract strategy performance
                    strategies = daily_data.get('strategies', {})
                    for strategy, products in strategies.items():
                        for product, result in products.items():
                            if 'error' not in result:
                                key = f"{strategy}_{product}"
                                performance_data[key] = {
                                    'total_return': result.get('total_return', 0.0),
                                    'sharpe_ratio': result.get('sharpe_ratio', 0.0),
                                    'max_drawdown': result.get('max_drawdown', 0.0),
                                    'win_rate': result.get('win_rate', 0.0),
                                    'source': 'daily_health',
                                    'timestamp': result.get('timestamp', datetime.now().isoformat())
                                }
            
            # Load weekly validation results
            weekly_reports_dir = Path("./reports/weekly")
            if weekly_reports_dir.exists():
                latest_weekly = weekly_reports_dir / "latest_weekly_validation.json"
                if latest_weekly.exists():
                    with open(latest_weekly, 'r') as f:
                        weekly_data = json.load(f)
                    
                    # Extract strategy performance
                    strategies = weekly_data.get('strategies', {})
                    for strategy, products in strategies.items():
                        for product, result in products.items():
                            if 'error' not in result:
                                key = f"{strategy}_{product}"
                                if key in performance_data:
                                    # Update with weekly data
                                    performance_data[key].update({
                                        'validation_score': result.get('validation_score', 0),
                                        'validation_status': result.get('validation_status', 'UNKNOWN'),
                                        'performance_grade': result.get('performance_grade', 'F'),
                                        'weekly_timestamp': result.get('timestamp', datetime.now().isoformat())
                                    })
            
            logger.info(f"Loaded performance data for {len(performance_data)} strategy/product combinations")
            return performance_data
            
        except Exception as e:
            logger.error(f"Failed to load recent performance data: {e}")
            return {}
    
    def update_parameter_monitor(self, performance_data: Dict[str, Any]):
        """Update parameter monitor with recent performance data"""
        try:
            for key, data in performance_data.items():
                if '_' in key:
                    strategy, product = key.split('_', 1)
                    self.parameter_monitor.update_performance_history(strategy, product, data)
            
            logger.info(f"Updated parameter monitor with {len(performance_data)} performance records")
            
        except Exception as e:
            logger.error(f"Failed to update parameter monitor: {e}")
    
    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a single monitoring cycle"""
        logger.info("🔍 Starting parameter monitoring cycle...")
        
        try:
            # Load recent market data
            market_data = self.load_recent_market_data(hours=48)
            
            if not market_data:
                logger.error("No market data available for monitoring")
                return {'error': 'No market data available'}
            
            # Load recent performance data
            performance_data = self.load_recent_performance_data()
            
            # Update parameter monitor
            self.update_parameter_monitor(performance_data)
            
            # Run comprehensive monitoring
            monitoring_report = self.parameter_monitor.run_comprehensive_monitoring(market_data)
            
            if 'error' in monitoring_report:
                logger.error(f"Monitoring failed: {monitoring_report['error']}")
                return monitoring_report
            
            # Check for critical alerts
            critical_alerts = self.parameter_monitor.get_critical_alerts(hours=24)
            
            # Check if any strategies should be paused
            strategy_pause_recommendations = {}
            strategies = ['momentum', 'mean_reversion', 'trend_following']
            products = list(market_data.keys())
            
            for strategy in strategies:
                for product in products:
                    should_pause, reasons = self.parameter_monitor.should_pause_strategy(strategy, product)
                    if should_pause:
                        strategy_pause_recommendations[f"{strategy}_{product}"] = {
                            'should_pause': True,
                            'reasons': reasons,
                            'timestamp': datetime.now().isoformat()
                        }
            
            # Enhance monitoring report
            monitoring_report.update({
                'critical_alerts_24h': len(critical_alerts),
                'strategy_pause_recommendations': strategy_pause_recommendations,
                'monitoring_cycle_complete': True
            })
            
            # Save results
            self.save_monitoring_results(monitoring_report)
            
            # Sync to GCS if enabled
            if self.sync_to_gcs and hasattr(self, 'gcs_sync'):
                try:
                    self.gcs_sync.upload_report(monitoring_report, 'parameter_monitoring', 'latest_parameter_monitoring.json', 'server')
                    logger.info("Monitoring results synced to GCS")
                except Exception as e:
                    logger.error(f"Failed to sync to GCS: {e}")
            
            logger.info(f"Monitoring cycle complete: {monitoring_report['total_alerts']} alerts generated")
            return monitoring_report
            
        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}")
            return {'error': str(e)}
    
    def save_monitoring_results(self, results: Dict[str, Any]):
        """Save monitoring results"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parameter_monitoring_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Save timestamped results
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Save as latest
            latest_filepath = self.results_dir / "latest_parameter_monitoring.json"
            with open(latest_filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Monitoring results saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save monitoring results: {e}")
    
    def run_continuous_monitoring(self, max_cycles: int = None):
        """Run continuous parameter monitoring"""
        logger.info(f"🚀 Starting continuous parameter monitoring (interval: {self.monitoring_interval}s)")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                
                if max_cycles and cycle_count > max_cycles:
                    logger.info(f"Reached maximum cycles ({max_cycles}), stopping")
                    break
                
                logger.info(f"Starting monitoring cycle #{cycle_count}")
                
                # Run monitoring cycle
                results = self.run_monitoring_cycle()
                
                if 'error' in results:
                    logger.error(f"Cycle #{cycle_count} failed: {results['error']}")
                else:
                    # Display summary
                    total_alerts = results.get('total_alerts', 0)
                    critical_alerts = results.get('critical_alerts_24h', 0)
                    pause_recommendations = len(results.get('strategy_pause_recommendations', {}))
                    
                    logger.info(f"Cycle #{cycle_count} complete: {total_alerts} alerts, {critical_alerts} critical, {pause_recommendations} pause recommendations")
                    
                    # Log critical alerts
                    if critical_alerts > 0:
                        logger.warning(f"⚠️  {critical_alerts} critical alerts in last 24 hours!")
                    
                    # Log pause recommendations
                    if pause_recommendations > 0:
                        logger.critical(f"🛑 {pause_recommendations} strategies recommended for pause!")
                        for strategy_product, rec in results.get('strategy_pause_recommendations', {}).items():
                            logger.critical(f"   {strategy_product}: {', '.join(rec['reasons'])}")
                
                # Wait for next cycle
                if max_cycles is None or cycle_count < max_cycles:
                    logger.info(f"Waiting {self.monitoring_interval}s for next cycle...")
                    time.sleep(self.monitoring_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Continuous monitoring failed: {e}")
            raise

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description='Parameter Stability Monitoring Service')
    
    parser.add_argument('--sync-gcs', action='store_true',
                       help='Sync results to Google Cloud Storage')
    
    parser.add_argument('--interval', type=int, default=3600,
                       help='Monitoring interval in seconds (default: 3600 = 1 hour)')
    
    parser.add_argument('--max-cycles', type=int,
                       help='Maximum number of monitoring cycles (default: unlimited)')
    
    parser.add_argument('--single-run', action='store_true',
                       help='Run single monitoring cycle and exit')
    
    args = parser.parse_args()
    
    try:
        # Initialize monitoring service
        monitoring_service = ParameterMonitoringService(
            sync_to_gcs=args.sync_gcs,
            monitoring_interval=args.interval
        )
        
        if args.single_run:
            # Run single cycle
            logger.info("🚀 Running single parameter monitoring cycle...")
            results = monitoring_service.run_monitoring_cycle()
            
            if 'error' in results:
                logger.error(f"Monitoring failed: {results['error']}")
                return False
            
            # Display results
            print("\n" + "="*80)
            print("🔍 PARAMETER MONITORING RESULTS")
            print("="*80)
            
            print(f"📊 Total Alerts: {results.get('total_alerts', 0)}")
            
            alert_breakdown = results.get('alert_breakdown', {})
            print(f"ℹ️  Info: {alert_breakdown.get('INFO', 0)}")
            print(f"⚠️  Warning: {alert_breakdown.get('WARNING', 0)}")
            print(f"🔴 Critical: {alert_breakdown.get('CRITICAL', 0)}")
            print(f"🚨 Emergency: {alert_breakdown.get('EMERGENCY', 0)}")
            
            print(f"🎯 Market Regime: {results.get('regime_info', 'UNKNOWN')}")
            print(f"📈 Regime Confidence: {results.get('regime_confidence', 0):.1%}")
            
            critical_alerts_24h = results.get('critical_alerts_24h', 0)
            if critical_alerts_24h > 0:
                print(f"\n⚠️  {critical_alerts_24h} critical alerts in last 24 hours")
            
            pause_recommendations = results.get('strategy_pause_recommendations', {})
            if pause_recommendations:
                print(f"\n🛑 STRATEGY PAUSE RECOMMENDATIONS:")
                for strategy_product, rec in pause_recommendations.items():
                    print(f"   {strategy_product}: {', '.join(rec['reasons'])}")
            
            if args.sync_gcs:
                print("☁️  Results synced to GCS")
            
            print("="*80)
            
        else:
            # Run continuous monitoring
            monitoring_service.run_continuous_monitoring(max_cycles=args.max_cycles)
        
        return True
        
    except Exception as e:
        logger.error(f"Parameter monitoring failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
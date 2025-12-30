#!/usr/bin/env python3
"""
Dashboard Integration for Backtesting

This module creates JSON data files for the backtesting dashboard
by running backtests and optimizations, then formatting the results
for web consumption.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, Any, Optional

from utils.performance.indicator_factory import calculate_indicators
from utils.backtest_suite import ComprehensiveBacktestSuite
from data_collector import DataCollector

logger = logging.getLogger(__name__)

class DashboardIntegration:
    """
    Integration layer between backtesting engine and web dashboard with GCS sync
    """
    
    def __init__(self, dashboard_data_dir: str = "./dashboard/data", sync_to_gcs: bool = True):
        """Initialize dashboard integration with optional GCS sync"""
        self.dashboard_data_dir = Path(dashboard_data_dir)
        self.dashboard_data_dir.mkdir(parents=True, exist_ok=True)
        self.sync_to_gcs = sync_to_gcs
        
        # Create subdirectories
        (self.dashboard_data_dir / "backtest_results").mkdir(exist_ok=True)
        
        # Initialize components
        # For dashboard integration, we don't need a live coinbase client
        # We'll work with cached/historical data
        self.data_collector = None  # Will be initialized when needed
        self.backtest_suite = ComprehensiveBacktestSuite()
        
        # Initialize GCS client if sync is enabled
        self.gcs_client = None
        if self.sync_to_gcs:
            try:
                from google.cloud import storage
                self.gcs_client = storage.Client()
                # Use the existing project ID from environment
                import os
                project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID', 'ai-crypto-bot')
                self.gcs_bucket_name = f"{project_id}-backtest-data"
                logger.info(f"GCS sync enabled for bucket: {self.gcs_bucket_name}")
            except Exception as e:
                logger.warning(f"GCS sync disabled due to error: {e}")
                self.sync_to_gcs = False
        
        logger.info(f"Dashboard integration initialized: {self.dashboard_data_dir} (GCS sync: {self.sync_to_gcs})")
    
    def generate_dashboard_data(self, product_id: str = "BTC-USD", days: int = 30) -> bool:
        """
        Generate all dashboard data files
        
        Args:
            product_id: Trading pair to analyze
            days: Number of days of historical data to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Generating dashboard data for {product_id} ({days} days)")
            
            # Load and prepare data
            data = self._load_historical_data(product_id, days)
            if data is None or data.empty:
                logger.error("Failed to load historical data")
                return False
            
            # Calculate indicators
            data_with_indicators = calculate_indicators(data, product_id)
            logger.info(f"Prepared {len(data_with_indicators)} rows with indicators")
            
            # Run comprehensive backtest
            backtest_results = self.backtest_suite.run_all_strategies(data_with_indicators, product_id)
            
            # Generate dashboard JSON files
            self._create_latest_backtest_file(backtest_results, product_id)
            self._create_data_summary_file(data_with_indicators, product_id)
            self._create_strategy_comparison_file(backtest_results)
            
            # Run parameter optimization for best strategy
            if backtest_results.get('comparative_analysis', {}).get('best_strategy'):
                best_strategy = backtest_results['comparative_analysis']['best_strategy']['name']
                self._run_parameter_optimization(data_with_indicators, best_strategy, product_id)
            
            logger.info("Dashboard data generation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}")
            return False
    
    def _load_historical_data(self, product_id: str, days: int) -> Optional[pd.DataFrame]:
        """Load historical data for backtesting"""
        try:
            # Try to load from local cache first
            data_dir = Path("./data/historical")
            cache_file = data_dir / f"{product_id}_hourly_{days}d.parquet"
            
            if cache_file.exists():
                logger.info(f"Loading cached data from {cache_file}")
                return pd.read_parquet(cache_file)
            
            # For dashboard integration, we'll work with existing cached data
            # or create sample data if no cache exists
            logger.warning(f"No cached data found for {product_id} ({days} days)")
            logger.info("Dashboard integration works with cached data. Run sync_historical_data.py first to populate cache.")
            
            # Return None to indicate no data available
            return None
            
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return None
    
    def _create_latest_backtest_file(self, results: Dict[str, Any], product_id: str):
        """Create the latest backtest results file for dashboard"""
        try:
            # Format results for dashboard consumption
            dashboard_results = {
                'timestamp': datetime.now().isoformat(),
                'product_id': product_id,
                'individual_results': results.get('individual_results', {}),
                'comparative_analysis': results.get('comparative_analysis', {}),
                'data_period': results.get('data_period', {}),
                'summary': {
                    'total_strategies': len(results.get('individual_results', {})),
                    'successful_strategies': len([r for r in results.get('individual_results', {}).values() if 'error' not in r]),
                    'best_return': 0,
                    'best_sharpe': 0
                }
            }
            
            # Calculate summary statistics
            valid_results = {k: v for k, v in results.get('individual_results', {}).items() if 'error' not in v}
            if valid_results:
                dashboard_results['summary']['best_return'] = max(r.get('total_return', 0) for r in valid_results.values())
                dashboard_results['summary']['best_sharpe'] = max(r.get('sharpe_ratio', 0) for r in valid_results.values())
            
            # Save to dashboard data directory
            output_file = self.dashboard_data_dir / "backtest_results" / "latest_backtest.json"
            with open(output_file, 'w') as f:
                json.dump(dashboard_results, f, indent=2, default=str)
            
            logger.info(f"Created latest backtest file: {output_file}")
            
        except Exception as e:
            logger.error(f"Error creating latest backtest file: {e}")
    
    def _create_data_summary_file(self, data: pd.DataFrame, product_id: str):
        """Create data summary file for dashboard"""
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'product_id': product_id,
                'data_points': len(data),
                'date_range': {
                    'start': data.index.min().isoformat(),
                    'end': data.index.max().isoformat(),
                    'days': (data.index.max() - data.index.min()).days
                },
                'data_quality': {
                    'completeness': 100.0,  # Assume good quality for now
                    'missing_values': data.isnull().sum().sum(),
                    'duplicate_rows': data.duplicated().sum()
                },
                'price_statistics': {
                    'min_price': float(data['low'].min()),
                    'max_price': float(data['high'].max()),
                    'avg_price': float(data['close'].mean()),
                    'volatility': float(data['close'].pct_change().std() * 100)
                }
            }
            
            output_file = self.dashboard_data_dir / "backtest_results" / "data_summary.json"
            with open(output_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"Created data summary file: {output_file}")
            
        except Exception as e:
            logger.error(f"Error creating data summary file: {e}")
    
    def _create_strategy_comparison_file(self, results: Dict[str, Any]):
        """Create strategy comparison file for dashboard"""
        try:
            if not results.get('individual_results'):
                return
            
            strategies = []
            for name, result in results['individual_results'].items():
                if 'error' in result:
                    continue
                
                strategies.append({
                    'name': name,
                    'display_name': name.replace('_', ' ').title(),
                    'total_return': result.get('total_return', 0),
                    'sharpe_ratio': result.get('sharpe_ratio', 0),
                    'sortino_ratio': result.get('sortino_ratio', 0),
                    'max_drawdown': result.get('max_drawdown', 0),
                    'total_trades': result.get('total_trades', 0),
                    'win_rate': result.get('win_rate', 0),
                    'profit_factor': result.get('profit_factor', 0),
                    'annual_return': result.get('annual_return', 0)
                })
            
            # Sort by total return
            strategies.sort(key=lambda x: x['total_return'], reverse=True)
            
            comparison_data = {
                'timestamp': datetime.now().isoformat(),
                'strategies': strategies,
                'rankings': {
                    'by_return': sorted(strategies, key=lambda x: x['total_return'], reverse=True),
                    'by_sharpe': sorted(strategies, key=lambda x: x['sharpe_ratio'], reverse=True),
                    'by_drawdown': sorted(strategies, key=lambda x: abs(x['max_drawdown']))
                }
            }
            
            output_file = self.dashboard_data_dir / "backtest_results" / "strategy_comparison.json"
            with open(output_file, 'w') as f:
                json.dump(comparison_data, f, indent=2, default=str)
            
            logger.info(f"Created strategy comparison file: {output_file}")
            
        except Exception as e:
            logger.error(f"Error creating strategy comparison file: {e}")
    
    def _run_parameter_optimization(self, data: pd.DataFrame, strategy_name: str, product_id: str):
        """Run parameter optimization and save results"""
        try:
            logger.info(f"Running parameter optimization for {strategy_name}")
            
            # Define parameter grid (simplified for demo)
            param_grid = {
                'confidence_threshold': [0.6, 0.7, 0.8],
                'lookback_period': [10, 20, 30],
                'volatility_threshold': [0.02, 0.03, 0.04]
            }
            
            # Run optimization
            optimization_results = self.backtest_suite.optimize_strategy_parameters(
                data, strategy_name, param_grid, product_id, "sortino_ratio"
            )
            
            if not optimization_results.empty:
                # Format for dashboard
                dashboard_optimization = {
                    'timestamp': datetime.now().isoformat(),
                    'strategy_name': strategy_name,
                    'product_id': product_id,
                    'optimization_metric': 'sortino_ratio',
                    'param_grid': param_grid,
                    'best_params': optimization_results.iloc[0][list(param_grid.keys())].to_dict(),
                    'best_performance': float(optimization_results.iloc[0]['sortino_ratio']),
                    'total_combinations': len(optimization_results),
                    'top_results': optimization_results.head(5).to_dict('records')
                }
                
                output_file = self.dashboard_data_dir / "backtest_results" / "latest_optimization.json"
                with open(output_file, 'w') as f:
                    json.dump(dashboard_optimization, f, indent=2, default=str)
                
                logger.info(f"Created optimization results file: {output_file}")
            
        except Exception as e:
            logger.error(f"Error running parameter optimization: {e}")
    
    def update_dashboard_data(self, product_id: str = "BTC-USD"):
        """Update dashboard data with latest information"""
        try:
            logger.info("Updating dashboard data...")
            
            # Generate fresh data
            success = self.generate_dashboard_data(product_id, days=30)
            
            if success:
                # Create a status file to indicate last update
                status = {
                    'last_update': datetime.now().isoformat(),
                    'status': 'success',
                    'product_id': product_id,
                    'next_update': (datetime.now() + timedelta(hours=1)).isoformat()
                }
            else:
                status = {
                    'last_update': datetime.now().isoformat(),
                    'status': 'error',
                    'product_id': product_id,
                    'error': 'Failed to generate dashboard data'
                }
            
            status_file = self.dashboard_data_dir / "backtest_results" / "update_status.json"
            with open(status_file, 'w') as f:
                json.dump(status, f, indent=2, default=str)
            
            # Sync to GCS if enabled
            if success and self.sync_to_gcs:
                self._sync_reports_to_gcs("daily")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating dashboard data: {e}")
            return False
    
    def _sync_reports_to_gcs(self, report_type: str = "daily"):
        """Sync dashboard reports to GCS"""
        if not self.gcs_client:
            logger.warning("GCS client not available for sync")
            return False
        
        try:
            logger.info(f"Syncing {report_type} reports to GCS...")
            
            # Get current date for organizing reports
            current_date = datetime.now()
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Define GCS paths based on report type
            if report_type == "daily":
                gcs_base_path = f"reports/daily/{date_str}/"
            elif report_type == "weekly":
                week_str = current_date.strftime("%Y-W%U")
                gcs_base_path = f"reports/weekly/{week_str}/"
            elif report_type == "monthly":
                month_str = current_date.strftime("%Y-%m")
                gcs_base_path = f"reports/monthly/{month_str}/"
            else:
                gcs_base_path = f"reports/{report_type}/"
            
            # Files to sync
            report_files = [
                "latest_backtest.json",
                "data_summary.json", 
                "strategy_comparison.json",
                "latest_optimization.json",
                "update_status.json"
            ]
            
            bucket = self.gcs_client.bucket(self.gcs_bucket_name)
            synced_files = []
            
            for filename in report_files:
                local_file = self.dashboard_data_dir / "backtest_results" / filename
                if local_file.exists():
                    try:
                        # Upload to GCS
                        gcs_path = gcs_base_path + filename
                        blob = bucket.blob(gcs_path)
                        blob.upload_from_filename(str(local_file))
                        
                        synced_files.append(gcs_path)
                        logger.info(f"Synced {filename} to gs://{self.gcs_bucket_name}/{gcs_path}")
                        
                    except Exception as e:
                        logger.error(f"Error syncing {filename}: {e}")
                else:
                    logger.warning(f"Report file not found: {filename}")
            
            # Create sync metadata
            sync_metadata = {
                'sync_timestamp': datetime.now().isoformat(),
                'report_type': report_type,
                'synced_files': synced_files,
                'total_files': len(synced_files),
                'gcs_bucket': self.gcs_bucket_name,
                'gcs_base_path': gcs_base_path
            }
            
            # Save sync metadata locally and to GCS
            metadata_file = self.dashboard_data_dir / "backtest_results" / "sync_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(sync_metadata, f, indent=2, default=str)
            
            # Upload metadata to GCS
            metadata_blob = bucket.blob(gcs_base_path + "sync_metadata.json")
            metadata_blob.upload_from_filename(str(metadata_file))
            
            logger.info(f"Successfully synced {len(synced_files)} files to GCS")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing reports to GCS: {e}")
            return False
    
    def download_reports_from_gcs(self, report_type: str = "daily", date_str: str = None):
        """Download reports from GCS to local dashboard"""
        if not self.gcs_client:
            logger.warning("GCS client not available for download")
            return False
        
        try:
            if date_str is None:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"Downloading {report_type} reports from GCS for {date_str}...")
            
            # Define GCS path
            if report_type == "daily":
                gcs_base_path = f"reports/daily/{date_str}/"
            elif report_type == "weekly":
                gcs_base_path = f"reports/weekly/{date_str}/"
            elif report_type == "monthly":
                gcs_base_path = f"reports/monthly/{date_str}/"
            else:
                gcs_base_path = f"reports/{report_type}/"
            
            bucket = self.gcs_client.bucket(self.gcs_bucket_name)
            downloaded_files = []
            
            # List all blobs with the prefix
            blobs = bucket.list_blobs(prefix=gcs_base_path)
            
            for blob in blobs:
                if blob.name.endswith('.json'):
                    try:
                        # Download to local dashboard directory
                        filename = Path(blob.name).name
                        local_file = self.dashboard_data_dir / "backtest_results" / filename
                        
                        blob.download_to_filename(str(local_file))
                        downloaded_files.append(filename)
                        logger.info(f"Downloaded {filename} from GCS")
                        
                    except Exception as e:
                        logger.error(f"Error downloading {blob.name}: {e}")
            
            logger.info(f"Successfully downloaded {len(downloaded_files)} files from GCS")
            return len(downloaded_files) > 0
            
        except Exception as e:
            logger.error(f"Error downloading reports from GCS: {e}")
            return False
    
    def generate_and_sync_reports(self, product_id: str = "BTC-USD", report_type: str = "daily", days: int = 30):
        """Generate reports and sync to GCS in one operation"""
        try:
            logger.info(f"Generating and syncing {report_type} reports...")
            
            # Generate dashboard data
            success = self.generate_dashboard_data(product_id, days)
            
            if success and self.sync_to_gcs:
                # Sync to GCS
                sync_success = self._sync_reports_to_gcs(report_type)
                return sync_success
            
            return success
            
        except Exception as e:
            logger.error(f"Error in generate_and_sync_reports: {e}")
            return False

def main():
    """Main function to generate dashboard data with optional GCS sync"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    import argparse
    parser = argparse.ArgumentParser(description='Generate dashboard data with optional GCS sync')
    parser.add_argument('--sync-gcs', action='store_true', help='Sync reports to Google Cloud Storage')
    parser.add_argument('--report-type', default='daily', choices=['daily', 'weekly', 'monthly'], 
                       help='Type of report to generate')
    parser.add_argument('--product', default='BTC-USD', help='Product to analyze')
    parser.add_argument('--days', type=int, default=30, help='Days of data to analyze')
    
    args = parser.parse_args()
    
    try:
        # Initialize dashboard integration with GCS sync option
        dashboard = DashboardIntegration(sync_to_gcs=args.sync_gcs)
        
        # Generate and optionally sync data
        if args.sync_gcs:
            success = dashboard.generate_and_sync_reports(args.product, args.report_type, args.days)
            if success:
                logger.info("✅ Dashboard data generated and synced to GCS successfully")
                print("Dashboard data has been generated and synced to GCS!")
                print(f"Report type: {args.report_type}")
                print(f"GCS bucket: gs://{dashboard.gcs_bucket_name}/reports/{args.report_type}/")
            else:
                logger.error("❌ Dashboard data generation or GCS sync failed")
                print("Failed to generate or sync dashboard data. Check the logs for details.")
        else:
            success = dashboard.generate_dashboard_data(args.product, args.days)
            if success:
                logger.info("✅ Dashboard data generation completed successfully")
                print("Dashboard data has been generated successfully!")
                print("You can now view the backtesting dashboard at: dashboard/static/backtesting.html")
            else:
                logger.error("❌ Dashboard data generation failed")
                print("Failed to generate dashboard data. Check the logs for details.")
        
        return success
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
GCS Sync for Backtest Reports - Hybrid Laptop/Server Workflow
Enables seamless backtesting on laptop with results visualization on production dashboard
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from google.cloud import storage
from google.cloud.exceptions import NotFound
import gzip
import tempfile

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GCSBacktestSync:
    """Synchronize backtest reports between laptop and server via GCS"""
    
    def __init__(self, bucket_name: str = None, project_id: str = None):
        """Initialize GCS sync client"""
        try:
            # Get project info from environment or config
            self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT', 'intense-base-456414-u5')
            self.bucket_name = bucket_name or f"{self.project_id}-backtest-data"
            
            # Initialize GCS client
            self.client = storage.Client(project=self.project_id)
            self.bucket = self.client.bucket(self.bucket_name)
            
            # Local paths
            self.local_reports_dir = Path("./reports")
            self.local_cache_dir = Path("./data/backtest_cache")
            self.dashboard_data_dir = Path("./dashboard/data/backtest_results")
            
            # Create directories
            for dir_path in [self.local_reports_dir, self.local_cache_dir, self.dashboard_data_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"GCS Backtest Sync initialized: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise
    
    def compress_json(self, data: Dict[str, Any]) -> bytes:
        """Compress JSON data with gzip"""
        json_str = json.dumps(data, indent=2, default=str)
        return gzip.compress(json_str.encode('utf-8'))
    
    def decompress_json(self, compressed_data: bytes) -> Dict[str, Any]:
        """Decompress gzip JSON data"""
        json_str = gzip.decompress(compressed_data).decode('utf-8')
        return json.loads(json_str)
    
    def upload_report(self, report_data: Dict[str, Any], report_type: str, 
                     report_name: str, source: str = "laptop") -> bool:
        """Upload a single report to GCS"""
        try:
            # Generate timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create GCS path
            if report_type == "interval_optimization":
                gcs_path = f"reports/{report_type}/{report_name}"
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
                gcs_path = f"reports/{report_type}/{date_str}/{report_name}"
            
            # Add metadata
            report_data['_metadata'] = {
                'source': source,
                'timestamp': timestamp,
                'upload_time': datetime.now().isoformat(),
                'report_type': report_type,
                'report_name': report_name
            }
            
            # Compress and upload
            compressed_data = self.compress_json(report_data)
            blob = self.bucket.blob(gcs_path)
            
            # Set metadata
            blob.metadata = {
                'source': source,
                'report_type': report_type,
                'timestamp': timestamp,
                'content_encoding': 'gzip'
            }
            
            blob.upload_from_string(compressed_data, content_type='application/json')
            
            # Also upload as "latest" for easy dashboard access
            latest_path = f"reports/{report_type}/latest_{report_name}"
            latest_blob = self.bucket.blob(latest_path)
            latest_blob.metadata = blob.metadata
            latest_blob.upload_from_string(compressed_data, content_type='application/json')
            
            logger.info(f"Uploaded report: {gcs_path} ({len(compressed_data)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload report {report_name}: {e}")
            return False
    
    def download_report(self, report_type: str, report_name: str, 
                       date: str = None) -> Optional[Dict[str, Any]]:
        """Download a specific report from GCS"""
        try:
            # Construct GCS path
            if date:
                gcs_path = f"reports/{report_type}/{date}/{report_name}"
            else:
                gcs_path = f"reports/{report_type}/latest_{report_name}"
            
            blob = self.bucket.blob(gcs_path)
            
            if not blob.exists():
                logger.warning(f"Report not found: {gcs_path}")
                return None
            
            # Download and decompress
            compressed_data = blob.download_as_bytes()
            report_data = self.decompress_json(compressed_data)
            
            logger.info(f"Downloaded report: {gcs_path}")
            return report_data
            
        except Exception as e:
            logger.error(f"Failed to download report {report_name}: {e}")
            return None
    
    def sync_local_reports_to_gcs(self, source: str = "laptop") -> Dict[str, Any]:
        """Sync all local reports to GCS"""
        results = {
            'uploaded': [],
            'failed': [],
            'total': 0
        }
        
        try:
            # Find all JSON report files
            report_patterns = [
                "interval_optimization/*.json",
                "daily/*.json",
                "weekly/*.json", 
                "monthly/*.json",
                "parameter_optimization/*.json",
                "walk_forward/*.json"
            ]
            
            for pattern in report_patterns:
                report_files = list(self.local_reports_dir.glob(pattern))
                
                for report_file in report_files:
                    results['total'] += 1
                    
                    try:
                        # Load report data
                        with open(report_file, 'r') as f:
                            report_data = json.load(f)
                        
                        # Determine report type from path
                        report_type = report_file.parent.name
                        report_name = report_file.name
                        
                        # Upload to GCS
                        if self.upload_report(report_data, report_type, report_name, source):
                            results['uploaded'].append(str(report_file))
                        else:
                            results['failed'].append(str(report_file))
                            
                    except Exception as e:
                        logger.error(f"Failed to process {report_file}: {e}")
                        results['failed'].append(str(report_file))
            
            logger.info(f"Sync complete: {len(results['uploaded'])}/{results['total']} reports uploaded")
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync local reports: {e}")
            return results
    
    def download_latest_reports_for_dashboard(self) -> Dict[str, Any]:
        """Download latest reports from GCS for dashboard display"""
        results = {
            'downloaded': [],
            'failed': [],
            'reports': {}
        }
        
        try:
            # Define reports needed for dashboard
            dashboard_reports = [
                ('interval_optimization', 'latest_interval_optimization.json'),
                ('daily', 'latest_daily_health.json'),
                ('weekly', 'latest_weekly_validation.json'),
                ('monthly', 'latest_monthly_analysis.json'),
                ('parameter_optimization', 'latest_optimization.json'),
                ('walk_forward', 'latest_walkforward.json')
            ]
            
            for report_type, report_name in dashboard_reports:
                try:
                    report_data = self.download_report(report_type, report_name)
                    
                    if report_data:
                        # Save to dashboard data directory
                        dashboard_file = self.dashboard_data_dir / f"gcs_{report_name}"
                        with open(dashboard_file, 'w') as f:
                            json.dump(report_data, f, indent=2, default=str)
                        
                        results['downloaded'].append(report_name)
                        results['reports'][report_type] = report_data
                        
                        logger.info(f"Downloaded for dashboard: {report_name}")
                    else:
                        results['failed'].append(report_name)
                        
                except Exception as e:
                    logger.error(f"Failed to download {report_name}: {e}")
                    results['failed'].append(report_name)
            
            # Create sync status file
            sync_status = {
                'last_sync': datetime.now().isoformat(),
                'downloaded_reports': results['downloaded'],
                'failed_reports': results['failed'],
                'total_reports': len(results['downloaded'])
            }
            
            with open(self.dashboard_data_dir / 'gcs_sync_status.json', 'w') as f:
                json.dump(sync_status, f, indent=2)
            
            logger.info(f"Dashboard sync complete: {len(results['downloaded'])} reports available")
            return results
            
        except Exception as e:
            logger.error(f"Failed to download reports for dashboard: {e}")
            return results
    
    def list_available_reports(self, report_type: str = None) -> List[Dict[str, Any]]:
        """List all available reports in GCS"""
        try:
            prefix = f"reports/{report_type}/" if report_type else "reports/"
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)
            
            reports = []
            for blob in blobs:
                if blob.name.endswith('.json'):
                    report_info = {
                        'name': blob.name,
                        'size': blob.size,
                        'created': blob.time_created.isoformat() if blob.time_created else None,
                        'updated': blob.updated.isoformat() if blob.updated else None,
                        'metadata': blob.metadata or {}
                    }
                    reports.append(report_info)
            
            logger.info(f"Found {len(reports)} reports in GCS")
            return reports
            
        except Exception as e:
            logger.error(f"Failed to list reports: {e}")
            return []
    
    def cleanup_old_reports(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """Clean up old reports from GCS (keep latest versions)"""
        results = {
            'deleted': [],
            'kept': [],
            'errors': []
        }
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # List all reports
            blobs = self.client.list_blobs(self.bucket, prefix="reports/")
            
            for blob in blobs:
                try:
                    # Skip "latest_" files
                    if "latest_" in blob.name:
                        results['kept'].append(blob.name)
                        continue
                    
                    # Check age
                    if blob.time_created and blob.time_created < cutoff_date:
                        blob.delete()
                        results['deleted'].append(blob.name)
                        logger.info(f"Deleted old report: {blob.name}")
                    else:
                        results['kept'].append(blob.name)
                        
                except Exception as e:
                    logger.error(f"Failed to process {blob.name}: {e}")
                    results['errors'].append(blob.name)
            
            logger.info(f"Cleanup complete: {len(results['deleted'])} deleted, {len(results['kept'])} kept")
            return results
            
        except Exception as e:
            logger.error(f"Failed to cleanup old reports: {e}")
            return results

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description='GCS Backtest Report Synchronization')
    
    parser.add_argument('action', choices=['upload', 'download', 'list', 'cleanup'],
                       help='Action to perform')
    
    parser.add_argument('--source', type=str, default='laptop',
                       choices=['laptop', 'server'],
                       help='Source of the reports (default: laptop)')
    
    parser.add_argument('--report-type', type=str,
                       help='Specific report type to sync')
    
    parser.add_argument('--days-to-keep', type=int, default=30,
                       help='Days to keep for cleanup (default: 30)')
    
    parser.add_argument('--bucket-name', type=str,
                       help='GCS bucket name (default: from environment)')
    
    args = parser.parse_args()
    
    try:
        # Initialize sync client
        sync_client = GCSBacktestSync(bucket_name=args.bucket_name)
        
        if args.action == 'upload':
            logger.info(f"🚀 Uploading local reports to GCS (source: {args.source})")
            results = sync_client.sync_local_reports_to_gcs(source=args.source)
            
            print(f"\n✅ Upload Results:")
            print(f"   📤 Uploaded: {len(results['uploaded'])} reports")
            print(f"   ❌ Failed: {len(results['failed'])} reports")
            print(f"   📊 Total: {results['total']} reports processed")
            
            if results['failed']:
                print(f"\n❌ Failed uploads:")
                for failed in results['failed']:
                    print(f"   - {failed}")
        
        elif args.action == 'download':
            logger.info("📥 Downloading latest reports from GCS for dashboard")
            results = sync_client.download_latest_reports_for_dashboard()
            
            print(f"\n✅ Download Results:")
            print(f"   📥 Downloaded: {len(results['downloaded'])} reports")
            print(f"   ❌ Failed: {len(results['failed'])} reports")
            
            if results['downloaded']:
                print(f"\n📊 Available reports:")
                for report in results['downloaded']:
                    print(f"   - {report}")
        
        elif args.action == 'list':
            logger.info("📋 Listing available reports in GCS")
            reports = sync_client.list_available_reports(report_type=args.report_type)
            
            print(f"\n📋 Available Reports ({len(reports)} total):")
            for report in reports:
                size_mb = report['size'] / (1024 * 1024) if report['size'] else 0
                source = report['metadata'].get('source', 'unknown')
                print(f"   📄 {report['name']}")
                print(f"      Size: {size_mb:.2f} MB | Source: {source}")
                if report['created']:
                    print(f"      Created: {report['created'][:19]}")
        
        elif args.action == 'cleanup':
            logger.info(f"🧹 Cleaning up reports older than {args.days_to_keep} days")
            results = sync_client.cleanup_old_reports(days_to_keep=args.days_to_keep)
            
            print(f"\n🧹 Cleanup Results:")
            print(f"   🗑️  Deleted: {len(results['deleted'])} reports")
            print(f"   ✅ Kept: {len(results['kept'])} reports")
            print(f"   ❌ Errors: {len(results['errors'])} reports")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to execute {args.action}: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
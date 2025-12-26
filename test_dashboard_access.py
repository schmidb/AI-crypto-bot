#!/usr/bin/env python3
"""
Test Dashboard Access

This script tests if the backtesting dashboard can be accessed and loads properly.
"""

import requests
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_dashboard_access():
    """Test if the dashboard is accessible and data files exist"""
    try:
        logger.info("Testing dashboard access...")
        
        # Test if HTTP server is running
        try:
            response = requests.get("http://127.0.0.1:8080/backtesting.html", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Dashboard HTML accessible at http://127.0.0.1:8080/backtesting.html")
                
                # Check if it contains expected content
                if "Backtesting & Optimization" in response.text:
                    logger.info("✅ Dashboard contains expected title")
                else:
                    logger.warning("⚠️ Dashboard title not found in HTML")
                    
            else:
                logger.error(f"❌ Dashboard not accessible: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Cannot connect to dashboard server: {e}")
            logger.info("💡 Make sure the HTTP server is running: python -m http.server 8080 --bind 127.0.0.1")
            return False
        
        # Test if data files exist and are valid JSON
        data_dir = Path("dashboard/data/backtest_results")
        required_files = [
            "latest_backtest.json",
            "data_summary.json", 
            "strategy_comparison.json",
            "latest_optimization.json",
            "latest_walkforward.json",
            "update_status.json"
        ]
        
        for filename in required_files:
            file_path = data_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    logger.info(f"✅ {filename} exists and is valid JSON")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ {filename} is not valid JSON: {e}")
                    return False
            else:
                logger.error(f"❌ Required file missing: {filename}")
                return False
        
        # Test data file accessibility via HTTP
        try:
            response = requests.get("http://127.0.0.1:8080/../data/backtest_results/latest_backtest.json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ Data files accessible via HTTP")
                logger.info(f"✅ Sample data loaded: {len(data.get('individual_results', {}))} strategies")
            else:
                logger.warning(f"⚠️ Data files not accessible via HTTP: {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Could not test HTTP data access: {e}")
        
        logger.info("🎉 Dashboard access test completed successfully!")
        print("\n📊 Dashboard Test Results:")
        print("=" * 50)
        print("✅ Dashboard HTML loads successfully")
        print("✅ All required JSON data files exist")
        print("✅ Data files contain valid JSON")
        print("✅ HTTP server is running properly")
        print("\n🌐 Access the dashboard at:")
        print("http://127.0.0.1:8080/backtesting.html")
        print("\n📁 Data files location:")
        print("dashboard/data/backtest_results/")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in dashboard access test: {e}")
        return False

if __name__ == "__main__":
    success = test_dashboard_access()
    exit(0 if success else 1)
#!/usr/bin/env python3
"""
Generate Live Performance Report

Quick script to generate a live performance report showing actual bot performance
from trading logs (not simulated backtests).

Usage:
    python generate_live_performance_report.py [days]
    
Examples:
    python generate_live_performance_report.py        # Last 7 days (default)
    python generate_live_performance_report.py 14     # Last 14 days
    python generate_live_performance_report.py 30     # Last 30 days
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.monitoring.live_performance_tracker import generate_live_performance_report
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Main function"""
    # Parse arguments
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
            if days < 1 or days > 365:
                print(f"Error: Days must be between 1 and 365")
                sys.exit(1)
        except ValueError:
            print(f"Error: Invalid days argument: {sys.argv[1]}")
            print("Usage: python generate_live_performance_report.py [days]")
            sys.exit(1)
    
    print(f"\n{'='*80}")
    print(f"Generating Live Performance Report - Last {days} Days")
    print(f"{'='*80}\n")
    
    # Generate report
    success = generate_live_performance_report(days)
    
    if success:
        print(f"\n{'='*80}")
        print("✅ Report generated successfully!")
        print(f"{'='*80}\n")
        print("Report saved to:")
        print("  - reports/live_performance/latest_live_performance.json")
        print("  - reports/live_performance/live_performance_YYYYMMDD_HHMMSS.json")
        print()
        sys.exit(0)
    else:
        print(f"\n{'='*80}")
        print("❌ Report generation failed")
        print(f"{'='*80}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()

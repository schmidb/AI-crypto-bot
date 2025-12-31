#!/usr/bin/env python3
"""
Test the daily report generation in console mode
"""

from daily_report import DailyReportGenerator

def main():
    """Test the daily report generation"""
    report_generator = DailyReportGenerator()
    report_generator.generate_and_send_daily_report(test_mode=True)

if __name__ == "__main__":
    main()

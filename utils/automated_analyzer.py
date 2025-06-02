#!/usr/bin/env python3
"""
Automated Strategy Analyzer

This module provides functionality to automatically run strategy analysis
on a scheduled basis and update the dashboard with results.
"""

import os
import json
import logging
from datetime import datetime
import schedule
import time
import threading
from typing import Dict, Any, Optional

# Import the strategy analyzer
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from strategy_analyzer import StrategyAnalyzer

logger = logging.getLogger(__name__)

class AutomatedAnalyzer:
    """Runs strategy analysis automatically and updates dashboard"""
    
    def __init__(self, dashboard_dir: str = "dashboard", reports_dir: str = "reports"):
        """
        Initialize the automated analyzer
        
        Args:
            dashboard_dir: Directory for dashboard files
            reports_dir: Directory for analysis reports
        """
        self.dashboard_dir = dashboard_dir
        self.reports_dir = reports_dir
        self.latest_analysis_file = os.path.join(reports_dir, "latest_analysis.json")
        self.analyzer = StrategyAnalyzer()
        
        # Create necessary directories
        os.makedirs(dashboard_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        
        # Create analysis dashboard page if it doesn't exist
        self._ensure_analysis_page_exists()
    
    def run_analysis(self, days_to_analyze: int = 30) -> Dict[str, Any]:
        """
        Run strategy analysis and update dashboard
        
        Args:
            days_to_analyze: Number of days of historical data to analyze
            
        Returns:
            Analysis results
        """
        try:
            logger.info(f"Running automated strategy analysis for past {days_to_analyze} days")
            
            # Run the analysis
            analysis = self.analyzer.analyze_strategy(days_to_analyze=days_to_analyze)
            
            # Save as latest analysis
            with open(self.latest_analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2, default=str)
            
            # Update the dashboard
            self._update_dashboard_with_analysis(analysis)
            
            logger.info("Automated analysis completed and dashboard updated")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in automated analysis: {e}")
            return {"error": str(e)}
    
    def _ensure_analysis_page_exists(self) -> None:
        """Create analysis dashboard page if it doesn't exist"""
        analysis_html_path = os.path.join(self.dashboard_dir, "analysis.html")
        
        if not os.path.exists(analysis_html_path):
            logger.info("Creating analysis dashboard page")
            
            # Create a basic HTML template for the analysis page
            html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Strategy Analysis</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding: 20px; }
        .analysis-card { margin-bottom: 20px; }
        .recommendation { padding: 10px; margin: 5px 0; background-color: #f8f9fa; border-radius: 5px; }
        .param-adjustment { display: flex; justify-content: space-between; padding: 5px 0; }
        .last-updated { font-style: italic; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <nav class="navbar navbar-expand-lg navbar-light bg-light mb-4">
            <div class="container-fluid">
                <a class="navbar-brand" href="index.html">Crypto Trading Bot</a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link" href="index.html">Dashboard</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link active" href="analysis.html">Strategy Analysis</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <h1 class="mb-4">Trading Strategy Analysis</h1>
        
        <div id="analysis-content">
            <div class="alert alert-info">
                No analysis data available yet. The first analysis will be generated soon.
            </div>
        </div>
        
        <p class="last-updated">Last updated: Never</p>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
            # Write the template to the file
            with open(analysis_html_path, 'w') as f:
                f.write(html_template)
    
    def _update_dashboard_with_analysis(self, analysis: Dict[str, Any]) -> None:
        """
        Update the dashboard with analysis results
        
        Args:
            analysis: Analysis results
        """
        analysis_html_path = os.path.join(self.dashboard_dir, "analysis.html")
        
        try:
            # Read the existing HTML file
            with open(analysis_html_path, 'r') as f:
                html_content = f.read()
            
            # Extract the analysis data
            analysis_text = analysis.get("analysis", "No detailed analysis available.")
            recommendations = analysis.get("recommendations", [])
            successful_patterns = analysis.get("successful_patterns", [])
            unsuccessful_patterns = analysis.get("unsuccessful_patterns", [])
            parameter_adjustments = analysis.get("parameter_adjustments", {})
            market_triggers = analysis.get("market_triggers", [])
            
            # Create HTML content for the analysis
            analysis_html = f"""
            <div class="row">
                <div class="col-md-12">
                    <div class="card analysis-card">
                        <div class="card-header">
                            <h2>Strategy Performance Analysis</h2>
                        </div>
                        <div class="card-body">
                            <p>{analysis_text}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card analysis-card">
                        <div class="card-header">
                            <h3>Successful Trading Patterns</h3>
                        </div>
                        <div class="card-body">
                            <ul class="list-group">
                                {"".join([f'<li class="list-group-item">{pattern}</li>' for pattern in successful_patterns])}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card analysis-card">
                        <div class="card-header">
                            <h3>Unsuccessful Trading Patterns</h3>
                        </div>
                        <div class="card-body">
                            <ul class="list-group">
                                {"".join([f'<li class="list-group-item">{pattern}</li>' for pattern in unsuccessful_patterns])}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-12">
                    <div class="card analysis-card">
                        <div class="card-header">
                            <h3>Recommendations</h3>
                        </div>
                        <div class="card-body">
                            <div class="recommendations">
                                {"".join([f'<div class="recommendation">{i+1}. {rec}</div>' for i, rec in enumerate(recommendations)])}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <div class="card analysis-card">
                        <div class="card-header">
                            <h3>Suggested Parameter Adjustments</h3>
                        </div>
                        <div class="card-body">
                            <div class="parameter-adjustments">
                                {"".join([f'<div class="param-adjustment"><span class="param-name">{param}:</span> <span class="param-value">{value}</span></div>' for param, value in parameter_adjustments.items()])}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card analysis-card">
                        <div class="card-header">
                            <h3>Market Triggers for Strategy Adjustment</h3>
                        </div>
                        <div class="card-body">
                            <ul class="list-group">
                                {"".join([f'<li class="list-group-item">{trigger}</li>' for trigger in market_triggers])}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            """
            
            # Replace the analysis content in the HTML
            updated_html = html_content.replace(
                '<div id="analysis-content">',
                f'<div id="analysis-content">{analysis_html}'
            )
            
            # Update the last updated timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_html = updated_html.replace(
                '<p class="last-updated">Last updated:',
                f'<p class="last-updated">Last updated: {timestamp}'
            )
            
            # Write the updated HTML back to the file
            with open(analysis_html_path, 'w') as f:
                f.write(updated_html)
                
            logger.info(f"Updated analysis dashboard page at {analysis_html_path}")
            
        except Exception as e:
            logger.error(f"Error updating analysis dashboard: {e}")
    
    def start_scheduled_analysis(self, run_time: str = "03:00", days_to_analyze: int = 30) -> None:
        """
        Start scheduled analysis at specified time daily
        
        Args:
            run_time: Time to run analysis daily (24-hour format, e.g., "03:00")
            days_to_analyze: Number of days of historical data to analyze
        """
        logger.info(f"Starting scheduled analysis at {run_time} daily")
        
        # Schedule the analysis to run daily at the specified time
        schedule.every().day.at(run_time).do(self.run_analysis, days_to_analyze=days_to_analyze)
        
        # Run once immediately
        self.run_analysis(days_to_analyze=days_to_analyze)
        
        # Start the scheduler in a separate thread
        scheduler_thread = threading.Thread(target=self._run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
    
    def _run_scheduler(self) -> None:
        """Run the scheduler loop"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def get_automated_analyzer() -> AutomatedAnalyzer:
    """
    Get a singleton instance of the automated analyzer
    
    Returns:
        AutomatedAnalyzer instance
    """
    if not hasattr(get_automated_analyzer, "instance"):
        get_automated_analyzer.instance = AutomatedAnalyzer()
    return get_automated_analyzer.instance

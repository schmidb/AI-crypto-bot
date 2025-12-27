#!/usr/bin/env python3
"""
Simple Daily Report using existing Google Cloud Vertex AI
No additional email setup required - uses existing bot infrastructure
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import subprocess

# Use existing bot imports
from llm_analyzer import LLMAnalyzer
from config import Config

logger = logging.getLogger(__name__)

class SimpleDailyReport:
    def __init__(self):
        self.config = Config()
        # Use existing LLM analyzer
        self.llm_analyzer = LLMAnalyzer()
        
    def analyze_last_24h(self) -> str:
        """Generate comprehensive 24h analysis using existing LLM"""
        try:
            # Get log data
            log_file = "/home/markus/AI-crypto-bot/logs/supervisor.log"
            recent_logs = []
            trades = []
            errors = []
            
            # Read recent entries
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-1000:]:  # Last 1000 lines
                    if '2025-12-27' in line or '2025-12-26' in line:
                        recent_logs.append(line.strip())
                        if 'order executed' in line:
                            trades.append(line.strip())
                        if 'ERROR' in line:
                            errors.append(line.strip())
            
            # Get portfolio
            try:
                with open("/home/markus/AI-crypto-bot/data/portfolio.json", 'r') as f:
                    portfolio = json.load(f)
            except:
                portfolio = {}
            
            # Create analysis prompt
            prompt = f"""
            Analyze this crypto trading bot's 24-hour performance and create an executive summary:

            CURRENT PORTFOLIO:
            - Total Value: €{portfolio.get('portfolio_value_eur', {}).get('amount', 'N/A')}
            - BTC: {portfolio.get('BTC', {}).get('amount', 0):.8f}
            - ETH: {portfolio.get('ETH', {}).get('amount', 0):.6f}  
            - EUR: €{portfolio.get('EUR', {}).get('amount', 0):.2f}

            24H ACTIVITY:
            - Log entries: {len(recent_logs)}
            - Trades executed: {len(trades)}
            - Errors: {len(errors)}

            RECENT TRADES:
            {chr(10).join(trades[-5:]) if trades else "No recent trades"}

            ERRORS (if any):
            {chr(10).join(errors[-3:]) if errors else "No errors"}

            Provide a concise executive summary with:
            1. 🟢/🟡/🔴 Overall health status
            2. Key highlights from last 24h
            3. Portfolio performance
            4. Any concerns or recommendations
            5. Trading activity summary

            Format as a professional daily briefing.
            """
            
            # Use existing LLM analyzer with correct method
            try:
                analysis_result = self.llm_analyzer.analyze_with_llm(prompt)
                if isinstance(analysis_result, dict):
                    return analysis_result.get('reasoning', str(analysis_result))
                else:
                    return str(analysis_result)
            except Exception as llm_error:
                logger.error(f"LLM analysis failed: {llm_error}")
                # Fallback to basic analysis
                return f"""
🤖 CRYPTO BOT DAILY REPORT - {datetime.now().strftime('%Y-%m-%d')}

📊 PORTFOLIO STATUS:
- Total Value: €{portfolio.get('portfolio_value_eur', {}).get('amount', 'N/A')}
- BTC: {portfolio.get('BTC', {}).get('amount', 0):.8f}
- ETH: {portfolio.get('ETH', {}).get('amount', 0):.6f}
- EUR: €{portfolio.get('EUR', {}).get('amount', 0):.2f}

📈 24H ACTIVITY:
- Log entries processed: {len(recent_logs)}
- Trades executed: {len(trades)}
- Errors encountered: {len(errors)}

🔄 RECENT TRADES:
{chr(10).join(['- ' + trade.split(' - ')[-1] if ' - ' in trade else '- ' + trade for trade in trades[-3:]]) if trades else "No recent trades"}

⚠️ ISSUES:
{chr(10).join(['- ' + error.split(' - ')[-1] if ' - ' in error else '- ' + error for error in errors[-2:]]) if errors else "No errors detected"}

🟢 STATUS: {"Active" if len(recent_logs) > 10 else "Low Activity"}

💡 AI Analysis temporarily unavailable - using basic report format.
                """
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            return f"Analysis failed: {str(e)}"
    
    def save_report(self, analysis: str):
        """Save report to file and display"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        report_file = f"/home/markus/AI-crypto-bot/logs/daily_report_{timestamp}.txt"
        
        report_content = f"""
🤖 AI CRYPTO BOT DAILY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}

{analysis}

{'='*50}
Report saved to: {report_file}
        """
        
        # Save to file
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        # Print to console
        print(report_content)
        
        return report_file

def main():
    """Generate and display daily report"""
    print("🤖 Generating Daily Crypto Bot Report...")
    
    reporter = SimpleDailyReport()
    analysis = reporter.analyze_last_24h()
    report_file = reporter.save_report(analysis)
    
    print(f"\n✅ Daily report generated: {report_file}")
    print("💡 To set up email delivery, run: ./setup_daily_reports.sh")

if __name__ == "__main__":
    main()

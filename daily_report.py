#!/usr/bin/env python3
"""
Daily Bot Report Generator using existing Vertex AI setup
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Use existing bot infrastructure
from llm_analyzer import LLMAnalyzer
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DailyReportGenerator:
    def __init__(self):
        self.config = Config()
        # Use gemini-1.5-pro for detailed email reports
        self.llm_analyzer = LLMAnalyzer(model="gemini-1.5-pro")
        
    def analyze_logs_last_24h(self) -> Dict[str, Any]:
        """Analyze bot logs from last 24 hours"""
        try:
            log_file = "/home/markus/AI-crypto-bot/logs/supervisor.log"
            
            recent_logs = []
            trades_executed = []
            errors = []
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-2000:]:  # Last 2000 lines
                    if '2025-12-27' in line or '2025-12-26' in line:
                        recent_logs.append(line.strip())
                        
                        if 'order executed' in line:
                            trades_executed.append(line.strip())
                        
                        if 'ERROR' in line:
                            errors.append(line.strip())
            
            return {
                'total_log_entries': len(recent_logs),
                'trades_executed': trades_executed,
                'errors': errors,
                'recent_logs': recent_logs[-50:]
            }
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return {'error': str(e)}
    
    def get_portfolio_status(self) -> Dict[str, Any]:
        """Get current portfolio status"""
        try:
            portfolio_file = "/home/markus/AI-crypto-bot/data/portfolio.json"
            with open(portfolio_file, 'r') as f:
                portfolio = json.load(f)
            return portfolio
        except Exception as e:
            logger.error(f"Error reading portfolio: {e}")
            return {'error': str(e)}
    
    def generate_ai_analysis(self, log_data: Dict, portfolio: Dict) -> str:
        """Generate AI analysis using existing Vertex AI setup"""
        try:
            prompt = f"""
            Analyze this crypto trading bot's performance over the last 24 hours and provide a concise executive summary:

            PORTFOLIO STATUS:
            - Total Value: €{portfolio.get('portfolio_value_eur', {}).get('amount', 'N/A')}
            - BTC: {portfolio.get('BTC', {}).get('amount', 0):.8f}
            - ETH: {portfolio.get('ETH', {}).get('amount', 0):.6f}
            - EUR: €{portfolio.get('EUR', {}).get('amount', 0):.2f}

            TRADING ACTIVITY (Last 24h):
            - Total log entries: {log_data.get('total_log_entries', 0)}
            - Trades executed: {len(log_data.get('trades_executed', []))}
            - Errors encountered: {len(log_data.get('errors', []))}

            RECENT TRADES:
            {chr(10).join(log_data.get('trades_executed', [])[-3:]) if log_data.get('trades_executed') else "No recent trades"}

            ERRORS (if any):
            {chr(10).join(log_data.get('errors', [])[-2:]) if log_data.get('errors') else "No errors detected"}

            Please provide a professional daily briefing with:
            1. Overall bot health status (🟢 Healthy / 🟡 Warning / 🔴 Critical)
            2. Key highlights from the last 24 hours
            3. Portfolio performance assessment
            4. Any issues or concerns that need attention
            5. Brief trading activity summary

            Keep it concise but informative for a daily executive briefing.
            """
            
            # Use existing LLM analyzer
            response = self.llm_analyzer.analyze_market({
                'prompt': prompt,
                'product_id': 'DAILY-REPORT',
                'current_price': 1.0
            })
            
            if isinstance(response, dict):
                return response.get('reasoning', response.get('analysis', str(response)))
            else:
                return str(response)
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            return f"AI analysis failed: {str(e)}"
    
    def send_email_report(self, subject: str, body: str, to_email: str = "markus@juntoai.org"):
        """Send email report via Gmail SMTP"""
        try:
            # Gmail SMTP configuration
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = os.getenv('GMAIL_USER', 'your-email@gmail.com')
            sender_password = os.getenv('GMAIL_APP_PASSWORD', '')
            
            if not sender_password:
                logger.error("Gmail app password not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, to_email, text)
            server.quit()
            
            logger.info(f"Email report sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def generate_and_send_daily_report(self):
        """Main function to generate and send daily report"""
        try:
            logger.info("Generating daily bot report...")
            
            # Collect data
            log_data = self.analyze_logs_last_24h()
            portfolio = self.get_portfolio_status()
            
            # Generate AI analysis using existing Vertex AI
            ai_analysis = self.generate_ai_analysis(log_data, portfolio)
            
            # Create email content
            subject = f"🤖 Crypto Bot Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""
AI Crypto Trading Bot - Daily Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{ai_analysis}

=== TECHNICAL DETAILS ===

Portfolio Status:
- Total Value: €{portfolio.get('portfolio_value_eur', {}).get('amount', 'N/A')}
- BTC: {portfolio.get('BTC', {}).get('amount', 0):.8f}
- ETH: {portfolio.get('ETH', {}).get('amount', 0):.6f}
- EUR: €{portfolio.get('EUR', {}).get('amount', 0):.2f}
- SOL: {portfolio.get('SOL', {}).get('amount', 0):.6f} (legacy)

24h Activity Summary:
- Log entries processed: {log_data.get('total_log_entries', 0)}
- Trades executed: {len(log_data.get('trades_executed', []))}
- Errors encountered: {len(log_data.get('errors', []))}

Recent Trades:
{chr(10).join([f"- {trade.split('order executed:')[-1].strip()}" for trade in log_data.get('trades_executed', [])[-5:]]) if log_data.get('trades_executed') else "No recent trades"}

Bot Status: {"🟢 Running" if log_data.get('total_log_entries', 0) > 0 else "🔴 Not Active"}

---
This is an automated report from your AI Crypto Trading Bot.
Dashboard: http://your-vm-ip/crypto-bot/
            """
            
            # Send email
            success = self.send_email_report(subject, body)
            
            if success:
                logger.info("Daily report generated and sent successfully")
            else:
                logger.error("Failed to send daily report")
                
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")

def main():
    """Main entry point"""
    report_generator = DailyReportGenerator()
    report_generator.generate_and_send_daily_report()

if __name__ == "__main__":
    main()

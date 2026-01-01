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
        # Use gemini-3-pro-preview for detailed email reports
        self.llm_analyzer = LLMAnalyzer(model="gemini-3-pro-preview")
        
    def analyze_logs_last_24h(self) -> Dict[str, Any]:
        """Analyze bot logs from last 24 hours using new structured logs"""
        try:
            # Use new structured log files for better analysis
            trading_log = "/home/markus/AI-crypto-bot/logs/trading_decisions.log"
            error_log = "/home/markus/AI-crypto-bot/logs/errors.log"
            main_log = "/home/markus/AI-crypto-bot/logs/trading_bot.log"
            
            trades_executed = []
            errors = []
            recent_activity = []
            
            # Get today's date for filtering
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Analyze trading decisions log
            try:
                with open(trading_log, 'r') as f:
                    for line in f:
                        if today in line or yesterday in line:
                            if 'order executed' in line or 'Trade executed' in line:
                                trades_executed.append(line.strip())
            except FileNotFoundError:
                logger.warning("Trading decisions log not found, using main log")
            
            # Analyze errors log
            try:
                with open(error_log, 'r') as f:
                    for line in f:
                        if today in line or yesterday in line:
                            errors.append(line.strip())
            except FileNotFoundError:
                logger.warning("Errors log not found")
            
            # Get recent activity from main log (last 100 lines)
            try:
                with open(main_log, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-100:]:
                        if today in line:
                            recent_activity.append(line.strip())
            except FileNotFoundError:
                # Fallback to supervisor.log
                supervisor_log = "/home/markus/AI-crypto-bot/logs/supervisor.log"
                with open(supervisor_log, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-100:]:
                        if today in line or yesterday in line:
                            recent_activity.append(line.strip())
            
            return {
                'total_log_entries': len(recent_activity),
                'trades_executed': trades_executed,
                'errors': errors,
                'recent_logs': recent_activity[-20:]  # Last 20 entries
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
    
    def get_server_ip(self) -> str:
        """Get the current server's public IP address"""
        try:
            import subprocess
            result = subprocess.run(['curl', '-s', 'ifconfig.me'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception as e:
            logger.warning(f"Could not get public IP: {e}")
        
        # Fallback to hardcoded IP
        return "34.29.9.115"
    
    def calculate_value_changes(self, portfolio: Dict) -> Dict[str, Any]:
        """Calculate portfolio value changes and performance metrics"""
        try:
            current_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
            initial_value = portfolio.get('initial_value_eur', {}).get('amount', 0)
            trades_executed = portfolio.get('trades_executed', 0)
            
            # Calculate trading performance vs buy-and-hold
            trading_performance = self.calculate_trading_vs_holding(portfolio)
            
            if initial_value > 0:
                total_change = current_value - initial_value
                total_change_pct = (total_change / initial_value) * 100
                
                # Determine change type
                if total_change > 0:
                    change_emoji = "📈"
                    change_status = "GAIN"
                elif total_change < 0:
                    change_emoji = "📉"
                    change_status = "LOSS"
                else:
                    change_emoji = "➡️"
                    change_status = "NEUTRAL"
                
                return {
                    'current_value': current_value,
                    'initial_value': initial_value,
                    'total_change': total_change,
                    'total_change_pct': total_change_pct,
                    'change_emoji': change_emoji,
                    'change_status': change_status,
                    'trades_executed': trades_executed,
                    'trading_performance': trading_performance
                }
            else:
                return {
                    'current_value': current_value,
                    'initial_value': 0,
                    'total_change': 0,
                    'total_change_pct': 0,
                    'change_emoji': "➡️",
                    'change_status': "NEUTRAL",
                    'trades_executed': trades_executed,
                    'trading_performance': trading_performance
                }
        except Exception as e:
            logger.error(f"Error calculating value changes: {e}")
            return {
                'current_value': 0,
                'initial_value': 0,
                'total_change': 0,
                'total_change_pct': 0,
                'change_emoji': "❓",
                'change_status': "UNKNOWN",
                'trades_executed': 0,
                'trading_performance': {'status': 'error'}
            }
    
    def calculate_trading_vs_holding(self, portfolio: Dict) -> Dict[str, Any]:
        """Calculate if trading outperformed buy-and-hold strategy"""
        try:
            from coinbase_client import CoinbaseClient
            coinbase_client = CoinbaseClient()
            
            # Get current prices
            btc_price = float(coinbase_client.get_product_ticker('BTC-EUR').get('price', 0))
            eth_price = float(coinbase_client.get_product_ticker('ETH-EUR').get('price', 0))
            sol_price = float(coinbase_client.get_product_ticker('SOL-EUR').get('price', 0))
            
            # Get initial holdings
            initial_btc = portfolio.get('BTC', {}).get('initial_amount', 0)
            initial_eth = portfolio.get('ETH', {}).get('initial_amount', 0)
            initial_sol = portfolio.get('SOL', {}).get('initial_amount', 0)
            initial_eur = portfolio.get('EUR', {}).get('initial_amount', 0)
            
            # Calculate what the portfolio would be worth if we just held (no trading)
            hold_value = (initial_btc * btc_price + 
                         initial_eth * eth_price + 
                         initial_sol * sol_price + 
                         initial_eur)
            
            # Current actual value
            current_value = portfolio.get('portfolio_value_eur', {}).get('amount', 0)
            
            # Trading performance vs holding
            trading_alpha = current_value - hold_value
            trading_alpha_pct = (trading_alpha / hold_value * 100) if hold_value > 0 else 0
            
            # Determine performance
            if trading_alpha > 0:
                performance_emoji = "🎯"
                performance_status = "OUTPERFORMING"
            elif trading_alpha < 0:
                performance_emoji = "📉"
                performance_status = "UNDERPERFORMING"
            else:
                performance_emoji = "➡️"
                performance_status = "NEUTRAL"
            
            return {
                'hold_value': hold_value,
                'current_value': current_value,
                'trading_alpha': trading_alpha,
                'trading_alpha_pct': trading_alpha_pct,
                'performance_emoji': performance_emoji,
                'performance_status': performance_status,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error calculating trading performance: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
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
            
            # Use existing LLM analyzer with real market context
            # Get current market data for context
            try:
                from coinbase_client import CoinbaseClient
                coinbase_client = CoinbaseClient()
                
                # Get current prices for context
                btc_price = coinbase_client.get_product_ticker('BTC-EUR')
                eth_price = coinbase_client.get_product_ticker('ETH-EUR')
                
                market_context = f"""
                Current Market Prices:
                - BTC-EUR: €{btc_price.get('price', 'N/A')}
                - ETH-EUR: €{eth_price.get('price', 'N/A')}
                """
            except Exception as e:
                market_context = "Market data unavailable"
            
            # Create a comprehensive prompt without dummy market analysis
            full_prompt = f"""
Generate a concise daily briefing for a crypto trading bot. Keep it under 300 words, well-formatted with emojis.

PORTFOLIO: €{portfolio.get('portfolio_value_eur', {}).get('amount', 0):.2f} total
- BTC: {portfolio.get('BTC', {}).get('amount', 0):.8f}
- ETH: {portfolio.get('ETH', {}).get('amount', 0):.6f}
- EUR: €{portfolio.get('EUR', {}).get('amount', 0):.2f}

ACTIVITY (24h):
- Trades: {len(log_data.get('trades_executed', []))}
- Errors: {len(log_data.get('errors', []))}

{market_context}

RECENT TRADES:
{chr(10).join([f"• {trade.split('order executed:')[-1].strip()}" for trade in log_data.get('trades_executed', [])[-3:]]) if log_data.get('trades_executed') else "• No recent trades"}

ERRORS:
{chr(10).join([f"• {error}" for error in log_data.get('errors', [])[-2:]]) if log_data.get('errors') else "• No errors"}

Provide:
1. 🟢/🟡/🔴 Health status with brief reason
2. Key highlights (2-3 bullet points)
3. Portfolio performance summary
4. Any concerns that need attention

Format with clear sections and emojis. Be concise and actionable.
            """
            
            # Use the LLM analyzer's client directly with proper prompt
            import google.genai as genai
            from google.genai import types
            
            try:
                response = self.llm_analyzer.client.models.generate_content(
                    model=self.llm_analyzer.model,
                    contents=[full_prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=2000  # Increased token limit
                    )
                )
                
                # Extract text properly
                analysis = None
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content:
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                analysis = candidate.content.parts[0].text
                                break
                
                if not analysis:
                    analysis = "AI analysis completed but no content returned"
                    
            except Exception as e:
                logger.error(f"Direct LLM call failed: {e}")
                analysis = f"AI analysis failed: {str(e)}"
            
            # Format the AI analysis to match the clean email style
            formatted_analysis = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 AI MARKET ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{analysis}"""
            return formatted_analysis
            
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
    
    def generate_and_send_daily_report(self, test_mode=False):
        """Main function to generate and send daily report"""
        try:
            logger.info("Generating daily bot report...")
            
            # Collect data
            log_data = self.analyze_logs_last_24h()
            portfolio = self.get_portfolio_status()
            value_changes = self.calculate_value_changes(portfolio)
            server_ip = self.get_server_ip()
            
            # Generate AI analysis using existing Vertex AI
            ai_analysis = self.generate_ai_analysis(log_data, portfolio)
            
            # Create email content
            subject = f"🤖 Crypto Bot Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Extract key metrics for header
            total_value = value_changes['current_value']
            trades_count = len(log_data.get('trades_executed', []))
            errors_count = len(log_data.get('errors', []))
            
            # Create improved HTML-like formatted email
            body = f"""🤖 AI Crypto Trading Bot - Daily Report
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 PORTFOLIO OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Value: €{total_value:.2f}
Initial Value: €{value_changes['initial_value']:.2f}
{value_changes['change_emoji']} Total Change: €{value_changes['total_change']:+.2f} ({value_changes['total_change_pct']:+.1f}%)
Status: {value_changes['change_status']}

📊 Activity: {trades_count} trades executed | ⚠️ {errors_count} errors detected

{self._format_trading_performance(value_changes['trading_performance'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 ASSET BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💶 EUR Cash: €{portfolio.get('EUR', {}).get('amount', 0):.2f}
🔶 BTC: {portfolio.get('BTC', {}).get('amount', 0):.8f} (~€{portfolio.get('BTC', {}).get('amount', 0) * portfolio.get('BTC', {}).get('last_price_eur', 0):.2f})
💎 ETH: {portfolio.get('ETH', {}).get('amount', 0):.6f} (~€{portfolio.get('ETH', {}).get('amount', 0) * portfolio.get('ETH', {}).get('last_price_eur', 0):.2f})
🟣 SOL: {portfolio.get('SOL', {}).get('amount', 0):.6f} (~€{portfolio.get('SOL', {}).get('amount', 0) * portfolio.get('SOL', {}).get('last_price_eur', 0):.2f})

{ai_analysis}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 QUICK ACCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Dashboard: http://{server_ip}/crypto-bot/
📈 Performance: http://{server_ip}/crypto-bot/performance.html
📋 Logs: http://{server_ip}/crypto-bot/logs.html

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
            """
            
            if test_mode:
                # Print to console instead of sending email
                print("=" * 80)
                print(f"SUBJECT: {subject}")
                print("=" * 80)
                print(body)
                print("=" * 80)
                logger.info("Daily report generated and displayed in console")
                return True
            else:
                # Send email
                success = self.send_email_report(subject, body)
                
                if success:
                    logger.info("Daily report generated and sent successfully")
                else:
                    logger.error("Failed to send daily report")
                    
                return success
                
        except Exception as e:
            logger.error(f"Error generating daily report: {e}")
    
    def _format_trading_performance(self, trading_perf: Dict) -> str:
        """Format trading performance vs buy-and-hold comparison"""
        if trading_perf.get('status') != 'success':
            return ""
        
        return f"""
🎯 Trading Performance vs Buy & Hold:
Hold Value: €{trading_perf['hold_value']:.2f} | Active Value: €{trading_perf['current_value']:.2f}
{trading_perf['performance_emoji']} Trading Alpha: €{trading_perf['trading_alpha']:+.2f} ({trading_perf['trading_alpha_pct']:+.1f}%)
Strategy: {trading_perf['performance_status']}"""

def main():
    """Main entry point"""
    report_generator = DailyReportGenerator()
    report_generator.generate_and_send_daily_report()

if __name__ == "__main__":
    main()

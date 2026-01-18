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

def markdown_to_html(text: str) -> str:
    """Convert simple markdown to HTML for email display"""
    import re
    
    # Convert headers
    text = re.sub(r'^### (.*?)$', r'<h3 style="color: #333; margin: 15px 0 10px 0; font-size: 16px;">\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\* (.*?)$', r'<h4 style="color: #555; margin: 12px 0 8px 0; font-size: 14px; font-weight: bold;">\1</h4>', text, flags=re.MULTILINE)
    
    # Convert bold text
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert bullet points
    text = re.sub(r'^\* (.*?)$', r'<li style="margin: 5px 0;">\1</li>', text, flags=re.MULTILINE)
    
    # Wrap consecutive <li> items in <ul>
    text = re.sub(r'(<li.*?</li>\n?)+', lambda m: f'<ul style="margin: 10px 0; padding-left: 20px;">{m.group(0)}</ul>', text)
    
    # Convert line breaks to paragraphs
    paragraphs = text.split('\n\n')
    formatted_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if p and not p.startswith('<'):
            formatted_paragraphs.append(f'<p style="margin: 10px 0; line-height: 1.6;">{p}</p>')
        else:
            formatted_paragraphs.append(p)
    
    return '\n'.join(formatted_paragraphs)

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
            
            # Convert markdown to HTML for nice email display
            return markdown_to_html(analysis)
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}")
            return f"<p>AI analysis failed: {str(e)}</p>"
    
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
            msg = MIMEMultipart('alternative')
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Create both plain text and HTML versions
            text_part = MIMEText(self._convert_html_to_text(body), 'plain')
            html_part = MIMEText(body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
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
            
            # Get live performance report (actual bot performance)
            live_performance = self.get_live_performance_report()
            
            # Generate AI analysis using existing Vertex AI
            ai_analysis_markdown = self.generate_ai_analysis(log_data, portfolio)
            
            # Convert markdown to HTML for email display
            ai_analysis = markdown_to_html(ai_analysis_markdown)
            
            # Create email content
            subject = f"🤖 Crypto Bot Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Extract key metrics for header
            total_value = value_changes['current_value']
            trades_count = len(log_data.get('trades_executed', []))
            errors_count = len(log_data.get('errors', []))
            
            # Create professional HTML email
            body = self._create_html_email(
                total_value, trades_count, errors_count, 
                portfolio, value_changes, ai_analysis, server_ip, live_performance
            )
            
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
    
    def get_live_performance_report(self) -> Dict[str, Any]:
        """Get live performance report (actual bot performance, not simulated)"""
        try:
            from utils.monitoring.live_performance_tracker import LivePerformanceTracker
            
            tracker = LivePerformanceTracker()
            report = tracker.generate_live_performance_report(days=7)
            
            if 'error' not in report:
                logger.info("Live performance report loaded successfully")
                return report
            else:
                logger.warning(f"Live performance report error: {report.get('error')}")
                return {'status': 'error', 'message': report.get('error')}
                
        except Exception as e:
            logger.error(f"Failed to load live performance report: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _format_trading_performance(self, trading_perf: Dict) -> str:
        """Format trading performance vs buy-and-hold comparison"""
        if trading_perf.get('status') != 'success':
            return ""
        
        return f"""
🎯 Trading Performance vs Buy & Hold:
Hold Value: €{trading_perf['hold_value']:.2f} | Active Value: €{trading_perf['current_value']:.2f}
{trading_perf['performance_emoji']} Trading Alpha: €{trading_perf['trading_alpha']:+.2f} ({trading_perf['trading_alpha_pct']:+.1f}%)
Strategy: {trading_perf['performance_status']}"""

    def _format_live_performance_html(self, live_performance: Dict) -> str:
        """Format live performance report for email (actual bot performance, not simulated)"""
        try:
            strategy_usage = live_performance.get('strategy_usage', {})
            trading_perf = live_performance.get('trading_performance', {})
            
            # Strategy usage stats
            total_decisions = strategy_usage.get('total_decisions', 0)
            actions = strategy_usage.get('action_breakdown', {})
            avg_confidence = strategy_usage.get('average_confidence', 0)
            
            # Trading performance stats
            total_trades = trading_perf.get('total_trades', 0)
            buy_trades = trading_perf.get('buy_trades', 0)
            sell_trades = trading_perf.get('sell_trades', 0)
            trading_freq = trading_perf.get('trading_frequency', 0)
            net_flow = trading_perf.get('net_flow', 0)
            
            net_flow_color = "#28a745" if net_flow >= 0 else "#dc3545"
            
            return f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #007bff;">
                <h3 style="color: #007bff; margin: 0 0 15px 0;">📊 Live Performance (Last 7 Days)</h3>
                <p style="margin: 5px 0; color: #666; font-size: 13px;">
                    <em>⚠️ This shows ACTUAL bot decisions from real Google Gemini API, not simulated backtests</em>
                </p>
                
                <div style="margin: 15px 0;">
                    <strong style="color: #333;">Decision Activity:</strong><br>
                    <span style="color: #666;">Total Decisions: {total_decisions}</span><br>
                    <span style="color: #28a745;">BUY: {actions.get('BUY', 0)}</span> | 
                    <span style="color: #dc3545;">SELL: {actions.get('SELL', 0)}</span> | 
                    <span style="color: #6c757d;">HOLD: {actions.get('HOLD', 0)}</span><br>
                    <span style="color: #666;">Avg Confidence: {avg_confidence:.1f}%</span>
                </div>
                
                <div style="margin: 15px 0;">
                    <strong style="color: #333;">Executed Trades:</strong><br>
                    <span style="color: #666;">Total: {total_trades} trades</span><br>
                    <span style="color: #28a745;">Buys: {buy_trades}</span> | 
                    <span style="color: #dc3545;">Sells: {sell_trades}</span><br>
                    <span style="color: #666;">Frequency: {trading_freq:.2f} trades/day</span><br>
                    <span style="color: {net_flow_color};">Net Flow: €{net_flow:+.2f}</span>
                </div>
                
                <p style="margin: 10px 0 0 0; font-size: 12px; color: #999;">
                    📈 Full report: <code>reports/live_performance/latest_live_performance.json</code>
                </p>
            </div>
            """
        except Exception as e:
            logger.error(f"Error formatting live performance: {e}")
            return ""

    def _create_html_email(self, total_value, trades_count, errors_count, portfolio, value_changes, ai_analysis, server_ip, live_performance=None):
        """Create professional HTML email"""
        # Get asset values
        eur_amount = portfolio.get('EUR', {}).get('amount', 0)
        btc_amount = portfolio.get('BTC', {}).get('amount', 0)
        btc_price = portfolio.get('BTC', {}).get('last_price_eur', 0)
        btc_value = btc_amount * btc_price
        eth_amount = portfolio.get('ETH', {}).get('amount', 0)
        eth_price = portfolio.get('ETH', {}).get('last_price_eur', 0)
        eth_value = eth_amount * eth_price
        sol_amount = portfolio.get('SOL', {}).get('amount', 0)
        sol_price = portfolio.get('SOL', {}).get('last_price_eur', 0)
        sol_value = sol_amount * sol_price
        
        # Status colors
        status_color = "#28a745" if value_changes['total_change'] >= 0 else "#dc3545"
        error_color = "#ffc107" if errors_count > 0 else "#28a745"
        
        # Format live performance section
        live_perf_html = self._format_live_performance_html(live_performance) if live_performance and live_performance.get('status') != 'error' else ""
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Bot Daily Report</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;">
    
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 24px;">🤖 AI Crypto Trading Bot</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">Daily Report - {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    
    <!-- Quick Stats -->
    <div style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 24px; font-weight: bold; color: {status_color};">€{total_value:.2f}</div>
            <div style="font-size: 12px; color: #666;">Portfolio Value</div>
        </div>
        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 24px; font-weight: bold; color: #007bff;">{trades_count}</div>
            <div style="font-size: 12px; color: #666;">Trades (24h)</div>
        </div>
        <div style="flex: 1; min-width: 150px; background: white; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <div style="font-size: 24px; font-weight: bold; color: {error_color};">{errors_count}</div>
            <div style="font-size: 12px; color: #666;">Errors</div>
        </div>
    </div>
    
    <!-- Performance Overview -->
    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="margin: 0 0 15px 0; color: #333; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px;">📊 Performance Overview</h2>
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span>Initial Value:</span>
            <span style="font-weight: bold;">€{value_changes['initial_value']:.2f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span>Current Value:</span>
            <span style="font-weight: bold;">€{total_value:.2f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
            <span>Total Change:</span>
            <span style="font-weight: bold; color: {status_color};">€{value_changes['total_change']:+.2f} ({value_changes['total_change_pct']:+.1f}%)</span>
        </div>
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 15px;">
            {self._format_trading_performance_html(value_changes['trading_performance'])}
        </div>
    </div>
    
    <!-- Asset Breakdown -->
    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="margin: 0 0 15px 0; color: #333; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px;">💎 Asset Breakdown</h2>
        
        <div style="margin-bottom: 15px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: bold;">💶 EUR Cash</span>
                <span style="font-size: 18px; font-weight: bold;">€{eur_amount:.2f}</span>
            </div>
        </div>
        
        <div style="margin-bottom: 15px; padding: 10px; background: #fff3cd; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <span style="font-weight: bold;">🔶 Bitcoin</span>
                <span style="font-size: 18px; font-weight: bold;">€{btc_value:.2f}</span>
            </div>
            <div style="font-size: 12px; color: #666;">
                {btc_amount:.8f} BTC @ €{btc_price:,.0f}
            </div>
        </div>
        
        <div style="margin-bottom: 15px; padding: 10px; background: #d1ecf1; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <span style="font-weight: bold;">💎 Ethereum</span>
                <span style="font-size: 18px; font-weight: bold;">€{eth_value:.2f}</span>
            </div>
            <div style="font-size: 12px; color: #666;">
                {eth_amount:.6f} ETH @ €{eth_price:,.0f}
            </div>
        </div>
        
        {f'''<div style="margin-bottom: 15px; padding: 10px; background: #e2e3ff; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <span style="font-weight: bold;">🟣 Solana</span>
                <span style="font-size: 18px; font-weight: bold;">€{sol_value:.2f}</span>
            </div>
            <div style="font-size: 12px; color: #666;">
                {sol_amount:.6f} SOL @ €{sol_price:,.0f}
            </div>
        </div>''' if sol_amount > 0 else ''}
    </div>
    
    <!-- Live Performance Report -->
    {live_perf_html}
    
    <!-- AI Analysis -->
    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="margin: 0 0 15px 0; color: #333; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px;">🤖 AI Market Analysis</h2>
        <div style="color: #333; line-height: 1.6;">
{ai_analysis}
        </div>
    </div>
    
    <!-- Quick Links -->
    <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h2 style="margin: 0 0 15px 0; color: #333; font-size: 18px; border-bottom: 2px solid #eee; padding-bottom: 10px;">🔗 Quick Access</h2>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
            <a href="http://{server_ip}/crypto-bot/" style="flex: 1; min-width: 150px; background: #007bff; color: white; padding: 12px; text-decoration: none; border-radius: 5px; text-align: center; font-weight: bold;">📊 Dashboard</a>
            <a href="http://{server_ip}/crypto-bot/performance.html" style="flex: 1; min-width: 150px; background: #28a745; color: white; padding: 12px; text-decoration: none; border-radius: 5px; text-align: center; font-weight: bold;">📈 Performance</a>
            <a href="http://{server_ip}/crypto-bot/logs.html" style="flex: 1; min-width: 150px; background: #6c757d; color: white; padding: 12px; text-decoration: none; border-radius: 5px; text-align: center; font-weight: bold;">📋 Logs</a>
        </div>
    </div>
    
    <!-- Footer -->
    <div style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
        Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
    </div>
    
</body>
</html>
        """

    def _format_trading_performance_html(self, trading_perf: Dict) -> str:
        """Format trading performance for HTML email"""
        if trading_perf.get('status') != 'success':
            return "<em>Trading performance data unavailable</em>"
        
        alpha_color = "#28a745" if trading_perf['trading_alpha'] >= 0 else "#dc3545"
        
        return f"""
        <strong>🎯 Trading Performance vs Buy & Hold:</strong><br>
        Hold Value: €{trading_perf['hold_value']:.2f} | Active Value: €{trading_perf['current_value']:.2f}<br>
        <span style="color: {alpha_color}; font-weight: bold;">
            Trading Alpha: €{trading_perf['trading_alpha']:+.2f} ({trading_perf['trading_alpha_pct']:+.1f}%)
        </span><br>
        Strategy: {trading_perf['performance_status']}
        """

    def _convert_html_to_text(self, html_content: str) -> str:
        """Convert HTML email to plain text fallback"""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()

def main():
    """Main entry point"""
    report_generator = DailyReportGenerator()
    report_generator.generate_and_send_daily_report()

if __name__ == "__main__":
    main()

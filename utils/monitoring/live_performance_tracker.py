"""
Live Performance Tracker - Monitor Actual Bot Performance

This module tracks actual trading decisions and outcomes from live bot operation,
providing real performance metrics that cannot be obtained through backtesting.

Unlike backtesting which simulates LLM decisions, this tracks ACTUAL decisions
made by the real Google Gemini API in production.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class LivePerformanceTracker:
    """Track and analyze actual bot performance from live trading"""
    
    def __init__(self, logs_dir: str = "logs", data_dir: str = "data"):
        self.logs_dir = Path(logs_dir)
        self.data_dir = Path(data_dir)
        self.trading_decisions_log = self.logs_dir / "trading_decisions.log"
        
    def load_trading_decisions(self, days: int = 7) -> List[Dict[str, Any]]:
        """Load actual trading decisions from logs"""
        try:
            decisions = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Read trading decisions log
            if not self.trading_decisions_log.exists():
                logger.warning(f"Trading decisions log not found: {self.trading_decisions_log}")
                return decisions
            
            with open(self.trading_decisions_log, 'r') as f:
                for line in f:
                    try:
                        # Parse log line
                        if 'Trade decision logged' in line or 'Analysis for' in line:
                            # Extract timestamp
                            timestamp_str = line.split(' - ')[0]
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                            
                            if timestamp >= cutoff_date:
                                # Parse decision details
                                if 'Analysis for' in line:
                                    # Format: "Analysis for BTC-EUR: BUY (confidence: 79.4%)"
                                    parts = line.split('Analysis for ')[1].split(': ')
                                    product_id = parts[0]
                                    decision_part = parts[1].strip()
                                    
                                    action = decision_part.split(' (')[0]
                                    confidence_str = decision_part.split('confidence: ')[1].split('%')[0]
                                    confidence = float(confidence_str)
                                    
                                    decisions.append({
                                        'timestamp': timestamp.isoformat(),
                                        'product_id': product_id,
                                        'action': action,
                                        'confidence': confidence,
                                        'source': 'analysis'
                                    })
                                    
                    except Exception as e:
                        # Skip malformed lines
                        continue
            
            logger.info(f"Loaded {len(decisions)} trading decisions from last {days} days")
            return decisions
            
        except Exception as e:
            logger.error(f"Failed to load trading decisions: {e}")
            return []
    
    def load_executed_trades(self, days: int = 7) -> List[Dict[str, Any]]:
        """Load actual executed trades from logs"""
        try:
            trades = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if not self.trading_decisions_log.exists():
                return trades
            
            with open(self.trading_decisions_log, 'r') as f:
                for line in f:
                    try:
                        if 'Trade logged:' in line:
                            # Format: "Trade logged: BUY 0.00139365 BTC at €82037.42"
                            timestamp_str = line.split(' - ')[0]
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                            
                            if timestamp >= cutoff_date:
                                trade_part = line.split('Trade logged: ')[1].strip()
                                parts = trade_part.split()
                                
                                action = parts[0]
                                amount = float(parts[1])
                                asset = parts[2]
                                price = float(parts[4].replace('€', '').replace(',', ''))
                                
                                trades.append({
                                    'timestamp': timestamp.isoformat(),
                                    'action': action,
                                    'amount': amount,
                                    'asset': asset,
                                    'price': price,
                                    'value': amount * price
                                })
                    except Exception as e:
                        continue
            
            logger.info(f"Loaded {len(trades)} executed trades from last {days} days")
            return trades
            
        except Exception as e:
            logger.error(f"Failed to load executed trades: {e}")
            return []
    
    def analyze_strategy_usage(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze which strategies are being used"""
        try:
            total_decisions = len(decisions)
            if total_decisions == 0:
                return {'error': 'No decisions to analyze'}
            
            # Count actions
            actions = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            for decision in decisions:
                action = decision.get('action', 'HOLD')
                actions[action] = actions.get(action, 0) + 1
            
            # Calculate confidence stats
            confidences = [d['confidence'] for d in decisions if 'confidence' in d]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'total_decisions': total_decisions,
                'action_breakdown': actions,
                'action_percentages': {
                    action: (count / total_decisions * 100) 
                    for action, count in actions.items()
                },
                'average_confidence': avg_confidence,
                'min_confidence': min(confidences) if confidences else 0,
                'max_confidence': max(confidences) if confidences else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze strategy usage: {e}")
            return {'error': str(e)}
    
    def calculate_actual_performance(self, trades: List[Dict[str, Any]], 
                                    days: int = 7) -> Dict[str, Any]:
        """Calculate actual performance from executed trades"""
        try:
            if not trades:
                return {
                    'total_trades': 0,
                    'note': 'No trades executed in period'
                }
            
            # Separate buys and sells
            buys = [t for t in trades if t['action'] == 'BUY']
            sells = [t for t in trades if t['action'] == 'SELL']
            
            # Calculate totals
            total_buy_value = sum(t['value'] for t in buys)
            total_sell_value = sum(t['value'] for t in sells)
            
            # Calculate by asset
            assets = set(t['asset'] for t in trades)
            asset_performance = {}
            
            for asset in assets:
                asset_buys = [t for t in buys if t['asset'] == asset]
                asset_sells = [t for t in sells if t['asset'] == asset]
                
                asset_performance[asset] = {
                    'buys': len(asset_buys),
                    'sells': len(asset_sells),
                    'buy_value': sum(t['value'] for t in asset_buys),
                    'sell_value': sum(t['value'] for t in asset_sells),
                    'avg_buy_price': sum(t['price'] for t in asset_buys) / len(asset_buys) if asset_buys else 0,
                    'avg_sell_price': sum(t['price'] for t in asset_sells) / len(asset_sells) if asset_sells else 0
                }
            
            return {
                'period_days': days,
                'total_trades': len(trades),
                'buy_trades': len(buys),
                'sell_trades': len(sells),
                'total_buy_value': total_buy_value,
                'total_sell_value': total_sell_value,
                'net_flow': total_sell_value - total_buy_value,
                'asset_performance': asset_performance,
                'trading_frequency': len(trades) / days
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate actual performance: {e}")
            return {'error': str(e)}
    
    def generate_live_performance_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive live performance report"""
        logger.info(f"📊 Generating live performance report for last {days} days...")
        
        # Load data
        decisions = self.load_trading_decisions(days)
        trades = self.load_executed_trades(days)
        
        # Analyze
        strategy_analysis = self.analyze_strategy_usage(decisions)
        performance_analysis = self.calculate_actual_performance(trades, days)
        
        # Load portfolio data
        portfolio_file = self.data_dir / "portfolio.json"
        current_portfolio = {}
        if portfolio_file.exists():
            with open(portfolio_file, 'r') as f:
                current_portfolio = json.load(f)
        
        # Compile report
        report = {
            'timestamp': datetime.now().isoformat(),
            'report_type': 'live_performance',
            'period_days': days,
            'data_source': 'actual_trading_logs',
            'note': 'This report tracks ACTUAL bot decisions and trades, not simulated backtests',
            'strategy_usage': strategy_analysis,
            'trading_performance': performance_analysis,
            'current_portfolio': {
                'total_value_eur': current_portfolio.get('portfolio_value_eur', {}).get('amount', 0),
                'last_updated': current_portfolio.get('last_updated', 'unknown')
            },
            'warnings': [
                "This report shows actual live trading performance",
                "LLM decisions are from real Google Gemini API calls",
                "Performance reflects actual market execution and fees"
            ]
        }
        
        logger.info(f"✅ Live performance report generated: {len(decisions)} decisions, {len(trades)} trades")
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save performance report to file"""
        try:
            reports_dir = Path("reports/live_performance")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"live_performance_{timestamp}.json"
            
            filepath = reports_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            # Also save as latest
            latest_filepath = reports_dir / "latest_live_performance.json"
            with open(latest_filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Report saved to: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return ""


def generate_live_performance_report(days: int = 7) -> bool:
    """
    Generate live performance report - function interface for scheduler
    
    Args:
        days: Number of days to analyze
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        tracker = LivePerformanceTracker()
        report = tracker.generate_live_performance_report(days)
        
        if 'error' in report:
            logger.error(f"Failed to generate report: {report['error']}")
            return False
        
        filepath = tracker.save_report(report)
        logger.info(f"✅ Live performance report saved: {filepath}")
        
        # Print summary
        print("\n" + "="*80)
        print("📊 LIVE PERFORMANCE REPORT")
        print("="*80)
        print(f"Period: Last {days} days")
        print(f"Data Source: Actual trading logs (not simulated)")
        print()
        
        strategy = report.get('strategy_usage', {})
        if 'total_decisions' in strategy:
            print(f"Total Decisions: {strategy['total_decisions']}")
            actions = strategy.get('action_breakdown', {})
            print(f"  BUY: {actions.get('BUY', 0)}")
            print(f"  SELL: {actions.get('SELL', 0)}")
            print(f"  HOLD: {actions.get('HOLD', 0)}")
            print(f"Average Confidence: {strategy.get('average_confidence', 0):.1f}%")
        
        print()
        performance = report.get('trading_performance', {})
        if 'total_trades' in performance:
            print(f"Executed Trades: {performance['total_trades']}")
            print(f"  Buys: {performance.get('buy_trades', 0)}")
            print(f"  Sells: {performance.get('sell_trades', 0)}")
            print(f"Trading Frequency: {performance.get('trading_frequency', 0):.2f} trades/day")
        
        print("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Live performance report generation failed: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print(f"Invalid days argument: {sys.argv[1]}, using default: 7")
    
    # Generate report
    success = generate_live_performance_report(days)
    sys.exit(0 if success else 1)

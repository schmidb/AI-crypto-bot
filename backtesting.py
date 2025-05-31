#!/usr/bin/env python3
"""
Backtesting module for the crypto trading bot
Tests trading strategies against historical data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from data_collector import DataCollector
from coinbase_client import CoinbaseClient

logger = logging.getLogger(__name__)

@dataclass
class BacktestTrade:
    """Class for keeping track of trades in backtesting"""
    timestamp: datetime
    product_id: str
    side: str  # 'buy' or 'sell'
    price: float
    size: float
    value_usd: float
    fee_usd: float = 0.0
    profit_loss_usd: float = 0.0
    profit_loss_percent: float = 0.0
    holding_period_hours: float = 0.0
    market_trend: str = "neutral"

class BacktestResult:
    """Class to store and analyze backtest results"""
    
    def __init__(self, product_id: str, start_date: datetime, end_date: datetime, 
                 initial_balance_usd: float, strategy_name: str):
        """Initialize backtest result"""
        self.product_id = product_id
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance_usd = initial_balance_usd
        self.final_balance_usd = initial_balance_usd
        self.strategy_name = strategy_name
        self.trades = []
        self.price_history = pd.DataFrame()
        self.decisions = []
        self.metrics = {}
        
    def add_trade(self, trade: BacktestTrade):
        """Add a trade to the backtest results"""
        self.trades.append(trade)
        
    def add_decision(self, decision: Dict):
        """Add a trading decision to the backtest results"""
        self.decisions.append(decision)
        
    def set_price_history(self, price_history: pd.DataFrame):
        """Set the price history used in the backtest"""
        self.price_history = price_history
        
    def calculate_metrics(self):
        """Calculate performance metrics for the backtest"""
        if not self.trades:
            logger.warning("No trades to calculate metrics")
            return {}
            
        # Create a DataFrame from trades
        trades_df = pd.DataFrame([vars(t) for t in self.trades])
        
        # Calculate basic metrics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['profit_loss_usd'] > 0])
        losing_trades = len(trades_df[trades_df['profit_loss_usd'] < 0])
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Calculate returns
        total_profit_loss = sum(t.profit_loss_usd for t in self.trades)
        self.final_balance_usd = self.initial_balance_usd + total_profit_loss
        
        total_return_percent = (self.final_balance_usd / self.initial_balance_usd - 1) * 100 if self.initial_balance_usd > 0 else 0
        
        # Calculate other metrics
        avg_profit_per_trade = total_profit_loss / total_trades if total_trades > 0 else 0
        avg_win = trades_df[trades_df['profit_loss_usd'] > 0]['profit_loss_usd'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['profit_loss_usd'] < 0]['profit_loss_usd'].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(trades_df[trades_df['profit_loss_usd'] > 0]['profit_loss_usd'].sum() / 
                           trades_df[trades_df['profit_loss_usd'] < 0]['profit_loss_usd'].sum()) if losing_trades > 0 else float('inf')
        
        # Store metrics
        self.metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit_loss_usd': total_profit_loss,
            'total_return_percent': total_return_percent,
            'profit_factor': profit_factor,
            'avg_profit_per_trade': avg_profit_per_trade,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'initial_balance_usd': self.initial_balance_usd,
            'final_balance_usd': self.final_balance_usd
        }
        
        return self.metrics
        
    def save_results(self, output_file: str):
        """Save backtest results to a JSON file"""
        if not self.metrics:
            self.calculate_metrics()
            
        # Create a dictionary with all results
        results = {
            'product_id': self.product_id,
            'strategy_name': self.strategy_name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_balance_usd': self.initial_balance_usd,
            'final_balance_usd': self.final_balance_usd,
            'metrics': self.metrics,
            'trades': [vars(t) for t in self.trades],
            'decisions': self.decisions
        }
        
        # Convert datetime objects to strings
        results_json = json.dumps(results, default=str, indent=2)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(results_json)
            
        logger.info(f"Saved backtest results to {output_file}")
        return True

class Backtester:
    """Class for backtesting trading strategies"""
    
    def __init__(self, data_collector: DataCollector):
        """Initialize backtester with data collector"""
        self.data_collector = data_collector
        logger.info("Backtester initialized")
        
    def run_backtest(self, product_id: str, start_date: datetime, end_date: datetime, 
                    initial_balance_usd: float = 10000.0, trade_size_usd: float = 1000.0,
                    strategy_name: str = "Default Strategy"):
        """
        Run a backtest for a specific product and time period
        
        Args:
            product_id: Trading pair (e.g., 'BTC-USD')
            start_date: Start date for the backtest
            end_date: End date for the backtest
            initial_balance_usd: Initial account balance in USD
            trade_size_usd: Size of each trade in USD
            strategy_name: Name of the strategy being tested
            
        Returns:
            BacktestResult object with test results
        """
        logger.info(f"Starting backtest for {product_id} from {start_date} to {end_date}")
        
        # Initialize result object
        result = BacktestResult(
            product_id=product_id,
            start_date=start_date,
            end_date=end_date,
            initial_balance_usd=initial_balance_usd,
            strategy_name=strategy_name
        )
        
        # Get historical data
        historical_data = self._get_historical_data(product_id, start_date, end_date)
        
        if historical_data.empty:
            logger.error(f"No historical data available for {product_id}")
            return result
            
        # Set price history in result
        result.set_price_history(historical_data)
        
        # Initialize variables for tracking position
        in_position = False
        position_size = 0.0
        entry_price = 0.0
        entry_time = None
        base_balance = 0.0  # Amount of crypto
        quote_balance = initial_balance_usd  # Amount of USD
        
        # Process each day in the historical data
        current_date = start_date
        day_increment = timedelta(days=1)
        
        while current_date <= end_date:
            # Get data up to current date
            data_slice = historical_data[historical_data.index <= current_date]
            
            if data_slice.empty:
                current_date += day_increment
                continue
                
            # Get the latest price
            current_price = data_slice['close'].iloc[-1]
            
            # Execute strategy
            decision = self._simplified_decision_logic(product_id, current_date, data_slice)
            
            # Add decision to results
            decision['timestamp'] = current_date
            decision['price'] = current_price
            result.add_decision(decision)
            
            # Execute trades based on decision
            if decision['decision'] == 'BUY' and not in_position and quote_balance >= trade_size_usd:
                # Calculate trade details
                size = trade_size_usd / current_price
                fee = trade_size_usd * 0.005  # Assuming 0.5% fee
                
                # Create trade object
                trade = BacktestTrade(
                    timestamp=current_date,
                    product_id=product_id,
                    side='buy',
                    price=current_price,
                    size=size,
                    value_usd=trade_size_usd,
                    fee_usd=fee,
                    market_trend=decision.get('market_trend', 'neutral')
                )
                
                # Update position
                in_position = True
                position_size = size
                entry_price = current_price
                entry_time = current_date
                
                # Update balances
                quote_balance -= (trade_size_usd + fee)
                base_balance += size
                
                # Add trade to results
                result.add_trade(trade)
                logger.info(f"BUY: {size} {product_id.split('-')[0]} at ${current_price}")
                
            elif decision['decision'] == 'SELL' and in_position:
                # Calculate trade details
                value_usd = position_size * current_price
                fee = value_usd * 0.005  # Assuming 0.5% fee
                
                # Calculate profit/loss
                profit_loss_usd = value_usd - (position_size * entry_price) - fee
                profit_loss_percent = (profit_loss_usd / (position_size * entry_price)) * 100
                
                # Calculate holding period
                holding_period_hours = (current_date - entry_time).total_seconds() / 3600
                
                # Create trade object
                trade = BacktestTrade(
                    timestamp=current_date,
                    product_id=product_id,
                    side='sell',
                    price=current_price,
                    size=position_size,
                    value_usd=value_usd,
                    fee_usd=fee,
                    profit_loss_usd=profit_loss_usd,
                    profit_loss_percent=profit_loss_percent,
                    holding_period_hours=holding_period_hours,
                    market_trend=decision.get('market_trend', 'neutral')
                )
                
                # Update position
                in_position = False
                
                # Update balances
                quote_balance += (value_usd - fee)
                base_balance = 0
                
                # Add trade to results
                result.add_trade(trade)
                logger.info(f"SELL: {position_size} {product_id.split('-')[0]} at ${current_price}, P/L: ${profit_loss_usd:.2f} ({profit_loss_percent:.2f}%)")
                
            # Move to next day
            current_date += day_increment
            
        # If still in position at the end, perform a final sell
        if in_position:
            final_price = historical_data['close'].iloc[-1]
            value_usd = position_size * final_price
            fee = value_usd * 0.005
            
            profit_loss_usd = value_usd - (position_size * entry_price) - fee
            profit_loss_percent = (profit_loss_usd / (position_size * entry_price)) * 100
            holding_period_hours = (end_date - entry_time).total_seconds() / 3600
            
            trade = BacktestTrade(
                timestamp=end_date,
                product_id=product_id,
                side='sell',
                price=final_price,
                size=position_size,
                value_usd=value_usd,
                fee_usd=fee,
                profit_loss_usd=profit_loss_usd,
                profit_loss_percent=profit_loss_percent,
                holding_period_hours=holding_period_hours,
                market_trend='neutral'
            )
            
            result.add_trade(trade)
            quote_balance += (value_usd - fee)
            
            logger.info(f"Final SELL: {position_size} {product_id.split('-')[0]} at ${final_price}, P/L: ${profit_loss_usd:.2f} ({profit_loss_percent:.2f}%)")
            
        # Calculate final metrics
        result.final_balance_usd = quote_balance + (base_balance * historical_data['close'].iloc[-1])
        result.calculate_metrics()
        
        logger.info(f"Backtest completed. Final balance: ${result.final_balance_usd:.2f}, Return: {result.metrics['total_return_percent']:.2f}%")
        
        return result
    
    def _get_historical_data(self, product_id: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical data for the specified period"""
        try:
            # Calculate days between start and end
            days = (end_date - start_date).days
            
            # Get data with daily granularity
            df = self.data_collector.get_historical_data(
                product_id=product_id,
                granularity="ONE_DAY",
                days_back=days + 10  # Add buffer for calculations
            )
            
            if df.empty:
                logger.error(f"No historical data retrieved for {product_id}")
                return pd.DataFrame()
                
            # Filter to the requested date range
            df = df[(df['start'] >= start_date) & (df['start'] <= end_date)]
            
            # Set index to datetime for easier slicing
            df = df.set_index('start')
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return pd.DataFrame()
    
    def _simplified_decision_logic(self, product_id: str, current_date: datetime, historical_data: pd.DataFrame) -> Dict:
        """
        Simplified decision logic for backtesting
        This mimics the LLM's decision making without actually calling the API
        """
        try:
            # Calculate technical indicators
            indicators = self.data_collector.calculate_technical_indicators(historical_data)
            
            # Get the current price
            current_price = historical_data['close'].iloc[-1]
            
            # Extract key indicators
            rsi = indicators.get("rsi", 50)
            macd_histogram = indicators.get("macd_histogram", 0)
            bollinger_lower = indicators.get("bollinger_lower", current_price * 0.98)
            bollinger_upper = indicators.get("bollinger_upper", current_price * 1.02)
            market_trend = indicators.get("market_trend", "neutral")
            
            decision = "HOLD"
            confidence = 50
            reasoning = []
            
            # Oversold conditions (buy signals)
            if rsi < 30:
                decision = "BUY"
                confidence += 20
                reasoning.append(f"RSI is oversold at {rsi:.2f}")
                
            if current_price < bollinger_lower:
                decision = "BUY"
                confidence += 15
                reasoning.append(f"Price below lower Bollinger Band")
                
            if macd_histogram > 0 and market_trend == "bullish":
                decision = "BUY"
                confidence += 15
                reasoning.append(f"Positive MACD histogram in bullish trend")
                
            # Overbought conditions (sell signals)
            if rsi > 70:
                decision = "SELL"
                confidence += 20
                reasoning.append(f"RSI is overbought at {rsi:.2f}")
                
            if current_price > bollinger_upper:
                decision = "SELL"
                confidence += 15
                reasoning.append(f"Price above upper Bollinger Band")
                
            if macd_histogram < 0 and market_trend == "bearish":
                decision = "SELL"
                confidence += 15
                reasoning.append(f"Negative MACD histogram in bearish trend")
                
            # Cap confidence at 95%
            confidence = min(confidence, 95)
            
            return {
                "decision": decision,
                "confidence": confidence,
                "market_trend": market_trend,
                "reasoning": reasoning
            }
            
        except Exception as e:
            logger.error(f"Error in decision logic: {e}")
            return {"decision": "HOLD", "confidence": 0, "market_trend": "neutral"}

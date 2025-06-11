#!/usr/bin/env python3
"""
Strategy Analyzer Script

This script analyzes the trading strategy performance by feeding historical data
to the LLM and getting recommendations for improvements.
"""

import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any

from llm_analyzer import LLMAnalyzer
from utils.strategy_evaluator import StrategyEvaluator
from utils.trade_logger import TradeLogger
from trading_strategy import TradingStrategy
from coinbase_client import CoinbaseClient
from data_collector import DataCollector
from config import TRADING_PAIRS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/strategy_analysis_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class StrategyAnalyzer:
    """Analyzes trading strategy performance and gets AI recommendations"""
    
    def __init__(self):
        """Initialize the strategy analyzer"""
        logger.info("Initializing strategy analyzer")
        
        # Initialize components
        self.coinbase_client = CoinbaseClient()
        self.llm_analyzer = LLMAnalyzer()
        self.data_collector = DataCollector(self.coinbase_client)
        self.trading_strategy = TradingStrategy(config)
        self.strategy_evaluator = StrategyEvaluator()
        self.trade_logger = TradeLogger()
        
    def get_performance_data(self) -> Dict[str, Any]:
        """
        Get comprehensive performance data for analysis
        
        Returns:
            Dictionary with performance metrics and trade history
        """
        # Get performance history
        performance_history = self.strategy_evaluator.get_performance_history()
        
        # Get recent trades for each trading pair
        trades = {}
        for product_id in TRADING_PAIRS:
            trades[product_id] = self.trade_logger.get_trades_by_product(product_id)
        
        # Get current portfolio
        portfolio = self.trading_strategy.portfolio
        
        # Combine all data
        return {
            "performance_history": performance_history,
            "trades": trades,
            "current_portfolio": portfolio
        }
    
    def analyze_strategy(self, days_to_analyze: int = 30) -> Dict[str, Any]:
        """
        Analyze trading strategy and get AI recommendations
        
        Args:
            days_to_analyze: Number of days of historical data to analyze
            
        Returns:
            Dictionary with analysis and recommendations
        """
        logger.info(f"Analyzing strategy performance for the past {days_to_analyze} days")
        
        # Get performance data
        performance_data = self.get_performance_data()
        
        # Create prompt for LLM analysis
        prompt = self._create_analysis_prompt(performance_data, days_to_analyze)
        
        # Get LLM response
        logger.info("Sending performance data to LLM for analysis")
        response = self.llm_analyzer._get_llm_response(prompt)
        
        # Parse response
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                analysis_result = json.loads(json_str)
            else:
                logger.warning(f"Could not find JSON in response: {response}")
                analysis_result = {
                    "analysis": response,
                    "recommendations": ["Could not parse structured recommendations"],
                    "parameter_adjustments": {}
                }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON from response")
            analysis_result = {
                "analysis": response,
                "recommendations": ["Could not parse structured recommendations"],
                "parameter_adjustments": {}
            }
        
        # Save analysis to file
        self._save_analysis(analysis_result)
        
        return analysis_result
    
    def _create_analysis_prompt(self, performance_data: Dict[str, Any], days_to_analyze: int) -> str:
        """
        Create prompt for LLM analysis
        
        Args:
            performance_data: Dictionary with performance metrics and trade history
            days_to_analyze: Number of days to analyze
            
        Returns:
            Prompt string for LLM
        """
        # Extract key metrics for the prompt
        latest_metrics = performance_data["performance_history"].get("latest", {})
        total_return = latest_metrics.get("total_return_pct", 0)
        portfolio_value = latest_metrics.get("portfolio_value_usd", 0)
        allocations = latest_metrics.get("allocations", {})
        
        # Count trades by action
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        for product_id, product_trades in performance_data["trades"].items():
            for trade in product_trades:
                action = trade.get("action", "").lower()
                if action == "buy":
                    buy_count += 1
                elif action == "sell":
                    sell_count += 1
                elif action == "hold":
                    hold_count += 1
        
        # Create prompt
        prompt = f"""
        You are an expert cryptocurrency trading strategy analyst. Your task is to analyze the performance of an AI-powered 
        crypto trading bot and provide recommendations for improving its strategy.

        The bot has been trading for the past {days_to_analyze} days with the following performance:
        
        PERFORMANCE SUMMARY:
        - Total Return: {total_return}%
        - Current Portfolio Value: ${portfolio_value}
        - Asset Allocation: {json.dumps(allocations)}
        - Total Trades: {buy_count + sell_count + hold_count}
        - Buy Trades: {buy_count}
        - Sell Trades: {sell_count}
        - Hold Decisions: {hold_count}
        
        DETAILED PERFORMANCE DATA:
        {json.dumps(performance_data, indent=2, default=str)}
        
        Based on this data, please provide:
        
        1. A detailed analysis of the trading strategy performance
        2. Identification of patterns in successful and unsuccessful trades
        3. Specific recommendations to improve the strategy
        4. Suggested parameter adjustments (risk levels, trade sizes, etc.)
        5. Any market conditions or indicators that should trigger strategy adjustments
        
        Format your response as JSON with the following structure:
        {{
            "analysis": "Your detailed analysis here",
            "successful_patterns": ["List of patterns in successful trades"],
            "unsuccessful_patterns": ["List of patterns in unsuccessful trades"],
            "recommendations": ["List of specific recommendations"],
            "parameter_adjustments": {{
                "param_name": "suggested_value",
                ...
            }},
            "market_triggers": ["List of market conditions that should trigger strategy adjustments"]
        }}
        """
        
        return prompt
    
    def _save_analysis(self, analysis: Dict[str, Any]) -> None:
        """
        Save analysis to file
        
        Args:
            analysis: Dictionary with analysis and recommendations
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/strategy_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        logger.info(f"Analysis saved to {filename}")


def main():
    """Main function to run the strategy analyzer"""
    parser = argparse.ArgumentParser(description="Analyze trading strategy performance")
    parser.add_argument("--days", type=int, default=30, help="Number of days of historical data to analyze")
    args = parser.parse_args()
    
    analyzer = StrategyAnalyzer()
    analysis = analyzer.analyze_strategy(days_to_analyze=args.days)
    
    print("\n=== STRATEGY ANALYSIS SUMMARY ===\n")
    print(f"Analysis saved to reports/strategy_analysis_*.json")
    print("\nKey Recommendations:")
    for i, rec in enumerate(analysis.get("recommendations", []), 1):
        print(f"{i}. {rec}")
    
    print("\nSuggested Parameter Adjustments:")
    for param, value in analysis.get("parameter_adjustments", {}).items():
        print(f"- {param}: {value}")


if __name__ == "__main__":
    main()

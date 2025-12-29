#!/usr/bin/env python3
"""
Test Fixed Backtest - Quick test of the fixed strategy vectorization with a simple backtest
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import sys

# Add project root to path
sys.path.append('.')

from utils.performance.indicator_factory import IndicatorFactory
from utils.backtest.strategy_vectorizer import VectorizedStrategyAdapter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simple_backtest(data: pd.DataFrame, signals: pd.DataFrame, initial_capital: float = 10000.0) -> dict:
    """
    Simple backtest implementation without VectorBT to avoid pandas boolean issues
    """
    try:
        # Align data and signals
        common_index = data.index.intersection(signals.index)
        if len(common_index) == 0:
            return {"error": "No common timestamps", "total_return": 0, "total_trades": 0}
        
        aligned_data = data.loc[common_index]
        aligned_signals = signals.loc[common_index]
        
        # Simple backtest logic
        cash = initial_capital
        position = 0.0  # BTC position
        trades = []
        portfolio_values = []
        
        for timestamp, row in aligned_data.iterrows():
            # Safe conversion to avoid pandas Series issues
            price = float(row['close'].item() if hasattr(row['close'], 'item') else row['close'])
            buy_signal = bool(aligned_signals.loc[timestamp, 'buy'])
            sell_signal = bool(aligned_signals.loc[timestamp, 'sell'])
            
            # Execute trades
            if buy_signal and cash > 100:  # Minimum $100 trade
                # Buy with 30% of available cash
                trade_amount = cash * 0.3
                btc_bought = trade_amount / price * 0.994  # 0.6% fee
                position += btc_bought
                cash -= trade_amount
                trades.append({"type": "BUY", "price": price, "amount": btc_bought, "timestamp": timestamp})
                
            elif sell_signal and position > 0.001:  # Minimum 0.001 BTC
                # Sell 50% of position
                btc_to_sell = position * 0.5
                cash_received = btc_to_sell * price * 0.994  # 0.6% fee
                position -= btc_to_sell
                cash += cash_received
                trades.append({"type": "SELL", "price": price, "amount": btc_to_sell, "timestamp": timestamp})
            
            # Calculate portfolio value
            portfolio_value = cash + (position * price)
            portfolio_values.append(portfolio_value)
        
        # Calculate results
        final_value = portfolio_values[-1] if portfolio_values else initial_capital
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # Calculate buy & hold comparison
        start_price = float(aligned_data.iloc[0]['close'].item() if hasattr(aligned_data.iloc[0]['close'], 'item') else aligned_data.iloc[0]['close'])
        end_price = float(aligned_data.iloc[-1]['close'].item() if hasattr(aligned_data.iloc[-1]['close'], 'item') else aligned_data.iloc[-1]['close'])
        buy_hold_return = ((end_price - start_price) / start_price) * 100
        
        return {
            "initial_capital": initial_capital,
            "final_value": final_value,
            "total_return": total_return,
            "total_trades": len(trades),
            "buy_trades": len([t for t in trades if t["type"] == "BUY"]),
            "sell_trades": len([t for t in trades if t["type"] == "SELL"]),
            "buy_hold_return": buy_hold_return,
            "outperformance": total_return - buy_hold_return,
            "data_points": len(aligned_data),
            "period_days": (aligned_data.index[-1] - aligned_data.index[0]).days
        }
        
    except Exception as e:
        logger.error(f"Simple backtest error: {e}")
        return {"error": str(e), "total_return": 0, "total_trades": 0}

def main():
    """Test the fixed backtesting system"""
    try:
        logger.info("=== TESTING FIXED BACKTESTING SYSTEM ===")
        
        # Load historical data
        df = pd.read_parquet('data/historical/BTC-USD_hour_180d.parquet')
        logger.info(f"Loaded {len(df)} rows of historical data")
        
        # Calculate indicators
        indicator_factory = IndicatorFactory()
        indicators_df = indicator_factory.calculate_all_indicators(df, "BTC-USD")
        
        # Combine data and indicators
        combined_df = pd.concat([df, indicators_df], axis=1)
        logger.info(f"Combined data has {len(combined_df.columns)} columns")
        
        # Initialize fixed vectorizer
        vectorizer = VectorizedStrategyAdapter()
        
        # Test each strategy
        strategies = ['momentum', 'mean_reversion', 'trend_following']
        results = {}
        
        for strategy_name in strategies:
            logger.info(f"\n=== TESTING {strategy_name.upper()} STRATEGY ===")
            
            # Generate signals
            signals_df = vectorizer.vectorize_strategy(strategy_name, combined_df, "BTC-USD")
            
            buy_signals = int(signals_df['buy'].sum())
            sell_signals = int(signals_df['sell'].sum())
            avg_confidence = float(signals_df['confidence'].mean())
            
            logger.info(f"Signals: {buy_signals} buys, {sell_signals} sells, {avg_confidence:.1f}% avg confidence")
            
            if buy_signals > 0 or sell_signals > 0:
                # Run simple backtest
                backtest_result = simple_backtest(combined_df, signals_df)
                results[strategy_name] = backtest_result
                
                logger.info(f"Backtest Results:")
                logger.info(f"  Total Return: {backtest_result['total_return']:.2f}%")
                logger.info(f"  Buy & Hold: {backtest_result['buy_hold_return']:.2f}%")
                logger.info(f"  Outperformance: {backtest_result['outperformance']:.2f}%")
                logger.info(f"  Total Trades: {backtest_result['total_trades']}")
                
            else:
                logger.warning(f"No signals generated for {strategy_name}")
                results[strategy_name] = {"error": "No signals", "total_return": 0}
        
        # Summary
        logger.info(f"\n=== SUMMARY ===")
        working_strategies = [s for s, r in results.items() if "error" not in r]
        logger.info(f"Working strategies: {len(working_strategies)}/{len(strategies)}")
        
        if working_strategies:
            best_strategy = max(working_strategies, key=lambda s: results[s]['total_return'])
            logger.info(f"Best performing strategy: {best_strategy} ({results[best_strategy]['total_return']:.2f}% return)")
            
            print(f"\n🎉 SUCCESS: Fixed backtesting system is working!")
            print(f"✅ {len(working_strategies)} strategies generating signals and returns")
            print(f"🏆 Best strategy: {best_strategy} with {results[best_strategy]['total_return']:.2f}% return")
        else:
            print(f"\n❌ Issues remain: No strategies producing valid results")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ TEST FAILED: {e}")

if __name__ == "__main__":
    main()
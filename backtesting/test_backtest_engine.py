#!/usr/bin/env python3
"""
Test script for the backtest engine
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from utils.performance.indicator_factory import calculate_indicators
from utils.backtest.backtest_engine import BacktestEngine, quick_backtest

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_simple_strategy_signals(data: pd.DataFrame, rsi_buy_threshold: float = 30, 
                                 rsi_sell_threshold: float = 70) -> pd.DataFrame:
    """
    Create simple RSI-based buy/sell signals for testing
    
    Args:
        data: DataFrame with indicators
        rsi_buy_threshold: RSI level to trigger buy (oversold)
        rsi_sell_threshold: RSI level to trigger sell (overbought)
        
    Returns:
        DataFrame with buy/sell signals
    """
    signals = pd.DataFrame(index=data.index)
    
    if 'rsi_14' not in data.columns:
        logger.warning("RSI not available, creating random signals for testing")
        # Create some random signals for testing
        np.random.seed(42)
        signals['buy'] = np.random.random(len(data)) < 0.05  # 5% chance of buy
        signals['sell'] = np.random.random(len(data)) < 0.05  # 5% chance of sell
    else:
        # RSI-based strategy
        rsi = data['rsi_14']
        
        # Buy when RSI is oversold and rising
        buy_condition = (rsi < rsi_buy_threshold) & (rsi > rsi.shift(1))
        
        # Sell when RSI is overbought and falling
        sell_condition = (rsi > rsi_sell_threshold) & (rsi < rsi.shift(1))
        
        signals['buy'] = buy_condition
        signals['sell'] = sell_condition
    
    # Ensure no simultaneous buy/sell
    simultaneous = signals['buy'] & signals['sell']
    signals.loc[simultaneous, ['buy', 'sell']] = False
    
    return signals

def create_macd_strategy_signals(data: pd.DataFrame) -> pd.DataFrame:
    """Create MACD crossover strategy signals"""
    signals = pd.DataFrame(index=data.index)
    
    if 'macd' not in data.columns or 'macd_signal' not in data.columns:
        logger.warning("MACD not available, using RSI strategy instead")
        return create_simple_strategy_signals(data)
    
    macd = data['macd']
    macd_signal = data['macd_signal']
    
    # Buy when MACD crosses above signal line
    buy_condition = (macd > macd_signal) & (macd.shift(1) <= macd_signal.shift(1))
    
    # Sell when MACD crosses below signal line
    sell_condition = (macd < macd_signal) & (macd.shift(1) >= macd_signal.shift(1))
    
    signals['buy'] = buy_condition
    signals['sell'] = sell_condition
    
    return signals

def test_backtest_engine():
    """Test the backtest engine with real data"""
    
    try:
        # Load historical data
        data_dir = Path("./data/historical")
        btc_file = data_dir / "BTC-USD_hourly_30d.parquet"
        
        if not btc_file.exists():
            logger.error(f"BTC data file not found: {btc_file}")
            logger.info("Please run sync_historical_data.py first")
            return False
        
        # Load and prepare data
        logger.info("Loading BTC historical data...")
        btc_data = pd.read_parquet(btc_file)
        logger.info(f"Loaded {len(btc_data)} rows of BTC data")
        
        # Calculate indicators
        logger.info("Calculating indicators...")
        btc_with_indicators = calculate_indicators(btc_data, "BTC-USD")
        logger.info(f"Added {len(btc_with_indicators.columns) - len(btc_data.columns)} indicators")
        
        # Test 1: Simple RSI Strategy
        logger.info("\n=== Test 1: RSI Strategy ===")
        rsi_signals = create_simple_strategy_signals(btc_with_indicators, rsi_buy_threshold=30, rsi_sell_threshold=70)
        
        logger.info(f"RSI Strategy signals: {rsi_signals['buy'].sum()} buys, {rsi_signals['sell'].sum()} sells")
        
        # Run backtest
        engine = BacktestEngine(initial_capital=10000.0, fees=0.006, slippage=0.0005)
        rsi_results = engine.run_backtest(btc_with_indicators, rsi_signals, "BTC-USD-RSI")
        
        # Display results
        logger.info("RSI Strategy Results:")
        logger.info(f"  Total Return: {rsi_results['total_return']:.2f}%")
        logger.info(f"  Annual Return: {rsi_results['annual_return']:.2f}%")
        logger.info(f"  Sharpe Ratio: {rsi_results['sharpe_ratio']:.3f}")
        logger.info(f"  Sortino Ratio: {rsi_results['sortino_ratio']:.3f}")
        logger.info(f"  Max Drawdown: {rsi_results['max_drawdown']:.2f}%")
        logger.info(f"  Total Trades: {rsi_results['total_trades']}")
        logger.info(f"  Win Rate: {rsi_results['win_rate']:.1f}%")
        logger.info(f"  Fees Paid: ${rsi_results['fees_paid']:.2f}")
        
        # Test 2: MACD Strategy
        logger.info("\n=== Test 2: MACD Strategy ===")
        macd_signals = create_macd_strategy_signals(btc_with_indicators)
        
        logger.info(f"MACD Strategy signals: {macd_signals['buy'].sum()} buys, {macd_signals['sell'].sum()} sells")
        
        macd_results = engine.run_backtest(btc_with_indicators, macd_signals, "BTC-USD-MACD")
        
        logger.info("MACD Strategy Results:")
        logger.info(f"  Total Return: {macd_results['total_return']:.2f}%")
        logger.info(f"  Sharpe Ratio: {macd_results['sharpe_ratio']:.3f}")
        logger.info(f"  Max Drawdown: {macd_results['max_drawdown']:.2f}%")
        logger.info(f"  Total Trades: {macd_results['total_trades']}")
        logger.info(f"  Win Rate: {macd_results['win_rate']:.1f}%")
        
        # Test 3: Quick Backtest Function
        logger.info("\n=== Test 3: Quick Backtest Function ===")
        
        # Create simple buy and hold strategy
        buy_and_hold_buy = pd.Series(False, index=btc_data.index)
        buy_and_hold_buy.iloc[0] = True  # Buy at the beginning
        buy_and_hold_sell = pd.Series(False, index=btc_data.index)
        buy_and_hold_sell.iloc[-1] = True  # Sell at the end
        
        bh_results = quick_backtest(btc_data, buy_and_hold_buy, buy_and_hold_sell, initial_capital=10000.0)
        
        logger.info("Buy & Hold Results:")
        logger.info(f"  Total Return: {bh_results['total_return']:.2f}%")
        logger.info(f"  Sharpe Ratio: {bh_results['sharpe_ratio']:.3f}")
        logger.info(f"  Max Drawdown: {bh_results['max_drawdown']:.2f}%")
        
        # Test 4: Parameter Optimization (small grid for demo)
        logger.info("\n=== Test 4: Parameter Optimization ===")
        
        def rsi_strategy_func(data, rsi_buy_threshold, rsi_sell_threshold):
            return create_simple_strategy_signals(data, rsi_buy_threshold, rsi_sell_threshold)
        
        param_grid = {
            'rsi_buy_threshold': [25, 30, 35],
            'rsi_sell_threshold': [65, 70, 75]
        }
        
        logger.info("Running parameter optimization (this may take a moment)...")
        optimization_results = engine.run_parameter_optimization(
            btc_with_indicators, 
            rsi_strategy_func, 
            param_grid, 
            "BTC-USD-OPT"
        )
        
        if not optimization_results.empty:
            best_params = optimization_results.iloc[0]
            logger.info("Best Parameters Found:")
            logger.info(f"  RSI Buy Threshold: {best_params['rsi_buy_threshold']}")
            logger.info(f"  RSI Sell Threshold: {best_params['rsi_sell_threshold']}")
            logger.info(f"  Sortino Ratio: {best_params['sortino_ratio']:.3f}")
            logger.info(f"  Total Return: {best_params['total_return']:.2f}%")
            
            # Show top 3 results
            logger.info("\nTop 3 Parameter Combinations:")
            for i in range(min(3, len(optimization_results))):
                row = optimization_results.iloc[i]
                logger.info(f"  {i+1}. Buy={row['rsi_buy_threshold']}, Sell={row['rsi_sell_threshold']}: "
                          f"{row['total_return']:.2f}% return, {row['sortino_ratio']:.3f} Sortino")
        
        # Performance comparison
        logger.info("\n=== Strategy Comparison ===")
        strategies = [
            ("RSI Strategy", rsi_results),
            ("MACD Strategy", macd_results),
            ("Buy & Hold", bh_results)
        ]
        
        logger.info("Performance Summary:")
        logger.info(f"{'Strategy':<15} {'Return':<10} {'Sharpe':<8} {'Drawdown':<10} {'Trades':<8}")
        logger.info("-" * 60)
        
        for name, results in strategies:
            logger.info(f"{name:<15} {results['total_return']:>7.2f}% {results['sharpe_ratio']:>7.3f} "
                       f"{results['max_drawdown']:>8.2f}% {results['total_trades']:>7}")
        
        logger.info("\nBacktest engine test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in backtest engine test: {e}")
        return False

if __name__ == "__main__":
    success = test_backtest_engine()
    exit(0 if success else 1)
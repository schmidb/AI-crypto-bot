"""
Vectorized Backtesting Engine

This module provides a comprehensive backtesting framework using VectorBT
for testing trading strategies against historical data with realistic
market conditions and constraints.
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
from typing import Dict, Any, Optional, List, Tuple
import logging
from pathlib import Path
from datetime import datetime, timedelta
import warnings

# Suppress VectorBT warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning, module='vectorbt')

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Comprehensive backtesting engine using VectorBT"""
    
    def __init__(self, initial_capital: float = 10000.0, fees: float = 0.006, 
                 slippage: float = 0.0005):
        """
        Initialize the backtest engine
        
        Args:
            initial_capital: Starting capital in USD
            fees: Trading fees as decimal (0.006 = 0.6%)
            slippage: Slippage as decimal (0.0005 = 0.05%)
        """
        self.initial_capital = initial_capital
        self.fees = fees
        self.slippage = slippage
        
        # Capital management constraints (from existing bot)
        self.min_eur_reserve = 50.0  # Minimum EUR reserve
        self.max_position_size_percent = 0.35  # Maximum 35% position size
        
        logger.info(f"Backtest engine initialized: ${initial_capital:,.2f} capital, {fees*100:.2f}% fees")
    
    def run_backtest(self, data: pd.DataFrame, signals: pd.DataFrame, 
                    product_id: str = "unknown") -> Dict[str, Any]:
        """
        Run a complete backtest with buy/sell signals
        
        Args:
            data: DataFrame with OHLCV data (indexed by datetime)
            signals: DataFrame with 'buy' and 'sell' boolean columns
            product_id: Product identifier for reporting
            
        Returns:
            Dictionary with comprehensive backtest results
        """
        try:
            logger.info(f"Running backtest for {product_id} ({len(data)} rows)")
            
            if data.empty or signals.empty:
                logger.error("Empty data or signals provided")
                return self._empty_results()
            
            # Align data and signals
            aligned_data, aligned_signals = self._align_data_signals(data, signals)
            
            if aligned_data.empty:
                logger.error("No aligned data after processing")
                return self._empty_results()
            
            # Apply capital management constraints
            position_sizes = self._calculate_position_sizes(aligned_data, aligned_signals)
            
            # Create VectorBT portfolio
            portfolio = self._create_portfolio(aligned_data, aligned_signals, position_sizes)
            
            if portfolio is None:
                logger.error("Failed to create portfolio")
                return self._empty_results()
            
            # Calculate comprehensive metrics
            results = self._calculate_metrics(portfolio, aligned_data, product_id)
            
            # Add trade analysis
            results.update(self._analyze_trades(portfolio))
            
            # Add drawdown analysis
            results.update(self._analyze_drawdowns(portfolio))
            
            # Add regime analysis if available
            if 'market_regime' in aligned_data.columns:
                results.update(self._analyze_by_regime(portfolio, aligned_data))
            
            logger.info(f"Backtest completed: {results['total_return']:.2f}% return, {results['sharpe_ratio']:.2f} Sharpe")
            return results
            
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return self._empty_results()
    
    def _align_data_signals(self, data: pd.DataFrame, signals: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Align data and signals by index"""
        try:
            # Ensure both have datetime index
            if not isinstance(data.index, pd.DatetimeIndex):
                logger.warning("Data index is not datetime, attempting conversion")
                data.index = pd.to_datetime(data.index)
            
            if not isinstance(signals.index, pd.DatetimeIndex):
                logger.warning("Signals index is not datetime, attempting conversion")
                signals.index = pd.to_datetime(signals.index)
            
            # Find common index
            common_index = data.index.intersection(signals.index)
            
            if len(common_index) == 0:
                logger.error("No common timestamps between data and signals")
                return pd.DataFrame(), pd.DataFrame()
            
            aligned_data = data.loc[common_index].copy()
            aligned_signals = signals.loc[common_index].copy()
            
            # Ensure required columns exist
            if 'buy' not in aligned_signals.columns:
                aligned_signals['buy'] = False
            if 'sell' not in aligned_signals.columns:
                aligned_signals['sell'] = False
            
            # Convert to boolean if needed
            aligned_signals['buy'] = aligned_signals['buy'].astype(bool)
            aligned_signals['sell'] = aligned_signals['sell'].astype(bool)
            
            logger.info(f"Aligned data: {len(aligned_data)} rows, {aligned_signals['buy'].sum()} buys, {aligned_signals['sell'].sum()} sells")
            return aligned_data, aligned_signals
            
        except Exception as e:
            logger.error(f"Error aligning data and signals: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def _calculate_position_sizes(self, data: pd.DataFrame, signals: pd.DataFrame) -> pd.Series:
        """Calculate position sizes based on capital management rules"""
        try:
            # Start with equal position sizing
            base_position_size = self.max_position_size_percent
            
            # Create position size series
            position_sizes = pd.Series(index=data.index, data=0.0)
            
            # Apply position sizing on buy signals
            buy_mask = signals['buy']
            position_sizes[buy_mask] = base_position_size
            
            # TODO: Add dynamic position sizing based on:
            # - Volatility (smaller positions in high volatility)
            # - Market regime (smaller positions in volatile regimes)
            # - Recent performance (reduce size after losses)
            
            return position_sizes
            
        except Exception as e:
            logger.error(f"Error calculating position sizes: {e}")
            return pd.Series(index=data.index, data=0.0)
    
    def _create_portfolio(self, data: pd.DataFrame, signals: pd.DataFrame, 
                         position_sizes: pd.Series) -> Optional[vbt.Portfolio]:
        """Create VectorBT portfolio from signals"""
        try:
            # Use close prices for execution
            close_prices = data['close']
            
            # Apply slippage to execution prices
            buy_prices = close_prices * (1 + self.slippage)
            sell_prices = close_prices * (1 - self.slippage)
            
            # Create entries and exits
            entries = signals['buy']
            exits = signals['sell']
            
            # Create portfolio with VectorBT
            portfolio = vbt.Portfolio.from_signals(
                close=close_prices,
                entries=entries,
                exits=exits,
                size=position_sizes,
                size_type='percent',  # Position size as percentage of capital
                fees=self.fees,
                init_cash=self.initial_capital,
                freq='1H'  # Assuming hourly data
            )
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error creating portfolio: {e}")
            return None
    
    def _calculate_metrics(self, portfolio: vbt.Portfolio, data: pd.DataFrame, 
                          product_id: str) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            # Basic portfolio stats
            total_return = portfolio.total_return() * 100
            
            # Risk metrics
            try:
                sharpe_ratio = portfolio.sharpe_ratio()
            except:
                sharpe_ratio = 0
                
            try:
                sortino_ratio = portfolio.sortino_ratio()
            except:
                sortino_ratio = 0
                
            max_drawdown = portfolio.max_drawdown() * 100
            
            # Trade metrics
            try:
                total_trades = portfolio.trades.count()
                win_rate = portfolio.trades.win_rate() * 100 if total_trades > 0 else 0
            except:
                total_trades = 0
                win_rate = 0
            
            # Fees calculation
            try:
                fees_paid = portfolio.trades.fees.sum() if hasattr(portfolio.trades, 'fees') else 0
            except:
                fees_paid = 0
            
            # Time-based metrics
            start_date = data.index.min()
            end_date = data.index.max()
            duration_days = (end_date - start_date).days
            
            # Annualized metrics
            annual_return = ((1 + total_return/100) ** (365/duration_days) - 1) * 100 if duration_days > 0 else 0
            
            # Portfolio value
            try:
                final_value = portfolio.value().iloc[-1]
            except:
                final_value = self.initial_capital
            
            # Exposure metrics
            try:
                gross_exposure = portfolio.gross_exposure().mean()
                net_exposure = portfolio.net_exposure().mean()
            except:
                gross_exposure = 0
                net_exposure = 0
            
            return {
                'product_id': product_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'duration_days': duration_days,
                'initial_capital': self.initial_capital,
                'final_value': final_value,
                'total_return': total_return,
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'fees_paid': fees_paid,
                'gross_exposure': gross_exposure,
                'net_exposure': net_exposure
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return {
                'product_id': product_id,
                'error': str(e),
                'total_return': 0,
                'annual_return': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'max_drawdown': 0,
                'total_trades': 0,
                'win_rate': 0,
                'fees_paid': 0,
                'gross_exposure': 0,
                'net_exposure': 0
            }
    
    def _analyze_trades(self, portfolio: vbt.Portfolio) -> Dict[str, Any]:
        """Analyze individual trades"""
        try:
            trades = portfolio.trades
            
            if trades.count() == 0:
                return {
                    'avg_trade_return': 0,
                    'best_trade': 0,
                    'worst_trade': 0,
                    'avg_trade_duration_hours': 0,
                    'profit_factor': 0,
                    'winning_trades': 0,
                    'losing_trades': 0
                }
            
            # Trade returns
            try:
                trade_returns = trades.returns
                avg_trade_return = trade_returns.mean() * 100
                best_trade = trade_returns.max() * 100
                worst_trade = trade_returns.min() * 100
            except:
                avg_trade_return = best_trade = worst_trade = 0
            
            # Trade durations
            try:
                trade_durations = trades.duration
                # Handle both numpy timedelta and pandas timedelta
                if hasattr(trade_durations, 'mean'):
                    avg_duration = trade_durations.mean()
                    if hasattr(avg_duration, 'total_seconds'):
                        avg_duration_hours = avg_duration.total_seconds() / 3600
                    else:
                        # Assume it's already in hours or convert from numpy timedelta
                        avg_duration_hours = float(avg_duration) / 3600000000000  # nanoseconds to hours
                else:
                    avg_duration_hours = 0
            except:
                avg_duration_hours = 0
            
            # Profit factor (gross profit / gross loss)
            try:
                winning_trades = trade_returns[trade_returns > 0]
                losing_trades = trade_returns[trade_returns < 0]
                
                gross_profit = winning_trades.sum() if len(winning_trades) > 0 else 0
                gross_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
                
                winning_count = len(winning_trades)
                losing_count = len(losing_trades)
            except:
                profit_factor = 0
                winning_count = losing_count = 0
            
            return {
                'avg_trade_return': avg_trade_return,
                'best_trade': best_trade,
                'worst_trade': worst_trade,
                'avg_trade_duration_hours': avg_duration_hours,
                'profit_factor': profit_factor,
                'winning_trades': winning_count,
                'losing_trades': losing_count
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trades: {e}")
            return {
                'avg_trade_return': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'avg_trade_duration_hours': 0,
                'profit_factor': 0,
                'winning_trades': 0,
                'losing_trades': 0
            }
    
    def _analyze_drawdowns(self, portfolio: vbt.Portfolio) -> Dict[str, Any]:
        """Analyze drawdown periods"""
        try:
            drawdowns = portfolio.drawdowns
            
            if drawdowns.count() == 0:
                return {
                    'max_drawdown_duration_hours': 0,
                    'avg_drawdown': 0,
                    'drawdown_periods': 0
                }
            
            # Drawdown metrics
            try:
                max_dd_duration = drawdowns.duration.max()
                if hasattr(max_dd_duration, 'total_seconds'):
                    max_dd_duration_hours = max_dd_duration.total_seconds() / 3600
                else:
                    # Handle numpy timedelta
                    max_dd_duration_hours = float(max_dd_duration) / 3600000000000  # nanoseconds to hours
            except:
                max_dd_duration_hours = 0
            
            try:
                avg_drawdown = drawdowns.drawdown.mean() * 100
            except:
                avg_drawdown = 0
            
            drawdown_periods = drawdowns.count()
            
            return {
                'max_drawdown_duration_hours': max_dd_duration_hours,
                'avg_drawdown': avg_drawdown,
                'drawdown_periods': drawdown_periods
            }
            
        except Exception as e:
            logger.error(f"Error analyzing drawdowns: {e}")
            return {
                'max_drawdown_duration_hours': 0,
                'avg_drawdown': 0,
                'drawdown_periods': 0
            }
    
    def _analyze_by_regime(self, portfolio: vbt.Portfolio, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by market regime"""
        try:
            if 'market_regime' not in data.columns:
                return {}
            
            returns = portfolio.returns()
            regimes = data['market_regime']
            
            regime_performance = {}
            regime_names = {0: 'ranging', 1: 'trending', 2: 'volatile'}
            
            for regime_id, regime_name in regime_names.items():
                regime_mask = regimes == regime_id
                if regime_mask.sum() > 0:
                    regime_returns = returns[regime_mask]
                    regime_performance[f'{regime_name}_return'] = regime_returns.sum() * 100
                    regime_performance[f'{regime_name}_sharpe'] = regime_returns.mean() / regime_returns.std() * np.sqrt(252) if regime_returns.std() > 0 else 0
                    regime_performance[f'{regime_name}_periods'] = regime_mask.sum()
            
            return regime_performance
            
        except Exception as e:
            logger.error(f"Error analyzing by regime: {e}")
            return {}
    
    def _empty_results(self) -> Dict[str, Any]:
        """Return empty results structure"""
        return {
            'product_id': 'unknown',
            'error': 'Backtest failed',
            'total_return': 0,
            'annual_return': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'total_trades': 0,
            'win_rate': 0,
            'fees_paid': 0,
            'gross_exposure': 0,
            'net_exposure': 0
        }
    
    def run_parameter_optimization(self, data: pd.DataFrame, 
                                 strategy_func: callable,
                                 param_grid: Dict[str, List],
                                 product_id: str = "unknown") -> pd.DataFrame:
        """
        Run parameter optimization using grid search
        
        Args:
            data: Historical data with indicators
            strategy_func: Function that takes (data, **params) and returns signals DataFrame
            param_grid: Dictionary of parameter names and values to test
            product_id: Product identifier
            
        Returns:
            DataFrame with optimization results
        """
        try:
            logger.info(f"Starting parameter optimization for {product_id}")
            
            # Generate parameter combinations
            from itertools import product
            param_names = list(param_grid.keys())
            param_values = list(param_grid.values())
            param_combinations = list(product(*param_values))
            
            logger.info(f"Testing {len(param_combinations)} parameter combinations")
            
            results = []
            
            for i, param_combo in enumerate(param_combinations):
                try:
                    # Create parameter dictionary
                    params = dict(zip(param_names, param_combo))
                    
                    # Generate signals with these parameters
                    signals = strategy_func(data, **params)
                    
                    # Run backtest
                    backtest_result = self.run_backtest(data, signals, f"{product_id}_opt_{i}")
                    
                    # Add parameters to result
                    result = {**params, **backtest_result}
                    results.append(result)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Completed {i + 1}/{len(param_combinations)} optimizations")
                
                except Exception as e:
                    logger.warning(f"Error in optimization {i}: {e}")
                    continue
            
            results_df = pd.DataFrame(results)
            
            if not results_df.empty:
                # Sort by Sortino ratio (better risk-adjusted returns)
                results_df = results_df.sort_values('sortino_ratio', ascending=False)
                logger.info(f"Optimization complete. Best Sortino ratio: {results_df.iloc[0]['sortino_ratio']:.3f}")
            
            return results_df
            
        except Exception as e:
            logger.error(f"Error in parameter optimization: {e}")
            return pd.DataFrame()

# Convenience function for quick backtesting
def quick_backtest(data: pd.DataFrame, buy_signals: pd.Series, sell_signals: pd.Series,
                  initial_capital: float = 10000.0) -> Dict[str, Any]:
    """
    Quick backtest function for simple use cases
    
    Args:
        data: DataFrame with OHLCV data
        buy_signals: Boolean series for buy signals
        sell_signals: Boolean series for sell signals
        initial_capital: Starting capital
        
    Returns:
        Dictionary with backtest results
    """
    engine = BacktestEngine(initial_capital=initial_capital)
    
    signals_df = pd.DataFrame({
        'buy': buy_signals,
        'sell': sell_signals
    }, index=data.index)
    
    return engine.run_backtest(data, signals_df)
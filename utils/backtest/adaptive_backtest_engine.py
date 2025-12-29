"""
Adaptive Backtest Engine - Aligned with Live Bot Decision Logic

This engine uses the actual AdaptiveStrategyManager to ensure backtesting
accurately represents the live bot's hierarchical decision-making process.
"""

import pandas as pd
import numpy as np
import vectorbt as vbt
from typing import Dict, Any, Optional, List, Tuple
import logging
from datetime import datetime
import warnings
import sys
import os

# Add project root to path for imports
sys.path.append('.')

from strategies.adaptive_strategy_manager import AdaptiveStrategyManager
from utils.backtest.backtest_engine import BacktestEngine
from utils.trading.capital_manager import CapitalManager
from config import Config

# Suppress VectorBT warnings
warnings.filterwarnings('ignore', category=UserWarning, module='vectorbt')

logger = logging.getLogger(__name__)

class AdaptiveBacktestEngine(BacktestEngine):
    """
    Enhanced backtesting engine that uses the actual AdaptiveStrategyManager
    to ensure alignment with live bot decision-making process.
    """
    
    def __init__(self, initial_capital: float = 10000.0, fees: float = 0.006, 
                 slippage: float = 0.0005, config: Optional[Config] = None):
        """
        Initialize the adaptive backtest engine
        
        Args:
            initial_capital: Starting capital in EUR
            fees: Trading fees as decimal (0.006 = 0.6%)
            slippage: Slippage as decimal (0.0005 = 0.05%)
            config: Bot configuration object
        """
        super().__init__(initial_capital, fees, slippage)
        
        # Initialize configuration
        self.config = config or Config()
        
        # Initialize AdaptiveStrategyManager with LLM simulator (same as live bot)
        try:
            # Import LLM strategy simulator for realistic backtesting
            from utils.backtest.llm_strategy_simulator import LLMStrategySimulator
            from unittest.mock import Mock
            
            # Initialize LLM simulator with appropriate trading style
            trading_style = getattr(self.config, 'TRADING_STYLE', 'day_trading')
            self.llm_simulator = LLMStrategySimulator(trading_style=trading_style)
            
            # Create LLM analyzer wrapper that uses the simulator
            class LLMAnalyzerWrapper:
                def __init__(self, simulator):
                    self.simulator = simulator
                
                def analyze_market(self, data):
                    """Wrapper to match LLM analyzer interface"""
                    try:
                        # Extract market data and indicators from the data dict
                        market_data = {
                            'current_price': data.get('current_price', 0),
                            'price': data.get('current_price', 0),
                            'product_id': data.get('product_id', 'BTC-EUR'),
                            'price_changes': data.get('market_data', {}).get('price_changes', {})
                        }
                        
                        technical_indicators = data.get('indicators', {})
                        
                        # Get simulation result
                        sim_result = self.simulator.analyze_market(market_data, technical_indicators)
                        
                        # Convert to expected format
                        return {
                            'decision': sim_result.get('decision', 'HOLD'),
                            'confidence': sim_result.get('confidence', 50),
                            'reasoning': sim_result.get('reasoning', ['LLM simulation analysis']),
                            'risk_assessment': sim_result.get('risk_assessment', 'medium').upper(),
                            'simulated': True
                        }
                    except Exception as e:
                        logger.warning(f"LLM simulation error: {e}")
                        return {
                            'decision': 'HOLD',
                            'confidence': 0,
                            'reasoning': [f'LLM simulation error: {str(e)}'],
                            'risk_assessment': 'HIGH',
                            'simulated': True
                        }
            
            # Mock other analyzers that aren't needed for backtesting
            mock_news_analyzer = Mock()
            mock_volatility_analyzer = Mock()
            
            # Initialize with LLM simulator
            llm_analyzer_wrapper = LLMAnalyzerWrapper(self.llm_simulator)
            
            self.adaptive_manager = AdaptiveStrategyManager(
                self.config,
                llm_analyzer=llm_analyzer_wrapper,
                news_sentiment_analyzer=mock_news_analyzer,
                volatility_analyzer=mock_volatility_analyzer
            )
            logger.info("✅ AdaptiveStrategyManager initialized with LLM simulator for backtesting")
        except Exception as e:
            logger.error(f"Failed to initialize AdaptiveStrategyManager with LLM simulator: {e}")
            raise
        
        # Initialize CapitalManager for risk management
        try:
            self.capital_manager = CapitalManager(self.config)
            logger.info("✅ CapitalManager initialized for backtesting")
        except Exception as e:
            logger.error(f"Failed to initialize CapitalManager: {e}")
            raise
        
        # Track decision details for analysis
        self.decision_log = []
        self.regime_log = []
        
        logger.info(f"🚀 AdaptiveBacktestEngine initialized with ${initial_capital:,.2f} capital")
    
    def run_adaptive_backtest(self, data: pd.DataFrame, product_id: str = "BTC-EUR") -> Dict[str, Any]:
        """
        Run backtest using the actual AdaptiveStrategyManager decision logic
        
        Args:
            data: DataFrame with OHLCV data and technical indicators
            product_id: Trading pair identifier
            
        Returns:
            Dictionary with comprehensive backtest results including regime analysis
        """
        try:
            logger.info(f"🔄 Running adaptive backtest for {product_id} ({len(data)} rows)")
            
            if data.empty:
                logger.error("Empty data provided")
                return self._empty_adaptive_results()
            
            # Generate adaptive signals using the actual AdaptiveStrategyManager
            signals_df = self._generate_adaptive_signals(data, product_id)
            
            if signals_df.empty:
                logger.error("No signals generated")
                return self._empty_adaptive_results()
            
            # Apply risk management to signals
            risk_adjusted_signals = self._apply_risk_management(data, signals_df, product_id)
            
            # Run the backtest with risk-adjusted signals
            base_results = super().run_backtest(data, risk_adjusted_signals, product_id)
            
            # Add adaptive-specific analysis
            adaptive_results = self._analyze_adaptive_performance(base_results, data, risk_adjusted_signals)
            
            # Combine results
            final_results = {**base_results, **adaptive_results}
            
            logger.info(f"✅ Adaptive backtest completed: {final_results.get('total_return', 0):.2f}% return")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in adaptive backtest: {e}")
            return self._empty_adaptive_results()
    
    def _generate_adaptive_signals(self, data: pd.DataFrame, product_id: str) -> pd.DataFrame:
        """
        Generate trading signals using the actual AdaptiveStrategyManager
        """
        try:
            logger.info("🧠 Generating signals using AdaptiveStrategyManager...")
            
            # Initialize signals DataFrame
            signals_df = pd.DataFrame(index=data.index)
            signals_df['buy'] = False
            signals_df['sell'] = False
            signals_df['confidence'] = 0.0
            signals_df['reasoning'] = ""
            signals_df['market_regime'] = "ranging"
            signals_df['primary_strategy'] = ""
            signals_df['position_multiplier'] = 1.0
            
            # Process each row using the actual AdaptiveStrategyManager
            for i, (timestamp, row) in enumerate(data.iterrows()):
                try:
                    # Prepare market data (same format as live bot)
                    market_data = self._prepare_market_data_for_adaptive(row, product_id, i, data)
                    
                    # Prepare technical indicators (same format as live bot)
                    technical_indicators = self._prepare_technical_indicators_for_adaptive(row)
                    
                    # Get decision from AdaptiveStrategyManager (SAME AS LIVE BOT)
                    signal = self.adaptive_manager.get_combined_signal(
                        market_data, technical_indicators, {}
                    )
                    
                    # Extract market regime and primary strategy
                    market_regime = getattr(self.adaptive_manager, 'current_market_regime', 'ranging')
                    primary_strategy = self._extract_primary_strategy_from_reasoning(signal.reasoning)
                    
                    # Store signal data
                    signals_df.loc[timestamp, 'buy'] = (signal.action == 'BUY')
                    signals_df.loc[timestamp, 'sell'] = (signal.action == 'SELL')
                    signals_df.loc[timestamp, 'confidence'] = float(signal.confidence)
                    signals_df.loc[timestamp, 'reasoning'] = str(signal.reasoning)
                    signals_df.loc[timestamp, 'market_regime'] = str(market_regime)
                    signals_df.loc[timestamp, 'primary_strategy'] = str(primary_strategy)
                    signals_df.loc[timestamp, 'position_multiplier'] = float(getattr(signal, 'position_size_multiplier', 1.0))
                    
                    # Log decision for analysis
                    self.decision_log.append({
                        'timestamp': timestamp,
                        'action': signal.action,
                        'confidence': signal.confidence,
                        'market_regime': market_regime,
                        'primary_strategy': primary_strategy,
                        'reasoning': signal.reasoning
                    })
                    
                    # Log regime for analysis
                    self.regime_log.append({
                        'timestamp': timestamp,
                        'regime': market_regime
                    })
                    
                except Exception as e:
                    logger.warning(f"Error processing row {i}: {e}")
                    # Set safe defaults
                    signals_df.loc[timestamp, 'buy'] = False
                    signals_df.loc[timestamp, 'sell'] = False
                    signals_df.loc[timestamp, 'confidence'] = 0.0
                    signals_df.loc[timestamp, 'reasoning'] = f"Error: {str(e)}"
                    signals_df.loc[timestamp, 'market_regime'] = "ranging"
                    signals_df.loc[timestamp, 'primary_strategy'] = "unknown"
                    signals_df.loc[timestamp, 'position_multiplier'] = 1.0
                    continue
            
            # Log signal statistics
            buy_count = signals_df['buy'].sum()
            sell_count = signals_df['sell'].sum()
            regime_counts = signals_df['market_regime'].value_counts().to_dict()
            strategy_counts = signals_df['primary_strategy'].value_counts().to_dict()
            
            logger.info(f"📊 Generated {buy_count} BUY and {sell_count} SELL signals")
            logger.info(f"📊 Market regimes: {regime_counts}")
            logger.info(f"📊 Primary strategies: {strategy_counts}")
            
            return signals_df
            
        except Exception as e:
            logger.error(f"Error generating adaptive signals: {e}")
            return pd.DataFrame()
    
    def _prepare_market_data_for_adaptive(self, row: pd.Series, product_id: str, 
                                        index: int, full_data: pd.DataFrame) -> Dict:
        """
        Prepare market data in the exact format expected by AdaptiveStrategyManager
        """
        try:
            current_price = float(row['close'])
            
            # Calculate price changes (same logic as live bot)
            price_changes = {'1h': 0.0, '24h': 0.0, '5d': 0.0}
            
            if index > 0:
                prev_price = float(full_data.iloc[index-1]['close'])
                price_changes['1h'] = ((current_price - prev_price) / prev_price) * 100
            
            if index >= 24:
                price_24h_ago = float(full_data.iloc[index-24]['close'])
                price_changes['24h'] = ((current_price - price_24h_ago) / price_24h_ago) * 100
            
            if index >= 120:  # 5 days * 24 hours
                price_5d_ago = float(full_data.iloc[index-120]['close'])
                price_changes['5d'] = ((current_price - price_5d_ago) / price_5d_ago) * 100
            
            return {
                'product_id': product_id,
                'price': current_price,
                'current_price': current_price,  # AdaptiveStrategyManager expects this
                'volume': float(row.get('volume', 1000000)),
                'timestamp': row.name.isoformat() if hasattr(row.name, 'isoformat') else str(row.name),
                'price_changes': price_changes
            }
            
        except Exception as e:
            logger.warning(f"Error preparing market data: {e}")
            return {
                'product_id': product_id,
                'price': 50000.0,
                'current_price': 50000.0,
                'volume': 1000000.0,
                'timestamp': str(row.name),
                'price_changes': {'1h': 0.0, '24h': 0.0, '5d': 0.0}
            }
    
    def _prepare_technical_indicators_for_adaptive(self, row: pd.Series) -> Dict:
        """
        Prepare technical indicators in the exact format expected by AdaptiveStrategyManager
        """
        try:
            indicators = {}
            
            # Map common indicator names
            indicator_mapping = {
                'rsi_14': 'rsi',
                'bb_upper_20': 'bb_upper',
                'bb_lower_20': 'bb_lower',
                'bb_middle_20': 'bb_middle',
                'macd': 'macd',
                'macd_signal': 'macd_signal',
                'sma_20': 'sma_20',
                'sma_50': 'sma_50',
                'ema_12': 'ema_12',
                'ema_26': 'ema_26',
                'volume_sma_20': 'volume_sma',
                'atr': 'atr',
                'stoch_k': 'stoch_k',
                'stoch_d': 'stoch_d'
            }
            
            # Extract indicators
            for col_name, indicator_name in indicator_mapping.items():
                if col_name in row.index:
                    try:
                        value = float(row[col_name])
                        if not np.isnan(value):
                            indicators[indicator_name] = value
                    except (ValueError, TypeError):
                        continue
            
            # Add current price to indicators (required by some strategies)
            if 'close' in row.index:
                indicators['current_price'] = float(row['close'])
            
            return indicators
            
        except Exception as e:
            logger.warning(f"Error preparing technical indicators: {e}")
            return {'current_price': 50000.0}
    
    def _extract_primary_strategy_from_reasoning(self, reasoning: str) -> str:
        """Extract the primary strategy name from reasoning text"""
        try:
            reasoning_lower = reasoning.lower()
            if 'trend_following' in reasoning_lower or 'trend following' in reasoning_lower:
                return 'trend_following'
            elif 'mean_reversion' in reasoning_lower or 'mean reversion' in reasoning_lower:
                return 'mean_reversion'
            elif 'momentum' in reasoning_lower:
                return 'momentum'
            elif 'llm' in reasoning_lower:
                return 'llm_strategy'
            elif 'adaptive' in reasoning_lower:
                return 'adaptive'
            else:
                return 'unknown'
        except:
            return 'unknown'
    
    def _apply_risk_management(self, data: pd.DataFrame, signals_df: pd.DataFrame, 
                             product_id: str) -> pd.DataFrame:
        """
        Apply risk management rules to signals (same as live bot)
        """
        try:
            logger.info("🛡️ Applying risk management to signals...")
            
            # Create risk-adjusted signals DataFrame
            risk_adjusted = signals_df.copy()
            risk_adjusted['original_action'] = 'HOLD'
            risk_adjusted['risk_adjustment'] = ''
            risk_adjusted['position_size'] = 0.0
            
            # Simulate portfolio state for risk management
            current_portfolio_value = self.initial_capital
            current_eur_balance = self.initial_capital
            current_crypto_balance = 0.0
            
            asset = product_id.split('-')[0]  # Extract BTC, ETH, etc.
            
            for i, (timestamp, row) in enumerate(risk_adjusted.iterrows()):
                try:
                    if not (row['buy'] or row['sell']):
                        continue  # Skip HOLD signals
                    
                    current_price = float(data.loc[timestamp, 'close'])
                    confidence = row['confidence']
                    action = 'BUY' if row['buy'] else 'SELL'
                    
                    # Store original action
                    risk_adjusted.loc[timestamp, 'original_action'] = action
                    
                    # Simulate portfolio state
                    portfolio = {
                        'EUR': {'amount': current_eur_balance},
                        asset: {'amount': current_crypto_balance},
                        'portfolio_value_eur': {'amount': current_portfolio_value}
                    }
                    
                    if action == 'BUY':
                        # Calculate trade size using same logic as live bot
                        base_trade_percentage = 0.10 + (confidence / 100.0 * 0.15)  # 10% to 25%
                        position_multiplier = row.get('position_multiplier', 1.0)
                        original_trade_size = current_eur_balance * base_trade_percentage * position_multiplier
                        
                        # Apply capital management
                        safe_trade_size, capital_reason = self.capital_manager.calculate_safe_trade_size(
                            "BUY", asset, portfolio, original_trade_size
                        )
                        
                        if safe_trade_size <= 0:
                            # Risk management blocked the trade
                            risk_adjusted.loc[timestamp, 'buy'] = False
                            risk_adjusted.loc[timestamp, 'risk_adjustment'] = f'Blocked: {capital_reason}'
                            risk_adjusted.loc[timestamp, 'position_size'] = 0.0
                        elif safe_trade_size < self.config.MIN_TRADE_AMOUNT:
                            # Trade size too small
                            risk_adjusted.loc[timestamp, 'buy'] = False
                            risk_adjusted.loc[timestamp, 'risk_adjustment'] = f'Too small: €{safe_trade_size:.2f} < €{self.config.MIN_TRADE_AMOUNT}'
                            risk_adjusted.loc[timestamp, 'position_size'] = 0.0
                        else:
                            # Trade approved
                            risk_adjusted.loc[timestamp, 'position_size'] = safe_trade_size / current_portfolio_value
                            risk_adjusted.loc[timestamp, 'risk_adjustment'] = f'Approved: €{safe_trade_size:.2f}'
                            
                            # Update simulated portfolio
                            crypto_amount = safe_trade_size / current_price
                            current_eur_balance -= safe_trade_size
                            current_crypto_balance += crypto_amount
                            current_portfolio_value = current_eur_balance + (current_crypto_balance * current_price)
                    
                    elif action == 'SELL':
                        # Calculate sell amount
                        base_trade_percentage = 0.10 + (confidence / 100.0 * 0.15)
                        position_multiplier = row.get('position_multiplier', 1.0)
                        max_crypto_amount = current_crypto_balance * base_trade_percentage * position_multiplier
                        original_trade_value = max_crypto_amount * current_price
                        
                        # Apply capital management
                        safe_trade_value, capital_reason = self.capital_manager.calculate_safe_trade_size(
                            "SELL", asset, portfolio, original_trade_value
                        )
                        
                        if safe_trade_value <= 0:
                            # Risk management blocked the trade
                            risk_adjusted.loc[timestamp, 'sell'] = False
                            risk_adjusted.loc[timestamp, 'risk_adjustment'] = f'Blocked: {capital_reason}'
                            risk_adjusted.loc[timestamp, 'position_size'] = 0.0
                        elif safe_trade_value < self.config.MIN_TRADE_AMOUNT:
                            # Trade size too small
                            risk_adjusted.loc[timestamp, 'sell'] = False
                            risk_adjusted.loc[timestamp, 'risk_adjustment'] = f'Too small: €{safe_trade_value:.2f} < €{self.config.MIN_TRADE_AMOUNT}'
                            risk_adjusted.loc[timestamp, 'position_size'] = 0.0
                        else:
                            # Trade approved
                            crypto_amount = safe_trade_value / current_price
                            risk_adjusted.loc[timestamp, 'position_size'] = safe_trade_value / current_portfolio_value
                            risk_adjusted.loc[timestamp, 'risk_adjustment'] = f'Approved: €{safe_trade_value:.2f}'
                            
                            # Update simulated portfolio
                            current_crypto_balance -= crypto_amount
                            current_eur_balance += safe_trade_value
                            current_portfolio_value = current_eur_balance + (current_crypto_balance * current_price)
                
                except Exception as e:
                    logger.warning(f"Error applying risk management to row {i}: {e}")
                    continue
            
            # Log risk management statistics
            original_buys = signals_df['buy'].sum()
            original_sells = signals_df['sell'].sum()
            final_buys = risk_adjusted['buy'].sum()
            final_sells = risk_adjusted['sell'].sum()
            
            logger.info(f"🛡️ Risk management: BUY {original_buys} → {final_buys}, SELL {original_sells} → {final_sells}")
            
            return risk_adjusted
            
        except Exception as e:
            logger.error(f"Error applying risk management: {e}")
            return signals_df
    
    def _analyze_adaptive_performance(self, base_results: Dict, data: pd.DataFrame, 
                                    signals_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze performance specific to adaptive strategy features
        """
        try:
            adaptive_analysis = {}
            
            # Market regime analysis
            if 'market_regime' in signals_df.columns:
                regime_analysis = self._analyze_regime_performance(signals_df, base_results)
                adaptive_analysis.update(regime_analysis)
            
            # Strategy attribution analysis
            if 'primary_strategy' in signals_df.columns:
                strategy_analysis = self._analyze_strategy_attribution(signals_df)
                adaptive_analysis.update(strategy_analysis)
            
            # Decision quality analysis
            decision_analysis = self._analyze_decision_quality()
            adaptive_analysis.update(decision_analysis)
            
            # Risk management effectiveness
            if 'risk_adjustment' in signals_df.columns:
                risk_analysis = self._analyze_risk_management_effectiveness(signals_df)
                adaptive_analysis.update(risk_analysis)
            
            return adaptive_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing adaptive performance: {e}")
            return {}
    
    def _analyze_regime_performance(self, signals_df: pd.DataFrame, base_results: Dict) -> Dict[str, Any]:
        """Analyze performance by market regime"""
        try:
            regime_analysis = {}
            
            # Count regime periods
            regime_counts = signals_df['market_regime'].value_counts().to_dict()
            regime_analysis['regime_distribution'] = regime_counts
            
            # Analyze signals by regime
            for regime in ['trending', 'ranging', 'volatile']:
                regime_mask = signals_df['market_regime'] == regime
                if regime_mask.sum() > 0:
                    regime_signals = signals_df[regime_mask]
                    regime_analysis[f'{regime}_buy_signals'] = int(regime_signals['buy'].sum())
                    regime_analysis[f'{regime}_sell_signals'] = int(regime_signals['sell'].sum())
                    regime_analysis[f'{regime}_avg_confidence'] = float(regime_signals['confidence'].mean())
                    regime_analysis[f'{regime}_periods'] = int(regime_mask.sum())
            
            logger.info(f"📊 Regime analysis: {regime_counts}")
            return regime_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing regime performance: {e}")
            return {}
    
    def _analyze_strategy_attribution(self, signals_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze which strategies contributed to decisions"""
        try:
            strategy_analysis = {}
            
            # Count strategy usage
            strategy_counts = signals_df['primary_strategy'].value_counts().to_dict()
            strategy_analysis['strategy_usage'] = strategy_counts
            
            # Analyze signals by strategy
            for strategy in ['trend_following', 'mean_reversion', 'momentum', 'llm_strategy']:
                strategy_mask = signals_df['primary_strategy'] == strategy
                if strategy_mask.sum() > 0:
                    strategy_signals = signals_df[strategy_mask]
                    strategy_analysis[f'{strategy}_decisions'] = int(strategy_mask.sum())
                    strategy_analysis[f'{strategy}_buy_signals'] = int(strategy_signals['buy'].sum())
                    strategy_analysis[f'{strategy}_sell_signals'] = int(strategy_signals['sell'].sum())
                    strategy_analysis[f'{strategy}_avg_confidence'] = float(strategy_signals['confidence'].mean())
            
            logger.info(f"📊 Strategy attribution: {strategy_counts}")
            return strategy_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing strategy attribution: {e}")
            return {}
    
    def _analyze_decision_quality(self) -> Dict[str, Any]:
        """Analyze quality of decisions made"""
        try:
            if not self.decision_log:
                return {}
            
            decision_df = pd.DataFrame(self.decision_log)
            
            quality_analysis = {
                'total_decisions': len(decision_df),
                'buy_decisions': int((decision_df['action'] == 'BUY').sum()),
                'sell_decisions': int((decision_df['action'] == 'SELL').sum()),
                'hold_decisions': int((decision_df['action'] == 'HOLD').sum()),
                'avg_confidence': float(decision_df['confidence'].mean()),
                'high_confidence_decisions': int((decision_df['confidence'] >= 70).sum()),
                'low_confidence_decisions': int((decision_df['confidence'] < 50).sum())
            }
            
            return quality_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing decision quality: {e}")
            return {}
    
    def _analyze_risk_management_effectiveness(self, signals_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze effectiveness of risk management"""
        try:
            risk_analysis = {}
            
            # Count risk adjustments
            if 'risk_adjustment' in signals_df.columns:
                blocked_trades = signals_df['risk_adjustment'].str.contains('Blocked', na=False).sum()
                approved_trades = signals_df['risk_adjustment'].str.contains('Approved', na=False).sum()
                too_small_trades = signals_df['risk_adjustment'].str.contains('Too small', na=False).sum()
                
                risk_analysis.update({
                    'blocked_trades': int(blocked_trades),
                    'approved_trades': int(approved_trades),
                    'too_small_trades': int(too_small_trades),
                    'risk_management_active': bool(blocked_trades > 0 or too_small_trades > 0)
                })
            
            return risk_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing risk management effectiveness: {e}")
            return {}
    
    def _empty_adaptive_results(self) -> Dict[str, Any]:
        """Return empty results structure for adaptive backtest"""
        base_empty = super()._empty_results()
        adaptive_empty = {
            'regime_distribution': {},
            'strategy_usage': {},
            'total_decisions': 0,
            'risk_management_active': False
        }
        return {**base_empty, **adaptive_empty}

# Convenience function for quick adaptive backtesting
def quick_adaptive_backtest(data: pd.DataFrame, product_id: str = "BTC-EUR",
                          initial_capital: float = 10000.0) -> Dict[str, Any]:
    """
    Quick adaptive backtest function using AdaptiveStrategyManager
    
    Args:
        data: DataFrame with OHLCV data and technical indicators
        product_id: Trading pair identifier
        initial_capital: Starting capital
        
    Returns:
        Dictionary with comprehensive adaptive backtest results
    """
    engine = AdaptiveBacktestEngine(initial_capital=initial_capital)
    return engine.run_adaptive_backtest(data, product_id)
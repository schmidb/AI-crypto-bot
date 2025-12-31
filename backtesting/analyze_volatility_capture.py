#!/usr/bin/env python3
"""
Volatility Capture Analysis
Analyze why aggressive volatility-based strategies are underperforming
"""

import sys
import os
sys.path.append('.')

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from pathlib import Path
import json
import matplotlib.pyplot as plt
from typing import Dict, Any, List

from utils.performance.indicator_factory import calculate_indicators

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VolatilityAnalyzer:
    """
    Analyze volatility patterns and why aggressive strategies fail to capture them
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_data(self, start_date: str = "2025-06-01", end_date: str = "2025-07-31", 
                  granularity: str = "hour") -> Dict[str, pd.DataFrame]:
        """Load historical data for analysis"""
        try:
            data_dir = Path("./data/historical")
            datasets = {}
            
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            
            for product_id in ['BTC-EUR', 'ETH-EUR']:
                # Choose file based on granularity
                if granularity == "15min":
                    file_patterns = [
                        f"BTC-USD_fifteenminute_90d.parquet" if 'BTC' in product_id else f"ETH-USD_fifteenminute_90d.parquet"
                    ]
                else:  # Default to hourly
                    file_patterns = [
                        f"BTC-USD_hour_365d.parquet" if 'BTC' in product_id else f"ETH-USD_hour_365d.parquet"
                    ]
                
                for pattern in file_patterns:
                    data_file = data_dir / pattern
                    if data_file.exists():
                        data = pd.read_parquet(data_file)
                        
                        # Ensure datetime index
                        if not isinstance(data.index, pd.DatetimeIndex):
                            if 'timestamp' in data.columns:
                                data.set_index('timestamp', inplace=True)
                        
                        # Filter to date range
                        filtered_data = data[(data.index >= start_dt) & (data.index <= end_dt)].copy()
                        
                        if len(filtered_data) > 0:
                            # Calculate indicators
                            data_with_indicators = calculate_indicators(filtered_data, product_id)
                            datasets[product_id] = data_with_indicators
                            logger.info(f"Loaded {len(data_with_indicators)} rows for {product_id} ({granularity} data)")
                        break
            
            return datasets
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {}
    
    def analyze_volatility_patterns(self, data: pd.DataFrame, product_id: str) -> Dict[str, Any]:
        """Analyze volatility patterns in the data"""
        try:
            logger.info(f"Analyzing volatility patterns for {product_id}")
            
            # Calculate various volatility measures
            data['returns'] = data['close'].pct_change()
            data['abs_returns'] = data['returns'].abs()
            
            # Rolling volatility (different windows)
            data['vol_1h'] = data['returns'].rolling(1).std()
            data['vol_4h'] = data['returns'].rolling(4).std()
            data['vol_24h'] = data['returns'].rolling(24).std()
            
            # Intraday range volatility
            data['high_low_range'] = (data['high'] - data['low']) / data['close']
            data['open_close_range'] = abs(data['open'] - data['close']) / data['close']
            
            # Bollinger Band width (volatility proxy)
            if 'bb_upper' in data.columns and 'bb_lower' in data.columns and 'bb_middle' in data.columns:
                data['bb_width'] = (data['bb_upper'] - data['bb_lower']) / data['bb_middle']
            
            # Identify high volatility periods
            vol_threshold_95 = data['abs_returns'].quantile(0.95)
            vol_threshold_90 = data['abs_returns'].quantile(0.90)
            vol_threshold_75 = data['abs_returns'].quantile(0.75)
            
            data['high_vol_95'] = data['abs_returns'] > vol_threshold_95
            data['high_vol_90'] = data['abs_returns'] > vol_threshold_90
            data['high_vol_75'] = data['abs_returns'] > vol_threshold_75
            
            # Calculate statistics
            analysis = {
                'total_periods': len(data),
                'avg_return': data['returns'].mean() * 100,
                'volatility_24h': data['returns'].std() * np.sqrt(24) * 100,
                'max_intraday_move': data['abs_returns'].max() * 100,
                'avg_intraday_range': data['high_low_range'].mean() * 100,
                'high_vol_periods_95': data['high_vol_95'].sum(),
                'high_vol_periods_90': data['high_vol_90'].sum(),
                'high_vol_periods_75': data['high_vol_75'].sum(),
                'vol_clustering': self._analyze_volatility_clustering(data),
                'directional_bias': self._analyze_directional_patterns(data),
                'mean_reversion': self._analyze_mean_reversion(data),
                'momentum_persistence': self._analyze_momentum_persistence(data)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing volatility for {product_id}: {e}")
            return {}
    
    def _analyze_volatility_clustering(self, data: pd.DataFrame) -> Dict[str, float]:
        """Analyze if high volatility periods cluster together"""
        try:
            # Look at autocorrelation of volatility
            vol_autocorr_1 = data['abs_returns'].autocorr(lag=1)
            vol_autocorr_4 = data['abs_returns'].autocorr(lag=4)
            vol_autocorr_24 = data['abs_returns'].autocorr(lag=24)
            
            return {
                'vol_autocorr_1h': vol_autocorr_1,
                'vol_autocorr_4h': vol_autocorr_4,
                'vol_autocorr_24h': vol_autocorr_24,
                'clustering_strength': (vol_autocorr_1 + vol_autocorr_4 + vol_autocorr_24) / 3
            }
        except:
            return {'clustering_strength': 0}
    
    def _analyze_directional_patterns(self, data: pd.DataFrame) -> Dict[str, float]:
        """Analyze if volatility has directional bias"""
        try:
            # Separate up and down moves
            up_moves = data[data['returns'] > 0]['abs_returns']
            down_moves = data[data['returns'] < 0]['abs_returns']
            
            return {
                'up_move_avg_vol': up_moves.mean() if len(up_moves) > 0 else 0,
                'down_move_avg_vol': down_moves.mean() if len(down_moves) > 0 else 0,
                'up_move_count': len(up_moves),
                'down_move_count': len(down_moves),
                'volatility_asymmetry': (down_moves.mean() - up_moves.mean()) if len(up_moves) > 0 and len(down_moves) > 0 else 0
            }
        except:
            return {}
    
    def _analyze_mean_reversion(self, data: pd.DataFrame) -> Dict[str, float]:
        """Analyze mean reversion patterns"""
        try:
            # Look at return reversals after large moves
            large_moves = data['abs_returns'] > data['abs_returns'].quantile(0.90)
            
            # Check what happens in next 1, 4, 24 hours after large moves
            next_1h_returns = []
            next_4h_returns = []
            next_24h_returns = []
            
            for i in range(len(data) - 24):
                if large_moves.iloc[i]:
                    if i + 1 < len(data):
                        next_1h_returns.append(data['returns'].iloc[i + 1])
                    if i + 4 < len(data):
                        next_4h_returns.append(data['returns'].iloc[i + 4])
                    if i + 24 < len(data):
                        next_24h_returns.append(data['returns'].iloc[i + 24])
            
            return {
                'mean_reversion_1h': -np.mean(next_1h_returns) if next_1h_returns else 0,
                'mean_reversion_4h': -np.mean(next_4h_returns) if next_4h_returns else 0,
                'mean_reversion_24h': -np.mean(next_24h_returns) if next_24h_returns else 0,
                'large_move_count': sum(large_moves)
            }
        except:
            return {}
    
    def _analyze_momentum_persistence(self, data: pd.DataFrame) -> Dict[str, float]:
        """Analyze momentum persistence patterns"""
        try:
            # Look at return continuation after moves
            returns_1h_ago = data['returns'].shift(1)
            returns_4h_ago = data['returns'].shift(4)
            
            # Correlation between current and past returns
            momentum_1h = data['returns'].corr(returns_1h_ago)
            momentum_4h = data['returns'].corr(returns_4h_ago)
            
            return {
                'momentum_1h': momentum_1h if not np.isnan(momentum_1h) else 0,
                'momentum_4h': momentum_4h if not np.isnan(momentum_4h) else 0
            }
        except:
            return {}
    
    def analyze_signal_quality(self, data: pd.DataFrame, product_id: str) -> Dict[str, Any]:
        """Analyze the quality of trading signals in different volatility regimes"""
        try:
            logger.info(f"Analyzing signal quality for {product_id}")
            
            # Define volatility regimes
            vol_low = data['abs_returns'] < data['abs_returns'].quantile(0.33)
            vol_medium = (data['abs_returns'] >= data['abs_returns'].quantile(0.33)) & (data['abs_returns'] < data['abs_returns'].quantile(0.67))
            vol_high = data['abs_returns'] >= data['abs_returns'].quantile(0.67)
            
            # Analyze RSI signals in different volatility regimes
            rsi_analysis = {}
            if 'rsi_14' in data.columns:
                rsi_analysis = self._analyze_rsi_by_volatility(data, vol_low, vol_medium, vol_high)
            
            # Analyze Bollinger Band signals
            bb_analysis = {}
            if all(col in data.columns for col in ['bb_upper', 'bb_lower', 'bb_middle']):
                bb_analysis = self._analyze_bb_by_volatility(data, vol_low, vol_medium, vol_high)
            
            # Analyze MACD signals
            macd_analysis = {}
            if all(col in data.columns for col in ['macd', 'macd_signal']):
                macd_analysis = self._analyze_macd_by_volatility(data, vol_low, vol_medium, vol_high)
            
            return {
                'volatility_regimes': {
                    'low_vol_periods': sum(vol_low),
                    'medium_vol_periods': sum(vol_medium),
                    'high_vol_periods': sum(vol_high)
                },
                'rsi_analysis': rsi_analysis,
                'bb_analysis': bb_analysis,
                'macd_analysis': macd_analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing signal quality: {e}")
            return {}
    
    def _analyze_rsi_by_volatility(self, data: pd.DataFrame, vol_low, vol_medium, vol_high) -> Dict[str, Any]:
        """Analyze RSI signal effectiveness by volatility regime"""
        try:
            rsi = data['rsi_14']
            returns_1h = data['returns'].shift(-1)  # Next hour return
            
            # RSI oversold/overbought signals
            oversold_30 = rsi < 30
            oversold_35 = rsi < 35
            overbought_70 = rsi > 70
            overbought_65 = rsi > 65
            
            analysis = {}
            
            for regime_name, regime_mask in [('low_vol', vol_low), ('medium_vol', vol_medium), ('high_vol', vol_high)]:
                # Analyze oversold signals (should predict positive returns)
                oversold_30_regime = oversold_30 & regime_mask
                oversold_35_regime = oversold_35 & regime_mask
                
                # Analyze overbought signals (should predict negative returns)
                overbought_70_regime = overbought_70 & regime_mask
                overbought_65_regime = overbought_65 & regime_mask
                
                analysis[regime_name] = {
                    'oversold_30_success_rate': (returns_1h[oversold_30_regime] > 0).mean() if oversold_30_regime.sum() > 0 else 0,
                    'oversold_35_success_rate': (returns_1h[oversold_35_regime] > 0).mean() if oversold_35_regime.sum() > 0 else 0,
                    'overbought_70_success_rate': (returns_1h[overbought_70_regime] < 0).mean() if overbought_70_regime.sum() > 0 else 0,
                    'overbought_65_success_rate': (returns_1h[overbought_65_regime] < 0).mean() if overbought_65_regime.sum() > 0 else 0,
                    'oversold_30_count': oversold_30_regime.sum(),
                    'oversold_35_count': oversold_35_regime.sum(),
                    'overbought_70_count': overbought_70_regime.sum(),
                    'overbought_65_count': overbought_65_regime.sum()
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in RSI analysis: {e}")
            return {}
    
    def _analyze_bb_by_volatility(self, data: pd.DataFrame, vol_low, vol_medium, vol_high) -> Dict[str, Any]:
        """Analyze Bollinger Band signal effectiveness by volatility regime"""
        try:
            price = data['close']
            bb_upper = data['bb_upper']
            bb_lower = data['bb_lower']
            bb_middle = data['bb_middle']
            returns_1h = data['returns'].shift(-1)
            
            # BB signals
            below_lower = price < bb_lower
            above_upper = price > bb_upper
            near_lower = (price - bb_lower) / (bb_middle - bb_lower) < 0.1
            near_upper = (bb_upper - price) / (bb_upper - bb_middle) < 0.1
            
            analysis = {}
            
            for regime_name, regime_mask in [('low_vol', vol_low), ('medium_vol', vol_medium), ('high_vol', vol_high)]:
                below_lower_regime = below_lower & regime_mask
                above_upper_regime = above_upper & regime_mask
                near_lower_regime = near_lower & regime_mask
                near_upper_regime = near_upper & regime_mask
                
                analysis[regime_name] = {
                    'below_lower_success_rate': (returns_1h[below_lower_regime] > 0).mean() if below_lower_regime.sum() > 0 else 0,
                    'above_upper_success_rate': (returns_1h[above_upper_regime] < 0).mean() if above_upper_regime.sum() > 0 else 0,
                    'near_lower_success_rate': (returns_1h[near_lower_regime] > 0).mean() if near_lower_regime.sum() > 0 else 0,
                    'near_upper_success_rate': (returns_1h[near_upper_regime] < 0).mean() if near_upper_regime.sum() > 0 else 0,
                    'below_lower_count': below_lower_regime.sum(),
                    'above_upper_count': above_upper_regime.sum(),
                    'near_lower_count': near_lower_regime.sum(),
                    'near_upper_count': near_upper_regime.sum()
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in BB analysis: {e}")
            return {}
    
    def _analyze_macd_by_volatility(self, data: pd.DataFrame, vol_low, vol_medium, vol_high) -> Dict[str, Any]:
        """Analyze MACD signal effectiveness by volatility regime"""
        try:
            macd = data['macd']
            macd_signal = data['macd_signal']
            returns_1h = data['returns'].shift(-1)
            
            # MACD crossover signals
            bullish_cross = (macd > macd_signal) & (macd.shift(1) <= macd_signal.shift(1))
            bearish_cross = (macd < macd_signal) & (macd.shift(1) >= macd_signal.shift(1))
            
            analysis = {}
            
            for regime_name, regime_mask in [('low_vol', vol_low), ('medium_vol', vol_medium), ('high_vol', vol_high)]:
                bullish_cross_regime = bullish_cross & regime_mask
                bearish_cross_regime = bearish_cross & regime_mask
                
                analysis[regime_name] = {
                    'bullish_cross_success_rate': (returns_1h[bullish_cross_regime] > 0).mean() if bullish_cross_regime.sum() > 0 else 0,
                    'bearish_cross_success_rate': (returns_1h[bearish_cross_regime] < 0).mean() if bearish_cross_regime.sum() > 0 else 0,
                    'bullish_cross_count': bullish_cross_regime.sum(),
                    'bearish_cross_count': bearish_cross_regime.sum()
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in MACD analysis: {e}")
            return {}
    
    def run_comprehensive_analysis(self, start_date: str = "2025-06-01", end_date: str = "2025-07-31", 
                                  granularity: str = "hour") -> Dict[str, Any]:
        """Run comprehensive volatility analysis"""
        try:
            logger.info(f"🔍 Starting Comprehensive Volatility Analysis ({granularity} data): {start_date} to {end_date}")
            logger.info("=" * 70)
            
            # Load data
            datasets = self.load_data(start_date, end_date, granularity)
            
            if not datasets:
                logger.error("No data available for analysis")
                return {'error': 'No data available'}
            
            results = {
                'analysis_period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'granularity': granularity
                },
                'assets': {}
            }
            
            for product_id, data in datasets.items():
                logger.info(f"\n📊 Analyzing {product_id} ({granularity} data)")
                logger.info("-" * 40)
                
                # Volatility pattern analysis
                vol_analysis = self.analyze_volatility_patterns(data, product_id)
                
                # Signal quality analysis
                signal_analysis = self.analyze_signal_quality(data, product_id)
                
                results['assets'][product_id] = {
                    'volatility_patterns': vol_analysis,
                    'signal_quality': signal_analysis,
                    'data_points': len(data)
                }
                
                # Log key findings
                self._log_asset_findings(product_id, vol_analysis, signal_analysis)
            
            # Generate overall conclusions
            conclusions = self._generate_conclusions(results)
            results['conclusions'] = conclusions
            
            # Save results
            self._save_analysis_results(results, start_date, end_date, granularity)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {'error': str(e)}
    
    def _log_asset_findings(self, product_id: str, vol_analysis: Dict, signal_analysis: Dict):
        """Log key findings for an asset"""
        try:
            logger.info(f"📈 {product_id} Volatility Patterns:")
            logger.info(f"  Average 24h volatility: {vol_analysis.get('volatility_24h', 0):.2f}%")
            logger.info(f"  Average intraday range: {vol_analysis.get('avg_intraday_range', 0):.2f}%")
            logger.info(f"  High volatility periods (95th percentile): {vol_analysis.get('high_vol_periods_95', 0)}")
            
            clustering = vol_analysis.get('vol_clustering', {})
            logger.info(f"  Volatility clustering strength: {clustering.get('clustering_strength', 0):.3f}")
            
            directional = vol_analysis.get('directional_bias', {})
            if directional:
                logger.info(f"  Down moves avg volatility: {directional.get('down_move_avg_vol', 0):.4f}")
                logger.info(f"  Up moves avg volatility: {directional.get('up_move_avg_vol', 0):.4f}")
            
            mean_rev = vol_analysis.get('mean_reversion', {})
            if mean_rev:
                logger.info(f"  Mean reversion 1h: {mean_rev.get('mean_reversion_1h', 0):.4f}")
                logger.info(f"  Mean reversion 24h: {mean_rev.get('mean_reversion_24h', 0):.4f}")
            
            # Signal quality summary
            rsi_analysis = signal_analysis.get('rsi_analysis', {})
            if rsi_analysis:
                logger.info(f"📊 RSI Signal Quality:")
                for regime in ['low_vol', 'medium_vol', 'high_vol']:
                    regime_data = rsi_analysis.get(regime, {})
                    oversold_35_success = regime_data.get('oversold_35_success_rate', 0)
                    overbought_65_success = regime_data.get('overbought_65_success_rate', 0)
                    logger.info(f"  {regime}: Oversold(35) success: {oversold_35_success:.1%}, Overbought(65) success: {overbought_65_success:.1%}")
            
        except Exception as e:
            logger.error(f"Error logging findings: {e}")
    
    def _generate_conclusions(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall conclusions from the analysis"""
        try:
            conclusions = {
                'volatility_capture_issues': [],
                'signal_quality_issues': [],
                'recommendations': []
            }
            
            # Analyze across all assets
            for product_id, asset_data in results['assets'].items():
                vol_patterns = asset_data.get('volatility_patterns', {})
                signal_quality = asset_data.get('signal_quality', {})
                
                # Check volatility clustering
                clustering_strength = vol_patterns.get('vol_clustering', {}).get('clustering_strength', 0)
                if clustering_strength < 0.1:
                    conclusions['volatility_capture_issues'].append(f"{product_id}: Low volatility clustering ({clustering_strength:.3f}) - volatility is random, not predictable")
                
                # Check mean reversion vs momentum
                mean_rev_1h = vol_patterns.get('mean_reversion', {}).get('mean_reversion_1h', 0)
                momentum_1h = vol_patterns.get('momentum_persistence', {}).get('momentum_1h', 0)
                
                if abs(mean_rev_1h) > abs(momentum_1h):
                    conclusions['volatility_capture_issues'].append(f"{product_id}: Strong mean reversion ({mean_rev_1h:.3f}) - aggressive entries get reversed quickly")
                
                # Check signal quality in high volatility
                rsi_analysis = signal_quality.get('rsi_analysis', {})
                high_vol_rsi = rsi_analysis.get('high_vol', {})
                if high_vol_rsi:
                    oversold_success = high_vol_rsi.get('oversold_35_success_rate', 0)
                    if oversold_success < 0.5:
                        conclusions['signal_quality_issues'].append(f"{product_id}: RSI oversold signals fail in high volatility ({oversold_success:.1%} success)")
            
            # Generate recommendations
            if len(conclusions['volatility_capture_issues']) > 0:
                conclusions['recommendations'].append("Volatility is not predictably clustered - aggressive strategies based on volatility prediction will struggle")
            
            if len(conclusions['signal_quality_issues']) > 0:
                conclusions['recommendations'].append("Technical indicators perform worse in high volatility - lower thresholds capture more noise than signal")
            
            conclusions['recommendations'].append("Consider volatility-adjusted position sizing instead of volatility-based entry signals")
            conclusions['recommendations'].append("Focus on regime detection rather than volatility prediction")
            
            return conclusions
            
        except Exception as e:
            logger.error(f"Error generating conclusions: {e}")
            return {}
    
    def _save_analysis_results(self, results: Dict[str, Any], start_date: str, end_date: str, granularity: str = "hour"):
        """Save analysis results to file"""
        try:
            reports_dir = Path("./backtesting/reports")
            reports_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            date_suffix = f"{start_date.replace('-', '')}_{end_date.replace('-', '')}"
            granularity_suffix = granularity.replace('min', 'm')
            results_file = reports_dir / f"volatility_analysis_{granularity_suffix}_{date_suffix}_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"📁 Volatility analysis saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")

def main():
    """Run volatility analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Volatility Capture Effectiveness')
    parser.add_argument('--start-date', type=str, default='2025-06-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2025-07-31', help='End date (YYYY-MM-DD)')
    parser.add_argument('--granularity', type=str, default='hour', choices=['hour', '15min'], 
                       help='Data granularity (hour or 15min)')
    
    args = parser.parse_args()
    
    try:
        analyzer = VolatilityAnalyzer()
        results = analyzer.run_comprehensive_analysis(args.start_date, args.end_date, args.granularity)
        
        if 'error' in results:
            logger.error(f"Analysis failed: {results['error']}")
            sys.exit(1)
        
        # Print key conclusions
        conclusions = results.get('conclusions', {})
        
        logger.info("\n" + "=" * 70)
        logger.info("🎯 KEY CONCLUSIONS")
        logger.info("=" * 70)
        
        for issue in conclusions.get('volatility_capture_issues', []):
            logger.info(f"⚠️  {issue}")
        
        for issue in conclusions.get('signal_quality_issues', []):
            logger.info(f"📊 {issue}")
        
        logger.info(f"\n💡 RECOMMENDATIONS:")
        for rec in conclusions.get('recommendations', []):
            logger.info(f"  • {rec}")
        
        logger.info(f"\n✅ Volatility analysis completed for {args.granularity} data!")
        
    except Exception as e:
        logger.error(f"Error running analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
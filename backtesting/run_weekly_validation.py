#!/usr/bin/env python3
"""
Weekly Validation - Automated Server-Side Backtesting
Comprehensive strategy validation with 30-day performance analysis
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

# Import our backtesting infrastructure
from utils.backtest_suite import ComprehensiveBacktestSuite
from utils.indicator_factory import IndicatorFactory
from data_collector import DataCollector
from coinbase_client import CoinbaseClient
from .sync_to_gcs import GCSBacktestSync

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WeeklyValidator:
    """Weekly validation for trading strategies"""
    
    def __init__(self, sync_to_gcs: bool = False):
        """Initialize weekly validator"""
        self.sync_to_gcs = sync_to_gcs
        self.results_dir = Path("./reports/weekly")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        try:
            coinbase_client = CoinbaseClient()
            self.data_collector = DataCollector(coinbase_client, gcs_bucket_name=None)
            self.backtest_suite = ComprehensiveBacktestSuite()
            self.indicator_factory = IndicatorFactory()
            
            if sync_to_gcs:
                self.gcs_sync = GCSBacktestSync()
            
            logger.info("Weekly Validator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def load_validation_data(self, days: int = 30) -> Dict[str, pd.DataFrame]:
        """Load historical data for validation"""
        try:
            data = {}
            products = ['BTC-USD', 'ETH-USD']
            
            for product in products:
                # Try to load from existing files first
                data_files = [
                    f"data/historical/{product}_hour_180d.parquet",
                    f"data/historical/{product}_hour_30d.parquet",
                    f"data/historical/{product}_hourly_30d.parquet"
                ]
                
                df = None
                for file_path in data_files:
                    if Path(file_path).exists():
                        df = pd.read_parquet(file_path)
                        break
                
                if df is None or len(df) < days * 24:
                    logger.warning(f"Insufficient data for {product}, fetching fresh data")
                    # Fetch fresh data if needed
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days + 1)
                    
                    df = self.data_collector.fetch_bulk_historical_data(
                        product_id=product,
                        start_date=start_date,
                        end_date=end_date,
                        granularity='ONE_HOUR'
                    )
                
                # Get last N days
                if df is not None and not df.empty:
                    cutoff_date = datetime.now() - timedelta(days=days)
                    recent_df = df[df.index >= cutoff_date].copy()
                    data[product] = recent_df
                    logger.info(f"Loaded {len(recent_df)} hours of {product} data")
                else:
                    logger.error(f"Failed to load data for {product}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load validation data: {e}")
            return {}
    
    def run_strategy_validation(self, data: pd.DataFrame, product: str, 
                               strategy: str) -> Dict[str, Any]:
        """Run comprehensive validation for a single strategy"""
        try:
            # Add indicators
            data_with_indicators = self.indicator_factory.calculate_all_indicators(data, product)
            
            # Run backtest
            result = self.backtest_suite.run_single_strategy(
                data_with_indicators=data_with_indicators,
                strategy_name=strategy,
                product_id=product
            )
            
            if 'error' in result:
                logger.error(f"Strategy {strategy} failed for {product}: {result['error']}")
                return {'error': result['error']}
            
            # Calculate validation metrics
            validation_metrics = self.calculate_validation_metrics(result, data)
            
            # Analyze trading patterns
            trading_analysis = self.analyze_trading_patterns(result, data)
            
            return {
                'strategy': strategy,
                'product': product,
                'total_return': result.get('total_return', 0.0),
                'sharpe_ratio': result.get('performance', {}).get('sharpe_ratio', 0.0),
                'sortino_ratio': result.get('performance', {}).get('sortino_ratio', 0.0),
                'max_drawdown': result.get('performance', {}).get('max_drawdown', 0.0),
                'win_rate': result.get('performance', {}).get('win_rate', 0.0),
                'total_trades': result.get('signal_count', 0),
                'buy_signals': result.get('buy_signals', 0),
                'sell_signals': result.get('sell_signals', 0),
                'validation_score': validation_metrics['validation_score'],
                'validation_status': validation_metrics['validation_status'],
                'performance_grade': validation_metrics['performance_grade'],
                'risk_assessment': validation_metrics['risk_assessment'],
                'trading_analysis': trading_analysis,
                'recommendations': validation_metrics['recommendations'],
                'data_period_days': (data.index[-1] - data.index[0]).days,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Validation failed for {strategy} on {product}: {e}")
            return {'error': str(e)}
    
    def calculate_validation_metrics(self, backtest_result: Dict[str, Any], 
                                   data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive validation metrics"""
        try:
            recommendations = []
            validation_score = 100
            
            # Get metrics
            total_return = backtest_result.get('total_return', 0.0)
            sharpe_ratio = backtest_result.get('performance', {}).get('sharpe_ratio', 0.0)
            sortino_ratio = backtest_result.get('performance', {}).get('sortino_ratio', 0.0)
            max_drawdown = backtest_result.get('performance', {}).get('max_drawdown', 0.0)
            win_rate = backtest_result.get('performance', {}).get('win_rate', 0.0)
            total_trades = backtest_result.get('signal_count', 0)
            
            # Market metrics for comparison
            market_return = ((data['close'].iloc[-1] / data['close'].iloc[0]) - 1) * 100
            market_volatility = data['close'].pct_change().std() * np.sqrt(24 * 365) * 100
            
            # Performance grading
            performance_grade = self.grade_performance(total_return, sharpe_ratio, max_drawdown, win_rate)
            
            # Risk assessment
            risk_assessment = self.assess_risk_profile(max_drawdown, sharpe_ratio, sortino_ratio, market_volatility)
            
            # Validation scoring
            
            # 1. Absolute performance
            if total_return > 10:
                validation_score += 10
            elif total_return > 5:
                validation_score += 5
            elif total_return < -10:
                validation_score -= 20
                recommendations.append("Consider reducing position sizes due to poor performance")
            elif total_return < -5:
                validation_score -= 10
            
            # 2. Risk-adjusted performance
            if sharpe_ratio > 2:
                validation_score += 15
            elif sharpe_ratio > 1:
                validation_score += 10
            elif sharpe_ratio < 0:
                validation_score -= 15
                recommendations.append("Negative risk-adjusted returns - review strategy logic")
            
            # 3. Drawdown management
            if abs(max_drawdown) < 5:
                validation_score += 10
            elif abs(max_drawdown) > 20:
                validation_score -= 20
                recommendations.append("High drawdown detected - implement tighter risk controls")
            elif abs(max_drawdown) > 10:
                validation_score -= 10
            
            # 4. Consistency (win rate)
            if win_rate > 0.6:
                validation_score += 10
            elif win_rate < 0.4:
                validation_score -= 10
                recommendations.append("Low win rate - consider strategy refinement")
            
            # 5. Trading activity
            expected_trades = len(data) / 24  # Roughly 1 trade per day
            if total_trades == 0:
                validation_score -= 25
                recommendations.append("No trading activity - check signal generation logic")
            elif total_trades < expected_trades * 0.5:
                validation_score -= 10
                recommendations.append("Low trading frequency - may miss opportunities")
            elif total_trades > expected_trades * 3:
                validation_score -= 5
                recommendations.append("High trading frequency - monitor transaction costs")
            
            # 6. Market relative performance
            relative_performance = total_return - market_return
            if relative_performance > 5:
                validation_score += 10
            elif relative_performance < -10:
                validation_score -= 15
                recommendations.append(f"Underperforming market by {abs(relative_performance):.1f}%")
            
            # Determine validation status
            if validation_score >= 90:
                validation_status = "EXCELLENT"
            elif validation_score >= 75:
                validation_status = "GOOD"
            elif validation_score >= 60:
                validation_status = "ACCEPTABLE"
            elif validation_score >= 45:
                validation_status = "POOR"
            else:
                validation_status = "FAILING"
            
            return {
                'validation_score': max(0, min(100, validation_score)),
                'validation_status': validation_status,
                'performance_grade': performance_grade,
                'risk_assessment': risk_assessment,
                'recommendations': recommendations,
                'market_return': market_return,
                'market_volatility': market_volatility,
                'relative_performance': relative_performance
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate validation metrics: {e}")
            return {
                'validation_score': 0,
                'validation_status': 'ERROR',
                'performance_grade': 'F',
                'risk_assessment': 'UNKNOWN',
                'recommendations': [f"Validation calculation failed: {str(e)}"],
                'market_return': 0.0,
                'market_volatility': 0.0,
                'relative_performance': 0.0
            }
    
    def grade_performance(self, total_return: float, sharpe_ratio: float, 
                         max_drawdown: float, win_rate: float) -> str:
        """Grade overall strategy performance"""
        score = 0
        
        # Return component (40%)
        if total_return > 15:
            score += 40
        elif total_return > 10:
            score += 35
        elif total_return > 5:
            score += 30
        elif total_return > 0:
            score += 20
        elif total_return > -5:
            score += 10
        else:
            score += 0
        
        # Risk-adjusted return component (30%)
        if sharpe_ratio > 2:
            score += 30
        elif sharpe_ratio > 1.5:
            score += 25
        elif sharpe_ratio > 1:
            score += 20
        elif sharpe_ratio > 0.5:
            score += 15
        elif sharpe_ratio > 0:
            score += 10
        else:
            score += 0
        
        # Drawdown component (20%)
        if abs(max_drawdown) < 3:
            score += 20
        elif abs(max_drawdown) < 5:
            score += 18
        elif abs(max_drawdown) < 10:
            score += 15
        elif abs(max_drawdown) < 15:
            score += 10
        elif abs(max_drawdown) < 20:
            score += 5
        else:
            score += 0
        
        # Win rate component (10%)
        if win_rate > 0.7:
            score += 10
        elif win_rate > 0.6:
            score += 8
        elif win_rate > 0.5:
            score += 6
        elif win_rate > 0.4:
            score += 4
        else:
            score += 0
        
        # Convert to letter grade
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        elif score >= 45:
            return 'D'
        else:
            return 'F'
    
    def assess_risk_profile(self, max_drawdown: float, sharpe_ratio: float, 
                           sortino_ratio: float, market_volatility: float) -> str:
        """Assess strategy risk profile"""
        risk_score = 0
        
        # Drawdown risk
        if abs(max_drawdown) < 5:
            risk_score += 3
        elif abs(max_drawdown) < 10:
            risk_score += 2
        elif abs(max_drawdown) < 15:
            risk_score += 1
        elif abs(max_drawdown) > 25:
            risk_score -= 2
        
        # Risk-adjusted returns
        if sharpe_ratio > 1.5:
            risk_score += 2
        elif sharpe_ratio > 1:
            risk_score += 1
        elif sharpe_ratio < 0:
            risk_score -= 2
        
        # Downside risk (Sortino)
        if sortino_ratio > sharpe_ratio * 1.2:
            risk_score += 1  # Good downside protection
        
        # Risk classification
        if risk_score >= 5:
            return "LOW_RISK"
        elif risk_score >= 2:
            return "MODERATE_RISK"
        elif risk_score >= 0:
            return "BALANCED_RISK"
        elif risk_score >= -2:
            return "HIGH_RISK"
        else:
            return "VERY_HIGH_RISK"
    
    def analyze_trading_patterns(self, backtest_result: Dict[str, Any], 
                                data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trading patterns and behavior"""
        try:
            total_trades = backtest_result.get('signal_count', 0)
            buy_signals = backtest_result.get('buy_signals', 0)
            sell_signals = backtest_result.get('sell_signals', 0)
            
            analysis = {
                'trading_frequency': total_trades / len(data) * 24 if len(data) > 0 else 0,  # Trades per day
                'signal_balance': {
                    'buy_signals': buy_signals,
                    'sell_signals': sell_signals,
                    'buy_sell_ratio': buy_signals / sell_signals if sell_signals > 0 else float('inf')
                },
                'activity_level': 'UNKNOWN'
            }
            
            # Classify activity level
            trades_per_day = analysis['trading_frequency']
            if trades_per_day > 2:
                analysis['activity_level'] = 'HIGH'
            elif trades_per_day > 1:
                analysis['activity_level'] = 'MODERATE'
            elif trades_per_day > 0.5:
                analysis['activity_level'] = 'LOW'
            elif trades_per_day > 0:
                analysis['activity_level'] = 'VERY_LOW'
            else:
                analysis['activity_level'] = 'INACTIVE'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze trading patterns: {e}")
            return {'error': str(e)}
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive weekly validation"""
        logger.info("📊 Starting weekly validation...")
        
        # Load validation data
        data = self.load_validation_data(days=30)
        
        if not data:
            logger.error("No data available for validation")
            return {'error': 'No data available'}
        
        # Strategies to validate
        strategies = ['momentum', 'mean_reversion', 'trend_following']
        
        # Run validations
        results = {
            'timestamp': datetime.now().isoformat(),
            'validation_type': 'weekly_comprehensive',
            'data_period_days': 30,
            'strategies': {},
            'summary': {
                'total_validations': 0,
                'excellent_strategies': 0,
                'good_strategies': 0,
                'acceptable_strategies': 0,
                'poor_strategies': 0,
                'failing_strategies': 0,
                'average_score': 0.0,
                'overall_grade': 'UNKNOWN'
            },
            'recommendations': []
        }
        
        total_validations = len(strategies) * len(data)
        current_validation = 0
        total_score = 0
        
        for strategy in strategies:
            results['strategies'][strategy] = {}
            
            for product, df in data.items():
                current_validation += 1
                logger.info(f"Progress: {current_validation}/{total_validations} - Validating {strategy} on {product}")
                
                validation_result = self.run_strategy_validation(df, product, strategy)
                results['strategies'][strategy][product] = validation_result
                
                # Update summary
                if 'error' not in validation_result:
                    results['summary']['total_validations'] += 1
                    score = validation_result.get('validation_score', 0)
                    total_score += score
                    
                    status = validation_result.get('validation_status', 'UNKNOWN')
                    if status == 'EXCELLENT':
                        results['summary']['excellent_strategies'] += 1
                    elif status == 'GOOD':
                        results['summary']['good_strategies'] += 1
                    elif status == 'ACCEPTABLE':
                        results['summary']['acceptable_strategies'] += 1
                    elif status == 'POOR':
                        results['summary']['poor_strategies'] += 1
                    elif status == 'FAILING':
                        results['summary']['failing_strategies'] += 1
                    
                    # Collect recommendations
                    recommendations = validation_result.get('recommendations', [])
                    for rec in recommendations:
                        results['recommendations'].append(f"{strategy}/{product}: {rec}")
        
        # Calculate overall metrics
        total = results['summary']['total_validations']
        if total > 0:
            results['summary']['average_score'] = total_score / total
            
            # Overall grade based on distribution
            excellent_pct = results['summary']['excellent_strategies'] / total
            good_pct = results['summary']['good_strategies'] / total
            failing_pct = results['summary']['failing_strategies'] / total
            
            if excellent_pct >= 0.5:
                results['summary']['overall_grade'] = 'EXCELLENT'
            elif excellent_pct + good_pct >= 0.7:
                results['summary']['overall_grade'] = 'GOOD'
            elif failing_pct <= 0.2:
                results['summary']['overall_grade'] = 'ACCEPTABLE'
            elif failing_pct <= 0.5:
                results['summary']['overall_grade'] = 'POOR'
            else:
                results['summary']['overall_grade'] = 'FAILING'
        
        logger.info(f"Weekly validation complete: {results['summary']['overall_grade']}")
        return results
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """Save validation results"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            week_number = datetime.now().strftime("%Y-W%U")
            filename = f"weekly_validation_{week_number}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Save timestamped results
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Save as latest
            latest_filepath = self.results_dir / "latest_weekly_validation.json"
            with open(latest_filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
            # Sync to GCS if enabled
            if self.sync_to_gcs and hasattr(self, 'gcs_sync'):
                try:
                    self.gcs_sync.upload_report(results, 'weekly', 'latest_weekly_validation.json', 'server')
                    logger.info("Results synced to GCS")
                except Exception as e:
                    logger.error(f"Failed to sync to GCS: {e}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return ""

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description='Weekly Strategy Validation')
    
    parser.add_argument('--sync-gcs', action='store_true',
                       help='Sync results to Google Cloud Storage')
    
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days to analyze (default: 30)')
    
    args = parser.parse_args()
    
    try:
        # Initialize validator
        validator = WeeklyValidator(sync_to_gcs=args.sync_gcs)
        
        # Run validation
        logger.info("🚀 Starting weekly validation...")
        results = validator.run_comprehensive_validation()
        
        if 'error' in results:
            logger.error(f"Validation failed: {results['error']}")
            return False
        
        # Save results
        filepath = validator.save_results(results)
        
        # Display summary
        print("\n" + "="*80)
        print("📊 WEEKLY VALIDATION RESULTS")
        print("="*80)
        
        summary = results.get('summary', {})
        print(f"🎯 Overall Grade: {summary.get('overall_grade', 'UNKNOWN')}")
        print(f"📈 Average Score: {summary.get('average_score', 0):.1f}/100")
        print(f"⭐ Excellent: {summary.get('excellent_strategies', 0)}")
        print(f"✅ Good: {summary.get('good_strategies', 0)}")
        print(f"🔶 Acceptable: {summary.get('acceptable_strategies', 0)}")
        print(f"⚠️  Poor: {summary.get('poor_strategies', 0)}")
        print(f"❌ Failing: {summary.get('failing_strategies', 0)}")
        
        recommendations = results.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS ({len(recommendations)}):")
            for rec in recommendations[:10]:  # Show first 10
                print(f"   • {rec}")
            if len(recommendations) > 10:
                print(f"   ... and {len(recommendations) - 10} more recommendations")
        
        print(f"\n💾 Results saved to: {filepath}")
        if args.sync_gcs:
            print("☁️  Results synced to GCS")
        
        print("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"Weekly validation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
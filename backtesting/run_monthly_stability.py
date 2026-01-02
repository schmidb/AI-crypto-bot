#!/usr/bin/env python3
"""
Monthly Stability Analysis - Automated Server-Side Backtesting
Parameter stability and walk-forward analysis with 90-day comprehensive validation
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import logging

# Import our backtesting infrastructure
from utils.backtest_suite import ComprehensiveBacktestSuite
from utils.indicator_factory import IndicatorFactory
from data_collector import DataCollector
from coinbase_client import CoinbaseClient
from backtesting.sync_to_gcs import GCSBacktestSync

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MonthlyStabilityAnalyzer:
    """Monthly parameter stability and walk-forward analysis"""
    
    def __init__(self, sync_to_gcs: bool = False):
        """Initialize monthly stability analyzer"""
        self.sync_to_gcs = sync_to_gcs
        self.results_dir = Path("./reports/monthly")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        try:
            coinbase_client = CoinbaseClient()
            self.data_collector = DataCollector(coinbase_client, gcs_bucket_name=None)
            self.backtest_suite = ComprehensiveBacktestSuite()
            self.indicator_factory = IndicatorFactory()
            
            if sync_to_gcs:
                self.gcs_sync = GCSBacktestSync()
            
            logger.info("Monthly Stability Analyzer initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    def load_stability_data(self, days: int = 90) -> Dict[str, pd.DataFrame]:
        """Load historical data for stability analysis"""
        try:
            data = {}
            products = ['BTC-USD', 'ETH-USD']
            
            for product in products:
                # Try to load from existing files first
                data_files = [
                    f"data/historical/{product}_hour_180d.parquet",
                    f"data/historical/{product}_hour_365d.parquet"
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
                    start_date = end_date - timedelta(days=days + 7)  # Extra week for safety
                    
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
            logger.error(f"Failed to load stability data: {e}")
            return {}
    
    def run_walk_forward_analysis(self, data: pd.DataFrame, product: str, 
                                 strategy: str) -> Dict[str, Any]:
        """Run walk-forward analysis for parameter stability"""
        try:
            logger.info(f"Running walk-forward analysis for {strategy} on {product}")
            
            # Define parameter grids for each strategy
            param_grids = {
                'momentum': {
                    'confidence_threshold': [0.5, 0.6, 0.7],
                    'lookback_period': [8, 10, 12],
                    'volatility_threshold': [0.015, 0.02, 0.025]
                },
                'mean_reversion': {
                    'rsi_oversold': [25, 30, 35],
                    'rsi_overbought': [65, 70, 75],
                    'lookback_period': [12, 14, 16]
                },
                'trend_following': {
                    'trend_strength': [0.6, 0.7, 0.8],
                    'lookback_period': [18, 20, 22],
                    'confirmation_period': [3, 4, 5]
                }
            }
            
            param_grid = param_grids.get(strategy, {})
            if not param_grid:
                logger.warning(f"No parameter grid defined for {strategy}")
                return {'error': f'No parameter grid for {strategy}'}
            
            # Add indicators
            data_with_indicators = self.indicator_factory.calculate_all_indicators(data, product)
            
            # Run walk-forward analysis
            walk_forward_results = self.backtest_suite.run_walk_forward_analysis(
                data_with_indicators=data_with_indicators,
                strategy_name=strategy,
                param_grid=param_grid,
                product_id=product,
                train_days=30,  # 30 days training
                test_days=7,    # 7 days testing
                step_days=7     # Move forward 7 days each time
            )
            
            if 'error' in walk_forward_results:
                logger.error(f"Walk-forward analysis failed: {walk_forward_results['error']}")
                return walk_forward_results
            
            # Analyze stability
            stability_metrics = self.analyze_parameter_stability(walk_forward_results)
            
            return {
                'strategy': strategy,
                'product': product,
                'walk_forward_results': walk_forward_results,
                'stability_metrics': stability_metrics,
                'data_period_days': (data.index[-1] - data.index[0]).days,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Walk-forward analysis failed for {strategy} on {product}: {e}")
            return {'error': str(e)}
    
    def analyze_parameter_stability(self, walk_forward_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze parameter stability from walk-forward results"""
        try:
            periods = walk_forward_results.get('periods', [])
            if not periods:
                return {'error': 'No walk-forward periods found'}
            
            # Extract performance metrics across periods
            returns = []
            sharpe_ratios = []
            max_drawdowns = []
            win_rates = []
            
            for period in periods:
                test_results = period.get('test_results', {})
                returns.append(test_results.get('total_return', 0.0))
                
                performance = test_results.get('performance', {})
                sharpe_ratios.append(performance.get('sharpe_ratio', 0.0))
                max_drawdowns.append(performance.get('max_drawdown', 0.0))
                win_rates.append(performance.get('win_rate', 0.0))
            
            # Calculate stability metrics
            stability_metrics = {
                'return_stability': {
                    'mean': np.mean(returns),
                    'std': np.std(returns),
                    'coefficient_of_variation': np.std(returns) / (abs(np.mean(returns)) + 1e-6),
                    'min': np.min(returns),
                    'max': np.max(returns)
                },
                'sharpe_stability': {
                    'mean': np.mean(sharpe_ratios),
                    'std': np.std(sharpe_ratios),
                    'coefficient_of_variation': np.std(sharpe_ratios) / (abs(np.mean(sharpe_ratios)) + 1e-6),
                    'consistency_score': self.calculate_consistency_score(sharpe_ratios)
                },
                'drawdown_stability': {
                    'mean': np.mean(max_drawdowns),
                    'std': np.std(max_drawdowns),
                    'worst_drawdown': np.min(max_drawdowns),
                    'best_drawdown': np.max(max_drawdowns)
                },
                'win_rate_stability': {
                    'mean': np.mean(win_rates),
                    'std': np.std(win_rates),
                    'consistency_score': self.calculate_consistency_score(win_rates)
                }
            }
            
            # Overall stability assessment
            stability_score = self.calculate_overall_stability_score(stability_metrics)
            stability_grade = self.grade_stability(stability_score)
            
            stability_metrics['overall'] = {
                'stability_score': stability_score,
                'stability_grade': stability_grade,
                'assessment': self.assess_stability(stability_score),
                'recommendations': self.generate_stability_recommendations(stability_metrics)
            }
            
            return stability_metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze parameter stability: {e}")
            return {'error': str(e)}
    
    def calculate_consistency_score(self, values: List[float]) -> float:
        """Calculate consistency score (0-100) where higher is more consistent"""
        if not values or len(values) < 2:
            return 0.0
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if abs(mean_val) < 1e-6:
            return 0.0
        
        # Coefficient of variation (lower is better)
        cv = std_val / abs(mean_val)
        
        # Convert to consistency score (0-100)
        consistency_score = max(0, 100 - (cv * 100))
        return min(100, consistency_score)
    
    def calculate_overall_stability_score(self, stability_metrics: Dict[str, Any]) -> float:
        """Calculate overall stability score"""
        try:
            # Weight different stability components
            weights = {
                'return_stability': 0.3,
                'sharpe_stability': 0.4,
                'drawdown_stability': 0.2,
                'win_rate_stability': 0.1
            }
            
            total_score = 0.0
            
            # Return stability (lower CV is better)
            return_cv = stability_metrics['return_stability']['coefficient_of_variation']
            return_score = max(0, 100 - (return_cv * 50))  # Scale CV to 0-100
            total_score += return_score * weights['return_stability']
            
            # Sharpe stability (use consistency score)
            sharpe_consistency = stability_metrics['sharpe_stability']['consistency_score']
            total_score += sharpe_consistency * weights['sharpe_stability']
            
            # Drawdown stability (lower std is better)
            drawdown_std = stability_metrics['drawdown_stability']['std']
            drawdown_score = max(0, 100 - (drawdown_std * 5))  # Scale std to 0-100
            total_score += drawdown_score * weights['drawdown_stability']
            
            # Win rate stability (use consistency score)
            win_rate_consistency = stability_metrics['win_rate_stability']['consistency_score']
            total_score += win_rate_consistency * weights['win_rate_stability']
            
            return min(100, max(0, total_score))
            
        except Exception as e:
            logger.error(f"Failed to calculate overall stability score: {e}")
            return 0.0
    
    def grade_stability(self, stability_score: float) -> str:
        """Convert stability score to letter grade"""
        if stability_score >= 90:
            return 'A+'
        elif stability_score >= 85:
            return 'A'
        elif stability_score >= 80:
            return 'A-'
        elif stability_score >= 75:
            return 'B+'
        elif stability_score >= 70:
            return 'B'
        elif stability_score >= 65:
            return 'B-'
        elif stability_score >= 60:
            return 'C+'
        elif stability_score >= 55:
            return 'C'
        elif stability_score >= 50:
            return 'C-'
        elif stability_score >= 40:
            return 'D'
        else:
            return 'F'
    
    def assess_stability(self, stability_score: float) -> str:
        """Provide stability assessment"""
        if stability_score >= 85:
            return "HIGHLY_STABLE"
        elif stability_score >= 70:
            return "STABLE"
        elif stability_score >= 55:
            return "MODERATELY_STABLE"
        elif stability_score >= 40:
            return "UNSTABLE"
        else:
            return "HIGHLY_UNSTABLE"
    
    def generate_stability_recommendations(self, stability_metrics: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on stability analysis"""
        recommendations = []
        
        try:
            # Return stability
            return_cv = stability_metrics['return_stability']['coefficient_of_variation']
            if return_cv > 2.0:
                recommendations.append("High return variability - consider parameter regularization")
            
            # Sharpe stability
            sharpe_consistency = stability_metrics['sharpe_stability']['consistency_score']
            if sharpe_consistency < 50:
                recommendations.append("Inconsistent risk-adjusted returns - review parameter sensitivity")
            
            # Drawdown stability
            worst_drawdown = stability_metrics['drawdown_stability']['worst_drawdown']
            if worst_drawdown < -20:
                recommendations.append("Severe drawdown detected - implement stricter risk controls")
            
            drawdown_std = stability_metrics['drawdown_stability']['std']
            if drawdown_std > 5:
                recommendations.append("High drawdown variability - consider dynamic position sizing")
            
            # Win rate stability
            win_rate_consistency = stability_metrics['win_rate_stability']['consistency_score']
            if win_rate_consistency < 60:
                recommendations.append("Inconsistent win rates - strategy may be overfitted")
            
            if not recommendations:
                recommendations.append("Strategy shows good parameter stability")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate stability recommendations: {e}")
            return ["Error generating recommendations"]
    
    def run_comprehensive_stability_analysis(self) -> Dict[str, Any]:
        """Run comprehensive monthly stability analysis"""
        logger.info("📊 Starting monthly stability analysis...")
        
        # Load stability data
        data = self.load_stability_data(days=90)
        
        if not data:
            logger.error("No data available for stability analysis")
            return {'error': 'No data available'}
        
        # Strategies to analyze
        strategies = ['momentum', 'mean_reversion', 'trend_following']
        
        # Run stability analysis
        results = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'monthly_stability',
            'data_period_days': 90,
            'strategies': {},
            'summary': {
                'total_analyses': 0,
                'highly_stable_strategies': 0,
                'stable_strategies': 0,
                'moderately_stable_strategies': 0,
                'unstable_strategies': 0,
                'highly_unstable_strategies': 0,
                'average_stability_score': 0.0,
                'overall_stability_grade': 'UNKNOWN'
            },
            'recommendations': []
        }
        
        total_analyses = len(strategies) * len(data)
        current_analysis = 0
        total_stability_score = 0
        
        for strategy in strategies:
            results['strategies'][strategy] = {}
            
            for product, df in data.items():
                current_analysis += 1
                logger.info(f"Progress: {current_analysis}/{total_analyses} - Analyzing {strategy} on {product}")
                
                stability_result = self.run_walk_forward_analysis(df, product, strategy)
                results['strategies'][strategy][product] = stability_result
                
                # Update summary
                if 'error' not in stability_result:
                    results['summary']['total_analyses'] += 1
                    
                    stability_metrics = stability_result.get('stability_metrics', {})
                    overall_metrics = stability_metrics.get('overall', {})
                    stability_score = overall_metrics.get('stability_score', 0)
                    total_stability_score += stability_score
                    
                    assessment = overall_metrics.get('assessment', 'UNKNOWN')
                    if assessment == 'HIGHLY_STABLE':
                        results['summary']['highly_stable_strategies'] += 1
                    elif assessment == 'STABLE':
                        results['summary']['stable_strategies'] += 1
                    elif assessment == 'MODERATELY_STABLE':
                        results['summary']['moderately_stable_strategies'] += 1
                    elif assessment == 'UNSTABLE':
                        results['summary']['unstable_strategies'] += 1
                    elif assessment == 'HIGHLY_UNSTABLE':
                        results['summary']['highly_unstable_strategies'] += 1
                    
                    # Collect recommendations
                    recommendations = overall_metrics.get('recommendations', [])
                    for rec in recommendations:
                        results['recommendations'].append(f"{strategy}/{product}: {rec}")
        
        # Calculate overall metrics
        total = results['summary']['total_analyses']
        if total > 0:
            results['summary']['average_stability_score'] = total_stability_score / total
            
            # Overall stability grade
            stable_count = (results['summary']['highly_stable_strategies'] + 
                          results['summary']['stable_strategies'])
            unstable_count = (results['summary']['unstable_strategies'] + 
                            results['summary']['highly_unstable_strategies'])
            
            if stable_count >= total * 0.7:
                results['summary']['overall_stability_grade'] = 'STABLE'
            elif unstable_count <= total * 0.3:
                results['summary']['overall_stability_grade'] = 'MODERATELY_STABLE'
            else:
                results['summary']['overall_stability_grade'] = 'UNSTABLE'
        
        logger.info(f"Monthly stability analysis complete: {results['summary']['overall_stability_grade']}")
        return results
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """Save stability analysis results"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            month_year = datetime.now().strftime("%Y-%m")
            filename = f"monthly_stability_{month_year}_{timestamp}.json"
            filepath = self.results_dir / filename
            
            # Save timestamped results
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Save as latest
            latest_filepath = self.results_dir / "latest_monthly_stability.json"
            with open(latest_filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {filepath}")
            
            # Sync to GCS if enabled
            if self.sync_to_gcs and hasattr(self, 'gcs_sync'):
                try:
                    self.gcs_sync.upload_report(results, 'monthly', 'latest_monthly_stability.json', 'server')
                    logger.info("Results synced to GCS")
                except Exception as e:
                    logger.error(f"Failed to sync to GCS: {e}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return ""

def run_monthly_stability(sync_gcs: bool = False) -> bool:
    """Run monthly stability analysis (called from main.py scheduler)"""
    try:
        # Initialize analyzer
        analyzer = MonthlyStabilityAnalyzer(sync_to_gcs=sync_gcs)
        
        # Run stability analysis
        logger.info("🚀 Starting monthly stability analysis...")
        results = analyzer.run_comprehensive_stability_analysis()
        
        if 'error' in results:
            logger.error(f"Stability analysis failed: {results['error']}")
            return False
        
        # Save results
        filepath = analyzer.save_results(results)
        
        # Log summary
        summary = results.get('summary', {})
        logger.info(f"Monthly stability analysis complete: {summary.get('overall_stability_grade', 'UNKNOWN')}")
        logger.info(f"Average stability score: {summary.get('average_stability_score', 0):.1f}/100")
        logger.info(f"Results saved to: {filepath}")
        
        return True
        
    except Exception as e:
        logger.error(f"Monthly stability analysis failed: {e}")
        return False

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description='Monthly Parameter Stability Analysis')
    
    parser.add_argument('--sync-gcs', action='store_true',
                       help='Sync results to Google Cloud Storage')
    
    parser.add_argument('--days', type=int, default=90,
                       help='Number of days to analyze (default: 90)')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = MonthlyStabilityAnalyzer(sync_to_gcs=args.sync_gcs)
        
        # Run stability analysis
        logger.info("🚀 Starting monthly stability analysis...")
        results = analyzer.run_comprehensive_stability_analysis()
        
        if 'error' in results:
            logger.error(f"Stability analysis failed: {results['error']}")
            return False
        
        # Save results
        filepath = analyzer.save_results(results)
        
        # Display summary
        print("\n" + "="*80)
        print("📊 MONTHLY STABILITY ANALYSIS RESULTS")
        print("="*80)
        
        summary = results.get('summary', {})
        print(f"🎯 Overall Stability: {summary.get('overall_stability_grade', 'UNKNOWN')}")
        print(f"📈 Average Score: {summary.get('average_stability_score', 0):.1f}/100")
        print(f"🟢 Highly Stable: {summary.get('highly_stable_strategies', 0)}")
        print(f"✅ Stable: {summary.get('stable_strategies', 0)}")
        print(f"🔶 Moderately Stable: {summary.get('moderately_stable_strategies', 0)}")
        print(f"⚠️  Unstable: {summary.get('unstable_strategies', 0)}")
        print(f"❌ Highly Unstable: {summary.get('highly_unstable_strategies', 0)}")
        
        recommendations = results.get('recommendations', [])
        if recommendations:
            print(f"\n💡 STABILITY RECOMMENDATIONS ({len(recommendations)}):")
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
        logger.error(f"Monthly stability analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
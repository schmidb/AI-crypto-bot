#!/usr/bin/env python3
"""
Command-line interface for running backtests
"""

import argparse
from datetime import datetime
import logging
import os
import json
from backtesting import Backtester
from data_collector import DataCollector
from coinbase_client import CoinbaseClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description='Run backtests for the crypto trading bot')
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Backtest command
    backtest_parser = subparsers.add_parser('backtest', help='Run a backtest')
    backtest_parser.add_argument('--product', type=str, default='BTC-USD', help='Trading pair (e.g., BTC-USD)')
    backtest_parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    backtest_parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    backtest_parser.add_argument('--balance', type=float, default=10000.0, help='Initial balance in USD')
    backtest_parser.add_argument('--trade-size', type=float, default=1000.0, help='Size of each trade in USD')
    backtest_parser.add_argument('--output', type=str, default='backtest_results.json', help='Output file for results')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple backtests')
    compare_parser.add_argument('--products', type=str, nargs='+', default=['BTC-USD', 'ETH-USD'], help='Trading pairs to compare')
    compare_parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    compare_parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    compare_parser.add_argument('--balance', type=float, default=10000.0, help='Initial balance in USD')
    compare_parser.add_argument('--output', type=str, default='comparison_results.json', help='Output file for results')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs('backtest_results', exist_ok=True)
    
    # Initialize components
    coinbase_client = CoinbaseClient()
    data_collector = DataCollector(coinbase_client)
    backtester = Backtester(data_collector)
    
    if args.command == 'backtest':
        # Parse dates
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
        
        # Run backtest
        result = backtester.run_backtest(
            product_id=args.product,
            start_date=start_date,
            end_date=end_date,
            initial_balance_usd=args.balance,
            trade_size_usd=args.trade_size
        )
        
        # Save results
        output_file = os.path.join('backtest_results', args.output)
        result.save_results(output_file)
        
        # Print summary
        print("\nBacktest Summary:")
        print(f"Product: {args.product}")
        print(f"Period: {args.start} to {args.end}")
        print(f"Initial Balance: ${args.balance:.2f}")
        print(f"Final Balance: ${result.final_balance_usd:.2f}")
        print(f"Total Return: {result.metrics['total_return_percent']:.2f}%")
        print(f"Total Trades: {result.metrics['total_trades']}")
        print(f"Win Rate: {result.metrics['win_rate']*100:.2f}%")
        print(f"Results saved to: {output_file}")
        
    elif args.command == 'compare':
        # Parse dates
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
        
        results = {}
        metrics_comparison = {}
        
        # Run backtest for each product
        for product in args.products:
            logger.info(f"Running backtest for {product}")
            
            result = backtester.run_backtest(
                product_id=product,
                start_date=start_date,
                end_date=end_date,
                initial_balance_usd=args.balance
            )
            
            results[product] = result
            metrics_comparison[product] = result.metrics
            
            # Save individual results
            output_file = os.path.join('backtest_results', f"{product.replace('-', '_')}_results.json")
            result.save_results(output_file)
        
        # Save comparison results
        comparison_file = os.path.join('backtest_results', args.output)
        with open(comparison_file, 'w') as f:
            json.dump(metrics_comparison, f, indent=2, default=str)
        
        # Print comparison summary
        print("\nComparison Summary:")
        print(f"Period: {args.start} to {args.end}")
        print(f"Initial Balance: ${args.balance:.2f}")
        print("\nPerformance by Product:")
        
        for product, metrics in metrics_comparison.items():
            print(f"\n{product}:")
            print(f"  Final Balance: ${metrics['final_balance_usd']:.2f}")
            print(f"  Total Return: {metrics['total_return_percent']:.2f}%")
            print(f"  Total Trades: {metrics['total_trades']}")
            print(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
        
        print(f"\nComparison results saved to: {comparison_file}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

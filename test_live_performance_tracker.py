#!/usr/bin/env python3
"""
Test Live Performance Tracker

Quick test to verify the live performance tracker works correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.monitoring.live_performance_tracker import LivePerformanceTracker, generate_live_performance_report
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_live_performance_tracker():
    """Test the live performance tracker"""
    print("\n" + "="*80)
    print("Testing Live Performance Tracker")
    print("="*80 + "\n")
    
    try:
        # Test tracker initialization
        print("1. Initializing tracker...")
        tracker = LivePerformanceTracker()
        print("   ✅ Tracker initialized\n")
        
        # Test loading decisions
        print("2. Loading trading decisions from logs...")
        decisions = tracker.load_trading_decisions(days=7)
        print(f"   ✅ Loaded {len(decisions)} decisions\n")
        
        if decisions:
            print("   Sample decision:")
            print(f"   {decisions[0]}\n")
        
        # Test loading trades
        print("3. Loading executed trades from logs...")
        trades = tracker.load_executed_trades(days=7)
        print(f"   ✅ Loaded {len(trades)} trades\n")
        
        if trades:
            print("   Sample trade:")
            print(f"   {trades[0]}\n")
        
        # Test strategy analysis
        print("4. Analyzing strategy usage...")
        strategy_analysis = tracker.analyze_strategy_usage(decisions)
        print(f"   ✅ Analysis complete")
        if 'total_decisions' in strategy_analysis:
            print(f"   Total decisions: {strategy_analysis['total_decisions']}")
            print(f"   Action breakdown: {strategy_analysis['action_breakdown']}\n")
        
        # Test performance calculation
        print("5. Calculating actual performance...")
        performance = tracker.calculate_actual_performance(trades, days=7)
        print(f"   ✅ Performance calculated")
        if 'total_trades' in performance:
            print(f"   Total trades: {performance['total_trades']}")
            print(f"   Trading frequency: {performance.get('trading_frequency', 0):.2f} trades/day\n")
        
        # Test full report generation
        print("6. Generating full report...")
        report = tracker.generate_live_performance_report(days=7)
        print(f"   ✅ Report generated\n")
        
        # Test saving report
        print("7. Saving report...")
        filepath = tracker.save_report(report)
        print(f"   ✅ Report saved to: {filepath}\n")
        
        print("="*80)
        print("✅ All tests passed!")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_function_interface():
    """Test the function interface for scheduler"""
    print("\n" + "="*80)
    print("Testing Function Interface (for scheduler)")
    print("="*80 + "\n")
    
    try:
        success = generate_live_performance_report(days=7)
        
        if success:
            print("\n✅ Function interface test passed!")
        else:
            print("\n❌ Function interface test failed")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Function interface test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🧪 Live Performance Tracker Test Suite\n")
    
    # Run tests
    test1 = test_live_performance_tracker()
    test2 = test_function_interface()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Live Performance Tracker: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Function Interface: {'✅ PASS' if test2 else '❌ FAIL'}")
    print("="*80 + "\n")
    
    sys.exit(0 if (test1 and test2) else 1)

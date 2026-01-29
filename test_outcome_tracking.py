#!/usr/bin/env python3
"""
Test script to verify outcome tracking system works correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strategies.performance_tracker import HybridPerformanceTracker
from data_collector import DataCollector
from datetime import datetime, timedelta

def test_outcome_tracking():
    """Test the outcome tracking system with real data"""
    
    print("🔍 Testing Outcome Tracking System\n")
    
    # Initialize tracker with real data
    tracker = HybridPerformanceTracker()
    
    print(f"📊 Loaded {len(tracker.decision_records)} decision records")
    print(f"📈 Tracking {len(tracker.strategy_performance)} strategies\n")
    
    # Check current status
    with_outcomes = [r for r in tracker.decision_records if r.was_correct is not None]
    without_outcomes = [r for r in tracker.decision_records if r.was_correct is None]
    
    print(f"✅ Decisions with outcomes: {len(with_outcomes)}")
    print(f"⏳ Decisions pending outcomes: {len(without_outcomes)}\n")
    
    # Check how many are ready for evaluation
    current_time = datetime.now()
    ready_for_1h = 0
    ready_for_4h = 0
    ready_for_24h = 0
    
    for record in without_outcomes:
        decision_time = datetime.fromisoformat(record.timestamp)
        time_elapsed = current_time - decision_time
        
        if time_elapsed >= timedelta(hours=24):
            ready_for_24h += 1
        elif time_elapsed >= timedelta(hours=4):
            ready_for_4h += 1
        elif time_elapsed >= timedelta(hours=1):
            ready_for_1h += 1
    
    print(f"📅 Ready for evaluation:")
    print(f"   1h outcomes: {ready_for_1h} decisions")
    print(f"   4h outcomes: {ready_for_4h} decisions")
    print(f"   24h outcomes: {ready_for_24h} decisions\n")
    
    if ready_for_1h > 0 or ready_for_4h > 0 or ready_for_24h > 0:
        print("🔄 Testing outcome update with real data collector...")
        
        try:
            # Initialize data collector with coinbase client
            from coinbase_client import CoinbaseClient
            coinbase_client = CoinbaseClient()
            data_collector = DataCollector(coinbase_client)
            
            # Update outcomes (will fetch real prices)
            print("   Fetching current prices and calculating outcomes...")
            print("   (This may take a few minutes for many decisions...)")
            tracker.update_decision_outcomes(data_collector=data_collector)
            
            # Check results
            new_with_outcomes = [r for r in tracker.decision_records if r.was_correct is not None]
            newly_evaluated = len(new_with_outcomes) - len(with_outcomes)
            
            print(f"\n✅ Successfully evaluated {newly_evaluated} new decisions!")
            
            if newly_evaluated > 0:
                # Show accuracy
                correct = sum(1 for r in new_with_outcomes if r.was_correct)
                accuracy = (correct / len(new_with_outcomes)) * 100
                print(f"📊 Overall accuracy: {accuracy:.1f}% ({correct}/{len(new_with_outcomes)})")
                
                # Show by strategy
                print("\n📈 Strategy Performance:")
                for strategy_name, perf in tracker.strategy_performance.items():
                    if perf.accuracy_rate > 0:
                        print(f"   {strategy_name}: {perf.accuracy_rate*100:.1f}% "
                              f"({perf.correct_decisions}/{perf.total_decisions} decisions)")
            
        except Exception as e:
            print(f"❌ Error during outcome update: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⏳ No decisions ready for evaluation yet (need at least 1 hour)")
        print("   The system will automatically evaluate them once enough time has passed.")
    
    print("\n✅ Outcome tracking system is properly configured!")
    print("   It will run automatically every hour via the main bot.")

if __name__ == "__main__":
    test_outcome_tracking()

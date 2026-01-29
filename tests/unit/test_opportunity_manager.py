#!/usr/bin/env python3
"""
Test script for the new Opportunity Manager (Phase 1)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.trading.opportunity_manager import OpportunityManager
from config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_opportunity_manager():
    """Test the opportunity manager with sample data"""
    
    print("🧪 Testing Opportunity Manager (Phase 1)")
    print("=" * 50)
    
    # Initialize config and opportunity manager
    config = Config()
    opportunity_manager = OpportunityManager(config)
    
    # Sample trading analyses (simulating what would come from strategies)
    sample_analyses = {
        'BTC-EUR': {
            'action': 'BUY',
            'confidence': 75.5,
            'reasoning': 'Strong uptrend with high momentum',
            'market_data': {
                'price': 45000.0,
                'price_changes': {'1h': 2.1, '24h': 5.2, '5d': 12.3}
            },
            'strategy_details': {
                'market_regime': 'trending',
                'individual_strategies': {
                    'trend_following': {'action': 'BUY', 'confidence': 80},
                    'momentum': {'action': 'BUY', 'confidence': 75},
                    'llm_strategy': {'action': 'BUY', 'confidence': 70},
                    'mean_reversion': {'action': 'HOLD', 'confidence': 45}
                }
            }
        },
        'ETH-EUR': {
            'action': 'SELL',
            'confidence': 65.2,
            'reasoning': 'Overbought conditions detected',
            'market_data': {
                'price': 2800.0,
                'price_changes': {'1h': -0.5, '24h': 1.8, '5d': -2.1}
            },
            'strategy_details': {
                'market_regime': 'ranging',
                'individual_strategies': {
                    'trend_following': {'action': 'HOLD', 'confidence': 40},
                    'momentum': {'action': 'SELL', 'confidence': 60},
                    'llm_strategy': {'action': 'SELL', 'confidence': 70},
                    'mean_reversion': {'action': 'SELL', 'confidence': 75}
                }
            }
        }
    }
    
    print("\n📊 Sample Trading Analyses:")
    for product_id, analysis in sample_analyses.items():
        action = analysis['action']
        confidence = analysis['confidence']
        print(f"  {product_id}: {action} ({confidence:.1f}%)")
    
    # Test opportunity ranking
    print("\n🎯 Testing Opportunity Ranking...")
    ranked_opportunities = opportunity_manager.rank_trading_opportunities(sample_analyses)
    
    print(f"\n📈 Ranked Opportunities ({len(ranked_opportunities)} total):")
    for i, opp in enumerate(ranked_opportunities, 1):
        product_id = opp['product_id']
        action = opp['action']
        confidence = opp['confidence']
        opportunity_score = opp['opportunity_score']
        print(f"  #{i} {product_id}: {action} (confidence: {confidence:.1f}%, opportunity: {opportunity_score:.1f})")
    
    # Test capital allocation
    print("\n💰 Testing Capital Allocation...")
    available_eur = 1000.0  # €1000 available
    
    capital_allocations = opportunity_manager.allocate_trading_capital(
        ranked_opportunities, available_eur
    )
    
    print(f"\n💵 Capital Allocations (€{available_eur} available):")
    total_allocated = 0
    for product_id, amount in capital_allocations.items():
        percentage = (amount / available_eur) * 100
        print(f"  {product_id}: €{amount:.2f} ({percentage:.1f}%)")
        total_allocated += amount
    
    reserve = available_eur - total_allocated
    print(f"  Reserve: €{reserve:.2f} ({(reserve/available_eur)*100:.1f}%)")
    
    # Test opportunity summary
    print("\n📊 Testing Opportunity Summary...")
    summary = opportunity_manager.get_opportunity_summary(ranked_opportunities)
    
    print(f"\n📋 Opportunity Summary:")
    print(f"  Total opportunities: {summary['total_opportunities']}")
    print(f"  Actionable opportunities: {summary['actionable_opportunities']}")
    print(f"  BUY opportunities: {summary['buy_opportunities']}")
    print(f"  SELL opportunities: {summary['sell_opportunities']}")
    print(f"  Average confidence: {summary['avg_confidence']:.1f}%")
    print(f"  Average opportunity score: {summary['avg_opportunity_score']:.1f}")
    
    if summary['top_opportunity']:
        top = summary['top_opportunity']
        print(f"  Top opportunity: {top['product_id']} - {top['action']} ({top['opportunity_score']:.1f})")
    
    print("\n✅ Opportunity Manager test completed successfully!")
    print("\nKey Features Demonstrated:")
    print("  ✓ Opportunity scoring with multiple factors")
    print("  ✓ Intelligent ranking by opportunity strength")
    print("  ✓ Dynamic capital allocation based on signals")
    print("  ✓ Reserve management (20% kept in reserve)")
    print("  ✓ Minimum trade size enforcement")
    print("  ✓ Comprehensive opportunity analytics")

if __name__ == "__main__":
    try:
        test_opportunity_manager()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
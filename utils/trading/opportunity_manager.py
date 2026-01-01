"""
Opportunity Manager - Phase 1 Implementation
Ranks trading opportunities and dynamically allocates capital based on signal strength
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class OpportunityManager:
    """
    Manages multi-coin trading opportunities with intelligent prioritization
    """
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("supervisor")
        
        # Opportunity scoring parameters
        self.min_actionable_confidence = 50  # Minimum confidence for actionable signals
        self.consensus_bonus_threshold = 2   # Strategies needed for consensus bonus
        self.strong_consensus_threshold = 3  # Strategies needed for strong consensus
        self.momentum_threshold = 3.0        # 24h price change threshold for momentum bonus
        
        # Capital allocation parameters
        self.capital_reserve_ratio = 0.2     # Keep 20% EUR in reserve
        self.min_trade_allocation = 50.0     # Minimum €50 per trade
        self.max_single_trade_ratio = 0.6    # Max 60% of available capital to single trade
        self.opportunity_weight_power = 1.2  # Power factor for opportunity weighting
        
        self.logger.info("🎯 Opportunity Manager initialized")
        self.logger.info(f"  Min actionable confidence: {self.min_actionable_confidence}%")
        self.logger.info(f"  Capital reserve ratio: {self.capital_reserve_ratio*100:.1f}%")
        self.logger.info(f"  Max single trade ratio: {self.max_single_trade_ratio*100:.1f}%")
    
    def rank_trading_opportunities(self, trading_analyses: Dict[str, Dict]) -> List[Dict]:
        """
        Analyze all coins and rank by trading opportunity strength
        
        Args:
            trading_analyses: Dict of {product_id: analysis_result}
            
        Returns:
            List of opportunities ranked by strength (highest first)
        """
        opportunities = []
        
        for product_id, analysis in trading_analyses.items():
            try:
                # Calculate opportunity score
                opportunity_score = self._calculate_opportunity_score(analysis, product_id)
                
                opportunities.append({
                    'product_id': product_id,
                    'analysis': analysis,
                    'opportunity_score': opportunity_score,
                    'action': analysis.get('action', 'HOLD'),
                    'confidence': analysis.get('confidence', 0),
                    'reasoning': analysis.get('reasoning', ''),
                    'market_data': analysis.get('market_data', {}),
                    'strategy_details': analysis.get('strategy_details', {})
                })
                
                self.logger.debug(f"🎯 {product_id}: {analysis.get('action', 'HOLD')} "
                                f"(confidence: {analysis.get('confidence', 0):.1f}%, "
                                f"opportunity: {opportunity_score:.1f})")
                
            except Exception as e:
                self.logger.error(f"Error calculating opportunity score for {product_id}: {e}")
                # Add with minimal score to avoid breaking the flow
                opportunities.append({
                    'product_id': product_id,
                    'analysis': analysis,
                    'opportunity_score': 0,
                    'action': 'HOLD',
                    'confidence': 0,
                    'reasoning': f'Scoring error: {str(e)}',
                    'market_data': {},
                    'strategy_details': {}
                })
        
        # Sort by opportunity score (highest first)
        ranked_opportunities = sorted(opportunities, 
                                    key=lambda x: x['opportunity_score'], 
                                    reverse=True)
        
        # Log ranking results
        self.logger.info("🎯 Trading Opportunity Ranking:")
        for i, opp in enumerate(ranked_opportunities, 1):
            action = opp['action']
            confidence = opp['confidence']
            score = opp['opportunity_score']
            product_id = opp['product_id']
            
            if action in ['BUY', 'SELL']:
                self.logger.info(f"  #{i} {product_id}: {action} "
                               f"(confidence: {confidence:.1f}%, opportunity: {score:.1f})")
            else:
                self.logger.debug(f"  #{i} {product_id}: {action} "
                                f"(confidence: {confidence:.1f}%, opportunity: {score:.1f})")
        
        return ranked_opportunities
    
    def _calculate_opportunity_score(self, analysis: Dict, product_id: str) -> float:
        """
        Calculate composite opportunity score (0-100)
        
        Factors considered:
        - Base confidence from strategy analysis
        - Action type bonus (BUY/SELL vs HOLD)
        - Market momentum bonus
        - Strategy consensus bonus
        - Market regime alignment
        """
        base_confidence = float(analysis.get('confidence', 0))
        action = analysis.get('action', 'HOLD')
        
        # Start with base confidence
        opportunity_score = base_confidence
        
        # Action type multiplier
        if action in ['BUY', 'SELL']:
            opportunity_score *= 1.2  # 20% bonus for actionable signals
            self.logger.debug(f"  {product_id}: Action bonus applied ({action})")
        
        # Market momentum bonus
        momentum_bonus = self._calculate_momentum_bonus(analysis, product_id)
        opportunity_score += momentum_bonus
        
        # Strategy consensus bonus
        consensus_bonus = self._calculate_consensus_bonus(analysis, product_id)
        opportunity_score += consensus_bonus
        
        # Market regime alignment bonus
        regime_bonus = self._calculate_regime_alignment_bonus(analysis, product_id)
        opportunity_score += regime_bonus
        
        # Ensure score is within bounds
        final_score = max(0, min(100, opportunity_score))
        
        if final_score != base_confidence:
            self.logger.debug(f"  {product_id}: Score adjusted {base_confidence:.1f} -> {final_score:.1f}")
        
        return final_score
    
    def _calculate_momentum_bonus(self, analysis: Dict, product_id: str) -> float:
        """Calculate bonus based on price momentum"""
        try:
            market_data = analysis.get('market_data', {})
            price_changes = market_data.get('price_changes', {})
            
            # Get 24h price change
            change_24h = abs(float(price_changes.get('24h', 0)))
            
            if change_24h > self.momentum_threshold:
                bonus = min(10, change_24h * 2)  # Up to 10 point bonus
                self.logger.debug(f"  {product_id}: Momentum bonus +{bonus:.1f} "
                                f"(24h change: {change_24h:.1f}%)")
                return bonus
            
            return 0
            
        except Exception as e:
            self.logger.debug(f"Error calculating momentum bonus for {product_id}: {e}")
            return 0
    
    def _calculate_consensus_bonus(self, analysis: Dict, product_id: str) -> float:
        """Calculate bonus based on strategy consensus"""
        try:
            strategy_details = analysis.get('strategy_details', {})
            individual_strategies = strategy_details.get('individual_strategies', {})
            
            if not individual_strategies:
                return 0
            
            action = analysis.get('action', 'HOLD')
            
            # Count strategies that agree with final decision
            agreeing_strategies = sum(1 for strategy_data in individual_strategies.values() 
                                    if strategy_data.get('action') == action)
            
            total_strategies = len(individual_strategies)
            
            if agreeing_strategies >= self.strong_consensus_threshold:
                bonus = 15  # Strong consensus bonus
                self.logger.debug(f"  {product_id}: Strong consensus bonus +{bonus} "
                                f"({agreeing_strategies}/{total_strategies} strategies agree)")
                return bonus
            elif agreeing_strategies >= self.consensus_bonus_threshold:
                bonus = 8   # Moderate consensus bonus
                self.logger.debug(f"  {product_id}: Consensus bonus +{bonus} "
                                f"({agreeing_strategies}/{total_strategies} strategies agree)")
                return bonus
            
            return 0
            
        except Exception as e:
            self.logger.debug(f"Error calculating consensus bonus for {product_id}: {e}")
            return 0
    
    def _calculate_regime_alignment_bonus(self, analysis: Dict, product_id: str) -> float:
        """Calculate bonus based on market regime alignment"""
        try:
            strategy_details = analysis.get('strategy_details', {})
            market_regime = strategy_details.get('market_regime', 'sideways')
            action = analysis.get('action', 'HOLD')
            
            # Bonus for regime-appropriate actions
            regime_bonuses = {
                'trending': {
                    'BUY': 5,   # Good to buy in uptrends
                    'SELL': 3,  # OK to sell in trends
                    'HOLD': 0
                },
                'ranging': {
                    'BUY': 3,   # OK to buy in ranges (mean reversion)
                    'SELL': 3,  # OK to sell in ranges
                    'HOLD': 2   # HOLD often good in ranges
                },
                'volatile': {
                    'BUY': 2,   # Risky but can work
                    'SELL': 2,  # Risky but can work
                    'HOLD': 5   # Often best in volatile markets
                },
                'bear_ranging': {
                    'BUY': 1,   # Very conservative
                    'SELL': 4,  # Good to sell in bear markets
                    'HOLD': 3   # Safe choice
                }
            }
            
            bonus = regime_bonuses.get(market_regime, {}).get(action, 0)
            
            if bonus > 0:
                self.logger.debug(f"  {product_id}: Regime alignment bonus +{bonus} "
                                f"({action} in {market_regime} market)")
            
            return bonus
            
        except Exception as e:
            self.logger.debug(f"Error calculating regime alignment bonus for {product_id}: {e}")
            return 0
    
    def allocate_trading_capital(self, ranked_opportunities: List[Dict], 
                               available_eur: float) -> Dict[str, float]:
        """
        Dynamically allocate capital based on opportunity strength
        
        Args:
            ranked_opportunities: List of opportunities ranked by strength
            available_eur: Total EUR available for trading
            
        Returns:
            Dict of {product_id: allocated_amount}
        """
        if available_eur <= 0:
            self.logger.warning("No EUR available for trading")
            return {}
        
        # Filter for actionable opportunities
        actionable = [opp for opp in ranked_opportunities 
                      if opp['action'] in ['BUY', 'SELL'] 
                      and opp['confidence'] >= self.min_actionable_confidence
                      and opp['opportunity_score'] > 0]
        
        if not actionable:
            self.logger.info("🎯 No actionable opportunities found")
            return {}
        
        # Calculate available capital (keeping reserve)
        trading_capital = available_eur * (1 - self.capital_reserve_ratio)
        
        self.logger.info(f"💰 Capital Allocation:")
        self.logger.info(f"  Available EUR: €{available_eur:.2f}")
        self.logger.info(f"  Trading capital: €{trading_capital:.2f} "
                        f"(reserve: €{available_eur * self.capital_reserve_ratio:.2f})")
        self.logger.info(f"  Actionable opportunities: {len(actionable)}")
        
        # Calculate allocation weights based on opportunity scores
        allocations = self._calculate_weighted_allocations(actionable, trading_capital)
        
        # Log allocation results
        total_allocated = sum(allocations.values())
        self.logger.info(f"💰 Capital Allocation Results:")
        for product_id, amount in allocations.items():
            percentage = (amount / available_eur) * 100
            self.logger.info(f"  {product_id}: €{amount:.2f} ({percentage:.1f}% of total)")
        
        self.logger.info(f"  Total allocated: €{total_allocated:.2f} "
                        f"({(total_allocated/available_eur)*100:.1f}% of available)")
        
        return allocations
    
    def _calculate_weighted_allocations(self, actionable_opportunities: List[Dict], 
                                      trading_capital: float) -> Dict[str, float]:
        """Calculate weighted capital allocations"""
        
        # Apply power factor to opportunity scores for more pronounced differences
        weighted_scores = {}
        total_weighted_score = 0
        
        for opp in actionable_opportunities:
            # Apply power factor to amplify differences
            weighted_score = opp['opportunity_score'] ** self.opportunity_weight_power
            weighted_scores[opp['product_id']] = weighted_score
            total_weighted_score += weighted_score
        
        if total_weighted_score == 0:
            return {}
        
        # Calculate base allocations
        allocations = {}
        remaining_capital = trading_capital
        
        for opp in actionable_opportunities:
            product_id = opp['product_id']
            
            # Calculate proportional allocation
            weight = weighted_scores[product_id] / total_weighted_score
            base_allocation = trading_capital * weight
            
            # Apply minimum and maximum constraints
            min_allocation = self.min_trade_allocation
            max_allocation = trading_capital * self.max_single_trade_ratio
            
            # Ensure we don't exceed remaining capital
            max_allocation = min(max_allocation, remaining_capital)
            
            if max_allocation < min_allocation:
                # Not enough capital remaining
                self.logger.debug(f"  {product_id}: Insufficient remaining capital "
                                f"(need: €{min_allocation}, available: €{max_allocation:.2f})")
                continue
            
            # Apply constraints
            final_allocation = max(min_allocation, min(max_allocation, base_allocation))
            
            allocations[product_id] = final_allocation
            remaining_capital -= final_allocation
            
            self.logger.debug(f"  {product_id}: Weight {weight:.3f}, "
                            f"Base €{base_allocation:.2f}, Final €{final_allocation:.2f}")
            
            # Stop if we don't have enough capital for minimum allocation
            if remaining_capital < min_allocation:
                break
        
        return allocations
    
    def get_opportunity_summary(self, ranked_opportunities: List[Dict]) -> Dict[str, Any]:
        """Get summary statistics of current opportunities"""
        
        total_opportunities = len(ranked_opportunities)
        actionable = [opp for opp in ranked_opportunities 
                     if opp['action'] in ['BUY', 'SELL'] 
                     and opp['confidence'] >= self.min_actionable_confidence]
        
        buy_opportunities = [opp for opp in actionable if opp['action'] == 'BUY']
        sell_opportunities = [opp for opp in actionable if opp['action'] == 'SELL']
        
        avg_confidence = sum(opp['confidence'] for opp in ranked_opportunities) / total_opportunities if total_opportunities > 0 else 0
        avg_opportunity_score = sum(opp['opportunity_score'] for opp in ranked_opportunities) / total_opportunities if total_opportunities > 0 else 0
        
        return {
            'total_opportunities': total_opportunities,
            'actionable_opportunities': len(actionable),
            'buy_opportunities': len(buy_opportunities),
            'sell_opportunities': len(sell_opportunities),
            'avg_confidence': avg_confidence,
            'avg_opportunity_score': avg_opportunity_score,
            'top_opportunity': ranked_opportunities[0] if ranked_opportunities else None
        }
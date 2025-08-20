"""
LLM Strategy - Integrates AI analysis into the multi-strategy framework
Enhanced for Phase 3 with news sentiment integration
"""

import logging
from typing import Dict
from .base_strategy import BaseStrategy, TradingSignal

class LLMStrategy(BaseStrategy):
    """Strategy that uses LLM analysis for trading decisions with Phase 3 enhancements"""
    
    def __init__(self, config, llm_analyzer=None, news_sentiment_analyzer=None):
        super().__init__("llm_strategy", config)
        self.llm_analyzer = llm_analyzer
        self.news_sentiment_analyzer = news_sentiment_analyzer
        self.min_confidence = 60  # Lower threshold for LLM decisions
        self.logger = logging.getLogger("supervisor")  # Use supervisor logger for consistency
        
        self.logger.info(f"🔧 LLM Strategy initializing with llm_analyzer={llm_analyzer is not None}, news_sentiment_analyzer={news_sentiment_analyzer is not None}")
        
        if not self.llm_analyzer:
            self.logger.warning("LLM analyzer not provided - LLM strategy will return neutral signals")
        
        if self.news_sentiment_analyzer:
            self.logger.info("✅ Phase 3: News sentiment integration enabled")
        else:
            self.logger.info("📰 Phase 3: News sentiment not available")
    
    def analyze(self, 
                market_data: Dict,
                technical_indicators: Dict,
                portfolio: Dict) -> TradingSignal:
        """Analyze market using LLM with Phase 3 enhancements"""
        
        try:
            if not self.llm_analyzer:
                return TradingSignal(
                    action="HOLD",
                    confidence=50,
                    reasoning="LLM analyzer not available"
                )
            
            # Phase 3: Get news sentiment
            news_sentiment = self._get_news_sentiment(market_data)
            
            # Prepare enhanced data for LLM analysis
            llm_input_data = self._prepare_enhanced_llm_data(
                market_data, technical_indicators, portfolio, news_sentiment
            )
            
            # Get LLM analysis
            self.logger.debug(f"Requesting enhanced LLM analysis for {llm_input_data.get('product_id', 'unknown')}")
            llm_result = self.llm_analyzer.analyze_market(llm_input_data)
            
            # Convert LLM result to TradingSignal format with sentiment adjustment
            signal = self._convert_llm_result_with_sentiment(llm_result, news_sentiment)
            
            self.logger.debug(f"Enhanced LLM strategy: {signal.action} (confidence: {signal.confidence:.1f}%)")
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in enhanced LLM strategy analysis: {e}")
            return TradingSignal(
                action="HOLD",
                confidence=30,
                reasoning=f"Enhanced LLM analysis error: {str(e)}"
            )
    
    def _get_news_sentiment(self, market_data: Dict) -> Dict:
        """Get news sentiment for the asset (Phase 3)"""
        
        if not self.news_sentiment_analyzer:
            self.logger.info("News sentiment analyzer not available")
            return {"overall_sentiment": 0.0, "sentiment_category": "neutral", "confidence": 0.3, "article_count": 0}
        
        try:
            # Extract asset name from product_id
            product_id = market_data.get('product_id', 'BTC-EUR')
            asset = product_id.split('-')[0].lower()
            
            # Map asset symbols to full names
            asset_mapping = {
                'btc': 'bitcoin',
                'eth': 'ethereum', 
                'sol': 'solana'
            }
            
            asset_name = asset_mapping.get(asset, asset)
            
            self.logger.info(f"Getting news sentiment for {product_id} -> {asset} -> {asset_name}")
            
            # Get sentiment analysis
            sentiment = self.news_sentiment_analyzer.get_market_sentiment(asset_name)
            
            self.logger.info(f"News sentiment for {asset_name}: {sentiment['sentiment_category']} ({sentiment['overall_sentiment']:.2f}), articles: {sentiment.get('article_count', 0)}")
            return sentiment
            
        except Exception as e:
            self.logger.error(f"Error getting news sentiment: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return {"overall_sentiment": 0.0, "sentiment_category": "neutral", "confidence": 0.3, "article_count": 0}
    
    def _prepare_enhanced_llm_data(self, 
                                 market_data: Dict, 
                                 technical_indicators: Dict, 
                                 portfolio: Dict,
                                 news_sentiment: Dict) -> Dict:
        """Prepare enhanced data for LLM analysis with Phase 3 features"""
        
        # Get product ID from market data or technical indicators
        product_id = market_data.get('product_id', 'Unknown')
        if not product_id or product_id == 'Unknown':
            product_id = technical_indicators.get('product_id', 'BTC-EUR')
        
        # Get current price from market data
        current_price = market_data.get('price', 0)
        
        # Prepare the enhanced data structure for LLM analyzer
        llm_data = {
            "product_id": product_id,
            "current_price": current_price,
            "indicators": technical_indicators,
            "market_data": market_data,
            "historical_data": [],  # Could be populated later if needed
            "portfolio": portfolio,
            # Phase 3 enhancements
            "news_sentiment": news_sentiment,
            "enhanced_context": self._create_enhanced_context(market_data, news_sentiment)
        }
        
        return llm_data
    
    def _create_enhanced_context(self, market_data: Dict, news_sentiment: Dict) -> str:
        """Create enhanced context string for LLM with Phase 3 information"""
        
        context_parts = []
        
        # Market context
        if 'price_changes' in market_data:
            changes = market_data['price_changes']
            context_parts.append(f"Recent price performance: 1h={changes.get('1h', 0):+.1f}%, 24h={changes.get('24h', 0):+.1f}%, 5d={changes.get('5d', 0):+.1f}%")
        
        # News sentiment context
        sentiment_category = news_sentiment.get('sentiment_category', 'neutral')
        sentiment_score = news_sentiment.get('overall_sentiment', 0)
        sentiment_confidence = news_sentiment.get('confidence', 0.3)
        article_count = news_sentiment.get('article_count', 0)
        
        if article_count > 0:
            context_parts.append(f"News sentiment: {sentiment_category} (score: {sentiment_score:+.2f}, confidence: {sentiment_confidence:.1%}, {article_count} articles)")
        else:
            context_parts.append("News sentiment: neutral (no recent news data)")
        
        # Market regime context
        current_price = market_data.get('price', 0)
        if current_price > 0 and 'price_changes' in market_data:
            changes = market_data['price_changes']
            if changes.get('24h', 0) > 5:
                context_parts.append("Market regime: Strong bullish momentum")
            elif changes.get('24h', 0) < -5:
                context_parts.append("Market regime: Strong bearish pressure")
            else:
                context_parts.append("Market regime: Consolidation/sideways")
        
        return "; ".join(context_parts)
    
    def _convert_llm_result_with_sentiment(self, llm_result: Dict, news_sentiment: Dict) -> TradingSignal:
        """Convert LLM analysis result to TradingSignal with sentiment adjustment"""
        
        # Extract action, confidence, and reasoning from LLM result
        # FIX: LLM analyzer returns 'decision' field, not 'action'
        action = llm_result.get('decision', 'HOLD').upper()
        confidence = float(llm_result.get('confidence', 50))
        reasoning = llm_result.get('reasoning', 'LLM analysis completed')
        
        # Ensure action is valid
        if action not in ['BUY', 'SELL', 'HOLD']:
            self.logger.warning(f"Invalid LLM action '{action}', defaulting to HOLD")
            action = 'HOLD'
            confidence = 30
            reasoning = f"Invalid LLM action: {reasoning}"
        
        # Phase 3: Apply news sentiment adjustment
        sentiment_adjustment = self._calculate_sentiment_adjustment(action, news_sentiment)
        adjusted_confidence = confidence + sentiment_adjustment
        
        # Ensure confidence is in valid range
        adjusted_confidence = max(0, min(100, adjusted_confidence))
        
        # Create enhanced reasoning with sentiment information
        sentiment_info = self._format_sentiment_info(news_sentiment, sentiment_adjustment)
        enhanced_reasoning = f"Enhanced LLM analysis: {reasoning}"
        
        if sentiment_info:
            enhanced_reasoning += f"; News sentiment: {sentiment_info}"
        
        return TradingSignal(
            action=action,
            confidence=adjusted_confidence,
            reasoning=enhanced_reasoning
        )
    
    def _calculate_sentiment_adjustment(self, action: str, news_sentiment: Dict) -> float:
        """Calculate confidence adjustment based on news sentiment alignment"""
        
        sentiment_score = news_sentiment.get('overall_sentiment', 0)
        sentiment_confidence = news_sentiment.get('confidence', 0.3)
        
        # Calculate alignment between action and sentiment
        if action == 'BUY' and sentiment_score > 0.2:
            # Bullish action with positive sentiment
            adjustment = sentiment_score * 10 * sentiment_confidence  # Up to +10 points
        elif action == 'SELL' and sentiment_score < -0.2:
            # Bearish action with negative sentiment  
            adjustment = abs(sentiment_score) * 10 * sentiment_confidence  # Up to +10 points
        elif action == 'HOLD':
            # HOLD action gets small boost for any clear sentiment
            adjustment = abs(sentiment_score) * 2 * sentiment_confidence  # Up to +2 points
        else:
            # Action conflicts with sentiment
            adjustment = -abs(sentiment_score) * 5 * sentiment_confidence  # Up to -5 points
        
        return adjustment
    
    def _format_sentiment_info(self, news_sentiment: Dict, adjustment: float) -> str:
        """Format sentiment information for reasoning"""
        
        sentiment_category = news_sentiment.get('sentiment_category', 'neutral')
        sentiment_score = news_sentiment.get('overall_sentiment', 0)
        article_count = news_sentiment.get('article_count', 0)
        
        if article_count == 0:
            return "no recent news data"
        
        sentiment_desc = f"{sentiment_category} ({sentiment_score:+.2f})"
        adjustment_desc = f"confidence {adjustment:+.1f}" if abs(adjustment) > 0.5 else "neutral impact"
        
        return f"{sentiment_desc} from {article_count} articles, {adjustment_desc}"
    
    def get_market_regime_suitability(self, regime: str) -> float:
        """Return suitability score for different market regimes (Phase 3 enhanced)"""
        
        # Enhanced suitability based on Phase 3 capabilities
        regime_suitability = {
            "bull": 0.85,     # Excellent with news sentiment for bull markets
            "bear": 0.85,     # Excellent with news sentiment for bear markets  
            "sideways": 0.95, # Outstanding at complex sideways market analysis
            "volatile": 0.95, # Outstanding at handling volatility with news context
            "high_volatility": 0.9,  # Very good with enhanced context
            "low_volatility": 0.8    # Good for stable conditions
        }
        
        return regime_suitability.get(regime.lower(), 0.85)
    
    def get_strategy_info(self) -> Dict:
        """Return enhanced strategy information"""
        return {
            "name": self.name,
            "type": "AI-powered (Phase 3 Enhanced)",
            "description": "Uses Large Language Model with news sentiment analysis",
            "min_confidence": self.min_confidence,
            "llm_available": self.llm_analyzer is not None,
            "news_sentiment_available": self.news_sentiment_analyzer is not None,
            "phase": 3,
            "enhancements": [
                "News sentiment integration",
                "Enhanced market context",
                "Sentiment-based confidence adjustment"
            ]
        }

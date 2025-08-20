"""
News Sentiment Analyzer for Phase 3
Integrates market news sentiment into trading decisions
"""

import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

class NewsSentimentAnalyzer:
    """Analyze news sentiment for cryptocurrency markets"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = 3600  # 1 hour cache
        
        # News sources (free APIs)
        self.news_sources = {
            "cryptonews": "https://cryptonews-api.com/api/v1/category",
            "newsapi": "https://newsapi.org/v2/everything"
        }
        
        self.logger.info("News sentiment analyzer initialized")
    
    def get_market_sentiment(self, asset: str = "bitcoin") -> Dict:
        """Get overall market sentiment for an asset"""
        
        cache_key = f"sentiment_{asset}"
        
        # Check cache
        if self._is_cached(cache_key):
            self.logger.debug(f"Using cached sentiment for {asset}")
            return self.cache[cache_key]["data"]
        
        try:
            # Get news articles
            articles = self._fetch_news_articles(asset)
            
            # Analyze sentiment
            sentiment_analysis = self._analyze_articles_sentiment(articles)
            
            # Cache results
            self.cache[cache_key] = {
                "timestamp": datetime.now(),
                "data": sentiment_analysis
            }
            
            self.logger.info(f"Sentiment analysis completed for {asset}: {sentiment_analysis['overall_sentiment']}")
            return sentiment_analysis
            
        except Exception as e:
            self.logger.error(f"Error getting market sentiment for {asset}: {e}")
            return self._get_neutral_sentiment()
    
    def _fetch_news_articles(self, asset: str) -> List[Dict]:
        """Fetch recent news articles about the asset"""
        
        articles = []
        
        # Mock news data for demonstration (in production, would use real APIs)
        mock_articles = self._get_mock_news_data(asset)
        articles.extend(mock_articles)
        
        self.logger.debug(f"Fetched {len(articles)} articles for {asset}")
        return articles
    
    def _get_mock_news_data(self, asset: str) -> List[Dict]:
        """Generate mock news data based on current market conditions"""
        
        # In production, this would fetch from real news APIs
        # For now, we'll generate contextual mock data
        
        current_time = datetime.now()
        
        if asset.lower() in ["bitcoin", "btc"]:
            return [
                {
                    "title": "Bitcoin Shows Strong Institutional Adoption",
                    "content": "Major corporations continue to add Bitcoin to their treasury reserves",
                    "sentiment_score": 0.7,
                    "timestamp": current_time - timedelta(hours=2),
                    "source": "crypto_news"
                },
                {
                    "title": "Regulatory Clarity Boosts Bitcoin Confidence",
                    "content": "New regulatory framework provides clearer guidelines for cryptocurrency trading",
                    "sentiment_score": 0.6,
                    "timestamp": current_time - timedelta(hours=4),
                    "source": "financial_times"
                },
                {
                    "title": "Market Volatility Concerns Persist",
                    "content": "Analysts warn of potential market corrections amid economic uncertainty",
                    "sentiment_score": -0.3,
                    "timestamp": current_time - timedelta(hours=6),
                    "source": "market_watch"
                }
            ]
        elif asset.lower() in ["ethereum", "eth"]:
            return [
                {
                    "title": "Ethereum Network Upgrades Drive Optimism",
                    "content": "Latest network improvements show significant scalability gains",
                    "sentiment_score": 0.8,
                    "timestamp": current_time - timedelta(hours=1),
                    "source": "eth_news"
                },
                {
                    "title": "DeFi Activity Surges on Ethereum",
                    "content": "Decentralized finance protocols see record transaction volumes",
                    "sentiment_score": 0.6,
                    "timestamp": current_time - timedelta(hours=3),
                    "source": "defi_pulse"
                }
            ]
        elif asset.lower() in ["solana", "sol"]:
            return [
                {
                    "title": "Solana Ecosystem Expansion Continues",
                    "content": "New partnerships and integrations boost Solana adoption",
                    "sentiment_score": 0.5,
                    "timestamp": current_time - timedelta(hours=2),
                    "source": "solana_news"
                },
                {
                    "title": "Network Stability Improvements Noted",
                    "content": "Recent upgrades address previous network reliability concerns",
                    "sentiment_score": 0.4,
                    "timestamp": current_time - timedelta(hours=5),
                    "source": "crypto_daily"
                }
            ]
        
        return []
    
    def _analyze_articles_sentiment(self, articles: List[Dict]) -> Dict:
        """Analyze sentiment from news articles"""
        
        if not articles:
            return self._get_neutral_sentiment()
        
        # Calculate weighted sentiment
        total_weight = 0
        weighted_sentiment = 0
        sentiment_distribution = {"positive": 0, "neutral": 0, "negative": 0}
        
        for article in articles:
            # Weight recent articles more heavily
            age_hours = (datetime.now() - article["timestamp"]).total_seconds() / 3600
            weight = max(0.1, 1.0 - (age_hours / 24))  # Decay over 24 hours
            
            sentiment_score = article.get("sentiment_score", 0)
            weighted_sentiment += sentiment_score * weight
            total_weight += weight
            
            # Categorize sentiment
            if sentiment_score > 0.2:
                sentiment_distribution["positive"] += weight
            elif sentiment_score < -0.2:
                sentiment_distribution["negative"] += weight
            else:
                sentiment_distribution["neutral"] += weight
        
        # Calculate overall sentiment
        overall_sentiment = weighted_sentiment / total_weight if total_weight > 0 else 0
        
        # Normalize distribution
        total_dist = sum(sentiment_distribution.values())
        if total_dist > 0:
            sentiment_distribution = {k: v/total_dist for k, v in sentiment_distribution.items()}
        
        # Determine sentiment category
        if overall_sentiment > 0.3:
            sentiment_category = "bullish"
        elif overall_sentiment < -0.3:
            sentiment_category = "bearish"
        else:
            sentiment_category = "neutral"
        
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_category": sentiment_category,
            "sentiment_distribution": sentiment_distribution,
            "article_count": len(articles),
            "confidence": min(0.9, abs(overall_sentiment) + 0.3),
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_neutral_sentiment(self) -> Dict:
        """Return neutral sentiment when no data available"""
        return {
            "overall_sentiment": 0.0,
            "sentiment_category": "neutral",
            "sentiment_distribution": {"positive": 0.33, "neutral": 0.34, "negative": 0.33},
            "article_count": 0,
            "confidence": 0.3,
            "last_updated": datetime.now().isoformat()
        }
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if data is cached and still valid"""
        
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]["timestamp"]
        age_seconds = (datetime.now() - cache_time).total_seconds()
        
        return age_seconds < self.cache_duration
    
    def get_sentiment_summary(self) -> Dict:
        """Get summary of all cached sentiment data"""
        
        summary = {
            "cached_assets": len(self.cache),
            "cache_status": {},
            "overall_market_sentiment": 0.0
        }
        
        total_sentiment = 0
        valid_entries = 0
        
        for asset, cache_data in self.cache.items():
            age_minutes = (datetime.now() - cache_data["timestamp"]).total_seconds() / 60
            is_fresh = age_minutes < 60
            
            summary["cache_status"][asset] = {
                "age_minutes": age_minutes,
                "is_fresh": is_fresh,
                "sentiment": cache_data["data"]["overall_sentiment"]
            }
            
            if is_fresh:
                total_sentiment += cache_data["data"]["overall_sentiment"]
                valid_entries += 1
        
        if valid_entries > 0:
            summary["overall_market_sentiment"] = total_sentiment / valid_entries
        
        return summary

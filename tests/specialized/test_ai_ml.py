"""
AI/ML Tests

Tests AI/ML model performance, prediction accuracy, decision consistency,
and bias detection for the LLM-based trading analysis system.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from collections import Counter
import json

from llm_analyzer import LLMAnalyzer
from strategies.llm_strategy import LLMStrategy
from strategies.adaptive_strategy_manager import AdaptiveStrategyManager


class TestModelPerformance:
    """Test AI model performance and reliability"""
    
    def test_llm_response_consistency(self):
        """Test that LLM responses are consistent for similar inputs"""
        analyzer = LLMAnalyzer()
        
        # Create identical market data
        market_data = pd.DataFrame({
            'close': [45000.0],
            'high': [46000.0],
            'low': [44000.0],
            'volume': [1000000],
            'rsi': [65.0],
            'macd': [0.5],
            'bb_position': [0.7]
        })
        
        responses = []
        with patch.object(analyzer, '_call_genai') as mock_genai:
            # Mock consistent response
            mock_genai.return_value = {
                'decision': 'BUY',
                'confidence': 75,
                'reasoning': 'Strong technical indicators'
            }
            
            # Get multiple responses for same input
            for _ in range(5):
                response = analyzer.analyze_market_data(market_data, 45000.0, 'BTC-EUR')
                responses.append(response)
        
        # All responses should be identical for same input
        first_response = responses[0]
        for response in responses[1:]:
            assert response['decision'] == first_response['decision']
            assert response['confidence'] == first_response['confidence']
    
    def test_confidence_score_reliability(self):
        """Test that confidence scores are reliable and within valid range"""
        analyzer = LLMAnalyzer()
        
        test_scenarios = [
            # Strong bullish scenario
            {'rsi': 30, 'macd': 1.5, 'bb_position': 0.2, 'expected_confidence': 80},
            # Strong bearish scenario  
            {'rsi': 80, 'macd': -1.5, 'bb_position': 0.9, 'expected_confidence': 80},
            # Neutral scenario
            {'rsi': 50, 'macd': 0.1, 'bb_position': 0.5, 'expected_confidence': 40},
        ]
        
        for scenario in test_scenarios:
            market_data = pd.DataFrame({
                'close': [45000.0],
                'high': [46000.0],
                'low': [44000.0],
                'volume': [1000000],
                'rsi': [scenario['rsi']],
                'macd': [scenario['macd']],
                'bb_position': [scenario['bb_position']]
            })
            
            with patch.object(analyzer, '_call_genai') as mock_genai:
                mock_genai.return_value = {
                    'decision': 'BUY' if scenario['rsi'] < 40 else 'SELL' if scenario['rsi'] > 70 else 'HOLD',
                    'confidence': scenario['expected_confidence'],
                    'reasoning': 'Test scenario'
                }
                
                response = analyzer.analyze_market_data(market_data, 45000.0, 'BTC-EUR')
                
                # Confidence should be within valid range
                assert 0 <= response['confidence'] <= 100
                # Should match expected confidence level
                assert abs(response['confidence'] - scenario['expected_confidence']) <= 10
    
    def test_decision_distribution(self):
        """Test that decisions are distributed appropriately across different market conditions"""
        analyzer = LLMAnalyzer()
        
        decisions = []
        market_conditions = [
            # Bullish conditions
            {'rsi': 25, 'macd': 2.0, 'bb_position': 0.1, 'expected': 'BUY'},
            {'rsi': 30, 'macd': 1.5, 'bb_position': 0.2, 'expected': 'BUY'},
            {'rsi': 35, 'macd': 1.0, 'bb_position': 0.3, 'expected': 'BUY'},
            # Bearish conditions
            {'rsi': 75, 'macd': -2.0, 'bb_position': 0.9, 'expected': 'SELL'},
            {'rsi': 80, 'macd': -1.5, 'bb_position': 0.8, 'expected': 'SELL'},
            {'rsi': 85, 'macd': -1.0, 'bb_position': 0.7, 'expected': 'SELL'},
            # Neutral conditions
            {'rsi': 50, 'macd': 0.1, 'bb_position': 0.5, 'expected': 'HOLD'},
            {'rsi': 55, 'macd': -0.1, 'bb_position': 0.4, 'expected': 'HOLD'},
        ]
        
        for condition in market_conditions:
            market_data = pd.DataFrame({
                'close': [45000.0],
                'high': [46000.0],
                'low': [44000.0],
                'volume': [1000000],
                'rsi': [condition['rsi']],
                'macd': [condition['macd']],
                'bb_position': [condition['bb_position']]
            })
            
            with patch.object(analyzer, '_call_genai') as mock_genai:
                mock_genai.return_value = {
                    'decision': condition['expected'],
                    'confidence': 70,
                    'reasoning': 'Test condition'
                }
                
                response = analyzer.analyze_market_data(market_data, 45000.0, 'BTC-EUR')
                decisions.append(response['decision'])
        
        # Count decision distribution
        decision_counts = Counter(decisions)
        
        # Should have reasonable distribution
        assert decision_counts['BUY'] >= 2  # At least 2 BUY decisions
        assert decision_counts['SELL'] >= 2  # At least 2 SELL decisions
        assert decision_counts['HOLD'] >= 1  # At least 1 HOLD decision
    
    def test_model_response_validation(self):
        """Test that model responses are properly validated"""
        analyzer = LLMAnalyzer()
        
        market_data = pd.DataFrame({
            'close': [45000.0],
            'high': [46000.0],
            'low': [44000.0],
            'volume': [1000000],
            'rsi': [65.0],
            'macd': [0.5],
            'bb_position': [0.7]
        })
        
        # Test with invalid model responses
        invalid_responses = [
            {'decision': 'INVALID', 'confidence': 75},  # Invalid decision
            {'decision': 'BUY', 'confidence': 150},     # Invalid confidence
            {'decision': 'BUY', 'confidence': -10},     # Negative confidence
            {'action': 'BUY', 'confidence': 75},        # Wrong key name
            {'decision': 'BUY'},                        # Missing confidence
        ]
        
        for invalid_response in invalid_responses:
            with patch.object(analyzer, '_call_genai') as mock_genai:
                mock_genai.return_value = invalid_response
                
                response = analyzer.analyze_market_data(market_data, 45000.0, 'BTC-EUR')
                
                # Should handle invalid responses gracefully
                assert response['decision'] in ['BUY', 'SELL', 'HOLD']
                assert 0 <= response['confidence'] <= 100


class TestPredictionAccuracy:
    """Test prediction accuracy and decision quality"""
    
    def test_technical_indicator_interpretation(self):
        """Test that technical indicators are interpreted correctly"""
        analyzer = LLMAnalyzer()
        
        # Test oversold condition (should suggest BUY)
        oversold_data = pd.DataFrame({
            'close': [45000.0],
            'high': [46000.0],
            'low': [44000.0],
            'volume': [1000000],
            'rsi': [20],  # Oversold
            'macd': [1.0],  # Bullish
            'bb_position': [0.1]  # Near lower band
        })
        
        with patch.object(analyzer, '_call_genai') as mock_genai:
            mock_genai.return_value = {
                'decision': 'BUY',
                'confidence': 80,
                'reasoning': 'Oversold conditions indicate buying opportunity'
            }
            
            response = analyzer.analyze_market_data(oversold_data, 45000.0, 'BTC-EUR')
            assert response['decision'] == 'BUY'
            assert response['confidence'] >= 70
        
        # Test overbought condition (should suggest SELL)
        overbought_data = pd.DataFrame({
            'close': [45000.0],
            'high': [46000.0],
            'low': [44000.0],
            'volume': [1000000],
            'rsi': [85],  # Overbought
            'macd': [-1.0],  # Bearish
            'bb_position': [0.9]  # Near upper band
        })
        
        with patch.object(analyzer, '_call_genai') as mock_genai:
            mock_genai.return_value = {
                'decision': 'SELL',
                'confidence': 80,
                'reasoning': 'Overbought conditions indicate selling opportunity'
            }
            
            response = analyzer.analyze_market_data(overbought_data, 45000.0, 'BTC-EUR')
            assert response['decision'] == 'SELL'
            assert response['confidence'] >= 70
    
    def test_market_trend_recognition(self):
        """Test market trend recognition accuracy"""
        analyzer = LLMAnalyzer()
        
        # Create trending market data
        uptrend_prices = [40000, 41000, 42000, 43000, 44000, 45000]
        downtrend_prices = [50000, 49000, 48000, 47000, 46000, 45000]
        sideways_prices = [45000, 45100, 44900, 45050, 44950, 45000]
        
        trend_scenarios = [
            (uptrend_prices, 'BUY', 'Uptrend'),
            (downtrend_prices, 'SELL', 'Downtrend'),
            (sideways_prices, 'HOLD', 'Sideways')
        ]
        
        for prices, expected_decision, trend_type in trend_scenarios:
            market_data = pd.DataFrame({
                'close': prices,
                'high': [p * 1.02 for p in prices],
                'low': [p * 0.98 for p in prices],
                'volume': [1000000] * len(prices),
                'rsi': [50] * len(prices),
                'macd': [0.5 if expected_decision == 'BUY' else -0.5 if expected_decision == 'SELL' else 0.1] * len(prices),
                'bb_position': [0.5] * len(prices)
            })
            
            with patch.object(analyzer, '_call_genai') as mock_genai:
                mock_genai.return_value = {
                    'decision': expected_decision,
                    'confidence': 75,
                    'reasoning': f'{trend_type} detected'
                }
                
                response = analyzer.analyze_market_data(market_data, prices[-1], 'BTC-EUR')
                assert response['decision'] == expected_decision
    
    def test_volatility_assessment(self):
        """Test volatility assessment accuracy"""
        analyzer = LLMAnalyzer()
        
        # High volatility scenario
        high_vol_data = pd.DataFrame({
            'close': [45000.0],
            'high': [48000.0],  # Large range
            'low': [42000.0],
            'volume': [5000000],  # High volume
            'rsi': [50],
            'macd': [0.1],
            'bb_position': [0.5]
        })
        
        # Low volatility scenario
        low_vol_data = pd.DataFrame({
            'close': [45000.0],
            'high': [45200.0],  # Small range
            'low': [44800.0],
            'volume': [500000],  # Low volume
            'rsi': [50],
            'macd': [0.1],
            'bb_position': [0.5]
        })
        
        volatility_scenarios = [
            (high_vol_data, 'high', 'HOLD'),  # High volatility -> cautious
            (low_vol_data, 'low', 'BUY')     # Low volatility -> more confident
        ]
        
        for data, vol_type, expected_decision in volatility_scenarios:
            with patch.object(analyzer, '_call_genai') as mock_genai:
                mock_genai.return_value = {
                    'decision': expected_decision,
                    'confidence': 60 if vol_type == 'high' else 80,
                    'reasoning': f'{vol_type} volatility detected'
                }
                
                response = analyzer.analyze_market_data(data, 45000.0, 'BTC-EUR')
                
                # High volatility should result in lower confidence
                if vol_type == 'high':
                    assert response['confidence'] <= 70
                else:
                    assert response['confidence'] >= 70


class TestDecisionConsistency:
    """Test decision consistency across different scenarios"""
    
    def test_similar_conditions_consistency(self):
        """Test that similar market conditions produce consistent decisions"""
        analyzer = LLMAnalyzer()
        
        # Create similar market conditions
        similar_conditions = []
        for i in range(5):
            data = pd.DataFrame({
                'close': [45000.0 + i * 10],  # Slight price variation
                'high': [46000.0 + i * 10],
                'low': [44000.0 + i * 10],
                'volume': [1000000 + i * 1000],
                'rsi': [65.0 + i * 0.5],  # Slight RSI variation
                'macd': [0.5 + i * 0.01],
                'bb_position': [0.7 + i * 0.01]
            })
            similar_conditions.append(data)
        
        decisions = []
        confidences = []
        
        for data in similar_conditions:
            with patch.object(analyzer, '_call_genai') as mock_genai:
                mock_genai.return_value = {
                    'decision': 'BUY',
                    'confidence': 75,
                    'reasoning': 'Similar conditions'
                }
                
                response = analyzer.analyze_market_data(data, 45000.0, 'BTC-EUR')
                decisions.append(response['decision'])
                confidences.append(response['confidence'])
        
        # Decisions should be consistent for similar conditions
        unique_decisions = set(decisions)
        assert len(unique_decisions) <= 2  # At most 2 different decisions
        
        # Confidence levels should be similar
        confidence_std = np.std(confidences)
        assert confidence_std <= 10  # Standard deviation <= 10
    
    def test_extreme_conditions_handling(self):
        """Test handling of extreme market conditions"""
        analyzer = LLMAnalyzer()
        
        extreme_conditions = [
            # Extreme oversold
            {'rsi': 5, 'macd': 3.0, 'bb_position': 0.0, 'expected': 'BUY'},
            # Extreme overbought
            {'rsi': 95, 'macd': -3.0, 'bb_position': 1.0, 'expected': 'SELL'},
            # Extreme volatility
            {'rsi': 50, 'macd': 0.0, 'bb_position': 0.5, 'volume_multiplier': 10, 'expected': 'HOLD'},
        ]
        
        for condition in extreme_conditions:
            market_data = pd.DataFrame({
                'close': [45000.0],
                'high': [46000.0],
                'low': [44000.0],
                'volume': [1000000 * condition.get('volume_multiplier', 1)],
                'rsi': [condition['rsi']],
                'macd': [condition['macd']],
                'bb_position': [condition['bb_position']]
            })
            
            with patch.object(analyzer, '_call_genai') as mock_genai:
                mock_genai.return_value = {
                    'decision': condition['expected'],
                    'confidence': 85 if condition['expected'] != 'HOLD' else 60,
                    'reasoning': 'Extreme condition detected'
                }
                
                response = analyzer.analyze_market_data(market_data, 45000.0, 'BTC-EUR')
                
                # Should handle extreme conditions without errors
                assert response['decision'] in ['BUY', 'SELL', 'HOLD']
                assert 0 <= response['confidence'] <= 100
    
    def test_temporal_consistency(self):
        """Test consistency across different time periods"""
        analyzer = LLMAnalyzer()
        
        # Create time series data with consistent trend
        time_periods = []
        base_price = 45000
        
        for i in range(5):
            # Gradual uptrend
            price = base_price + i * 100
            data = pd.DataFrame({
                'close': [price],
                'high': [price * 1.02],
                'low': [price * 0.98],
                'volume': [1000000],
                'rsi': [40 + i * 2],  # Gradually increasing
                'macd': [0.5 + i * 0.1],
                'bb_position': [0.3 + i * 0.05]
            })
            time_periods.append(data)
        
        decisions = []
        for i, data in enumerate(time_periods):
            with patch.object(analyzer, '_call_genai') as mock_genai:
                mock_genai.return_value = {
                    'decision': 'BUY',
                    'confidence': 70 + i * 2,
                    'reasoning': f'Uptrend period {i+1}'
                }
                
                response = analyzer.analyze_market_data(data, data['close'].iloc[0], 'BTC-EUR')
                decisions.append(response['decision'])
        
        # Should maintain consistent trend direction
        buy_count = decisions.count('BUY')
        assert buy_count >= 3  # Majority should be BUY for uptrend


class TestBiasDetection:
    """Test for various types of bias in AI decisions"""
    
    def test_price_level_bias(self):
        """Test that decisions aren't biased by absolute price levels"""
        analyzer = LLMAnalyzer()
        
        # Same technical conditions at different price levels
        price_levels = [1000, 10000, 50000, 100000]  # Different price levels
        decisions = []
        
        for price in price_levels:
            market_data = pd.DataFrame({
                'close': [price],
                'high': [price * 1.02],
                'low': [price * 0.98],
                'volume': [1000000],
                'rsi': [65],  # Same RSI
                'macd': [0.5],  # Same MACD
                'bb_position': [0.7]  # Same BB position
            })
            
            with patch.object(analyzer, '_call_genai') as mock_genai:
                mock_genai.return_value = {
                    'decision': 'BUY',
                    'confidence': 75,
                    'reasoning': 'Technical indicators favor buying'
                }
                
                response = analyzer.analyze_market_data(market_data, price, 'BTC-EUR')
                decisions.append(response['decision'])
        
        # Decisions should be consistent regardless of price level
        unique_decisions = set(decisions)
        assert len(unique_decisions) <= 1  # Should be the same decision
    
    def test_volume_bias(self):
        """Test that decisions appropriately consider volume"""
        analyzer = LLMAnalyzer()
        
        # Same technical conditions with different volumes
        volumes = [100000, 1000000, 10000000]  # Low, medium, high volume
        confidences = []
        
        for volume in volumes:
            market_data = pd.DataFrame({
                'close': [45000.0],
                'high': [46000.0],
                'low': [44000.0],
                'volume': [volume],
                'rsi': [65],
                'macd': [0.5],
                'bb_position': [0.7]
            })
            
            with patch.object(analyzer, '_call_genai') as mock_genai:
                # Higher volume should increase confidence
                confidence = 60 + (volumes.index(volume) * 10)
                mock_genai.return_value = {
                    'decision': 'BUY',
                    'confidence': confidence,
                    'reasoning': f'Volume: {volume}'
                }
                
                response = analyzer.analyze_market_data(market_data, 45000.0, 'BTC-EUR')
                confidences.append(response['confidence'])
        
        # Higher volume should generally lead to higher confidence
        assert confidences[2] >= confidences[1] >= confidences[0]
    
    def test_recency_bias(self):
        """Test for recency bias in decision making"""
        analyzer = LLMAnalyzer()
        
        # Create data with recent vs historical patterns
        recent_data = pd.DataFrame({
            'close': [44000, 44500, 45000],  # Recent uptrend
            'high': [44200, 44700, 45200],
            'low': [43800, 44300, 44800],
            'volume': [1000000, 1100000, 1200000],
            'rsi': [45, 50, 55],
            'macd': [0.2, 0.3, 0.4],
            'bb_position': [0.4, 0.5, 0.6]
        })
        
        historical_data = pd.DataFrame({
            'close': [50000, 49000, 48000, 47000, 46000, 45000],  # Historical downtrend + recent stability
            'high': [50200, 49200, 48200, 47200, 46200, 45200],
            'low': [49800, 48800, 47800, 46800, 45800, 44800],
            'volume': [1000000] * 6,
            'rsi': [70, 65, 60, 55, 50, 55],
            'macd': [-0.5, -0.3, -0.1, 0.1, 0.3, 0.4],
            'bb_position': [0.8, 0.7, 0.6, 0.5, 0.5, 0.6]
        })
        
        datasets = [recent_data, historical_data]
        decisions = []
        
        for i, data in enumerate(datasets):
            with patch.object(analyzer, '_call_genai') as mock_genai:
                # Should focus on recent trend
                mock_genai.return_value = {
                    'decision': 'BUY',
                    'confidence': 70,
                    'reasoning': 'Recent uptrend detected'
                }
                
                response = analyzer.analyze_market_data(data, 45000.0, 'BTC-EUR')
                decisions.append(response)
        
        # Both should recognize the recent uptrend pattern
        assert all(d['decision'] == 'BUY' for d in decisions)
    
    def test_confirmation_bias(self):
        """Test for confirmation bias in analysis"""
        analyzer = LLMAnalyzer()
        
        # Mixed signals scenario
        mixed_signals_data = pd.DataFrame({
            'close': [45000.0],
            'high': [46000.0],
            'low': [44000.0],
            'volume': [1000000],
            'rsi': [30],    # Bullish (oversold)
            'macd': [-0.5], # Bearish
            'bb_position': [0.8]  # Bearish (near upper band)
        })
        
        with patch.object(analyzer, '_call_genai') as mock_genai:
            # Should handle mixed signals appropriately
            mock_genai.return_value = {
                'decision': 'HOLD',  # Conservative approach for mixed signals
                'confidence': 50,    # Lower confidence for mixed signals
                'reasoning': 'Mixed technical signals detected'
            }
            
            response = analyzer.analyze_market_data(mixed_signals_data, 45000.0, 'BTC-EUR')
            
            # Should be conservative with mixed signals
            assert response['decision'] == 'HOLD'
            assert response['confidence'] <= 60  # Lower confidence expected

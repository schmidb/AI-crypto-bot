"""
Performance Tracker for Hybrid Framework
Tracks accuracy and performance of rule-based vs LLM strategies
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import os

@dataclass
class StrategyPerformance:
    """Track performance metrics for a strategy"""
    strategy_name: str
    total_decisions: int = 0
    correct_decisions: int = 0
    buy_decisions: int = 0
    sell_decisions: int = 0
    hold_decisions: int = 0
    avg_confidence: float = 0.0
    accuracy_rate: float = 0.0
    last_updated: str = ""

@dataclass
class DecisionRecord:
    """Record of a trading decision for performance tracking"""
    timestamp: str
    product_id: str
    strategy_name: str
    action: str
    confidence: float
    price_at_decision: float
    price_after_1h: Optional[float] = None
    price_after_4h: Optional[float] = None
    price_after_24h: Optional[float] = None
    was_correct: Optional[bool] = None
    profit_loss_1h: Optional[float] = None
    profit_loss_4h: Optional[float] = None
    profit_loss_24h: Optional[float] = None

class HybridPerformanceTracker:
    """Track performance of hybrid framework strategies"""
    
    def __init__(self, data_dir: str = "data/performance"):
        self.data_dir = data_dir
        self.logger = logging.getLogger(__name__)
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        self.performance_file = os.path.join(data_dir, "strategy_performance.json")
        self.decisions_file = os.path.join(data_dir, "decision_records.json")
        
        # Load existing data
        self.strategy_performance = self._load_performance_data()
        self.decision_records = self._load_decision_records()
        
        self.logger.info(f"Performance tracker initialized with {len(self.decision_records)} historical records")
    
    def record_decision(self, 
                       product_id: str,
                       strategy_signals: Dict[str, any],
                       final_decision: Dict[str, any],
                       current_price: float):
        """Record a trading decision for performance tracking"""
        
        timestamp = datetime.now().isoformat()
        
        # Record individual strategy decisions
        for strategy_name, signal in strategy_signals.items():
            # Handle both TradingSignal objects and dictionaries
            if hasattr(signal, 'action'):
                # TradingSignal object
                action = signal.action
                confidence = signal.confidence
            else:
                # Dictionary format
                action = signal.get('action', 'HOLD')
                confidence = signal.get('confidence', 50.0)
            
            decision_record = DecisionRecord(
                timestamp=timestamp,
                product_id=product_id,
                strategy_name=strategy_name,
                action=action,
                confidence=confidence,
                price_at_decision=current_price
            )
            
            self.decision_records.append(decision_record)
            
            # Update strategy performance stats
            self._update_strategy_performance(strategy_name, signal)
        
        # Record combined decision
        combined_record = DecisionRecord(
            timestamp=timestamp,
            product_id=product_id,
            strategy_name="combined_hybrid",
            action=final_decision.get('action', 'HOLD'),
            confidence=final_decision.get('confidence', 0),
            price_at_decision=current_price
        )
        
        self.decision_records.append(combined_record)
        
        # Save updated records
        self._save_decision_records()
        self._save_performance_data()
        
        self.logger.debug(f"Recorded decision for {product_id}: {len(strategy_signals)} strategies + combined")
    
    def update_decision_outcomes(self):
        """Update decision outcomes based on price movements"""
        
        current_time = datetime.now()
        updated_count = 0
        
        for record in self.decision_records:
            if record.was_correct is not None:
                continue  # Already evaluated
            
            decision_time = datetime.fromisoformat(record.timestamp)
            
            # Check if enough time has passed for evaluation (24h)
            if current_time - decision_time < timedelta(hours=24):
                continue
            
            # Get price data for evaluation (would need to implement price fetching)
            # For now, we'll mark as placeholder
            record.was_correct = self._evaluate_decision_accuracy(record)
            
            if record.was_correct is not None:
                updated_count += 1
        
        if updated_count > 0:
            self._save_decision_records()
            self._recalculate_accuracy_rates()
            self.logger.info(f"Updated outcomes for {updated_count} decisions")
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary for all strategies"""
        
        summary = {
            "last_updated": datetime.now().isoformat(),
            "total_decisions": len(self.decision_records),
            "strategies": {}
        }
        
        for strategy_name, performance in self.strategy_performance.items():
            summary["strategies"][strategy_name] = asdict(performance)
        
        # Add comparative metrics
        if "llm_strategy" in self.strategy_performance and len([s for s in self.strategy_performance if s != "llm_strategy" and s != "combined_hybrid"]) > 0:
            llm_perf = self.strategy_performance["llm_strategy"]
            rule_based_strategies = [s for s in self.strategy_performance if s not in ["llm_strategy", "combined_hybrid"]]
            
            if rule_based_strategies:
                avg_rule_based_accuracy = sum(
                    self.strategy_performance[s].accuracy_rate for s in rule_based_strategies
                ) / len(rule_based_strategies)
                
                summary["comparison"] = {
                    "llm_accuracy": llm_perf.accuracy_rate,
                    "rule_based_avg_accuracy": avg_rule_based_accuracy,
                    "llm_advantage": llm_perf.accuracy_rate - avg_rule_based_accuracy,
                    "llm_avg_confidence": llm_perf.avg_confidence
                }
        
        return summary
    
    def get_recent_performance(self, hours: int = 24) -> Dict:
        """Get performance for recent decisions"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_records = [
            r for r in self.decision_records 
            if datetime.fromisoformat(r.timestamp) > cutoff_time
        ]
        
        strategy_stats = {}
        
        for record in recent_records:
            if record.strategy_name not in strategy_stats:
                strategy_stats[record.strategy_name] = {
                    "decisions": 0,
                    "avg_confidence": 0,
                    "actions": {"BUY": 0, "SELL": 0, "HOLD": 0}
                }
            
            stats = strategy_stats[record.strategy_name]
            stats["decisions"] += 1
            stats["avg_confidence"] = (stats["avg_confidence"] * (stats["decisions"] - 1) + record.confidence) / stats["decisions"]
            stats["actions"][record.action] += 1
        
        return {
            "period_hours": hours,
            "total_recent_decisions": len(recent_records),
            "strategies": strategy_stats
        }
    
    def _load_performance_data(self) -> Dict[str, StrategyPerformance]:
        """Load strategy performance data"""
        
        if not os.path.exists(self.performance_file):
            return {}
        
        try:
            with open(self.performance_file, 'r') as f:
                data = json.load(f)
            
            performance = {}
            for name, perf_data in data.items():
                performance[name] = StrategyPerformance(**perf_data)
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error loading performance data: {e}")
            return {}
    
    def _load_decision_records(self) -> List[DecisionRecord]:
        """Load decision records"""
        
        if not os.path.exists(self.decisions_file):
            return []
        
        try:
            with open(self.decisions_file, 'r') as f:
                data = json.load(f)
            
            records = []
            for record_data in data:
                records.append(DecisionRecord(**record_data))
            
            return records
            
        except Exception as e:
            self.logger.error(f"Error loading decision records: {e}")
            return []
    
    def _save_performance_data(self):
        """Save strategy performance data"""
        
        try:
            data = {}
            for name, performance in self.strategy_performance.items():
                data[name] = asdict(performance)
            
            with open(self.performance_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving performance data: {e}")
    
    def _save_decision_records(self):
        """Save decision records"""
        
        try:
            data = []
            for record in self.decision_records:
                data.append(asdict(record))
            
            with open(self.decisions_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving decision records: {e}")
    
    def _update_strategy_performance(self, strategy_name: str, signal):
        """Update performance stats for a strategy"""
        
        if strategy_name not in self.strategy_performance:
            self.strategy_performance[strategy_name] = StrategyPerformance(
                strategy_name=strategy_name,
                last_updated=datetime.now().isoformat()
            )
        
        perf = self.strategy_performance[strategy_name]
        perf.total_decisions += 1
        
        # Handle both TradingSignal objects and dictionaries
        if hasattr(signal, 'action'):
            # TradingSignal object
            action = signal.action
            confidence = signal.confidence
        else:
            # Dictionary format
            action = signal.get('action', 'HOLD')
            confidence = signal.get('confidence', 50.0)
        
        # Update action counts
        if action == "BUY":
            perf.buy_decisions += 1
        elif action == "SELL":
            perf.sell_decisions += 1
        else:
            perf.hold_decisions += 1
        
        # Update average confidence
        perf.avg_confidence = (perf.avg_confidence * (perf.total_decisions - 1) + confidence) / perf.total_decisions
        perf.last_updated = datetime.now().isoformat()
    
    def _evaluate_decision_accuracy(self, record: DecisionRecord) -> Optional[bool]:
        """Evaluate if a decision was correct (placeholder implementation)"""
        
        # This would need actual price data to evaluate
        # For now, return None to indicate not evaluated
        return None
    
    def get_adaptive_weights(self, base_weights: Dict[str, float]) -> Dict[str, float]:
        """Calculate adaptive weights based on historical performance (Phase 3)"""
        
        try:
            # Get recent performance data (last 7 days)
            recent_performance = self._get_recent_performance_metrics(days=7)
            
            if not recent_performance:
                self.logger.debug("No recent performance data, using base weights")
                return base_weights
            
            # Calculate performance-based adjustments
            adaptive_weights = base_weights.copy()
            
            # Performance factors
            total_performance_score = 0
            strategy_performance_scores = {}
            
            for strategy_name in base_weights.keys():
                if strategy_name in recent_performance:
                    perf = recent_performance[strategy_name]
                    
                    # Calculate performance score (0-2 scale, 1 = neutral)
                    accuracy_factor = perf.get('accuracy_rate', 0.5) * 2  # 0-2 scale
                    confidence_factor = min(2.0, perf.get('avg_confidence', 50) / 50)  # 0-2 scale
                    decision_count_factor = min(1.5, perf.get('total_decisions', 1) / 10)  # More decisions = more reliable
                    
                    # Combine factors
                    performance_score = (accuracy_factor * 0.5 + confidence_factor * 0.3 + decision_count_factor * 0.2)
                    strategy_performance_scores[strategy_name] = performance_score
                    total_performance_score += performance_score
                else:
                    strategy_performance_scores[strategy_name] = 1.0  # Neutral for no data
                    total_performance_score += 1.0
            
            # Apply performance-based adjustments
            if total_performance_score > 0:
                for strategy_name in adaptive_weights:
                    performance_score = strategy_performance_scores.get(strategy_name, 1.0)
                    
                    # Calculate adjustment factor (0.5 to 1.5 range)
                    adjustment_factor = 0.5 + (performance_score / 2.0)
                    
                    # Apply adjustment with dampening to prevent extreme changes
                    base_weight = base_weights[strategy_name]
                    adjusted_weight = base_weight * adjustment_factor
                    
                    # Limit adjustment to ±50% of base weight
                    max_adjustment = base_weight * 0.5
                    adjusted_weight = max(base_weight - max_adjustment, 
                                        min(base_weight + max_adjustment, adjusted_weight))
                    
                    adaptive_weights[strategy_name] = adjusted_weight
                
                # Normalize weights to sum to 1.0
                total_weight = sum(adaptive_weights.values())
                if total_weight > 0:
                    adaptive_weights = {k: v / total_weight for k, v in adaptive_weights.items()}
                
                # Log significant changes
                significant_changes = []
                for strategy in adaptive_weights:
                    base = base_weights[strategy]
                    adapted = adaptive_weights[strategy]
                    if abs(adapted - base) > 0.05:  # 5% threshold
                        change_pct = ((adapted - base) / base) * 100
                        significant_changes.append(f"{strategy}: {change_pct:+.1f}%")
                
                if significant_changes:
                    self.logger.info(f"📈 Performance-based weight adaptations: {', '.join(significant_changes)}")
            
            return adaptive_weights
            
        except Exception as e:
            self.logger.error(f"Error calculating adaptive weights: {e}")
            return base_weights
    
    def _get_recent_performance_metrics(self, days: int = 7) -> Dict:
        """Get performance metrics for recent period"""
        
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_records = [
            r for r in self.decision_records 
            if datetime.fromisoformat(r.timestamp) > cutoff_time
        ]
        
        if not recent_records:
            return {}
        
        # Group by strategy
        strategy_metrics = {}
        
        for record in recent_records:
            strategy = record.strategy_name
            if strategy not in strategy_metrics:
                strategy_metrics[strategy] = {
                    'total_decisions': 0,
                    'correct_decisions': 0,
                    'confidence_sum': 0,
                    'avg_confidence': 0,
                    'accuracy_rate': 0
                }
            
            metrics = strategy_metrics[strategy]
            metrics['total_decisions'] += 1
            metrics['confidence_sum'] += record.confidence
            
            if record.was_correct is True:
                metrics['correct_decisions'] += 1
        
        # Calculate final metrics
        for strategy, metrics in strategy_metrics.items():
            if metrics['total_decisions'] > 0:
                metrics['avg_confidence'] = metrics['confidence_sum'] / metrics['total_decisions']
                metrics['accuracy_rate'] = metrics['correct_decisions'] / metrics['total_decisions']
            
            # Remove intermediate calculation fields
            del metrics['confidence_sum']
        
        return strategy_metrics
    
    def get_performance_insights(self) -> Dict:
        """Get insights for performance-based adaptations (Phase 3)"""
        
        insights = {
            "timestamp": datetime.now().isoformat(),
            "total_strategies": len(self.strategy_performance),
            "insights": []
        }
        
        # Analyze each strategy's performance trends
        for strategy_name, performance in self.strategy_performance.items():
            strategy_insights = []
            
            # Confidence analysis
            avg_conf = performance.avg_confidence
            if avg_conf > 80:
                strategy_insights.append(f"Very high confidence ({avg_conf:.1f}%)")
            elif avg_conf > 60:
                strategy_insights.append(f"Good confidence ({avg_conf:.1f}%)")
            elif avg_conf < 40:
                strategy_insights.append(f"Low confidence ({avg_conf:.1f}%)")
            
            # Decision pattern analysis
            total_decisions = performance.total_decisions
            if total_decisions > 0:
                buy_ratio = performance.buy_decisions / total_decisions
                sell_ratio = performance.sell_decisions / total_decisions
                hold_ratio = performance.hold_decisions / total_decisions
                
                if buy_ratio > 0.6:
                    strategy_insights.append("Bullish bias")
                elif sell_ratio > 0.6:
                    strategy_insights.append("Bearish bias")
                elif hold_ratio > 0.8:
                    strategy_insights.append("Conservative approach")
            
            # Accuracy analysis (if available)
            if performance.accuracy_rate > 0:
                if performance.accuracy_rate > 0.7:
                    strategy_insights.append(f"High accuracy ({performance.accuracy_rate:.1%})")
                elif performance.accuracy_rate < 0.4:
                    strategy_insights.append(f"Low accuracy ({performance.accuracy_rate:.1%})")
            
            insights["insights"].append({
                "strategy": strategy_name,
                "summary": strategy_insights,
                "total_decisions": total_decisions,
                "avg_confidence": avg_conf,
                "accuracy_rate": performance.accuracy_rate
            })
        
        return insights
    
    def _recalculate_accuracy_rates(self):
        """Recalculate accuracy rates based on evaluated decisions"""
        
        for strategy_name in self.strategy_performance:
            strategy_records = [r for r in self.decision_records if r.strategy_name == strategy_name]
            evaluated_records = [r for r in strategy_records if r.was_correct is not None]
            
            if evaluated_records:
                correct_count = sum(1 for r in evaluated_records if r.was_correct)
                accuracy_rate = correct_count / len(evaluated_records)
                self.strategy_performance[strategy_name].accuracy_rate = accuracy_rate
                self.strategy_performance[strategy_name].correct_decisions = correct_count
        
        self._save_performance_data()

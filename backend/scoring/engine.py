"""Scoring engine for business ideas."""
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ScoreBreakdown:
    demand_strength: float
    demand_velocity: float
    competition_proxy: float
    feasibility: float
    automation_friendly: float
    monetization_clarity: float
    total: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'demand_strength': round(self.demand_strength, 2),
            'demand_velocity': round(self.demand_velocity, 2),
            'competition_proxy': round(self.competition_proxy, 2),
            'feasibility': round(self.feasibility, 2),
            'automation_friendly': round(self.automation_friendly, 2),
            'monetization_clarity': round(self.monetization_clarity, 2),
            'total': round(self.total, 2)
        }

class ScoringEngine:
    """Transparent scoring model for business ideas."""
    
    DEFAULT_WEIGHTS = {
        'demand_strength': 0.25,
        'demand_velocity': 0.20,
        'competition_proxy': 0.15,
        'feasibility': 0.20,
        'automation_friendly': 0.10,
        'monetization_clarity': 0.10
    }
    
    def __init__(self, weights_path: Optional[Path] = None):
        self.weights = self._load_weights(weights_path)
        self._validate_weights()
    
    def _load_weights(self, weights_path: Optional[Path]) -> Dict[str, float]:
        """Load weights from config file or use defaults."""
        if weights_path and weights_path.exists():
            try:
                with open(weights_path, 'r') as f:
                    config = yaml.safe_load(f)
                    return config.get('weights', self.DEFAULT_WEIGHTS)
            except Exception as e:
                print(f"Warning: Could not load weights from {weights_path}: {e}")
                return self.DEFAULT_WEIGHTS
        return self.DEFAULT_WEIGHTS
    
    def _validate_weights(self):
        """Ensure weights sum to 1.0."""
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            print(f"Warning: Weights sum to {total}, normalizing...")
            self.weights = {k: v / total for k, v in self.weights.items()}
    
    def calculate_demand_strength(self, signals: List[Dict[str, Any]]) -> float:
        """Calculate demand strength from signals (0-100 scale)."""
        if not signals:
            return 0.0
        
        # Aggregate all volume/count metrics
        volume_metrics = [
            s['metric_value'] for s in signals 
            if s['metric_type'] in ['volume', 'post_count', 'story_count', 'video_count', 'interest_score']
        ]
        
        if not volume_metrics:
            return 50.0  # Neutral if no volume data
        
        # Normalize: log scale to handle large ranges, cap at 100
        import math
        avg_volume = sum(volume_metrics) / len(volume_metrics)
        score = min(100, math.log1p(avg_volume) * 10)
        
        return score
    
    def calculate_demand_velocity(self, signals: List[Dict[str, Any]]) -> float:
        """Calculate demand velocity/trend (0-100 scale)."""
        if not signals:
            return 50.0
        
        # Look for growth_rate metrics
        growth_signals = [
            s['metric_value'] for s in signals 
            if s['metric_type'] in ['growth_rate', 'trend_slope']
        ]
        
        if growth_signals:
            avg_growth = sum(growth_signals) / len(growth_signals)
            # Normalize: -100% to +100% growth maps to 0-100 score
            # 0% growth = 50, +100% = 100, -100% = 0
            score = 50 + (avg_growth / 2)
            return max(0, min(100, score))
        
        # Fallback: use recency of signals
        recent_signals = [
            s for s in signals 
            if s.get('data_date') and self._is_recent(s['data_date'], days=7)
        ]
        
        if recent_signals:
            return 70.0  # Recent activity = decent velocity
        
        return 50.0
    
    def calculate_competition_proxy(self, signals: List[Dict[str, Any]], 
                                   idea: Dict[str, Any]) -> float:
        """Estimate competition level (inverse: low competition = high score)."""
        # High volume + high engagement = likely saturated
        volume = self.calculate_demand_strength(signals)
        
        # Check for Show HN posts (product launches)
        show_hn_count = len([s for s in signals if 'show_hn' in s.get('source', '')])
        
        if show_hn_count > 5:
            return 30.0  # Many existing products = high competition
        elif volume > 80:
            return 50.0  # High volume = moderate competition
        elif volume < 30:
            return 80.0  # Low volume = potentially underserved
        else:
            return 65.0
    
    def calculate_feasibility(self, idea: Dict[str, Any]) -> float:
        """Estimate build feasibility (0-100 scale)."""
        ops_burden = idea.get('ops_burden_estimate', 'medium').lower()
        
        burden_scores = {
            'low': 85.0,
            'medium': 65.0,
            'high': 40.0
        }
        
        base_score = burden_scores.get(ops_burden, 65.0)
        
        # Bonus for clear distribution channel
        if idea.get('distribution_channel'):
            base_score += 10
        
        # Penalty for compliance risks
        if idea.get('compliance_risks'):
            base_score -= 15
        
        return max(0, min(100, base_score))
    
    def calculate_automation_friendly(self, idea: Dict[str, Any]) -> float:
        """Estimate automation potential (0-100 scale)."""
        ops_burden = idea.get('ops_burden_estimate', 'medium').lower()
        
        # Low ops burden = more automatable
        burden_scores = {
            'low': 90.0,
            'medium': 60.0,
            'high': 30.0
        }
        
        return burden_scores.get(ops_burden, 60.0)
    
    def calculate_monetization_clarity(self, idea: Dict[str, Any]) -> float:
        """Estimate monetization potential (0-100 scale)."""
        score = 50.0  # Base
        
        # Clear pricing model = +20
        if idea.get('pricing_model'):
            score += 20
        
        # Clear target user = +15
        if idea.get('target_user'):
            score += 15
        
        # Clear value prop = +15
        if idea.get('value_prop'):
            score += 15
        
        return min(100, score)
    
    def score_idea(self, idea: Dict[str, Any], 
                   signals: List[Dict[str, Any]]) -> ScoreBreakdown:
        """Calculate full score breakdown for a business idea."""
        
        # Calculate each component
        demand_strength = self.calculate_demand_strength(signals)
        demand_velocity = self.calculate_demand_velocity(signals)
        competition_proxy = self.calculate_competition_proxy(signals, idea)
        feasibility = self.calculate_feasibility(idea)
        automation_friendly = self.calculate_automation_friendly(idea)
        monetization_clarity = self.calculate_monetization_clarity(idea)
        
        # Weighted total
        total = (
            demand_strength * self.weights['demand_strength'] +
            demand_velocity * self.weights['demand_velocity'] +
            competition_proxy * self.weights['competition_proxy'] +
            feasibility * self.weights['feasibility'] +
            automation_friendly * self.weights['automation_friendly'] +
            monetization_clarity * self.weights['monetization_clarity']
        )
        
        return ScoreBreakdown(
            demand_strength=demand_strength,
            demand_velocity=demand_velocity,
            competition_proxy=competition_proxy,
            feasibility=feasibility,
            automation_friendly=automation_friendly,
            monetization_clarity=monetization_clarity,
            total=total
        )
    
    def rank_ideas(self, ideas_with_signals: List[tuple]) -> List[Dict[str, Any]]:
        """Rank multiple ideas with their signals.
        
        Args:
            ideas_with_signals: List of (idea_dict, signals_list) tuples
            
        Returns:
            List of ideas with score and rank added
        """
        scored_ideas = []
        
        for idea, signals in ideas_with_signals:
            breakdown = self.score_idea(idea, signals)
            idea_with_score = dict(idea)
            idea_with_score['total_score'] = breakdown.total
            idea_with_score['score_breakdown'] = breakdown.to_dict()
            scored_ideas.append(idea_with_score)
        
        # Sort by total score descending
        scored_ideas.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Add rank
        for i, idea in enumerate(scored_ideas, 1):
            idea['rank'] = i
        
        return scored_ideas
    
    def _is_recent(self, date_str: str, days: int = 7) -> bool:
        """Check if a date string is within N days."""
        from datetime import datetime, timedelta
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            return datetime.utcnow() - date < timedelta(days=days)
        except:
            return False
    
    def get_weights_config(self) -> Dict[str, Any]:
        """Get current weights configuration."""
        return {
            'weights': self.weights,
            'description': {
                'demand_strength': 'Volume of mentions/signals',
                'demand_velocity': 'Growth trend / recency',
                'competition_proxy': 'Market saturation (inverse)',
                'feasibility': 'Build complexity and risk',
                'automation_friendly': 'Low oversight potential',
                'monetization_clarity': 'Clear pricing and buyer'
            }
        }

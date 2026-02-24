"""Tests for scoring engine."""
import pytest
import json
from pathlib import Path
from backend.scoring.engine import ScoringEngine, ScoreBreakdown


class TestScoringEngine:
    """Test scoring engine functionality."""
    
    @pytest.fixture
    def engine(self):
        return ScoringEngine()
    
    @pytest.fixture
    def sample_signals(self):
        """Sample demand signals for testing."""
        return [
            {
                'source': 'reddit',
                'metric_type': 'post_count',
                'metric_value': 150.0,
                'url': 'https://reddit.com/r/startups',
                'data_date': '2026-02-23'
            },
            {
                'source': 'google_trends',
                'metric_type': 'interest_score',
                'metric_value': 75.0,
                'url': 'https://trends.google.com',
                'data_date': '2026-02-23'
            },
            {
                'source': 'hackernews',
                'metric_type': 'story_count',
                'metric_value': 25.0,
                'url': 'https://news.ycombinator.com',
                'data_date': '2026-02-23'
            }
        ]
    
    @pytest.fixture
    def sample_idea(self):
        """Sample business idea for testing."""
        return {
            'id': 1,
            'title': 'Test SaaS',
            'target_user': 'Freelancers',
            'value_prop': 'Automate invoicing',
            'pricing_model': '$29/mo subscription',
            'distribution_channel': 'Content marketing',
            'ops_burden_estimate': 'low',
            'compliance_risks': None
        }
    
    def test_default_weights_sum_to_one(self, engine):
        """Weights should sum to approximately 1.0."""
        total = sum(engine.weights.values())
        assert abs(total - 1.0) < 0.001
    
    def test_demand_strength_calculation(self, engine, sample_signals):
        score = engine.calculate_demand_strength(sample_signals)
        assert 0 <= score <= 100
        assert score > 0  # Should have positive score with signals
    
    def test_demand_strength_empty(self, engine):
        score = engine.calculate_demand_strength([])
        assert score == 0.0
    
    def test_demand_velocity_with_growth(self, engine):
        signals = [
            {'metric_type': 'growth_rate', 'metric_value': 50.0, 'data_date': '2026-02-23'}
        ]
        score = engine.calculate_demand_velocity(signals)
        assert score > 50  # Positive growth should be > 50
    
    def test_demand_velocity_no_data(self, engine):
        score = engine.calculate_demand_velocity([])
        assert score == 50.0  # Neutral when no data
    
    def test_competition_proxy_high_saturation(self, engine, sample_signals):
        # Create many Show HN signals (high competition)
        idea = {'id': 1}  # Minimal idea
        signals = sample_signals + [
            {'source': 'hackernews_show_hn', 'metric_value': 100}
            for _ in range(10)
        ]
        score = engine.calculate_competition_proxy(signals, idea)
        assert score < 50  # High competition = lower score
    
    def test_feasibility_low_burden(self, engine):
        idea = {'ops_burden_estimate': 'low', 'compliance_risks': None}
        score = engine.calculate_feasibility(idea)
        assert score >= 80
    
    def test_feasibility_high_burden(self, engine):
        idea = {'ops_burden_estimate': 'high', 'compliance_risks': 'High regulatory'}
        score = engine.calculate_feasibility(idea)
        assert score < 50
    
    def test_automation_friendly(self, engine):
        low = {'ops_burden_estimate': 'low'}
        high = {'ops_burden_estimate': 'high'}
        
        assert engine.calculate_automation_friendly(low) > \
               engine.calculate_automation_friendly(high)
    
    def test_monetization_clarity_complete(self, engine):
        idea = {
            'pricing_model': '$29/mo',
            'target_user': 'Freelancers',
            'value_prop': 'Saves time'
        }
        score = engine.calculate_monetization_clarity(idea)
        assert score >= 80  # All fields present = high score
    
    def test_monetization_clarity_incomplete(self, engine):
        idea = {}  # Empty
        score = engine.calculate_monetization_clarity(idea)
        assert score == 50.0  # Base score only
    
    def test_full_score_idea(self, engine, sample_idea, sample_signals):
        breakdown = engine.score_idea(sample_idea, sample_signals)
        
        assert isinstance(breakdown, ScoreBreakdown)
        assert 0 <= breakdown.total <= 100
        assert breakdown.demand_strength >= 0
        assert breakdown.feasibility >= 0
    
    def test_score_breakdown_to_dict(self, engine, sample_idea, sample_signals):
        breakdown = engine.score_idea(sample_idea, sample_signals)
        d = breakdown.to_dict()
        
        assert 'demand_strength' in d
        assert 'total' in d
        assert all(isinstance(v, (int, float)) for v in d.values())
    
    def test_rank_ideas(self, engine, sample_signals):
        ideas = [
            ({'id': 1, 'title': 'Idea A', 'ops_burden_estimate': 'low'}, sample_signals),
            ({'id': 2, 'title': 'Idea B', 'ops_burden_estimate': 'high'}, sample_signals[:1]),
        ]
        
        ranked = engine.rank_ideas(ideas)
        
        assert len(ranked) == 2
        assert ranked[0]['rank'] == 1
        assert ranked[1]['rank'] == 2
        # Low burden idea should rank higher
        assert ranked[0]['ops_burden_estimate'] == 'low'
    
    def test_weight_customization(self, tmp_path):
        """Test loading custom weights from file."""
        weights_file = tmp_path / "weights.yaml"
        weights_file.write_text("""
weights:
  demand_strength: 0.5
  demand_velocity: 0.1
  competition_proxy: 0.1
  feasibility: 0.1
  automation_friendly: 0.1
  monetization_clarity: 0.1
""")
        
        engine = ScoringEngine(weights_file)
        assert engine.weights['demand_strength'] == 0.5
    
    def test_invalid_weights_normalized(self, tmp_path):
        """Weights that don't sum to 1.0 should be normalized."""
        weights_file = tmp_path / "weights.yaml"
        weights_file.write_text("""
weights:
  demand_strength: 1.0
  demand_velocity: 1.0
  competition_proxy: 1.0
  feasibility: 1.0
  automation_friendly: 1.0
  monetization_clarity: 1.0
""")
        
        engine = ScoringEngine(weights_file)
        total = sum(engine.weights.values())
        assert abs(total - 1.0) < 0.001


class TestScoreBreakdown:
    """Test ScoreBreakdown dataclass."""
    
    def test_creation(self):
        breakdown = ScoreBreakdown(
            demand_strength=80.0,
            demand_velocity=70.0,
            competition_proxy=60.0,
            feasibility=90.0,
            automation_friendly=85.0,
            monetization_clarity=75.0,
            total=76.5
        )
        assert breakdown.total == 76.5
    
    def test_to_dict_rounds_values(self):
        breakdown = ScoreBreakdown(
            demand_strength=80.12345,
            demand_velocity=70.0,
            competition_proxy=60.0,
            feasibility=90.0,
            automation_friendly=85.0,
            monetization_clarity=75.0,
            total=76.51234
        )
        d = breakdown.to_dict()
        assert d['demand_strength'] == 80.12
        assert d['total'] == 76.51


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for demand signal connectors."""
import pytest
from datetime import datetime
from backend.connectors.base import DemandSignal, BaseConnector
from backend.connectors.google_trends import GoogleTrendsConnector
from backend.connectors.reddit import RedditConnector
from backend.connectors.hackernews import HackerNewsConnector
from backend.connectors.youtube import YouTubeConnector


class TestDemandSignal:
    """Test DemandSignal dataclass."""
    
    def test_creation(self):
        signal = DemandSignal(
            source="test",
            query="example",
            metric_type="volume",
            metric_value=100.0,
            metric_unit="mentions",
            url="https://example.com"
        )
        assert signal.source == "test"
        assert signal.metric_value == 100.0
        assert signal.timestamp is not None
    
    def test_to_dict(self):
        signal = DemandSignal(
            source="test",
            query="example",
            metric_type="volume",
            metric_value=100.0,
            metric_unit="mentions",
            url="https://example.com"
        )
        d = signal.to_dict()
        assert d['source'] == "test"
        assert d['metric_value'] == 100.0
        assert 'timestamp' in d


class TestGoogleTrendsConnector:
    """Test Google Trends connector."""
    
    @pytest.fixture
    def connector(self):
        return GoogleTrendsConnector(mock_mode=True)
    
    def test_mock_mode(self, connector):
        assert connector.mock_mode is True
        signals = connector.search("test query")
        assert len(signals) == 1
        assert signals[0].source == "google_trends"
    
    def test_mock_signals_deterministic(self, connector):
        """Same query should generate same mock values."""
        signals1 = connector.search("python")
        signals2 = connector.search("python")
        assert signals1[0].metric_value == signals2[0].metric_value
    
    def test_source_name(self, connector):
        assert connector.source_name == "google_trends"


class TestRedditConnector:
    """Test Reddit connector."""
    
    @pytest.fixture
    def connector(self):
        return RedditConnector(mock_mode=True)
    
    def test_mock_mode(self, connector):
        signals = connector.search("startup")
        assert len(signals) == 3
        assert all(s.source == "reddit" for s in signals)
    
    def test_problem_posts_mock(self, connector):
        posts = connector.get_problem_posts("startups")
        assert len(posts) > 0
        assert "title" in posts[0]


class TestHackerNewsConnector:
    """Test Hacker News connector."""
    
    @pytest.fixture
    def connector(self):
        # HN doesn't need API keys
        return HackerNewsConnector()
    
    def test_search_mock(self, connector):
        connector.mock_mode = True
        signals = connector.search("python")
        assert len(signals) == 3
        assert signals[0].source == "hackernews"
    
    def test_source_name(self, connector):
        assert connector.source_name == "hackernews"


class TestYouTubeConnector:
    """Test YouTube connector."""
    
    @pytest.fixture
    def connector(self):
        return YouTubeConnector(mock_mode=True)
    
    def test_mock_mode(self, connector):
        signals = connector.search("tutorial")
        assert len(signals) == 3
        assert all(s.source == "youtube" for s in signals)
    
    def test_no_api_key_fallback(self):
        """Should switch to mock mode without API key."""
        connector = YouTubeConnector(api_key=None)
        assert connector.mock_mode is True


class TestBaseConnector:
    """Test base connector functionality."""
    
    class MockConnector(BaseConnector):
        @property
        def source_name(self):
            return "mock"
        
        def search(self, query, **kwargs):
            return self._generate_mock_signals(query, count=2)
    
    @pytest.fixture
    def connector(self):
        return self.MockConnector(mock_mode=True)
    
    def test_mock_signal_generation(self, connector):
        signals = connector._generate_mock_signals("test", count=3)
        assert len(signals) == 3
        assert all(isinstance(s, DemandSignal) for s in signals)
    
    def test_mock_signal_url(self, connector):
        signals = connector._generate_mock_signals("test")
        assert all(s.url.startswith("https://") for s in signals)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

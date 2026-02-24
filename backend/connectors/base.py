"""Base connector class for demand signal sources."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)

class DemandSignal:
    """Represents a single demand signal."""
    def __init__(self, source: str, query: str, metric_type: str, 
                 metric_value: float, metric_unit: str, url: str,
                 timestamp: Optional[datetime] = None, data_date: Optional[str] = None):
        self.source = source
        self.query = query
        self.metric_type = metric_type
        self.metric_value = metric_value
        self.metric_unit = metric_unit
        self.url = url
        self.timestamp = timestamp or datetime.utcnow()
        self.data_date = data_date or datetime.utcnow().strftime('%Y-%m-%d')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'query': self.query,
            'metric_type': self.metric_type,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'url': self.url,
            'timestamp': self.timestamp.isoformat(),
            'data_date': self.data_date
        }

class BaseConnector(ABC):
    """Abstract base class for demand signal connectors."""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        self.api_key = api_key
        self.mock_mode = mock_mode or not api_key
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if self.mock_mode:
            self.logger.warning(f"{self.__class__.__name__} running in MOCK mode")
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this source."""
        pass
    
    @abstractmethod
    def search(self, query: str, **kwargs) -> List[DemandSignal]:
        """Search for demand signals matching the query.
        
        Args:
            query: Search term or phrase
            **kwargs: Additional source-specific parameters
            
        Returns:
            List of DemandSignal objects
        """
        pass
    
    def is_available(self) -> bool:
        """Check if this connector is available (has required keys/config)."""
        return True  # Override in subclasses if needed
    
    def _generate_mock_signals(self, query: str, count: int = 3) -> List[DemandSignal]:
        """Generate mock signals for testing without API keys."""
        import random
        
        signals = []
        for i in range(count):
            # Generate deterministic "random" values based on query
            query_hash = int(hashlib.md5(f"{query}:{i}".encode()).hexdigest(), 16)
            value = (query_hash % 1000) + 100
            
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='volume',
                metric_value=float(value),
                metric_unit='mentions',
                url=f'https://example.com/mock/{self.source_name}/{query_hash}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
        
        return signals
    
    def _respect_rate_limit(self, min_interval: float = 1.0):
        """Simple rate limiter - sleep if needed."""
        import time
        
        if not hasattr(self, '_last_request_time'):
            self._last_request_time = 0
        
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self._last_request_time = time.time()

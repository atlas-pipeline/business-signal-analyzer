"""Google Trends connector for demand signals."""
from typing import List, Optional
from datetime import datetime, timedelta
from .base import BaseConnector, DemandSignal

class GoogleTrendsConnector(BaseConnector):
    """Connector for Google Trends data using pytrends."""
    
    @property
    def source_name(self) -> str:
        return "google_trends"
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        super().__init__(api_key, mock_mode)
        self._pytrends = None
        
        if not self.mock_mode:
            try:
                from pytrends.request import TrendReq
                self._pytrends = TrendReq(hl='en-US', tz=360)
                self.logger.info("Google Trends connector initialized")
            except ImportError:
                self.logger.warning("pytrends not installed, switching to mock mode")
                self.mock_mode = True
            except Exception as e:
                self.logger.error(f"Failed to initialize pytrends: {e}")
                self.mock_mode = True
    
    def search(self, query: str, geo: str = 'CA', timeframe: str = 'today 3-m') -> List[DemandSignal]:
        """Search Google Trends for interest over time.
        
        Args:
            query: Search term
            geo: Geographic region (default: Canada)
            timeframe: Time window (default: last 3 months)
        """
        if self.mock_mode:
            return self._generate_mock_signals(query, count=1)
        
        try:
            self._respect_rate_limit(2.0)  # Google Trends is rate-limited
            
            self._pytrends.build_payload([query], cat=0, timeframe=timeframe, geo=geo)
            data = self._pytrends.interest_over_time()
            
            if data is None or data.empty:
                self.logger.warning(f"No trends data for query: {query}")
                return []
            
            # Calculate trend metrics
            avg_interest = data[query].mean()
            max_interest = data[query].max()
            recent_interest = data[query].tail(7).mean()  # Last 7 days
            
            # Calculate growth rate
            first_half = data[query].iloc[:len(data)//2].mean()
            second_half = data[query].iloc[len(data)//2:].mean()
            growth_rate = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
            
            signals = []
            
            # Signal 1: Current volume
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='interest_score',
                metric_value=float(recent_interest),
                metric_unit='relative_0_to_100',
                url=f'https://trends.google.com/trends/explore?geo={geo}&q={query}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            # Signal 2: Growth trend
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='growth_rate',
                metric_value=float(growth_rate),
                metric_unit='percent_change',
                url=f'https://trends.google.com/trends/explore?geo={geo}&q={query}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            # Signal 3: Peak interest
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='peak_interest',
                metric_value=float(max_interest),
                metric_unit='relative_0_to_100',
                url=f'https://trends.google.com/trends/explore?geo={geo}&q={query}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            self.logger.info(f"Retrieved {len(signals)} signals for '{query}'")
            return signals
            
        except Exception as e:
            self.logger.error(f"Error fetching trends for '{query}': {e}")
            return []
    
    def get_related_queries(self, query: str, geo: str = 'CA') -> List[str]:
        """Get related queries for a search term."""
        if self.mock_mode:
            return [f"{query} software", f"{query} app", f"{query} tool"]
        
        try:
            self._respect_rate_limit(2.0)
            
            self._pytrends.build_payload([query], cat=0, timeframe='today 3-m', geo=geo)
            related = self._pytrends.related_queries()
            
            if related and query in related:
                rising = related[query].get('rising', [])
                if rising is not None and not rising.empty:
                    return rising['query'].head(5).tolist()
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error fetching related queries: {e}")
            return []

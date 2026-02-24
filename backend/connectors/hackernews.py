"""Hacker News connector for demand signals."""
from typing import List, Optional
from datetime import datetime
import requests
from .base import BaseConnector, DemandSignal

class HackerNewsConnector(BaseConnector):
    """Connector for Hacker News using official Firebase API.
    
    No API key required - HN API is public.
    https://github.com/HackerNews/API
    """
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    SEARCH_URL = "https://hn.algolia.com/api/v1"  # Algolia search for HN
    
    @property
    def source_name(self) -> str:
        return "hackernews"
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        # HN doesn't need API keys, but we support mock mode for testing
        super().__init__(None, mock_mode)
        self.logger.info("Hacker News connector initialized (no API key needed)")
    
    def search(self, query: str, tags: Optional[List[str]] = None,
               numericFilters: Optional[str] = None) -> List[DemandSignal]:
        """Search Hacker News for stories matching query.
        
        Uses Algolia's HN search API (official)."""
        if self.mock_mode:
            return self._generate_mock_signals(query, count=3)
        
        try:
            self._respect_rate_limit(0.5)  # Be nice to Algolia
            
            params = {
                'query': query,
                'hitsPerPage': 50,
                'tags': tags or ['story']
            }
            
            if numericFilters:
                params['numericFilters'] = numericFilters
            
            response = requests.get(
                f"{self.SEARCH_URL}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            hits = data.get('hits', [])
            
            if not hits:
                self.logger.warning(f"No HN results for: {query}")
                return []
            
            # Calculate metrics
            total_hits = data.get('nbHits', len(hits))
            total_comments = sum(hit.get('num_comments', 0) for hit in hits)
            total_points = sum(hit.get('points', 0) for hit in hits)
            avg_points = total_points / len(hits) if hits else 0
            
            # Get top story URL for citation
            top_story = hits[0] if hits else {}
            top_url = f"https://news.ycombinator.com/item?id={top_story.get('objectID')}"
            
            signals = []
            
            # Signal 1: Total matching stories
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='story_count',
                metric_value=float(total_hits),
                metric_unit='stories',
                url=f'https://hn.algolia.com/?q={query}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            # Signal 2: Total engagement (comments)
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='engagement',
                metric_value=float(total_comments),
                metric_unit='comments',
                url=top_url,
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            # Signal 3: Average points (quality)
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='avg_points',
                metric_value=float(avg_points),
                metric_unit='points',
                url=top_url,
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            self.logger.info(f"Found {total_hits} HN stories for '{query}'")
            return signals
            
        except requests.RequestException as e:
            self.logger.error(f"Error searching HN for '{query}': {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []
    
    def get_top_stories(self, limit: int = 30) -> List[dict]:
        """Get current top stories (useful for trend detection)."""
        if self.mock_mode:
            return [
                {
                    'title': 'Mock HN Top Story',
                    'url': 'https://news.ycombinator.com/mock',
                    'score': 150,
                    'descendants': 45
                }
            ]
        
        try:
            self._respect_rate_limit(0.5)
            
            # Get top story IDs
            response = requests.get(f"{self.BASE_URL}/topstories.json", timeout=10)
            response.raise_for_status()
            
            story_ids = response.json()[:limit]
            stories = []
            
            for story_id in story_ids:
                self._respect_rate_limit(0.1)  # Small delay between requests
                
                story_resp = requests.get(
                    f"{self.BASE_URL}/item/{story_id}.json",
                    timeout=10
                )
                story_resp.raise_for_status()
                story = story_resp.json()
                
                if story and story.get('title'):
                    stories.append({
                        'title': story.get('title'),
                        'url': story.get('url') or f"https://news.ycombinator.com/item?id={story_id}",
                        'score': story.get('score', 0),
                        'comments': story.get('descendants', 0),
                        'time': story.get('time')
                    })
            
            return stories
            
        except Exception as e:
            self.logger.error(f"Error fetching top stories: {e}")
            return []
    
    def search_show_hn(self, query: str) -> List[DemandSignal]:
        """Search Show HN (product launches) for a topic.
        
        Useful for finding competing products."""
        return self.search(query, tags=['show_hn'])
    
    def search_ask_hn(self, query: str) -> List[DemandSignal]:
        """Search Ask HN (questions) for a topic.
        
        Useful for finding problems people are asking about."""
        return self.search(query, tags=['ask_hn'])

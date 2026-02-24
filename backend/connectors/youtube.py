"""YouTube connector for demand signals."""
from typing import List, Optional
from datetime import datetime
from .base import BaseConnector, DemandSignal

class YouTubeConnector(BaseConnector):
    """Connector for YouTube Data API.
    
    Requires Google Cloud API key with YouTube Data API enabled.
    https://console.cloud.google.com/apis/credentials
    """
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    @property
    def source_name(self) -> str:
        return "youtube"
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = False):
        super().__init__(api_key, mock_mode)
        
        if not self.mock_mode and not api_key:
            self.logger.warning("YouTube API key not provided, switching to mock mode")
            self.mock_mode = True
    
    def search(self, query: str, max_results: int = 50,
               order: str = 'relevance') -> List[DemandSignal]:
        """Search YouTube for videos matching query.
        
        Args:
            query: Search term
            max_results: Max videos to fetch (default 50)
            order: 'relevance', 'date', 'rating', 'viewCount'
        """
        if self.mock_mode:
            return self._generate_mock_signals(query, count=3)
        
        try:
            import requests
            
            self._respect_rate_limit(0.5)
            
            params = {
                'key': self.api_key,
                'q': query,
                'part': 'snippet,statistics',
                'type': 'video',
                'maxResults': min(max_results, 50),  # API limit
                'order': order,
                'relevanceLanguage': 'en'
            }
            
            response = requests.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                self.logger.warning(f"No YouTube results for: {query}")
                return []
            
            # Get video IDs for statistics
            video_ids = [item['id']['videoId'] for item in items if 'videoId' in item.get('id', {})]
            
            if video_ids:
                self._respect_rate_limit(0.5)
                stats_response = requests.get(
                    f"{self.BASE_URL}/videos",
                    params={
                        'key': self.api_key,
                        'id': ','.join(video_ids[:10]),  # Batch request, limit 10 for simplicity
                        'part': 'statistics'
                    },
                    timeout=10
                )
                stats_response.raise_for_status()
                stats_data = {item['id']: item.get('statistics', {}) for item in stats_response.json().get('items', [])}
            else:
                stats_data = {}
            
            # Calculate metrics
            total_views = 0
            total_likes = 0
            total_comments = 0
            video_count = len(video_ids)
            
            for vid_id, stats in stats_data.items():
                total_views += int(stats.get('viewCount', 0))
                total_likes += int(stats.get('likeCount', 0))
                total_comments += int(stats.get('commentCount', 0))
            
            avg_views = total_views / video_count if video_count else 0
            
            signals = []
            
            # Signal 1: Video volume
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='video_count',
                metric_value=float(video_count),
                metric_unit='videos',
                url=f'https://www.youtube.com/results?search_query={query}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            # Signal 2: Total views (interest indicator)
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='total_views',
                metric_value=float(total_views),
                metric_unit='views',
                url=f'https://www.youtube.com/results?search_query={query}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            # Signal 3: Average views per video (content saturation)
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='avg_views',
                metric_value=float(avg_views),
                metric_unit='views_per_video',
                url=f'https://www.youtube.com/results?search_query={query}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            self.logger.info(f"Found {video_count} YouTube videos for '{query}'")
            return signals
            
        except Exception as e:
            self.logger.error(f"Error searching YouTube for '{query}': {e}")
            return []
    
    def get_trending_videos(self, category_id: str = '0', 
                           region_code: str = 'US') -> List[dict]:
        """Get trending videos (general trend detection)."""
        if self.mock_mode:
            return [
                {
                    'title': 'Mock Trending Video',
                    'url': 'https://youtube.com/mock',
                    'view_count': 1000000
                }
            ]
        
        try:
            import requests
            
            self._respect_rate_limit(0.5)
            
            response = requests.get(
                f"{self.BASE_URL}/videos",
                params={
                    'key': self.api_key,
                    'part': 'snippet,statistics',
                    'chart': 'mostPopular',
                    'regionCode': region_code,
                    'videoCategoryId': category_id,
                    'maxResults': 25
                },
                timeout=10
            )
            response.raise_for_status()
            
            return [
                {
                    'title': item['snippet']['title'],
                    'url': f"https://youtube.com/watch?v={item['id']}",
                    'view_count': int(item['statistics'].get('viewCount', 0)),
                    'channel': item['snippet']['channelTitle']
                }
                for item in response.json().get('items', [])
            ]
            
        except Exception as e:
            self.logger.error(f"Error fetching trending videos: {e}")
            return []

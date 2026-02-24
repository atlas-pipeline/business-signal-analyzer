"""Reddit connector for demand signals."""
from typing import List, Optional
from datetime import datetime, timedelta
from .base import BaseConnector, DemandSignal

class RedditConnector(BaseConnector):
    """Connector for Reddit data using official API (PRAW)."""
    
    @property
    def source_name(self) -> str:
        return "reddit"
    
    def __init__(self, client_id: Optional[str] = None, 
                 client_secret: Optional[str] = None,
                 user_agent: str = "BusinessSignalAnalyzer/1.0",
                 mock_mode: bool = False):
        super().__init__(None, mock_mode)
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self._reddit = None
        
        if not self.mock_mode:
            if not client_id or not client_secret:
                self.logger.warning("Reddit API credentials not provided, switching to mock mode")
                self.mock_mode = True
            else:
                try:
                    import praw
                    self._reddit = praw.Reddit(
                        client_id=client_id,
                        client_secret=client_secret,
                        user_agent=user_agent
                    )
                    self.logger.info("Reddit connector initialized")
                except ImportError:
                    self.logger.warning("praw not installed, switching to mock mode")
                    self.mock_mode = True
                except Exception as e:
                    self.logger.error(f"Failed to initialize Reddit: {e}")
                    self.mock_mode = True
    
    def search(self, query: str, subreddits: Optional[List[str]] = None,
               time_filter: str = 'month', limit: int = 100) -> List[DemandSignal]:
        """Search Reddit for posts matching query.
        
        Args:
            query: Search term
            subreddits: List of subreddits to search (default: all)
            time_filter: 'day', 'week', 'month', 'year', 'all'
            limit: Max posts to fetch
        """
        if self.mock_mode:
            return self._generate_mock_signals(query, count=3)
        
        try:
            self._respect_rate_limit(1.0)
            
            signals = []
            total_posts = 0
            total_comments = 0
            total_score = 0
            
            # Search all of Reddit
            search_results = self._reddit.subreddit('all').search(
                query, 
                time_filter=time_filter,
                limit=limit,
                sort='relevance'
            )
            
            posts = list(search_results)
            
            if not posts:
                self.logger.warning(f"No Reddit posts found for: {query}")
                return []
            
            for post in posts:
                total_posts += 1
                total_comments += post.num_comments
                total_score += post.score
            
            avg_score = total_score / len(posts) if posts else 0
            avg_comments = total_comments / len(posts) if posts else 0
            
            # Signal 1: Post volume
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='post_count',
                metric_value=float(total_posts),
                metric_unit='posts',
                url=f'https://www.reddit.com/search/?q={query}&sort=new&t={time_filter}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            # Signal 2: Total engagement (comments)
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='engagement',
                metric_value=float(total_comments),
                metric_unit='comments',
                url=f'https://www.reddit.com/search/?q={query}&sort=new&t={time_filter}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            # Signal 3: Average upvotes (quality indicator)
            signals.append(DemandSignal(
                source=self.source_name,
                query=query,
                metric_type='avg_upvotes',
                metric_value=float(avg_score),
                metric_unit='upvotes',
                url=f'https://www.reddit.com/search/?q={query}&sort=new&t={time_filter}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            ))
            
            self.logger.info(f"Found {total_posts} Reddit posts for '{query}'")
            return signals
            
        except Exception as e:
            self.logger.error(f"Error searching Reddit for '{query}': {e}")
            return []
    
    def get_subreddit_stats(self, subreddit_name: str) -> List[DemandSignal]:
        """Get general stats for a subreddit (community size, activity)."""
        if self.mock_mode:
            return []
        
        try:
            self._respect_rate_limit(1.0)
            
            subreddit = self._reddit.subreddit(subreddit_name)
            
            return [DemandSignal(
                source=self.source_name,
                query=f"r/{subreddit_name}",
                metric_type='subscriber_count',
                metric_value=float(subreddit.subscribers),
                metric_unit='subscribers',
                url=f'https://www.reddit.com/r/{subreddit_name}',
                data_date=datetime.utcnow().strftime('%Y-%m-%d')
            )]
            
        except Exception as e:
            self.logger.error(f"Error fetching subreddit stats: {e}")
            return []
    
    def get_problem_posts(self, subreddit: str = 'startups', 
                         problem_keywords: Optional[List[str]] = None) -> List[dict]:
        """Get recent posts that mention problems or pain points."""
        if self.mock_mode:
            return [
                {
                    'title': f'Mock problem post about {subreddit}',
                    'url': f'https://reddit.com/r/{subreddit}/mock',
                    'score': 42,
                    'num_comments': 10
                }
            ]
        
        if not problem_keywords:
            problem_keywords = ['problem', 'pain', 'struggling', 'difficult', 'frustrated', 'help']
        
        try:
            self._respect_rate_limit(1.0)
            
            posts = []
            sub = self._reddit.subreddit(subreddit)
            
            for post in sub.new(limit=100):
                title_lower = post.title.lower()
                if any(kw in title_lower for kw in problem_keywords):
                    posts.append({
                        'title': post.title,
                        'url': f'https://www.reddit.com{post.permalink}',
                        'score': post.score,
                        'num_comments': post.num_comments,
                        'created_utc': post.created_utc
                    })
            
            return sorted(posts, key=lambda x: x['score'], reverse=True)[:20]
            
        except Exception as e:
            self.logger.error(f"Error fetching problem posts: {e}")
            return []

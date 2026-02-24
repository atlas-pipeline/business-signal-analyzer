"""Reddit auto-scraper for business signal discovery."""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from connectors.reddit import RedditConnector

class RedditAutoScraper:
    """Auto-scrape Reddit for business pain points and signals."""
    
    # Target subreddits for business signals
    DEFAULT_SUBREDDITS = [
        'startups',
        'smallbusiness',
        'entrepreneur',
        'SaaS',
        'SideProject',
        'business',
        'freelance',
        'marketing'
    ]
    
    # Pain point indicators
    PAIN_KEYWORDS = [
        'problem', 'pain', 'struggle', 'frustrated', 'annoying',
        'difficult', 'hard', 'challenging', 'issue', 'trouble',
        'wish', 'need', 'want', 'looking for', 'recommendation',
        'help with', 'advice on', 'how do you', 'best way to'
    ]
    
    def __init__(self, reddit_connector: Optional[RedditConnector] = None):
        self.reddit = reddit_connector or RedditConnector(mock_mode=True)
    
    def find_pain_posts(self, subreddits: Optional[List[str]] = None,
                       limit: int = 50,
                       time_filter: str = 'week') -> List[Dict[str, Any]]:
        """Find posts that express pain points or problems.
        
        Args:
            subreddits: List of subreddits to search (default: DEFAULT_SUBREDDITS)
            limit: Posts per subreddit
            time_filter: 'day', 'week', 'month', 'year'
        """
        subreddits = subreddits or self.DEFAULT_SUBREDDITS
        pain_posts = []
        
        for subreddit in subreddits:
            if self.reddit.mock_mode:
                # Generate mock data
                pain_posts.extend(self._generate_mock_posts(subreddit, 3))
                continue
            
            try:
                posts = self.reddit._reddit.subreddit(subreddit).new(limit=limit)
                
                for post in posts:
                    title_lower = post.title.lower()
                    
                    # Check if post contains pain keywords
                    if any(kw in title_lower for kw in self.PAIN_KEYWORDS):
                        pain_posts.append({
                            'title': post.title,
                            'text': post.selftext[:500],
                            'url': f'https://www.reddit.com{post.permalink}',
                            'subreddit': subreddit,
                            'score': post.score,
                            'num_comments': post.num_comments,
                            'created_utc': post.created_utc,
                            'author': str(post.author) if post.author else 'deleted',
                            'pain_signals': [kw for kw in self.PAIN_KEYWORDS if kw in title_lower]
                        })
                        
            except Exception as e:
                print(f"Error scraping r/{subreddit}: {e}")
                continue
        
        # Sort by engagement (score + comments)
        pain_posts.sort(
            key=lambda x: x['score'] + x['num_comments'] * 2,
            reverse=True
        )
        
        return pain_posts[:100]  # Return top 100
    
    def extract_topics(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract topic clusters from pain posts."""
        # Simple keyword-based clustering
        topic_keywords = {
            'compliance': ['compliance', 'regulation', 'legal', 'documentation', 'audit'],
            'payments': ['payment', 'invoice', 'billing', 'charge', 'fee'],
            'marketing': ['marketing', 'leads', 'customers', 'acquisition', 'growth'],
            'operations': ['operations', 'workflow', 'process', 'automation', 'efficiency'],
            'software': ['software', 'tool', 'app', 'platform', 'SaaS'],
            'hiring': ['hire', 'employee', 'team', 'contractor', 'freelancer'],
            'communication': ['email', 'slack', 'communication', 'meeting', 'client']
        }
        
        topics = {name: [] for name in topic_keywords}
        
        for post in posts:
            text = f"{post['title']} {post['text']}".lower()
            
            for topic_name, keywords in topic_keywords.items():
                if any(kw in text for kw in keywords):
                    topics[topic_name].append(post)
        
        # Create topic summaries
        topic_summaries = []
        for topic_name, posts in topics.items():
            if posts:
                topic_summaries.append({
                    'name': topic_name.title(),
                    'description': f'Posts about {topic_name} challenges and solutions',
                    'post_count': len(posts),
                    'posts': posts[:5],  # Top 5 posts
                    'keywords': topic_keywords[topic_name],
                    'total_engagement': sum(p['score'] + p['num_comments'] for p in posts)
                })
        
        # Sort by engagement
        topic_summaries.sort(key=lambda x: x['total_engagement'], reverse=True)
        
        return topic_summaries
    
    def generate_search_queries(self, topic: Dict[str, Any]) -> List[str]:
        """Generate search queries for demand signal collection."""
        queries = []
        
        # Base queries from topic name
        queries.append(f"{topic['name'].lower()} software")
        queries.append(f"{topic['name'].lower()} tool")
        queries.append(f"best {topic['name'].lower()}")
        queries.append(f"{topic['name'].lower()} for small business")
        
        # Extract additional queries from post titles
        for post in topic['posts'][:3]:
            # Simple noun phrase extraction
            words = post['title'].lower().split()[:4]
            if len(words) >= 2:
                queries.append(' '.join(words))
        
        return list(set(queries))[:10]  # Deduplicate, limit to 10
    
    def _generate_mock_posts(self, subreddit: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate mock posts for testing."""
        mock_templates = [
            {
                'title': f'How do you handle {subreddit} compliance paperwork?',
                'text': 'Spending hours every week on documentation...',
                'pain_signals': ['handle', 'how do you']
            },
            {
                'title': f'Struggling with {subreddit} automation - need help',
                'text': 'Current process is manual and error-prone...',
                'pain_signals': ['struggling', 'need help']
            },
            {
                'title': f'What is the best tool for {subreddit} management?',
                'text': 'Looking for recommendations on software...',
                'pain_signals': ['best', 'looking for']
            }
        ]
        
        posts = []
        for i in range(count):
            template = mock_templates[i % len(mock_templates)]
            posts.append({
                'title': template['title'],
                'text': template['text'],
                'url': f'https://reddit.com/r/{subreddit}/mock_{i}',
                'subreddit': subreddit,
                'score': 50 + i * 10,
                'num_comments': 10 + i * 5,
                'created_utc': datetime.utcnow().timestamp(),
                'author': 'mock_user',
                'pain_signals': template['pain_signals']
            })
        
        return posts
    
    def scrape_and_create_conversation(self, db_create_func, 
                                       subreddits: Optional[List[str]] = None) -> Dict[str, Any]:
        """Full pipeline: scrape Reddit → extract topics → create in DB.
        
        Args:
            db_create_func: Function to create conversation in database
            subreddits: List of subreddits to scrape
        """
        # Scrape posts
        posts = self.find_pain_posts(subreddits)
        
        if not posts:
            return {'error': 'No pain point posts found'}
        
        # Create conversation from aggregated posts
        conversation_text = "\n\n".join([
            f"Reddit user ({p['subreddit']}): {p['title']}\n{p['text'][:300]}"
            for p in posts[:10]
        ])
        
        # Extract topics
        topics = self.extract_topics(posts)
        
        return {
            'posts_found': len(posts),
            'topics_extracted': len(topics),
            'conversation_text': conversation_text,
            'topics': topics,
            'top_subreddits': list(set(p['subreddit'] for p in posts[:20]))
        }

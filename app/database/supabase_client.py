"""
API Client - Sends scraped data to your Node.js API
NO direct database access - uses your existing API endpoints
"""

import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime

from app.config.settings import settings

logger = logging.getLogger(__name__)

class APIClient:
    """Client to communicate with your Node.js API"""
    
    def __init__(self):
        # Your Node.js API base URL
        self.api_base_url = settings.nodejs_api_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_link_exists(self, link: str) -> bool:
        """Check if article link already exists via your API"""
        try:
            # Check if your API has an endpoint to check existing links
            # If not, we'll just try to post and handle duplicates
            return False  # For now, always return False (let API handle duplicates)
        except Exception as e:
            logger.error(f"Error checking link existence: {e}")
            return False
    
    async def post_article(self, article_data: Dict) -> bool:
        """Post scraped article to your Node.js API"""
        try:
            # Prepare data for your API format
            api_data = {
                "timestamp": article_data.get("timestamp"),
                "text_content": article_data.get("text_content", ""),
                "source": article_data.get("source"),
                "link": article_data.get("link"),
                "title": article_data.get("title"),
                "category": article_data.get("category", "general"),
                "story_id": article_data.get("story_id"),
                "keywords": article_data.get("keywords", []),
                "is_primary_article": article_data.get("is_primary_article", False)
            }
            
            # POST to your API endpoint
            async with self.session.post(f"{self.api_base_url}/api/rss", json=api_data) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    logger.info(f"Successfully posted article: {article_data.get('title', '')[:50]}...")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error posting article to API: {e}")
            return False
    
    async def get_recent_stories(self, hours_back: int = 24) -> List[Dict]:
        """Get recent stories for clustering via your API"""
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow().isoformat()
            
            # Get recent articles from your API
            params = {
                "limit": 500,  # Get enough for clustering
                "since": cutoff_time  # If your API supports time filtering
            }
            
            async with self.session.get(f"{self.api_base_url}/api/rss", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filter articles that have story_id (existing stories)
                    stories = []
                    for article in data.get("data", []):
                        if article.get("story_id"):
                            stories.append({
                                "story_id": article["story_id"],
                                "keywords": article.get("keywords", []),
                                "title": article.get("title", ""),
                                "category": article.get("category", "general")
                            })
                    
                    logger.info(f"Retrieved {len(stories)} recent stories for clustering")
                    return stories
                else:
                    logger.error(f"Failed to get recent stories: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting recent stories: {e}")
            return []
    
    async def test_connection(self) -> bool:
        """Test connection to your Node.js API"""
        try:
            async with self.session.get(f"{self.api_base_url}/health") as response:
                if response.status == 200:
                    logger.info("API connection test successful")
                    return True
                else:
                    logger.error(f"API health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False

# Singleton instance
api_client = APIClient()
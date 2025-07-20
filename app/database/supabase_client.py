import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class APIClient:
    """Client to communicate with your Node.js API"""
    
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def post_article(self, article_data: Dict) -> bool:
        """Post scraped article to your Node.js API"""
        try:
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
            
            async with self.session.post(f"{self.api_base_url}/api/rss", json=api_data) as response:
                if response.status in [200, 201]:
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
            async with self.session.get(f"{self.api_base_url}/api/rss") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filter articles that have story_id
                    stories = []
                    for article in data.get("data", []):
                        if article.get("story_id"):
                            stories.append({
                                "story_id": article["story_id"],
                                "keywords": article.get("keywords", []),
                                "title": article.get("title", ""),
                                "category": article.get("category", "general")
                            })
                    
                    return stories
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting recent stories: {e}")
            return []
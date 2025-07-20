import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import uuid
from app.config.settings import settings

logger = logging.getLogger(__name__)

class SimpleNewsScraper:
    """Simple scraper to test the pipeline"""
    
    def __init__(self):
        self.api_base_url = settings.nodejs_api_url
    
    async def test_scrape_single_source(self):
        """Test scraping a single reliable source"""
        try:
            # Test with BBC News Middle East (reliable structure)
            url = "https://www.bbc.com/news/world/middle_east"
            
            async with aiohttp.ClientSession() as session:
                # Scrape the page
                async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                    if response.status != 200:
                        return {"error": f"Failed to fetch {url}"}
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find articles (BBC structure)
                    articles = []
                    article_elements = soup.select('[data-testid="liverpool-card"]')[:5]  # Get first 5
                    
                    for element in article_elements:
                        try:
                            # Extract headline
                            headline_elem = element.select_one('h2')
                            if not headline_elem:
                                continue
                                
                            headline = headline_elem.get_text(strip=True)
                            
                            # Extract link
                            link_elem = element.select_one('a[href]')
                            if not link_elem:
                                continue
                                
                            link = link_elem.get('href')
                            if link.startswith('/'):
                                link = f"https://www.bbc.com{link}"
                            
                            # Extract summary
                            summary_elem = element.select_one('p')
                            summary = summary_elem.get_text(strip=True) if summary_elem else ""
                            
                            article_data = {
                                "timestamp": datetime.utcnow().isoformat(),
                                "text_content": summary or headline,
                                "source": "BBC News",
                                "link": link,
                                "title": headline,
                                "category": "regional",
                                "story_id": str(uuid.uuid4()),
                                "keywords": ["middle", "east", "news"],
                                "is_primary_article": True
                            }
                            
                            articles.append(article_data)
                            
                        except Exception as e:
                            logger.error(f"Error processing article: {e}")
                            continue
                    
                    # Post articles to your API
                    posted_count = 0
                    for article in articles:
                        success = await self.post_to_api(article, session)
                        if success:
                            posted_count += 1
                    
                    return {
                        "status": "success",
                        "source": "BBC News Middle East",
                        "articles_found": len(articles),
                        "articles_posted": posted_count,
                        "sample_articles": articles[:2]  # Show first 2 for inspection
                    }
                    
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return {"error": str(e)}
    
    async def post_to_api(self, article_data, session):
        """Post article to your Node.js API"""
        try:
            async with session.post(
                f"{self.api_base_url}/api/rss",
                json=article_data,
                headers={'Content-Type': 'application/json'}
            ) as response:
                return response.status in [200, 201]
        except Exception as e:
            logger.error(f"Error posting to API: {e}")
            return False

# Create instance
simple_scraper = SimpleNewsScraper()
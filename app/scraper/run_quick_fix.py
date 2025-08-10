# File: app/scraper/quick_fix_scraper.py
"""
Quick-Fix UAE Scraper - Only working sources with longer delays
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import uuid
import re
import time
from typing import Dict, List, Set, Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)

class QuickFixScraper:
    """Quick fix scraper focusing on working sources only"""
    
    def __init__(self):
        self.api_base_url = settings.nodejs_api_url
        self.scraped_urls = set()
        
        # ONLY WORKING SOURCES - based on your logs
        self.working_sources = {
            "bbc_me": {
                "url": "https://www.bbc.com/news/world/middle_east",
                "name": "BBC Middle East",
                "selectors": {
                    "articles": "[data-testid='liverpool-card'], .media-list__item",
                    "headline": "h2, h3, .media__title",
                    "link": "a[href]",
                    "summary": "p, .media__summary"
                }
            },
            
            "reuters_me": {
                "url": "https://www.reuters.com/world/middle-east/",
                "name": "Reuters Middle East",
                "selectors": {
                    "articles": "[data-testid='MediaStoryCard']",
                    "headline": "h2, h3, .text__text",
                    "link": "a[href]",
                    "summary": "p"
                }
            },
            
            "construction_week": {
                "url": "https://www.constructionweekonline.com",
                "name": "Construction Week",
                "selectors": {
                    "articles": "article",
                    "headline": "h1, h2, h3, .title",
                    "link": "a[href]",
                    "summary": "p"
                }
            },
            
            # Add more working sources gradually
            "al_jazeera": {
                "url": "https://www.aljazeera.com/news/",
                "name": "Al Jazeera",
                "selectors": {
                    "articles": "article, .gc",
                    "headline": "h1, h2, h3, .gc__title",
                    "link": "a[href]",
                    "summary": "p, .gc__excerpt"
                }
            },
            
            "middle_east_monitor": {
                "url": "https://www.middleeastmonitor.com",
                "name": "Middle East Monitor",
                "selectors": {
                    "articles": "article, .post",
                    "headline": "h1, h2, h3, .entry-title",
                    "link": "a[href]",
                    "summary": "p, .entry-summary"
                }
            }
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        if not text:
            return []
        
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter keywords
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'news', 'said', 'says'}
        keywords = [word for word in words if len(word) >= 3 and word not in stop_words and not word.isdigit()]
        
        return keywords[:10]  # Limit to 10 keywords
    
    def clean_text(self, text: str) -> str:
        """Clean text"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text).strip()[:500]
    
    async def fetch_page(self, url: str, source_name: str, session: aiohttp.ClientSession) -> Optional[BeautifulSoup]:
        """Fetch page with better headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',  # Removed brotli
            'Connection': 'keep-alive'
        }
        
        try:
            logger.info(f"🌐 Fetching {source_name}: {url}")
            async with session.get(url, headers=headers, timeout=20) as response:
                if response.status == 200:
                    html = await response.text()
                    logger.info(f"✅ {source_name} - Got {len(html)} chars")
                    return BeautifulSoup(html, 'html.parser')
                else:
                    logger.warning(f"❌ {source_name} - Status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ {source_name} - Error: {e}")
            return None
    
    def extract_articles(self, soup: BeautifulSoup, source_name: str, selectors: Dict) -> List[Dict]:
        """Extract articles from page"""
        articles = []
        
        try:
            # Find articles
            article_elements = soup.select(selectors["articles"])
            logger.info(f"📦 {source_name} - Found {len(article_elements)} containers")
            
            for element in article_elements[:20]:  # Limit to 20 per source
                try:
                    # Get headline
                    headline_elem = element.select_one(selectors["headline"])
                    if not headline_elem:
                        continue
                    
                    headline = self.clean_text(headline_elem.get_text(strip=True))
                    if not headline or len(headline) < 10:
                        continue
                    
                    # Get link
                    link_elem = element.select_one(selectors["link"])
                    if not link_elem:
                        continue
                    
                    url = link_elem.get('href', '')
                    if not url:
                        continue
                    
                    # Make absolute URL
                    if url.startswith('/'):
                        base_url = selectors.get("base_url", "")
                        if "bbc.com" in source_name.lower():
                            url = f"https://www.bbc.com{url}"
                        elif "reuters.com" in source_name.lower():
                            url = f"https://www.reuters.com{url}"
                        elif "aljazeera.com" in source_name.lower():
                            url = f"https://www.aljazeera.com{url}"
                        else:
                            continue
                    
                    if url in self.scraped_urls or not url.startswith('http'):
                        continue
                    
                    # Get summary
                    summary = ""
                    summary_elem = element.select_one(selectors.get("summary", "p"))
                    if summary_elem:
                        summary = self.clean_text(summary_elem.get_text(strip=True))
                    
                    # Pick image from card if available
                    image_url = None
                    img = element.select_one('img')
                    if img:
                        image_url = img.get('src') or img.get('data-src') or None

                    # Create article data (only required fields)
                    article_data = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "link": url,
                        "title": headline,
                        "category": "regional",
                        "image_url": image_url
                    }
                    
                    articles.append(article_data)
                    self.scraped_urls.add(url)
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting article: {e}")
                    continue
            
            logger.info(f"✅ {source_name} - Extracted {len(articles)} valid articles")
            return articles
            
        except Exception as e:
            logger.error(f"❌ {source_name} - Extraction error: {e}")
            return []
    
    async def post_article(self, article_data: Dict, session: aiohttp.ClientSession) -> bool:
        """Post article with long delay"""
        try:
            # LONG delay to avoid rate limiting
            await asyncio.sleep(5)  # 5 seconds between each article
            
            async with session.post(
                f"{self.api_base_url}/api/rss",
                json={
                    "timestamp": article_data.get("timestamp"),
                    "link": article_data.get("link"),
                    "title": article_data.get("title"),
                    "category": article_data.get("category"),
                    "image_url": article_data.get("image_url")
                },
                headers={'Content-Type': 'application/json'},
                timeout=10
            ) as response:
                
                if response.status in [200, 201]:
                    logger.info(f"✅ Posted: {article_data['title'][:50]}...")
                    return True
                elif response.status == 429:
                    logger.warning(f"⏰ Rate limited - backing off 30 seconds")
                    await asyncio.sleep(30)  # Long backoff
                    return False
                elif response.status == 409:
                    error_text = await response.text()
                    logger.info(f"👉 Duplicate article found, skipping: {article_data['title'][:50]}... ({error_text})")
                    return False
                else:
                    error = await response.text()
                    logger.error(f"❌ API error {response.status}: {error}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Post error: {e}")
            return False
    
    async def scrape_source(self, source_key: str, source_config: Dict, session: aiohttp.ClientSession) -> Dict:
        """Scrape single source"""
        logger.info(f"🚀 Starting {source_config['name']}")
        
        # Fetch page
        soup = await self.fetch_page(source_config["url"], source_config["name"], session)
        if not soup:
            return {"source": source_config["name"], "articles_found": 0, "articles_posted": 0, "error": "Failed to fetch"}
        
        # Extract articles
        articles = self.extract_articles(soup, source_config["name"], source_config["selectors"])
        if not articles:
            return {"source": source_config["name"], "articles_found": 0, "articles_posted": 0, "error": "No articles extracted"}
        
        # Post articles with delays
        posted_count = 0
        for article in articles:
            success = await self.post_article(article, session)
            if success:
                posted_count += 1
        
        logger.info(f"✅ {source_config['name']} completed: {posted_count}/{len(articles)} posted")
        
        return {
            "source": source_config["name"],
            "articles_found": len(articles),
            "articles_posted": posted_count
        }
    
    async def run_quick_scrape(self) -> Dict:
        """Run quick scrape with working sources only"""
        logger.info("🚀 Starting QUICK-FIX UAE scrape...")
        start_time = time.time()
        
        results = []
        total_found = 0
        total_posted = 0
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            for source_key, source_config in self.working_sources.items():
                try:
                    result = await self.scrape_source(source_key, source_config, session)
                    results.append(result)
                    total_found += result["articles_found"]
                    total_posted += result["articles_posted"]
                    
                    # Long delay between sources to avoid rate limiting
                    logger.info(f"😴 Waiting 10 seconds before next source...")
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    logger.error(f"❌ Error with {source_key}: {e}")
                    results.append({
                        "source": source_config["name"],
                        "articles_found": 0,
                        "articles_posted": 0,
                        "error": str(e)
                    })
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"🎉 QUICK SCRAPE COMPLETED!")
        logger.info(f"⏱️ Time: {elapsed_time:.2f}s")
        logger.info(f"📊 Total: {total_posted}/{total_found} articles posted")
        
        return {
            "status": "completed",
            "summary": {
                "sources_processed": len(results),
                "total_articles_found": total_found,
                "total_articles_posted": total_posted,
                "elapsed_time_seconds": round(elapsed_time, 2)
            },
            "detailed_results": results,
            "recommendations": [
                f"🐌 Used 5-second delays between articles to avoid rate limiting",
                f"📊 Posted {total_posted} articles total",
                f"⚡ To get more articles, increase rate limits in your Node.js API"
            ]
        }

# Global instance
quick_scraper = QuickFixScraper()
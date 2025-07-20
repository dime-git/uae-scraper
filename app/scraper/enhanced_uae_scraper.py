# File: app/scraper/enhanced_uae_scraper.py
"""
Enhanced UAE News Scraper with Detailed Logging and Error Handling
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
from dataclasses import dataclass
from urllib.parse import urljoin
import json

from app.config.settings import settings

logger = logging.getLogger(__name__)

@dataclass
class ScrapingResult:
    """Detailed scraping result for each source"""
    source_name: str
    url: str
    status: str  # 'success', 'partial', 'failed'
    articles_found: int
    articles_posted: int
    error_details: Dict = None
    fetch_status: Optional[int] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.error_details is None:
            self.error_details = {}

@dataclass
class Article:
    headline: str
    url: str
    source: str
    summary: str = ""
    category: str = "general"
    keywords: Set[str] = None
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = set()
        if self.scraped_at is None:
            self.scraped_at = datetime.utcnow()

class EnhancedUAENewsConfig:
    """Enhanced configuration with better selectors and fallbacks"""
    
    SOURCES = {
        # TIER 1: Working and reliable sources
        "bbc_me": {
            "url": "https://www.bbc.com/news/world/middle_east",
            "name": "BBC Middle East",
            "priority": 1,
            "selectors": {
                "articles": "[data-testid='liverpool-card'], [data-testid='media-card'], .media-list__item, article",
                "headline": "h2, h3, .media__title, .gel-trafalgar",
                "link": "a[href]",
                "summary": "p, .media__summary, .gel-body-copy"
            },
            "category": "regional",
            "timeout": 15
        },
        
        "reuters_me": {
            "url": "https://www.reuters.com/world/middle-east/",
            "name": "Reuters Middle East",
            "priority": 1,
            "selectors": {
                "articles": "[data-testid='MediaStoryCard'], .story-card, article, .media-story-card",
                "headline": "h2, h3, .text__text, .story-title",
                "link": "a[href]",
                "summary": "p, .story-summary"
            },
            "category": "regional",
            "timeout": 15
        },
        
        "cnn_me": {
            "url": "https://edition.cnn.com/middle-east",
            "name": "CNN Middle East",
            "priority": 1,
            "selectors": {
                "articles": ".card, .cd, article, .zn-body__read-all",
                "headline": "h1, h2, h3, .cd__headline, .card__title",
                "link": "a[href]",
                "summary": "p, .cd__description, .card__summary"
            },
            "category": "regional",
            "timeout": 15
        },
        
        "arab_news": {
            "url": "https://www.arabnews.com",
            "name": "Arab News",
            "priority": 1,
            "selectors": {
                "articles": ".article-item, .story-card, article, .post-item",
                "headline": "h1, h2, h3, .title, .headline, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .post-excerpt"
            },
            "category": "regional",
            "timeout": 20
        },
        
        "the_national": {
            "url": "https://www.thenationalnews.com",
            "name": "The National",
            "priority": 1,
            "selectors": {
                "articles": "article, [data-testid], .card, .story-card, .post, .article-card",
                "headline": "h1, h2, h3, .headline, a[data-link-name], .title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .standfirst, .description, .excerpt"
            },
            "category": "regional",
            "timeout": 20
        },
        
        "gulf_news": {
            "url": "https://gulfnews.com",
            "name": "Gulf News", 
            "priority": 1,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "regional",
            "timeout": 20
        },
        
        "khaleej_times": {
            "url": "https://khaleejtimes.com",
            "name": "Khaleej Times",
            "priority": 1,
            "selectors": {
                "articles": ".story-card, article, .news-item, .card, .post, .entry",
                "headline": "h1, h2, h3, .title, .headline, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .entry-summary"
            },
            "category": "regional",
            "timeout": 20
        },
        
        "wam_news": {
            "url": "https://www.wam.ae/en/",
            "name": "WAM News",
            "priority": 1,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "official",
            "timeout": 20
        },

        "arabian_business": {
            "url": "https://www.arabianbusiness.com/",
            "name": "Arabian Business",
            "priority": 1,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "economy",
            "timeout": 20
        },

        "bloomberg_me": {
            "url": "https://www.bloomberg.com/middle-east",
            "name": "Bloomberg ME",
            "priority": 1,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "economy",
            "timeout": 20
        },

        "gulf_business": {
            "url": "https://gulfbusiness.com/",
            "name": "Gulf Business",
            "priority": 1,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "economy",
            "timeout": 20
        },
        
        # TIER 2: Business sources
        "zawya": {
            "url": "https://www.zawya.com",
            "name": "Zawya",
            "priority": 2,
            "selectors": {
                "articles": ".story-card, .news-item, article, .post, .article-card",
                "headline": "h1, h2, h3, .title, .headline, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description"
            },
            "category": "economy",
            "timeout": 25
        },
        
        "construction_week": {
            "url": "https://www.constructionweekonline.com",
            "name": "Construction Week",
            "priority": 2,
            "selectors": {
                "articles": ".article-card, article, .news-item, .post, .story",
                "headline": "h1, h2, h3, .title, .headline, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description"
            },
            "category": "economy",
            "timeout": 20
        },
        
        "time_out_dubai": {
            "url": "https://www.timeoutdubai.com/news",
            "name": "Time Out Dubai",
            "priority": 2,
            "selectors": {
                "articles": ".article-card, article, .post, .news-item, .story",
                "headline": "h1, h2, h3, .title, .headline, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description"
            },
            "category": "lifestyle",
            "timeout": 15
        },
        
        "wamda": {
            "url": "https://www.wamda.com",
            "name": "Wamda",
            "priority": 2,
            "selectors": {
                "articles": ".post, article, .news-item, .story, .article",
                "headline": "h1, h2, h3, .title, .headline, .post-title",
                "link": "a[href]",
                "summary": "p, .excerpt, .summary, .description"
            },
            "category": "technology",
            "timeout": 20
        },

        "al_arabiya": {
            "url": "https://english.alarabiya.net/",
            "name": "Al Arabiya",
            "priority": 2,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "regional",
            "timeout": 20
        },

        "middle_east_eye": {
            "url": "https://www.middleeasteye.net/",
            "name": "Middle East Eye",
            "priority": 2,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "regional",
            "timeout": 20
        },

        "trade_arabia": {
            "url": "http://www.tradearabia.com/",
            "name": "Trade Arabia",
            "priority": 2,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "economy",
            "timeout": 20
        },

        "emirates_247": {
            "url": "https://www.emirates247.com/",
            "name": "Emirates 24/7",
            "priority": 2,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "regional",
            "timeout": 20
        },

        "techcrunch_me": {
            "url": "https://techcrunch.com/tag/mena/",
            "name": "TechCrunch ME",
            "priority": 2,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "technology",
            "timeout": 20
        },

        "whats_on_dubai": {
            "url": "https://whatson.ae/",
            "name": "What's On Dubai",
            "priority": 2,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "lifestyle",
            "timeout": 20
        },

        # TIER 3: Supplementary sources
        "meed": {
            "url": "https://www.meed.com/",
            "name": "MEED",
            "priority": 3,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "economy",
            "timeout": 20
        },

        "property_finder": {
            "url": "https://www.propertyfinder.ae/blog/",
            "name": "Property Finder",
            "priority": 3,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "lifestyle",
            "timeout": 20
        },

        "bayut_blog": {
            "url": "https://www.bayut.com/blog/",
            "name": "Bayut Blog",
            "priority": 3,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "lifestyle",
            "timeout": 20
        },

        "sport360": {
            "url": "https://sport360.com/",
            "name": "Sport360",
            "priority": 3,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "lifestyle",
            "timeout": 20
        },

        "entrepreneur_me": {
            "url": "https://www.entrepreneur.com/en/entrepreneur-middle-east",
            "name": "Entrepreneur ME",
            "priority": 3,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "economy",
            "timeout": 20
        },

        # TIER 4: Official sources
        "dubai_media_office": {
            "url": "https://mediaoffice.ae/en/",
            "name": "Dubai Media Office",
            "priority": 4,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "official",
            "timeout": 20
        },

        "abu_dhabi_media_office": {
            "url": "https://www.mediaoffice.abudhabi/en/",
            "name": "Abu Dhabi Media Office",
            "priority": 4,
            "selectors": {
                "articles": ".story-card, .article-card, article, .news-item, .post, .entry, .media-story-card",
                "headline": "h1, h2, h3, .headline, .title, .entry-title, .post-title",
                "link": "a[href]",
                "summary": "p, .summary, .excerpt, .description, .entry-summary"
            },
            "category": "official",
            "timeout": 20
        }
    }

class TextProcessor:
    """Enhanced text processing with better cleaning"""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'news', 'report', 'said', 'says', 'new', 'first', 'latest', 'breaking',
            'uae', 'dubai', 'abu', 'dhabi', 'emirates'
        }
    
    def extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords with enhanced cleaning"""
        if not text:
            return set()
        
        try:
            # More aggressive cleaning
            text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text.lower())
            text = re.sub(r'\s+', ' ', text).strip()
            words = text.split()
            
            keywords = set()
            for word in words:
                if (len(word) >= 3 and 
                    word not in self.stop_words and
                    not word.isdigit() and
                    not re.match(r'^[0-9]+$', word)):
                    keywords.add(word)
            
            return keywords
        except Exception as e:
            logger.warning(f"Error extracting keywords: {e}")
            return set()

class EnhancedUAEScraper:
    """Enhanced scraper with detailed logging and error handling"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.api_base_url = settings.nodejs_api_url
        self.scraped_urls = set()
        self.last_request_time = 0
        self.rate_limit_delay = max(settings.scraper_delay, 3.0)  # Minimum 3 seconds
        
        # Enhanced error tracking
        self.error_summary = {
            "network_errors": [],
            "parsing_errors": [],
            "api_errors": [],
            "rate_limit_hits": 0
        }
    
    async def respect_rate_limit(self):
        """Enhanced rate limiting with exponential backoff"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        delay = self.rate_limit_delay
        
        # Increase delay if we've hit rate limits
        if self.error_summary["rate_limit_hits"] > 5:
            delay = delay * 2
            logger.warning(f"Rate limit hits detected, increasing delay to {delay}s")
        
        if time_since_last < delay:
            sleep_time = delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def fetch_page_with_retry(self, url: str, source_name: str, session: aiohttp.ClientSession, timeout: int = 20) -> tuple[Optional[BeautifulSoup], Dict]:
        """Enhanced page fetching with retry logic and detailed error tracking"""
        await self.respect_rate_limit()
        
        error_details = {}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        for attempt in range(3):  # 3 attempts
            try:
                logger.info(f"🌐 Fetching {source_name} (attempt {attempt + 1}): {url}")
                
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    logger.info(f"📊 {source_name} - Status: {response.status}, Content-Type: {response.headers.get('content-type', 'unknown')}")
                    
                    if response.status == 200:
                        html = await response.text()
                        logger.info(f"📄 {source_name} - HTML length: {len(html)} chars")
                        
                        if len(html) < 1000:
                            error_details["html_too_short"] = f"HTML only {len(html)} chars"
                            logger.warning(f"⚠️ {source_name} - HTML suspiciously short: {len(html)} chars")
                        
                        soup = BeautifulSoup(html, 'html.parser')
                        logger.info(f"✅ {source_name} - Successfully parsed HTML")
                        return soup, error_details
                        
                    elif response.status == 403:
                        error_details["status_403"] = "Forbidden - likely bot detection"
                        logger.error(f"🚫 {source_name} - 403 Forbidden (bot detection)")
                        self.error_summary["network_errors"].append(f"{source_name}: 403 Forbidden")
                        
                    elif response.status == 404:
                        error_details["status_404"] = "Page not found"
                        logger.error(f"🔍 {source_name} - 404 Not Found")
                        self.error_summary["network_errors"].append(f"{source_name}: 404 Not Found")
                        break  # Don't retry 404s
                        
                    elif response.status == 429:
                        error_details["status_429"] = "Rate limited"
                        logger.error(f"⏰ {source_name} - 429 Rate Limited")
                        self.error_summary["network_errors"].append(f"{source_name}: 429 Rate Limited")
                        await asyncio.sleep(10)  # Wait longer for rate limits
                        
                    else:
                        error_details[f"status_{response.status}"] = f"HTTP {response.status}"
                        logger.error(f"❌ {source_name} - HTTP {response.status}")
                        
            except asyncio.TimeoutError:
                error_details["timeout"] = f"Timeout after {timeout}s"
                logger.error(f"⏰ {source_name} - Timeout after {timeout}s")
                self.error_summary["network_errors"].append(f"{source_name}: Timeout")
                
            except aiohttp.ClientError as e:
                error_details["client_error"] = str(e)
                logger.error(f"🌐 {source_name} - Client error: {e}")
                self.error_summary["network_errors"].append(f"{source_name}: {e}")
                
            except Exception as e:
                error_details["unexpected_error"] = str(e)
                logger.error(f"💥 {source_name} - Unexpected error: {e}")
                self.error_summary["network_errors"].append(f"{source_name}: {e}")
            
            if attempt < 2:  # Don't sleep after last attempt
                sleep_time = (attempt + 1) * 2
                logger.info(f"😴 {source_name} - Retrying in {sleep_time}s...")
                await asyncio.sleep(sleep_time)
        
        return None, error_details
    
    def extract_articles_with_debugging(self, soup: BeautifulSoup, source_name: str, source_config: Dict) -> tuple[List[Article], Dict]:
        """Enhanced article extraction with detailed debugging"""
        articles = []
        debug_info = {}
        selectors = source_config["selectors"]
        
        try:
            # Test each selector and log results
            article_selector = selectors["articles"]
            headline_selector = selectors["headline"]
            link_selector = selectors["link"]
            
            logger.info(f"🔍 {source_name} - Testing selectors:")
            logger.info(f"   Articles: '{article_selector}'")
            logger.info(f"   Headlines: '{headline_selector}'")
            logger.info(f"   Links: '{link_selector}'")
            
            # Find article containers
            article_elements = soup.select(article_selector)
            debug_info["total_containers"] = len(article_elements)
            logger.info(f"📦 {source_name} - Found {len(article_elements)} article containers")
            
            if len(article_elements) == 0:
                # Try alternative selectors
                alternative_selectors = [
                    "article", ".article", ".post", ".story", ".news-item",
                    ".card", "[class*='article']", "[class*='post']", "[class*='story']"
                ]
                
                logger.info(f"🔧 {source_name} - Trying alternative selectors...")
                for alt_selector in alternative_selectors:
                    alt_elements = soup.select(alt_selector)
                    logger.info(f"   '{alt_selector}': {len(alt_elements)} elements")
                    if len(alt_elements) > 0:
                        article_elements = alt_elements[:10]  # Use first 10
                        debug_info["used_alternative"] = alt_selector
                        break
            
            valid_articles = 0
            processing_errors = []
            
            for i, element in enumerate(article_elements[:settings.max_articles_per_source]):
                try:
                    logger.debug(f"🔍 {source_name} - Processing article {i+1}")
                    
                    # Extract headline with multiple attempts
                    headline_elem = element.select_one(headline_selector)
                    if not headline_elem:
                        # Try alternative headline selectors
                        for alt_headline in ["h1", "h2", "h3", ".title", ".headline", "a"]:
                            headline_elem = element.select_one(alt_headline)
                            if headline_elem:
                                break
                    
                    if not headline_elem:
                        logger.debug(f"   ❌ No headline found for article {i+1}")
                        continue
                    
                    headline = self.clean_text(headline_elem.get_text(strip=True))
                    if not headline or len(headline) < 10:
                        logger.debug(f"   ❌ Headline too short: '{headline}'")
                        continue
                    
                    # Extract URL
                    link_elem = element.select_one(link_selector)
                    if not link_elem:
                        link_elem = element.select_one("a[href]")  # Fallback
                    
                    if not link_elem:
                        logger.debug(f"   ❌ No link found for article {i+1}")
                        continue
                    
                    url = link_elem.get('href', '')
                    if not url:
                        logger.debug(f"   ❌ Empty URL for article {i+1}")
                        continue
                    
                    # Make URL absolute
                    if url.startswith('/'):
                        base_url = source_config["url"]
                        url = urljoin(base_url, url)
                    elif not url.startswith('http'):
                        logger.debug(f"   ❌ Invalid URL format: {url}")
                        continue
                    
                    # Skip if already processed
                    if url in self.scraped_urls:
                        logger.debug(f"   ⚠️ Duplicate URL: {url}")
                        continue
                    
                    # Extract summary
                    summary = ""
                    summary_elem = element.select_one(selectors.get("summary", ""))
                    if summary_elem:
                        summary = self.clean_text(summary_elem.get_text(strip=True))
                    
                    # Extract keywords
                    text_for_keywords = f"{headline} {summary}"
                    keywords = self.text_processor.extract_keywords(text_for_keywords)
                    
                    # Create article
                    article = Article(
                        headline=headline,
                        url=url,
                        source=source_config["name"],
                        summary=summary,
                        category=source_config.get("category", "general"),
                        keywords=keywords
                    )
                    
                    articles.append(article)
                    self.scraped_urls.add(url)
                    valid_articles += 1
                    
                    logger.debug(f"   ✅ Valid article: {headline[:50]}...")
                    
                except Exception as e:
                    error_msg = f"Error processing article {i+1}: {e}"
                    processing_errors.append(error_msg)
                    logger.warning(f"   ⚠️ {error_msg}")
                    self.error_summary["parsing_errors"].append(f"{source_name}: {error_msg}")
                    continue
            
            debug_info.update({
                "valid_articles": valid_articles,
                "processing_errors": processing_errors,
                "selectors_used": selectors
            })
            
            logger.info(f"✅ {source_name} - Extracted {valid_articles} valid articles")
            
        except Exception as e:
            error_msg = f"Critical extraction error: {e}"
            debug_info["critical_error"] = error_msg
            logger.error(f"💥 {source_name} - {error_msg}")
            self.error_summary["parsing_errors"].append(f"{source_name}: {error_msg}")
        
        return articles, debug_info
    
    def clean_text(self, text: str) -> str:
        """Enhanced text cleaning"""
        if not text:
            return ""
        
        try:
            # Remove extra whitespace and normalize
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Remove common artifacts
            text = re.sub(r'\n+', ' ', text)
            text = re.sub(r'\t+', ' ', text)
            
            # Remove common website artifacts
            text = re.sub(r'(Share|Tweet|Email|Print|Read more|Continue reading).*$', '', text, flags=re.IGNORECASE)
            
            return text[:500]  # Limit length
        except Exception as e:
            logger.warning(f"Error cleaning text: {e}")
            return text[:500] if text else ""
    
    async def post_article_with_retry(self, article: Article, session: aiohttp.ClientSession) -> tuple[bool, Dict]:
        """Enhanced API posting with retry and rate limit handling"""
        error_details = {}
        
        for attempt in range(3):
            try:
                article_data = {
                    "timestamp": article.scraped_at.isoformat(),
                    "text_content": article.summary or article.headline,
                    "source": article.source,
                    "link": article.url,
                    "title": article.headline,
                    "category": article.category,
                    "story_id": str(uuid.uuid4()),
                    "keywords": list(article.keywords),
                    "is_primary_article": True
                }
                
                # Add extra delay between API calls
                await asyncio.sleep(1.0)
                
                async with session.post(
                    f"{self.api_base_url}/api/rss",
                    json=article_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                ) as response:
                    
                    if response.status in [200, 201]:
                        logger.info(f"✅ Posted: {article.headline[:50]}... from {article.source}")
                        return True, {}
                    
                    elif response.status == 429:
                        self.error_summary["rate_limit_hits"] += 1
                        error_text = await response.text()
                        error_details["rate_limited"] = error_text
                        logger.error(f"⏰ API Rate Limited (attempt {attempt + 1}): {error_text}")
                        
                        # Exponential backoff for rate limits
                        backoff_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                        logger.info(f"😴 Backing off for {backoff_time}s due to rate limit...")
                        await asyncio.sleep(backoff_time)
                        continue
                        
                    elif response.status == 409:
                        error_text = await response.text()
                        logger.info(f"👉 Duplicate article found, skipping: {article.headline[:50]}... ({error_text})")
                        self.error_summary["api_errors"].append(f"Status 409: Duplicate article found - {error_text}")
                        return False, error_details
                        
                    else:
                        error_text = await response.text()
                        error_details[f"api_error_{response.status}"] = error_text
                        logger.error(f"❌ API error {response.status}: {error_text}")
                        self.error_summary["api_errors"].append(f"Status {response.status}: {error_text}")
                        
                        if response.status >= 500:  # Server errors - retry
                            await asyncio.sleep(2 * (attempt + 1))
                            continue
                        else:  # Client errors - don't retry
                            break
                            
            except Exception as e:
                error_details[f"post_error_attempt_{attempt}"] = str(e)
                logger.error(f"❌ Error posting article (attempt {attempt + 1}): {e}")
                self.error_summary["api_errors"].append(f"Post error: {e}")
                
                if attempt < 2:
                    await asyncio.sleep(2 * (attempt + 1))
        
        return False, error_details
    
    async def scrape_source_enhanced(self, source_name: str, source_config: Dict, session: aiohttp.ClientSession) -> ScrapingResult:
        """Enhanced source scraping with comprehensive logging"""
        start_time = time.time()
        logger.info(f"🚀 Starting enhanced scrape: {source_config['name']}")
        
        result = ScrapingResult(
            source_name=source_config['name'],
            url=source_config['url'],
            status='failed',
            articles_found=0,
            articles_posted=0
        )
        
        try:
            # Fetch page with detailed error tracking
            soup, fetch_errors = await self.fetch_page_with_retry(
                source_config["url"], 
                source_config["name"], 
                session,
                source_config.get("timeout", 20)
            )
            
            result.error_details.update(fetch_errors)
            
            if not soup:
                result.status = 'failed'
                result.error_details["no_content"] = "Failed to fetch page content"
                logger.error(f"❌ {source_config['name']} - Failed to fetch content")
                return result
            
            # Extract articles with debugging
            articles, extract_debug = self.extract_articles_with_debugging(soup, source_name, source_config)
            result.error_details.update(extract_debug)
            result.articles_found = len(articles)
            
            if len(articles) == 0:
                result.status = 'failed'
                result.error_details["no_articles"] = "No articles extracted"
                logger.warning(f"⚠️ {source_config['name']} - No articles extracted")
                return result
            
            # Post articles with retry logic
            posted_count = 0
            posting_errors = []
            
            for i, article in enumerate(articles):
                success, post_errors = await self.post_article_with_retry(article, session)
                if success:
                    posted_count += 1
                else:
                    posting_errors.append(f"Article {i+1}: {post_errors}")
                
                # Small delay between posts
                await asyncio.sleep(0.5)
            
            result.articles_posted = posted_count
            result.error_details["posting_errors"] = posting_errors
            
            if posted_count > 0:
                result.status = 'success' if posted_count == len(articles) else 'partial'
            else:
                result.status = 'failed'
                result.error_details["no_posts"] = "No articles posted successfully"
            
            result.processing_time = time.time() - start_time
            
            logger.info(f"✅ {source_config['name']} completed: {posted_count}/{len(articles)} posted in {result.processing_time:.2f}s")
            
        except Exception as e:
            result.status = 'failed'
            result.error_details["critical_error"] = str(e)
            result.processing_time = time.time() - start_time
            logger.error(f"💥 {source_config['name']} - Critical error: {e}")
            self.error_summary["parsing_errors"].append(f"{source_config['name']}: Critical error: {e}")
        
        return result
    
    async def run_enhanced_scrape(self) -> Dict:
        """Run enhanced scrape with comprehensive reporting"""
        logger.info("🚀 Starting ENHANCED UAE news scrape...")
        start_time = time.time()
        
        # Reset error tracking
        self.error_summary = {
            "network_errors": [],
            "parsing_errors": [],
            "api_errors": [],
            "rate_limit_hits": 0
        }
        
        results = []
        total_found = 0
        total_posted = 0
        
        # Sort sources by priority
        sorted_sources = sorted(
            EnhancedUAENewsConfig.SOURCES.items(),
            key=lambda x: x[1].get('priority', 999)
        )
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=5, limit_per_host=2),
            timeout=aiohttp.ClientTimeout(total=60)
        ) as session:
            
            for source_name, source_config in sorted_sources:
                try:
                    result = await self.scrape_source_enhanced(source_name, source_config, session)
                    results.append(result)
                    total_found += result.articles_found
                    total_posted += result.articles_posted
                    
                    # Adaptive delay based on success
                    if result.status == 'success':
                        await asyncio.sleep(2)
                    else:
                        await asyncio.sleep(5)  # Longer delay after failures
                        
                except Exception as e:
                    logger.error(f"❌ Critical error scraping {source_name}: {e}")
                    error_result = ScrapingResult(
                        source_name=source_config['name'],
                        url=source_config['url'],
                        status='failed',
                        articles_found=0,
                        articles_posted=0,
                        error_details={"critical_error": str(e)}
                    )
                    results.append(error_result)
        
        elapsed_time = time.time() - start_time
        
        # Generate comprehensive summary
        success_count = sum(1 for r in results if r.status == 'success')
        partial_count = sum(1 for r in results if r.status == 'partial')
        failed_count = sum(1 for r in results if r.status == 'failed')
        
        # Category breakdown
        category_summary = {}
        for result in results:
            category = EnhancedUAENewsConfig.SOURCES.get(
                [k for k, v in EnhancedUAENewsConfig.SOURCES.items() if v['name'] == result.source_name][0], 
                {}
            ).get('category', 'unknown')
            
            if category not in category_summary:
                category_summary[category] = {"found": 0, "posted": 0, "sources": 0}
            category_summary[category]["found"] += result.articles_found
            category_summary[category]["posted"] += result.articles_posted
            category_summary[category]["sources"] += 1
        
        # Error analysis
        error_analysis = {
            "network_errors": len(self.error_summary["network_errors"]),
            "parsing_errors": len(self.error_summary["parsing_errors"]),
            "api_errors": len(self.error_summary["api_errors"]),
            "rate_limit_hits": self.error_summary["rate_limit_hits"],
            "details": self.error_summary
        }
        
        # Success rate analysis
        success_rate = (success_count / len(results)) * 100 if results else 0
        posting_rate = (total_posted / total_found) * 100 if total_found > 0 else 0
        
        logger.info(f"🎉 ENHANCED SCRAPING COMPLETED!")
        logger.info(f"⏱️  Total time: {elapsed_time:.2f} seconds")
        logger.info(f"📊 Results: {success_count} success, {partial_count} partial, {failed_count} failed")
        logger.info(f"📈 Success rate: {success_rate:.1f}%")
        logger.info(f"📋 Articles: {total_posted}/{total_found} posted ({posting_rate:.1f}%)")
        logger.info(f"⚠️  Errors: {len(self.error_summary['network_errors'])} network, {len(self.error_summary['parsing_errors'])} parsing, {len(self.error_summary['api_errors'])} API")
        
        return {
            "status": "completed",
            "summary": {
                "total_sources": len(results),
                "successful_sources": success_count,
                "partial_sources": partial_count,
                "failed_sources": failed_count,
                "success_rate_percent": round(success_rate, 1),
                "total_articles_found": total_found,
                "total_articles_posted": total_posted,
                "posting_rate_percent": round(posting_rate, 1),
                "elapsed_time_seconds": round(elapsed_time, 2)
            },
            "by_category": category_summary,
            "error_analysis": error_analysis,
            "detailed_results": [
                {
                    "source": r.source_name,
                    "url": r.url,
                    "status": r.status,
                    "articles_found": r.articles_found,
                    "articles_posted": r.articles_posted,
                    "processing_time": round(r.processing_time, 2),
                    "error_details": r.error_details
                }
                for r in results
            ],
            "recommendations": self._generate_recommendations(results, error_analysis)
        }
    
    def _generate_recommendations(self, results: List[ScrapingResult], error_analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on scraping results"""
        recommendations = []
        
        # Rate limiting recommendations
        if error_analysis["rate_limit_hits"] > 5:
            recommendations.append("🐌 Consider increasing delay between API calls - detected high rate limiting")
        
        # Failed sources recommendations
        failed_sources = [r for r in results if r.status == 'failed']
        if len(failed_sources) > len(results) * 0.5:
            recommendations.append("🔧 More than 50% of sources failed - check selectors and URLs")
        
        # 403 errors
        forbidden_sources = [r for r in results if any('403' in str(e) for e in r.error_details.values())]
        if forbidden_sources:
            recommendations.append(f"🚫 {len(forbidden_sources)} sources blocked (403) - consider rotating User-Agents")
        
        # No articles found
        no_articles = [r for r in results if r.articles_found == 0 and r.status != 'failed']
        if no_articles:
            recommendations.append(f"🔍 {len(no_articles)} sources found but extracted 0 articles - update CSS selectors")
        
        # Posting failures
        posting_failures = [r for r in results if r.articles_found > 0 and r.articles_posted == 0]
        if posting_failures:
            recommendations.append(f"📤 {len(posting_failures)} sources found articles but posted none - check API connectivity")
        
        # Performance recommendations
        avg_time = sum(r.processing_time for r in results) / len(results) if results else 0
        if avg_time > 30:
            recommendations.append("⚡ Average processing time high - consider timeout optimization")
        
        if not recommendations:
            recommendations.append("✅ Scraping performance looks good!")
        
        return recommendations

# Create global instance
enhanced_scraper = EnhancedUAEScraper()
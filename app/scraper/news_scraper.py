# File: app/scraper/news_scraper.py
"""
UAE News Scraper - Advanced multi-source scraper with story clustering
Implements TIME.mk style aggregation for MENA region
"""

import asyncio
import hashlib
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
import uuid

import aiohttp
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, BackgroundTasks

from app.config.settings import settings
from app.database.supabase_client import db_manager

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class Article:
    """Article data structure"""
    headline: str
    url: str
    source: str
    summary: str = ""
    image_url: str = ""
    category: str = "general"
    keywords: Set[str] = None
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = set()
        if self.scraped_at is None:
            self.scraped_at = datetime.utcnow()

class UAENewsSourceConfig:
    """Configuration for UAE news sources - COMPLETE LIST from our priority matrix"""
    
    SOURCES = {
        # TIER 1: ESSENTIAL SOURCES (Must Have)
        
        # General News & Politics
        "the_national": {
            "url": "https://www.thenationalnews.com",
            "name": "The National",
            "priority": 1,
            "selectors": {
                "articles": "article, .card, .story-card",
                "headline": "h1, h2, h3, .headline, .card__title a, .story-card__title a",
                "link": "a[href]",
                "image": "img[src]",
                "summary": ".standfirst, .summary, .excerpt, .card__excerpt"
            },
            "category_map": {
                "/business": "economy",
                "/uae": "regional", 
                "/world": "politics",
                "/sport": "sports",
                "/lifestyle": "lifestyle",
                "/arts-culture": "entertainment"
            }
        },
        
        "gulf_news": {
            "url": "https://gulfnews.com",
            "name": "Gulf News",
            "priority": 1,
            "selectors": {
                "articles": ".story-card, .article-item, .news-item",
                "headline": ".story-card__headline a, .headline a, h3 a, h2 a",
                "link": ".story-card__headline a, .headline a, h3 a, h2 a",
                "image": ".story-card__media img, .article-image img, img",
                "summary": ".story-card__summary, .excerpt, .summary"
            },
            "category_map": {
                "/business": "economy",
                "/uae": "regional",
                "/world": "politics", 
                "/sport": "sports",
                "/lifestyle": "lifestyle",
                "/technology": "technology"
            }
        },
        
        "khaleej_times": {
            "url": "https://khaleejtimes.com",
            "name": "Khaleej Times", 
            "priority": 1,
            "selectors": {
                "articles": ".story-card, .news-card, article",
                "headline": ".story-title a, .headline a, h3 a, h2 a",
                "link": ".story-title a, .headline a, h3 a, h2 a",
                "image": ".story-image img, img",
                "summary": ".story-summary, .excerpt"
            },
            "category_map": {
                "/business": "economy",
                "/uae": "regional",
                "/world": "politics",
                "/sport": "sports",
                "/lifestyle": "lifestyle"
            }
        },
        
        "wam_news": {
            "url": "https://wam.ae/en",
            "name": "Emirates News Agency (WAM)",
            "priority": 1,
            "selectors": {
                "articles": ".news-item, .article-card, article",
                "headline": ".news-title a, h3 a, h2 a",
                "link": ".news-title a, h3 a, h2 a",
                "image": ".news-image img, img",
                "summary": ".news-summary, .excerpt"
            },
            "category_map": {
                "/": "politics"  # WAM is primarily official/government news
            }
        },
        
        # Business & Finance (Tier 1)
        "arabian_business": {
            "url": "https://www.arabianbusiness.com",
            "name": "Arabian Business",
            "priority": 1,
            "selectors": {
                "articles": ".article-card, .story-card, article",
                "headline": ".article-title a, .headline a, h3 a",
                "link": ".article-title a, .headline a, h3 a",
                "image": ".article-image img, img",
                "summary": ".article-excerpt, .summary"
            },
            "category_map": {
                "/": "economy",
                "/technology": "technology",
                "/real-estate": "economy",
                "/finance": "economy"
            }
        },
        
        "bloomberg_middle_east": {
            "url": "https://www.bloomberg.com/middleeast",
            "name": "Bloomberg Middle East",
            "priority": 1,
            "selectors": {
                "articles": "article, .story-package-module__story",
                "headline": "h3 a, .headline a",
                "link": "h3 a, .headline a",
                "image": "img",
                "summary": ".summary"
            },
            "category_map": {
                "/": "economy"
            }
        },
        
        "zawya": {
            "url": "https://www.zawya.com",
            "name": "Zawya",
            "priority": 1,
            "selectors": {
                "articles": ".story-card, .news-item, article",
                "headline": ".story-title a, h3 a, h2 a",
                "link": ".story-title a, h3 a, h2 a",
                "image": ".story-image img, img",
                "summary": ".story-summary, .excerpt"
            },
            "category_map": {
                "/": "economy"
            }
        },
        
        # Technology (Tier 1)
        "gulf_business": {
            "url": "https://gulfbusiness.com",
            "name": "Gulf Business",
            "priority": 1,
            "selectors": {
                "articles": ".post, .article-item, article",
                "headline": ".post-title a, h3 a, h2 a",
                "link": ".post-title a, h3 a, h2 a",
                "image": ".post-image img, img",
                "summary": ".post-excerpt, .excerpt"
            },
            "category_map": {
                "/technology": "technology",
                "/": "economy"
            }
        },
        
        # TIER 2: IMPORTANT SOURCES (High Priority)
        
        # General News
        "al_arabiya": {
            "url": "https://english.alarabiya.net",
            "name": "Al Arabiya English",
            "priority": 2,
            "selectors": {
                "articles": ".article-item, .news-card, article",
                "headline": ".article-title a, h2 a, h3 a",
                "link": ".article-title a, h2 a, h3 a", 
                "image": ".article-thumb img, img",
                "summary": ".article-excerpt, .summary"
            },
            "category_map": {
                "/business": "economy",
                "/politics": "politics",
                "/sports": "sports"
            }
        },
        
        "arab_news": {
            "url": "https://www.arabnews.com",
            "name": "Arab News",
            "priority": 2,
            "selectors": {
                "articles": ".article-item, .story-card, article",
                "headline": ".article-title a, h3 a, h2 a",
                "link": ".article-title a, h3 a, h2 a",
                "image": ".article-img img, img",
                "summary": ".article-summary, .excerpt"
            },
            "category_map": {
                "/business": "economy",
                "/saudi-arabia": "regional",
                "/sports": "sports"
            }
        },
        
        "middle_east_eye": {
            "url": "https://www.middleeasteye.net",
            "name": "Middle East Eye",
            "priority": 2,
            "selectors": {
                "articles": ".views-row, article",
                "headline": ".node-title a, h3 a, h2 a",
                "link": ".node-title a, h3 a, h2 a",
                "image": ".field-name-field-image img, img",
                "summary": ".field-name-body, .summary"
            },
            "category_map": {
                "/news": "politics",
                "/opinion": "politics"
            }
        },
        
        # Business & Economy (Tier 2)
        "trade_arabia": {
            "url": "https://www.tradearabia.com",
            "name": "Trade Arabia",
            "priority": 2,
            "selectors": {
                "articles": ".news-item, article",
                "headline": ".news-title a, h3 a, h2 a",
                "link": ".news-title a, h3 a, h2 a",
                "image": ".news-image img, img",
                "summary": ".news-summary, .excerpt"
            },
            "category_map": {
                "/": "economy"
            }
        },
        
        "construction_week": {
            "url": "https://www.constructionweekonline.com",
            "name": "Construction Week",
            "priority": 2,
            "selectors": {
                "articles": ".article-card, .news-item, article",
                "headline": ".article-title a, h3 a, h2 a",
                "link": ".article-title a, h3 a, h2 a",
                "image": ".article-image img, img",
                "summary": ".article-excerpt, .summary"
            },
            "category_map": {
                "/": "economy"
            }
        },
        
        "emirates_247": {
            "url": "https://www.emirates247.com",
            "name": "Emirates 24/7",
            "priority": 2,
            "selectors": {
                "articles": ".story-card, .news-item, article",
                "headline": ".story-title a, h3 a, h2 a",
                "link": ".story-title a, h3 a, h2 a",
                "image": ".story-image img, img",
                "summary": ".story-summary, .excerpt"
            },
            "category_map": {
                "/business": "economy",
                "/lifestyle": "lifestyle",
                "/technology": "technology"
            }
        },
        
        # Technology & Innovation (Tier 2)
        "wamda": {
            "url": "https://www.wamda.com/news",
            "name": "Wamda",
            "priority": 2,
            "selectors": {
                "articles": ".post-item, .article-card, article",
                "headline": ".post-title a, h3 a, h2 a", 
                "link": ".post-title a, h3 a, h2 a",
                "image": ".post-image img, img",
                "summary": ".post-excerpt, .excerpt"
            },
            "category_map": {
                "/": "technology"
            }
        },
        
        "techcrunch_me": {
            "url": "https://techcrunch.com/tag/middle-east/",
            "name": "TechCrunch Middle East",
            "priority": 2,
            "selectors": {
                "articles": ".post-block, article",
                "headline": ".post-block__title a, h2 a, h3 a",
                "link": ".post-block__title a, h2 a, h3 a",
                "image": ".post-block__media img, img",
                "summary": ".post-block__content, .excerpt"
            },
            "category_map": {
                "/": "technology"
            }
        },
        
        # Lifestyle & Entertainment (Tier 2)
        "time_out_dubai": {
            "url": "https://www.timeoutdubai.com/news",
            "name": "Time Out Dubai",
            "priority": 2,
            "selectors": {
                "articles": ".article-card, .news-item, article",
                "headline": ".article-title a, h3 a, h2 a",
                "link": ".article-title a, h3 a, h2 a",
                "image": ".article-image img, img", 
                "summary": ".article-excerpt, .summary"
            },
            "category_map": {
                "/": "lifestyle"
            }
        },
        
        "whats_on_dubai": {
            "url": "https://whatson.ae/news",
            "name": "What's On Dubai",
            "priority": 2,
            "selectors": {
                "articles": ".article-card, .news-item, article",
                "headline": ".article-title a, h3 a, h2 a",
                "link": ".article-title a, h3 a, h2 a",
                "image": ".article-image img, img",
                "summary": ".article-excerpt, .summary"
            },
            "category_map": {
                "/": "lifestyle"
            }
        },
        
        # TIER 3: SUPPLEMENTARY SOURCES (Medium Priority)
        
        # Specialized Business
        "meed": {
            "url": "https://www.meed.com",
            "name": "MEED",
            "priority": 3,
            "selectors": {
                "articles": ".article-card, .news-item, article",
                "headline": ".article-title a, h3 a, h2 a",
                "link": ".article-title a, h3 a, h2 a",
                "image": ".article-image img, img",
                "summary": ".article-excerpt, .summary"
            },
            "category_map": {
                "/": "economy"
            }
        },
        
        # Real Estate
        "property_finder_blog": {
            "url": "https://www.propertyfinder.ae/en/blog",
            "name": "Property Finder Blog",
            "priority": 3,
            "selectors": {
                "articles": ".blog-post, .post-item, article",
                "headline": ".post-title a, h3 a, h2 a",
                "link": ".post-title a, h3 a, h2 a",
                "image": ".post-image img, img",
                "summary": ".post-excerpt, .excerpt"
            },
            "category_map": {
                "/": "economy"
            }
        },
        
        "bayut_blog": {
            "url": "https://www.bayut.com/blog",
            "name": "Bayut Blog",
            "priority": 3,
            "selectors": {
                "articles": ".blog-post, .post-item, article",
                "headline": ".post-title a, h3 a, h2 a",
                "link": ".post-title a, h3 a, h2 a",
                "image": ".post-image img, img",
                "summary": ".post-excerpt, .excerpt"
            },
            "category_map": {
                "/": "economy"
            }
        },
        
        # Sports
        "sport360": {
            "url": "https://sport360.com",
            "name": "Sport360",
            "priority": 3,
            "selectors": {
                "articles": ".article-card, .news-item, article",
                "headline": ".article-title a, h3 a, h2 a",
                "link": ".article-title a, h3 a, h2 a",
                "image": ".article-image img, img",
                "summary": ".article-excerpt, .summary"
            },
            "category_map": {
                "/": "sports"
            }
        },
        
        # Technology & Startups
        "entrepreneur_me": {
            "url": "https://www.entrepreneurmiddleeast.com",
            "name": "Entrepreneur Middle East",
            "priority": 3,
            "selectors": {
                "articles": ".article-card, .post-item, article",
                "headline": ".article-title a, h3 a, h2 a",
                "link": ".article-title a, h3 a, h2 a",
                "image": ".article-image img, img",
                "summary": ".article-excerpt, .summary"
            },
            "category_map": {
                "/": "technology"
            }
        },
        
        "menabytes": {
            "url": "https://www.menabytes.com",
            "name": "MENAbytes",
            "priority": 3,
            "selectors": {
                "articles": ".post, .article-item, article",
                "headline": ".post-title a, h3 a, h2 a",
                "link": ".post-title a, h3 a, h2 a",
                "image": ".post-image img, img",
                "summary": ".post-excerpt, .excerpt"
            },
            "category_map": {
                "/": "technology"
            }
        },
        
        # TIER 4: GOVERNMENT & OFFICIAL SOURCES
        
        "dubai_media_office": {
            "url": "https://www.mediaoffice.ae",
            "name": "Dubai Media Office",
            "priority": 4,
            "selectors": {
                "articles": ".news-item, .press-release, article",
                "headline": ".news-title a, h3 a, h2 a",
                "link": ".news-title a, h3 a, h2 a",
                "image": ".news-image img, img",
                "summary": ".news-summary, .excerpt"
            },
            "category_map": {
                "/": "politics"
            }
        },
        
        "abu_dhabi_media": {
            "url": "https://www.admediaoffice.ae",
            "name": "Abu Dhabi Media Office",
            "priority": 4,
            "selectors": {
                "articles": ".news-item, .press-release, article",
                "headline": ".news-title a, h3 a, h2 a",
                "link": ".news-title a, h3 a, h2 a",
                "image": ".news-image img, img",
                "summary": ".news-summary, .excerpt"
            },
            "category_map": {
                "/": "politics"
            }
        }
    }

class TextProcessor:
    """Text processing utilities for clustering"""
    
    def __init__(self):
        # Common English stop words
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        }
        
        # News-specific stop words
        news_stop_words = {
            'news', 'report', 'reports', 'says', 'said', 'according', 'sources',
            'breaking', 'latest', 'update', 'today', 'yesterday', 'new', 'first',
            'announces', 'announced', 'reuters', 'bloomberg', 'associated', 'press'
        }
        self.stop_words.update(news_stop_words)
        
        # UAE/MENA common words that shouldn't be primary keywords
        regional_stop_words = {
            'uae', 'dubai', 'abu', 'dhabi', 'emirates', 'gulf', 'middle', 'east',
            'mena', 'arab', 'arabic', 'region', 'regional'
        }
        self.stop_words.update(regional_stop_words)
    
    def extract_keywords(self, text: str, min_length: int = 3) -> Set[str]:
        """Extract meaningful keywords from text"""
        if not text:
            return set()
        
        # Clean and normalize text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split into words
        words = text.split()
        
        # Filter keywords
        keywords = set()
        for word in words:
            if (len(word) >= min_length and 
                word not in self.stop_words and
                not word.isdigit() and
                not re.match(r'^[0-9]+$', word)):
                keywords.add(word.strip())
        
        return keywords
    
    def calculate_similarity(self, keywords1: Set[str], keywords2: Set[str]) -> float:
        """Calculate Jaccard similarity between two keyword sets"""
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0

class UAENewsScraper:
    """Main scraper class for UAE news sources"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
        self.session: Optional[aiohttp.ClientSession] = None
        self.scraped_urls: Set[str] = set()
        self.last_request_time = 0
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def respect_rate_limit(self):
        """Ensure we don't overwhelm servers"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < settings.scraper_delay:
            await asyncio.sleep(settings.scraper_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    async def fetch_page(self, url: str, source_name: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page"""
        await self.respect_rate_limit()
        
        try:
            logger.info(f"Fetching {source_name}: {url}")
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return BeautifulSoup(html, 'html.parser')
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common artifacts
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\t+', ' ', text)
        
        return text[:500]  # Limit length
    
    def determine_category(self, url: str, headline: str, source_config: Dict) -> str:
        """Determine article category based on URL and content"""
        category_map = source_config.get("category_map", {})
        
        # Check URL path first
        for path_pattern, category in category_map.items():
            if path_pattern in url.lower():
                return category
        
        # Check headline keywords
        headline_lower = headline.lower()
        
        # Economy/Business keywords
        if any(word in headline_lower for word in [
            'economy', 'business', 'financial', 'market', 'investment', 'bank', 'banking',
            'fund', 'revenue', 'profit', 'economic', 'finance', 'money', 'currency',
            'trade', 'export', 'import', 'gdp', 'inflation', 'stock', 'shares'
        ]):
            return 'economy'
        
        # Technology keywords
        if any(word in headline_lower for word in [
            'technology', 'tech', 'digital', 'ai', 'artificial intelligence', 'startup',
            'innovation', 'app', 'software', 'platform', 'online', 'internet',
            'cyber', 'data', 'cloud', 'blockchain', 'cryptocurrency'
        ]):
            return 'technology'
        
        # Politics keywords
        if any(word in headline_lower for word in [
            'government', 'minister', 'president', 'politics', 'policy', 'law',
            'parliament', 'election', 'vote', 'summit', 'diplomatic', 'visa',
            'regulation', 'legislation', 'cabinet', 'official'
        ]):
            return 'politics'
        
        # Sports keywords
        if any(word in headline_lower for word in [
            'sport', 'football', 'soccer', 'tennis', 'golf', 'cricket', 'racing',
            'championship', 'tournament', 'match', 'game', 'team', 'player',
            'olympic', 'fifa', 'league'
        ]):
            return 'sports'
        
        # Lifestyle keywords
        if any(word in headline_lower for word in [
            'lifestyle', 'culture', 'art', 'music', 'fashion', 'food', 'travel',
            'entertainment', 'celebrity', 'festival', 'event', 'exhibition',
            'restaurant', 'hotel', 'tourism'
        ]):
            return 'lifestyle'
        
        return 'general'
    
    def extract_articles_from_page(self, soup: BeautifulSoup, source_name: str, 
                                  source_config: Dict) -> List[Article]:
        """Extract articles from a parsed page"""
        articles = []
        selectors = source_config["selectors"]
        
        try:
            # Find article containers
            article_elements = soup.select(selectors["articles"])
            logger.info(f"Found {len(article_elements)} article elements for {source_name}")
            
            for element in article_elements[:settings.max_articles_per_source]:
                try:
                    # Extract headline
                    headline_elem = element.select_one(selectors["headline"])
                    if not headline_elem:
                        continue
                    
                    headline = self.clean_text(headline_elem.get_text(strip=True))
                    if not headline or len(headline) < 10:
                        continue
                    
                    # Extract URL
                    link_elem = element.select_one(selectors["link"])
                    if not link_elem:
                        continue
                    
                    url = link_elem.get('href', '')
                    if not url:
                        continue
                    
                    # Make URL absolute
                    if url.startswith('/'):
                        base_url = source_config["url"]
                        url = urljoin(base_url, url)
                    elif not url.startswith('http'):
                        continue
                    
                    # Check if already processed
                    if url in self.scraped_urls:
                        continue
                    
                    # Extract summary
                    summary = ""
                    summary_elem = element.select_one(selectors.get("summary", ""))
                    if summary_elem:
                        summary = self.clean_text(summary_elem.get_text(strip=True))
                    
                    # Extract image
                    image_url = ""
                    image_elem = element.select_one(selectors.get("image", ""))
                    if image_elem:
                        image_url = image_elem.get('src', '') or image_elem.get('data-src', '')
                        if image_url and image_url.startswith('/'):
                            image_url = urljoin(source_config["url"], image_url)
                    
                    # Determine category
                    category = self.determine_category(url, headline, source_config)
                    
                    # Extract keywords
                    text_for_keywords = f"{headline} {summary}"
                    keywords = self.text_processor.extract_keywords(text_for_keywords)
                    
                    # Create article
                    article = Article(
                        headline=headline,
                        url=url,
                        source=source_config["name"],
                        summary=summary,
                        image_url=image_url,
                        category=category,
                        keywords=keywords
                    )
                    
                    articles.append(article)
                    self.scraped_urls.add(url)
                    
                except Exception as e:
                    logger.warning(f"Error extracting article from {source_name}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error extracting articles from {source_name}: {e}")
        
        logger.info(f"Extracted {len(articles)} valid articles from {source_name}")
        return articles
    
    async def find_matching_story(self, article: Article) -> Optional[str]:
        """Find if article belongs to existing story using clustering"""
        try:
            # Get recent stories for clustering
            recent_stories = await db_manager.get_recent_stories(
                hours_back=settings.clustering_hours_back
            )
            
            best_match_id = None
            best_similarity = 0.0
            
            for story in recent_stories:
                story_keywords = set(story.get('keywords', []))
                similarity = self.text_processor.calculate_similarity(
                    article.keywords, story_keywords
                )
                
                if (similarity > best_similarity and 
                    similarity >= settings.similarity_threshold and
                    story.get('category') == article.category):  # Same category
                    best_similarity = similarity
                    best_match_id = story['story_id']
            
            if best_match_id:
                logger.info(f"Found matching story for article: {article.headline[:50]}... (similarity: {best_similarity:.3f})")
            
            return best_match_id
            
        except Exception as e:
            logger.error(f"Error finding matching story: {e}")
            return None
    
    async def process_article(self, article: Article) -> bool:
        """Process article - add to existing story or create new one"""
        try:
            # Check if link already exists
            if await db_manager.link_exists(article.url):
                logger.debug(f"Article already exists: {article.url}")
                return False
            
            # Find matching story
            matching_story_id = await self.find_matching_story(article)
            
            # Prepare article data
            article_data = {
                'timestamp': article.scraped_at.isoformat(),
                'text_content': article.summary or article.headline,
                'source': article.source,
                'link': article.url,
                'title': article.headline,
                'category': article.category,
                'keywords': list(article.keywords)
            }
            
            if matching_story_id:
                # Add to existing story
                article_data['story_id'] = matching_story_id
                article_data['is_primary_article'] = False
                
                article_id = await db_manager.add_article_to_story(article_data, matching_story_id)
                if article_id:
                    logger.info(f"Added to story {matching_story_id}: {article.headline[:50]}...")
                return article_id is not None
            else:
                # Create new story
                article_data['story_id'] = str(uuid.uuid4())
                article_data['is_primary_article'] = True
                
                article_id = await db_manager.create_article(article_data)
                if article_id:
                    logger.info(f"Created new story: {article.headline[:50]}...")
                return article_id is not None
                
        except Exception as e:
            logger.error(f"Error processing article {article.url}: {e}")
            return False
    
    async def scrape_source(self, source_name: str, source_config: Dict) -> int:
        """Scrape a single news source"""
        logger.info(f"Scraping {source_config['name']}...")
        
        soup = await self.fetch_page(source_config["url"], source_config["name"])
        if not soup:
            return 0
        
        articles = self.extract_articles_from_page(soup, source_name, source_config)
        
        processed_count = 0
        for article in articles:
            success = await self.process_article(article)
            if success:
                processed_count += 1
            
            # Small delay between articles
            await asyncio.sleep(0.1)
        
        logger.info(f"Processed {processed_count} new articles from {source_config['name']}")
        return processed_count
    
    async def run_full_scrape(self) -> Dict[str, int]:
        """Run full scrape of all sources"""
        logger.info("Starting UAE news scrape...")
        start_time = time.time()
        
        results = {}
        total_processed = 0
        
        # Sort sources by priority
        sorted_sources = sorted(
            UAENewsSourceConfig.SOURCES.items(),
            key=lambda x: x[1].get('priority', 999)
        )
        
        for source_name, source_config in sorted_sources:
            try:
                count = await self.scrape_source(source_name, source_config)
                results[source_config['name']] = count
                total_processed += count
                
                # Delay between sources
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {e}")
                results[source_config['name']] = 0
        
        elapsed_time = time.time() - start_time
        logger.info(f"Scraping completed in {elapsed_time:.2f}s. Total processed: {total_processed}")
        
        return results

# FastAPI Router
scraper_router = APIRouter()

@scraper_router.post("/run")
async def run_scraper(background_tasks: BackgroundTasks):
    """Trigger manual scraping"""
    try:
        async with UAENewsScraper() as scraper:
            results = await scraper.run_full_scrape()
        
        return {
            "status": "success",
            "message": "Scraping completed",
            "results": results,
            "total_articles": sum(results.values())
        }
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        raise HTTPException(status_code=500, detail=f"Scraper error: {str(e)}")

@scraper_router.get("/status")
async def scraper_status():
    """Get scraper status"""
    return {
        "status": "ready",
        "sources_configured": len(UAENewsSourceConfig.SOURCES),
        "settings": {
            "delay": settings.scraper_delay,
            "timeout": settings.scraper_timeout,
            "max_articles_per_source": settings.max_articles_per_source,
            "similarity_threshold": settings.similarity_threshold
        }
    }

@scraper_router.get("/sources")
async def list_sources():
    """List configured news sources"""
    sources = []
    for source_name, config in UAENewsSourceConfig.SOURCES.items():
        sources.append({
            "name": config["name"],
            "url": config["url"],
            "priority": config.get("priority", 999),
            "categories": list(config.get("category_map", {}).values())
        })
    
    return {"sources": sources}
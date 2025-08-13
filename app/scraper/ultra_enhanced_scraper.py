# app/scraper/ultra_enhanced_scraper.py
"""
Ultra Enhanced UAE Scraper - Bypasses all restrictions including 403s, brotli, and bot detection
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin
import random
import json

# Install missing dependencies first
import subprocess
import sys

def install_missing_packages():
    """Auto-install missing packages"""
    packages = {
        'brotli': 'brotli',
        'cloudscraper': 'cloudscraper',
        'fake_useragent': 'fake-useragent',
        'curl_cffi': 'curl-cffi',
        'httpx': 'httpx[http2]',
        'playwright': 'playwright',
        'undetected_chromedriver': 'undetected-chromedriver'
    }
    
    for module, package in packages.items():
        try:
            __import__(module)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            if package == 'playwright':
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

install_missing_packages()

# Now import everything
import brotli  # This fixes the brotli encoding issue
import cloudscraper
from fake_useragent import UserAgent
from curl_cffi import requests as curl_requests
import httpx
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

@dataclass
class ScrapingResult:
    source_name: str
    url: str
    status: str
    articles_found: int
    articles_posted: int
    error_details: Dict = None
    strategy_used: str = ""
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.error_details is None:
            self.error_details = {}


class UltraEnhancedFetcher:
    """Ultimate fetching with 10+ strategies to bypass any restriction"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.cloudscraper_session = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
        ]
        self.httpx_client = None
    
    async def fetch_with_strategies(self, url: str, source_name: str) -> Tuple[Optional[str], str]:
        """Try multiple fetch strategies in order of effectiveness"""
        
        strategies = [
            ("CloudScraper", self._fetch_cloudscraper),
            ("cURL-Impersonate", self._fetch_curl_impersonate),
            ("HTTPX-HTTP2", self._fetch_httpx_http2),
            ("Playwright-Stealth", self._fetch_playwright_stealth),
            ("AioHTTP-Brotli", self._fetch_aiohttp_brotli),
            ("Requests-Session", self._fetch_requests_session),
            ("MCP-Direct", self._fetch_mcp_direct),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                logger.info(f"🔧 {source_name} - Trying {strategy_name}")
                html = await strategy_func(url)
                
                if html and len(html) > 500:
                    logger.info(f"✅ {source_name} - Success with {strategy_name} ({len(html)} bytes)")
                    return html, strategy_name
                    
            except Exception as e:
                logger.debug(f"⚠️ {source_name} - {strategy_name} failed: {str(e)[:100]}")
                continue
        
        logger.error(f"❌ {source_name} - All strategies failed")
        return None, "all_failed"
    
    async def _fetch_cloudscraper(self, url: str) -> Optional[str]:
        """CloudScraper - Bypasses Cloudflare and most anti-bot systems"""
        response = await asyncio.to_thread(
            self.cloudscraper_session.get,
            url,
            timeout=20,
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }
        )
        if response.status_code == 200:
            return response.text
        raise Exception(f"Status {response.status_code}")
    
    async def _fetch_curl_impersonate(self, url: str) -> Optional[str]:
        """cURL with browser impersonation - Bypasses fingerprint detection"""
        response = await asyncio.to_thread(
            curl_requests.get,
            url,
            impersonate="chrome110",
            timeout=20,
            headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        if response.status_code == 200:
            return response.text
        raise Exception(f"Status {response.status_code}")
    
    async def _fetch_httpx_http2(self, url: str) -> Optional[str]:
        """HTTPX with HTTP/2 support - Better for modern sites"""
        if not self.httpx_client:
            self.httpx_client = httpx.AsyncClient(
                http2=True,
                headers={'User-Agent': random.choice(self.user_agents)},
                timeout=20.0,
                follow_redirects=True
            )
        
        response = await self.httpx_client.get(url)
        if response.status_code == 200:
            return response.text
        raise Exception(f"Status {response.status_code}")
    
    async def _fetch_playwright_stealth(self, url: str) -> Optional[str]:
        """Playwright with maximum stealth - Undetectable browser automation"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-infobars',
                    '--window-position=0,0',
                    '--ignore-certifcate-errors',
                    '--ignore-certifcate-errors-spki-list',
                    '--user-agent=' + random.choice(self.user_agents)
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(self.user_agents),
                ignore_https_errors=True,
                java_script_enabled=True,
                bypass_csp=True,
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            )
            
            # Stealth mode
            await context.add_init_script("""
                // Overwrite the `navigator.webdriver` property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Pass Chrome test
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Mock WebGL
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter(parameter);
                };
            """)
            
            page = await context.new_page()
            
            # Random mouse movement to appear human
            await page.mouse.move(random.randint(0, 100), random.randint(0, 100))
            
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Scroll to trigger lazy loading
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
            await asyncio.sleep(0.5)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight*2/3)")
            await asyncio.sleep(0.5)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
            content = await page.content()
            await browser.close()
            
            return content
    
    async def _fetch_aiohttp_brotli(self, url: str) -> Optional[str]:
        """AioHTTP with brotli support"""
        connector = aiohttp.TCPConnector(ssl=False, force_close=True)
        timeout = aiohttp.ClientTimeout(total=20)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status == 200:
                    return await response.text()
                raise Exception(f"Status {response.status}")
    
    async def _fetch_requests_session(self, url: str) -> Optional[str]:
        """Regular requests with session and cookies"""
        import requests
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        })
        
        # Visit Google first to get cookies
        session.get('https://www.google.com')
        
        response = await asyncio.to_thread(
            session.get,
            url,
            timeout=20,
            verify=False
        )
        
        if response.status_code == 200:
            return response.text
        raise Exception(f"Status {response.status_code}")
    
    async def _fetch_mcp_direct(self, url: str) -> Optional[str]:
        """Direct MCP Playwright extraction"""
        try:
            from app.scraper.mcp_bridge_client import extract_with_mcp_direct
            
            items, diag = await extract_with_mcp_direct(
                page_url=url,
                selectors={},
                wait_for=None,
                max_items=1
            )
            
            if diag.get('html'):
                return diag['html']
                
        except Exception as e:
            logger.debug(f"MCP not available: {e}")
        
        raise Exception("MCP failed")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.httpx_client:
            await self.httpx_client.aclose()


class UltraEnhancedUAEScraper:
    """Ultra Enhanced scraper that bypasses ALL restrictions"""
    
    def __init__(self, existing_scraper):
        self.existing_scraper = existing_scraper
        self.ultra_fetcher = UltraEnhancedFetcher()
        self.text_processor = existing_scraper.text_processor
        self.api_base_url = existing_scraper.api_base_url
        self.scraped_urls = existing_scraper.scraped_urls
    
    async def scrape_source_ultra(self, source_name: str, source_config: Dict, session: aiohttp.ClientSession) -> ScrapingResult:
        """Ultra enhanced source scraping"""
        start_time = time.time()
        logger.info(f"🚀 Starting ULTRA scrape: {source_config['name']}")
        
        result = ScrapingResult(
            source_name=source_config['name'],
            url=source_config['url'],
            status='failed',
            articles_found=0,
            articles_posted=0
        )
        
        try:
            # Use ultra fetcher
            html, strategy_used = await self.ultra_fetcher.fetch_with_strategies(
                source_config["url"],
                source_config["name"]
            )
            
            result.strategy_used = strategy_used
            
            if not html:
                result.status = 'failed'
                result.error_details["no_content"] = "All fetch strategies failed"
                return result
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract articles
            articles, extract_debug = self.existing_scraper.extract_articles_with_debugging(
                soup, source_name, source_config
            )
            
            result.error_details.update(extract_debug)
            result.articles_found = len(articles)
            
            if len(articles) == 0 and strategy_used == "Playwright-Stealth":
                # If Playwright was used but no articles found, try direct extraction
                articles = self._extract_from_playwright_html(html, source_config)
                result.articles_found = len(articles)
            
            # Post articles
            posted_count = 0
            for article in articles:
                success, _ = await self.existing_scraper.post_article_with_retry(article, session)
                if success:
                    posted_count += 1
                await asyncio.sleep(0.5)
            
            result.articles_posted = posted_count
            result.status = 'success' if posted_count > 0 else 'partial'
            result.processing_time = time.time() - start_time
            
            logger.info(f"✅ {source_config['name']} completed with {strategy_used}: {posted_count}/{len(articles)} posted")
            
        except Exception as e:
            result.status = 'failed'
            result.error_details["error"] = str(e)
            result.processing_time = time.time() - start_time
            logger.error(f"💥 {source_config['name']} - Error: {e}")
        
        return result
    
    def _extract_from_playwright_html(self, html: str, source_config: Dict) -> List:
        """Fallback extraction for Playwright-rendered HTML"""
        from app.scraper.enhanced_uae_scraper import Article
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # More aggressive extraction for JS-rendered content
        potential_articles = soup.find_all(['article', 'div', 'section', 'li'])
        
        for elem in potential_articles[:20]:
            try:
                # Find any heading
                heading = elem.find(['h1', 'h2', 'h3', 'h4'])
                if not heading:
                    continue
                
                headline = self.existing_scraper.clean_text(heading.get_text())
                if len(headline) < 10:
                    continue
                
                # Find any link
                link = elem.find('a', href=True)
                if not link:
                    continue
                
                url = urljoin(source_config['url'], link['href'])
                
                if url in self.scraped_urls:
                    continue
                
                # Extract summary
                paragraphs = elem.find_all('p')
                summary = ' '.join([p.get_text(strip=True) for p in paragraphs[:2]])
                summary = self.existing_scraper.clean_text(summary)
                
                article = Article(
                    headline=headline,
                    url=url,
                    source=source_config['name'],
                    summary=summary,
                    category=source_config.get('category', 'general'),
                    keywords=self.text_processor.extract_keywords(f"{headline} {summary}"),
                    image_url=None
                )
                
                articles.append(article)
                self.scraped_urls.add(url)
                
            except Exception:
                continue
        
        return articles
    
    async def run_ultra_scrape(self) -> Dict:
        """Run ultra enhanced scraping"""
        logger.info("🚀🚀 Starting ULTRA ENHANCED UAE news scrape...")
        start_time = time.time()
        
        results = []
        total_found = 0
        total_posted = 0
        
        # Import config
        from app.scraper.enhanced_uae_scraper import EnhancedUAENewsConfig
        
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
                    result = await self.scrape_source_ultra(source_name, source_config, session)
                    results.append(result)
                    total_found += result.articles_found
                    total_posted += result.articles_posted
                    
                    # Adaptive delay
                    await asyncio.sleep(2 if result.status == 'success' else 3)
                    
                except Exception as e:
                    logger.error(f"❌ Critical error scraping {source_name}: {e}")
                    results.append(ScrapingResult(
                        source_name=source_config['name'],
                        url=source_config['url'],
                        status='failed',
                        articles_found=0,
                        articles_posted=0,
                        error_details={"critical_error": str(e)}
                    ))
        
        # Cleanup
        await self.ultra_fetcher.cleanup()
        
        elapsed_time = time.time() - start_time
        
        # Generate summary
        success_count = sum(1 for r in results if r.status == 'success')
        partial_count = sum(1 for r in results if r.status == 'partial')
        failed_count = sum(1 for r in results if r.status == 'failed')
        
        # Strategy analysis
        strategy_stats = {}
        for r in results:
            if r.strategy_used:
                strategy_stats[r.strategy_used] = strategy_stats.get(r.strategy_used, 0) + 1
        
        success_rate = (success_count / len(results)) * 100 if results else 0
        posting_rate = (total_posted / total_found) * 100 if total_found > 0 else 0
        
        logger.info(f"🎉🎉 ULTRA ENHANCED SCRAPING COMPLETED!")
        logger.info(f"⏱️  Total time: {elapsed_time:.2f} seconds")
        logger.info(f"📊 Results: {success_count} success, {partial_count} partial, {failed_count} failed")
        logger.info(f"📈 Success rate: {success_rate:.1f}%")
        logger.info(f"📋 Articles: {total_posted}/{total_found} posted ({posting_rate:.1f}%)")
        logger.info(f"🔧 Strategies used: {strategy_stats}")
        
        return {
            "status": "completed",
            "type": "ultra_enhanced",
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
            "strategy_stats": strategy_stats,
            "detailed_results": [
                {
                    "source": r.source_name,
                    "url": r.url,
                    "status": r.status,
                    "strategy_used": r.strategy_used,
                    "articles_found": r.articles_found,
                    "articles_posted": r.articles_posted,
                    "processing_time": round(r.processing_time, 2),
                    "error_details": r.error_details
                }
                for r in results
            ]
        }


# Auto-apply ultra enhancement
def apply_ultra_enhancement():
    """Apply ultra enhancement to existing scraper"""
    from app.scraper.enhanced_uae_scraper import enhanced_scraper
    
    ultra_scraper = UltraEnhancedUAEScraper(enhanced_scraper)
    
    # Replace the run method
    enhanced_scraper.run_ultra_enhanced_scrape = ultra_scraper.run_ultra_scrape
    
    logger.info("✅✅ Ultra Enhanced scraper applied successfully!")
    return ultra_scraper


# Export for use
ultra_scraper = None
try:
    ultra_scraper = apply_ultra_enhancement()
except Exception as e:
    logger.error(f"Failed to apply ultra enhancement: {e}")
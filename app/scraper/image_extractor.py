# app/scraper/image_extraction_fix.py
"""
Enhanced image extraction that handles lazy loading placeholders
"""

import logging
from typing import Optional, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json

logger = logging.getLogger(__name__)

class EnhancedImageExtractor:
    """
    Handles all types of lazy loading techniques including:
    - SVG placeholders
    - data-src attributes
    - srcset attributes
    - JavaScript-loaded images
    """
    
    @staticmethod
    def extract_image_from_element(element, base_url: str) -> Optional[str]:
        """
        Extract real image URL, skipping SVG placeholders
        """
        def make_absolute(url: str) -> str:
            if not url:
                return ""
            if url.startswith("//"):
                return f"https:{url}"
            if url.startswith("http"):
                return url
            return urljoin(base_url, url)
        
        def is_placeholder(url: str) -> bool:
            """Check if URL is a placeholder"""
            if not url:
                return True
            placeholders = [
                'data:image/svg+xml',
                'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP',
                'placeholder',
                'blank.gif',
                'blank.png',
                'transparent.png',
                '1x1.png',
                'spacer.gif'
            ]
            return any(p in url.lower() for p in placeholders)
        
        # Strategy 1: Look for lazy-loading attributes FIRST
        imgs = element.select('img')
        
        for img in imgs:
            # Check all possible lazy loading attributes in priority order
            lazy_attrs = [
                'data-src',           # Most common
                'data-lazy-src',      # Alternative
                'data-original',      # jQuery lazy load
                'data-srcset',        # Responsive images
                'data-lazy-srcset',   # Lazy responsive
                'data-echo',          # Echo.js
                'data-unveil',        # Unveil.js
                'data-image',         # Generic
                'data-img',           # Generic short
                'data-url',           # Generic URL
                'data-hi-res-src',    # High resolution
                'data-low-src',       # Low quality placeholder
                'data-thumb',         # Thumbnail that might have full URL
            ]
            
            # First, check lazy loading attributes
            for attr in lazy_attrs:
                if img.has_attr(attr):
                    url = img[attr]
                    if url and not is_placeholder(url):
                        # Handle srcset format
                        if ',' in url and ('w' in url or 'x' in url):
                            # Parse srcset and get highest resolution
                            parts = url.split(',')
                            best_url = parts[-1].strip().split(' ')[0]
                            return make_absolute(best_url)
                        return make_absolute(url)
            
            # Strategy 2: Check if src is NOT a placeholder
            if img.has_attr('src'):
                src = img['src']
                if src and not is_placeholder(src):
                    return make_absolute(src)
            
            # Strategy 3: Check srcset (even if src is placeholder)
            if img.has_attr('srcset'):
                srcset = img['srcset']
                if srcset and not is_placeholder(srcset):
                    # Parse srcset and get highest resolution
                    parts = srcset.split(',')
                    best_url = parts[-1].strip().split(' ')[0]
                    if not is_placeholder(best_url):
                        return make_absolute(best_url)
        
        # Strategy 4: Look in picture/source elements
        picture = element.find('picture')
        if picture:
            sources = picture.find_all('source')
            for source in sources:
                if source.has_attr('srcset'):
                    srcset = source['srcset']
                    if srcset and not is_placeholder(srcset):
                        parts = srcset.split(',')
                        best_url = parts[-1].strip().split(' ')[0]
                        return make_absolute(best_url)
                if source.has_attr('data-srcset'):
                    srcset = source['data-srcset']
                    if srcset and not is_placeholder(srcset):
                        parts = srcset.split(',')
                        best_url = parts[-1].strip().split(' ')[0]
                        return make_absolute(best_url)
        
        # Strategy 5: Check background images in style attributes
        for elem in element.select('[style*="background-image"]'):
            style = elem.get('style', '')
            match = re.search(r'url\(["\']?([^"\'()]+)["\']?\)', style)
            if match:
                url = match.group(1)
                if not is_placeholder(url):
                    return make_absolute(url)
        
        # Strategy 6: Check data attributes with full URLs
        for elem in element.select('[data-bg], [data-background-image]'):
            for attr in ['data-bg', 'data-background-image']:
                if elem.has_attr(attr):
                    url = elem[attr]
                    if url and not is_placeholder(url):
                        return make_absolute(url)
        
        return None
    
    @staticmethod
    async def extract_with_javascript_execution(url: str, selectors: dict) -> List[dict]:
        """
        Use Playwright to execute JavaScript and get real images
        """
        try:
            from playwright.async_api import async_playwright
            import asyncio
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Navigate to page
                await page.goto(url, wait_until='networkidle')
                
                # Scroll to trigger lazy loading
                await page.evaluate("""
                    async () => {
                        // Scroll slowly to trigger all lazy loading
                        const distance = 100;
                        const delay = 100;
                        const height = document.body.scrollHeight;
                        
                        for (let i = 0; i < height; i += distance) {
                            window.scrollTo(0, i);
                            await new Promise(r => setTimeout(r, delay));
                        }
                        
                        // Scroll back to top
                        window.scrollTo(0, 0);
                        await new Promise(r => setTimeout(r, 500));
                    }
                """)
                
                # Wait for images to load
                await page.wait_for_timeout(2000)
                
                # Extract articles with real image URLs
                articles = await page.evaluate("""
                    () => {
                        const articles = [];
                        const containers = document.querySelectorAll('article, .article-card, .story-card, .post');
                        
                        containers.forEach(container => {
                            // Get headline
                            const headlineElem = container.querySelector('h1, h2, h3, .title, .headline');
                            const headline = headlineElem ? headlineElem.textContent.trim() : '';
                            
                            // Get link
                            const linkElem = container.querySelector('a[href]');
                            const link = linkElem ? linkElem.href : '';
                            
                            // Get image - now it should be loaded
                            let imageUrl = '';
                            const img = container.querySelector('img');
                            if (img) {
                                // Get computed src (after lazy loading)
                                imageUrl = img.currentSrc || img.src;
                                
                                // Skip if still placeholder
                                if (imageUrl && !imageUrl.includes('data:image/svg')) {
                                    imageUrl = imageUrl;
                                }
                            }
                            
                            if (headline && link) {
                                articles.push({
                                    headline: headline,
                                    link: link,
                                    image_url: imageUrl
                                });
                            }
                        });
                        
                        return articles;
                    }
                """)
                
                await browser.close()
                return articles
                
        except Exception as e:
            logger.error(f"JavaScript execution failed: {e}")
            return []


def apply_image_extraction_fix():
    """
    Apply the image extraction fix to your existing scraper
    """
    from app.scraper.enhanced_uae_scraper import EnhancedUAEScraper
    
    # Replace the image extraction method
    original_method = EnhancedUAEScraper.extract_image_from_element
    
    def fixed_extract_image(self, element, base_url: str) -> Optional[str]:
        """Fixed image extraction that handles lazy loading"""
        # Try enhanced extraction first
        result = EnhancedImageExtractor.extract_image_from_element(element, base_url)
        
        if result and 'data:image/svg' not in result:
            logger.debug(f"✅ Extracted real image: {result[:50]}...")
            return result
        
        # Fallback to original method if needed
        logger.debug("⚠️ No real image found, SVG placeholder detected")
        return None
    
    # Monkey patch the method
    EnhancedUAEScraper.extract_image_from_element = fixed_extract_image
    
    logger.info("✅ Image extraction fix applied!")
    return True


# Special handling for TimeOut and Construction Week
class SpecialSiteHandlers:
    """
    Site-specific handlers for problematic sites
    """
    
    @staticmethod
    async def handle_timeout_dubai(url: str) -> List[dict]:
        """
        Special handler for TimeOut Dubai
        """
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url)
            
            # TimeOut specific: They use lazy loading with data-src
            await page.evaluate("""
                () => {
                    // Force load all images
                    document.querySelectorAll('img[data-src]').forEach(img => {
                        img.src = img.dataset.src;
                    });
                    
                    // Trigger any lazy load libraries
                    if (window.LazyLoad) {
                        window.LazyLoad.update();
                    }
                }
            """)
            
            await page.wait_for_timeout(2000)
            
            articles = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('.article-card, article')).map(el => {
                        const img = el.querySelector('img');
                        return {
                            headline: el.querySelector('h2, h3, .title')?.textContent?.trim() || '',
                            link: el.querySelector('a')?.href || '',
                            image_url: img?.currentSrc || img?.src || img?.dataset?.src || ''
                        };
                    }).filter(a => a.headline && a.link && !a.image_url.includes('data:image/svg'));
                }
            """)
            
            await browser.close()
            return articles
    
    @staticmethod
    async def handle_construction_week(url: str) -> List[dict]:
        """
        Special handler for Construction Week
        """
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until='networkidle')
            
            # Construction Week specific handling
            await page.evaluate("""
                () => {
                    // They use a specific lazy load library
                    document.querySelectorAll('.lazy').forEach(img => {
                        if (img.dataset.original) {
                            img.src = img.dataset.original;
                        }
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                        }
                    });
                    
                    // Scroll to load more
                    window.scrollTo(0, document.body.scrollHeight);
                }
            """)
            
            await page.wait_for_timeout(3000)
            
            articles = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('article, .post, .article-card')).map(el => {
                        // Multiple image selection strategies
                        let imageUrl = '';
                        const img = el.querySelector('img');
                        
                        if (img) {
                            imageUrl = img.currentSrc || 
                                      img.src || 
                                      img.dataset.original || 
                                      img.dataset.src || 
                                      '';
                        }
                        
                        // Filter out SVG placeholders
                        if (imageUrl.includes('data:image/svg')) {
                            imageUrl = '';
                        }
                        
                        return {
                            headline: el.querySelector('h1, h2, h3, .title')?.textContent?.trim() || '',
                            link: el.querySelector('a[href]')?.href || '',
                            image_url: imageUrl
                        };
                    }).filter(a => a.headline && a.link);
                }
            """)
            
            await browser.close()
            return articles


# Auto-apply the fix
try:
    apply_image_extraction_fix()
    logger.info("🖼️ Image extraction fix has been applied!")
except Exception as e:
    logger.error(f"Failed to apply image fix: {e}")
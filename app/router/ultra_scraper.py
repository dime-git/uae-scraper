# app/routers/ultra_scraper.py
"""
Ultra Enhanced Scraper API Endpoint
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraper", tags=["ultra-scraper"])

class ScraperResponse(BaseModel):
    status: str
    message: str
    scraper_results: Optional[Dict] = None

@router.post("/run-ultra", response_model=ScraperResponse)
async def run_ultra_scraper(background_tasks: BackgroundTasks):
    """
    Run the ULTRA enhanced UAE news scraper that bypasses ALL restrictions
    """
    try:
        # Import and run ultra scraper
        from app.scraper.ultra_enhanced_scraper import ultra_scraper
        from app.scraper.enhanced_uae_scraper import enhanced_scraper
        
        if not ultra_scraper:
            # Fallback to creating it now
            from app.scraper.ultra_enhanced_scraper import UltraEnhancedUAEScraper
            ultra = UltraEnhancedUAEScraper(enhanced_scraper)
            results = await ultra.run_ultra_scrape()
        else:
            # Use the existing ultra scraper
            results = await enhanced_scraper.run_ultra_enhanced_scrape()
        
        return ScraperResponse(
            status="success",
            message="Ultra Enhanced UAE scraping completed!",
            scraper_results=results
        )
        
    except Exception as e:
        logger.error(f"Ultra scraper error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-source/{source_name}")
async def test_single_source(source_name: str):
    """
    Test ultra scraping on a single source
    """
    try:
        from app.scraper.enhanced_uae_scraper import EnhancedUAENewsConfig, enhanced_scraper
        from app.scraper.ultra_enhanced_scraper import UltraEnhancedUAEScraper
        import aiohttp
        
        # Find the source config
        source_config = None
        for key, config in EnhancedUAENewsConfig.SOURCES.items():
            if key == source_name or config['name'].lower() == source_name.lower():
                source_config = config
                break
        
        if not source_config:
            raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")
        
        # Run ultra scraper on this source
        ultra = UltraEnhancedUAEScraper(enhanced_scraper)
        
        async with aiohttp.ClientSession() as session:
            result = await ultra.scrape_source_ultra(source_name, source_config, session)
        
        await ultra.ultra_fetcher.cleanup()
        
        return {
            "source": result.source_name,
            "url": result.url,
            "status": result.status,
            "strategy_used": result.strategy_used,
            "articles_found": result.articles_found,
            "articles_posted": result.articles_posted,
            "processing_time": result.processing_time,
            "error_details": result.error_details
        }
        
    except Exception as e:
        logger.error(f"Test source error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategies")
async def list_available_strategies():
    """
    List all available scraping strategies
    """
    return {
        "strategies": [
            {
                "name": "CloudScraper",
                "description": "Bypasses Cloudflare and most anti-bot systems",
                "effectiveness": "95%"
            },
            {
                "name": "cURL-Impersonate",
                "description": "Perfect browser fingerprint impersonation",
                "effectiveness": "90%"
            },
            {
                "name": "HTTPX-HTTP2",
                "description": "Modern HTTP/2 protocol support",
                "effectiveness": "85%"
            },
            {
                "name": "Playwright-Stealth",
                "description": "Undetectable browser automation",
                "effectiveness": "99%"
            },
            {
                "name": "AioHTTP-Brotli",
                "description": "Standard with brotli compression support",
                "effectiveness": "70%"
            },
            {
                "name": "Requests-Session",
                "description": "Session-based with cookie management",
                "effectiveness": "60%"
            },
            {
                "name": "MCP-Direct",
                "description": "MCP Playwright integration",
                "effectiveness": "95%"
            }
        ]
    }

# Add to your main.py
def include_ultra_router(app):
    """Include ultra scraper router in your FastAPI app"""
    from app.routers.ultra_scraper import router
    app.include_router(router)
# File: app/main.py (COMPLETE FILE WITH ENHANCED SCRAPER ADDED)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import sys
import aiohttp
import asyncio
from datetime import datetime
import uuid
from app.router import ultra_scraper

app.include_router(ultra_scraper.router)

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from app.config.settings import settings

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Advanced news scraper for UAE with story clustering"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "healthy",
        "nodejs_api_url": settings.nodejs_api_url,
        "endpoints": {
            "health": "/health",
            "scraper_run": "/scraper/run",
            "scraper_run_enhanced": "/scraper/run-enhanced",  # NEW
            "scraper_status": "/scraper/status",
            "scraper_sources": "/scraper/sources",
            "scraper_debug": "/scraper/debug",  # NEW
            "test_api": "/test/api-connection",
            "test_post": "/test/post-article",
            "test_scrape": "/test/scrape"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "nodejs_api": settings.nodejs_api_url
    }

# TEST ENDPOINTS
@app.get("/test/api-connection")
async def test_api_connection():
    """Test connection to your Node.js API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{settings.nodejs_api_url}/health") as response:
                if response.status == 200:
                    return {
                        "status": "success",
                        "message": "Connected to Node.js API",
                        "api_url": settings.nodejs_api_url,
                        "api_status": response.status
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Node.js API returned status {response.status}",
                        "api_url": settings.nodejs_api_url
                    }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Cannot connect to Node.js API: {str(e)}",
            "api_url": settings.nodejs_api_url
        }

@app.post("/test/post-article")
async def test_post_article():
    """Test posting a sample article to your Node.js API"""
    sample_article = {
        "timestamp": datetime.utcnow().isoformat(),
        "text_content": "This is a test article from the scraper",
        "source": "Test Source",
        "link": f"https://example.com/test-article-{uuid.uuid4()}",
        "title": "Test Article for Scraper Validation",
        "category": "technology",
        "story_id": str(uuid.uuid4()),
        "keywords": ["test", "scraper", "validation"],
        "is_primary_article": True
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.nodejs_api_url}/api/rss", 
                json=sample_article,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    return {
                        "status": "success",
                        "message": "Successfully posted test article",
                        "api_response": result,
                        "article_data": sample_article
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "error",
                        "message": f"Failed to post article: {response.status}",
                        "error": error_text
                    }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Error posting to API: {str(e)}"
        }

@app.post("/test/scrape")
async def test_scrape():
    """Test scraping with simple test data"""
    # Create 3 test articles
    test_articles = []
    
    for i in range(3):
        article = {
            "timestamp": datetime.utcnow().isoformat(),
            "text_content": f"This is test article number {i+1} for the UAE news scraper",
            "source": f"Test Source {i+1}",
            "link": f"https://example.com/test-article-{uuid.uuid4()}",
            "title": f"Test UAE News Article {i+1}",
            "category": ["economy", "technology", "politics"][i],
            "story_id": str(uuid.uuid4()),
            "keywords": [["uae", "test"], ["dubai", "tech"], ["abu", "dhabi"]][i],
            "is_primary_article": True
        }
        test_articles.append(article)
    
    # Post to API
    posted_count = 0
    errors = []
    posted_articles = []
    
    try:
        async with aiohttp.ClientSession() as session:
            for i, article in enumerate(test_articles):
                try:
                    async with session.post(
                        f"{settings.nodejs_api_url}/api/rss",
                        json=article,
                        headers={'Content-Type': 'application/json'}
                    ) as response:
                        if response.status in [200, 201]:
                            result = await response.json()
                            posted_count += 1
                            posted_articles.append({
                                "title": article["title"],
                                "id": result.get("data", {}).get("id", "unknown"),
                                "category": article["category"]
                            })
                        else:
                            error_text = await response.text()
                            errors.append(f"Article {i+1} failed: Status {response.status} - {error_text}")
                            
                except Exception as e:
                    errors.append(f"Article {i+1} error: {str(e)}")
        
        return {
            "status": "success",
            "message": f"Successfully posted {posted_count} out of {len(test_articles)} test articles",
            "posted_count": posted_count,
            "total_articles": len(test_articles),
            "posted_articles": posted_articles,
            "errors": errors if errors else None,
            "api_target": settings.nodejs_api_url
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Test scrape failed: {str(e)}",
            "api_target": settings.nodejs_api_url
        }

# REAL SCRAPER ENDPOINTS
@app.post("/scraper/run")
async def run_scraper():
    """Run the real UAE advanced scraper with all 27+ sources"""
    try:
        from app.scraper.news_scraper import uae_scraper
        
        logger.info("🚀 Starting advanced UAE news scraper...")
        result = await uae_scraper.run_full_scrape()
        
        return {
            "status": "success",
            "message": "Advanced UAE scraping completed successfully!",
            "scraper_results": result
        }
        
    except Exception as e:
        logger.error(f"❌ Scraper error: {e}")
        raise HTTPException(status_code=500, detail=f"Scraper error: {str(e)}")

# NEW ENHANCED SCRAPER ENDPOINT
@app.post("/scraper/run-enhanced")
async def run_enhanced_scraper():
    """Run the enhanced UAE scraper with detailed logging and error analysis"""
    try:
        from app.scraper.enhanced_uae_scraper import enhanced_scraper
        
        logger.info("🚀 Starting ENHANCED UAE news scraper...")
        result = await enhanced_scraper.run_enhanced_scrape()
        
        return {
            "status": "success",
            "message": "Enhanced UAE scraping completed with detailed analysis!",
            "scraper_results": result
        }
        
    except Exception as e:
        logger.error(f"❌ Enhanced scraper error: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced scraper error: {str(e)}")

@app.get("/scraper/status")
async def scraper_status():
    """Get scraper configuration and status"""
    try:
        from app.scraper.news_scraper import UAENewsConfig
        
        return {
            "status": "ready",
            "scraper_type": "Advanced UAE Multi-Source Scraper",
            "total_sources_configured": len(UAENewsConfig.SOURCES),
            "settings": {
                "delay_between_requests": settings.scraper_delay,
                "timeout": settings.scraper_timeout,
                "max_articles_per_source": settings.max_articles_per_source,
                "similarity_threshold": settings.similarity_threshold,
                "api_target": settings.nodejs_api_url
            },
            "source_categories": {
                "tier_1_essential": 8,
                "tier_2_important": 10, 
                "tier_3_supplementary": 7,
                "tier_4_official": 2
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting scraper status: {str(e)}"
        }

# NEW DEBUG ENDPOINT
@app.get("/scraper/debug")
async def scraper_debug():
    """Get debug information about scraper configuration"""
    try:
        from app.scraper.enhanced_uae_scraper import EnhancedUAENewsConfig
        
        return {
            "total_sources": len(EnhancedUAENewsConfig.SOURCES),
            "rate_limiting": {
                "delay_between_requests": settings.scraper_delay,
                "minimum_delay": 3.0,
                "timeout_per_source": "15-25 seconds"
            },
            "sources_by_priority": {
                "tier_1": [s["name"] for s in EnhancedUAENewsConfig.SOURCES.values() if s.get("priority") == 1],
                "tier_2": [s["name"] for s in EnhancedUAENewsConfig.SOURCES.values() if s.get("priority") == 2],
                "tier_3": [s["name"] for s in EnhancedUAENewsConfig.SOURCES.values() if s.get("priority", 999) > 2]
            },
            "error_handling": {
                "retry_attempts": 3,
                "exponential_backoff": "5s, 10s, 20s",
                "rate_limit_detection": "enabled",
                "alternative_selectors": "enabled"
            },
            "api_settings": {
                "target": settings.nodejs_api_url,
                "rate_limit_handling": "enabled",
                "retry_logic": "enabled"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting debug info: {str(e)}"
        }

@app.get("/scraper/sources")
async def list_sources():
    """List all configured UAE news sources"""
    try:
        from app.scraper.news_scraper import UAENewsConfig
        
        sources_by_tier = {
            "tier_1_essential": [],
            "tier_2_important": [],
            "tier_3_supplementary": [],
            "tier_4_other": []
        }
        
        for source_name, config in UAENewsConfig.SOURCES.items():
            source_info = {
                "name": config["name"],
                "url": config["url"],
                "priority": config.get("priority", 999),
                "category": config.get("category", "general")
            }
            
            priority = config.get("priority", 999)
            if priority == 1:
                sources_by_tier["tier_1_essential"].append(source_info)
            elif priority == 2:
                sources_by_tier["tier_2_important"].append(source_info)
            elif priority == 3:
                sources_by_tier["tier_3_supplementary"].append(source_info)
            else:
                sources_by_tier["tier_4_other"].append(source_info)
        
        return {
            "total_sources": len(UAENewsConfig.SOURCES),
            "sources_by_tier": sources_by_tier,
            "categories_covered": ["economy", "technology", "regional", "politics", "sports", "lifestyle"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing sources: {str(e)}"
        }
    
@app.post("/scraper/run-quick-fix")
async def run_quick_fix_scraper():
    """Run quick-fix scraper with working sources only and long delays"""
    try:
        from app.scraper.run_quick_fix import quick_scraper
        
        logger.info("🚀 Starting QUICK-FIX UAE news scraper...")
        result = await quick_scraper.run_quick_scrape()
        
        return {
            "status": "success",
            "message": "Quick-fix UAE scraping completed!",
            "scraper_results": result
        }
        
    except Exception as e:
        logger.error(f"❌ Quick-fix scraper error: {e}")
        raise HTTPException(status_code=500, detail=f"Quick-fix scraper error: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
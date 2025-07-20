from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
# Add this import at the top
import aiohttp


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
            "scraper_status": "/scraper/status"
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

@app.post("/scraper/run")
async def run_scraper():
    """Trigger manual scraping"""
    try:
        # We'll implement the actual scraper next
        return {
            "status": "success",
            "message": "Scraper functionality coming next!",
            "sources_configured": 27
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scraper/status")
async def scraper_status():
    return {
        "status": "ready",
        "sources_configured": 27,
        "api_target": settings.nodejs_api_url
    }

# Add this new endpoint after your existing ones
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
        "timestamp": "2024-01-20T10:30:00Z",
        "text_content": "This is a test article from the scraper",
        "source": "Test Source",
        "link": "https://example.com/test-article",
        "title": "Test Article for Scraper Validation",
        "category": "technology",
        "story_id": "test-story-123",
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
                        "api_response": result
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
    """Test scraping and posting to database"""
    result = await news_scraper.test_scrape_single_source()
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
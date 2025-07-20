from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.config.settings import settings
from app.scraper.news_scraper import scraper_router

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Advanced news scraper for UAE with TIME.mk style story clustering",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include scraper router
app.include_router(
    scraper_router, 
    prefix="/api/v1/scraper",
    tags=["scraper"]
)

@app.get("/")
async def root():
    """Root endpoint - API welcome message"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "healthy",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "scraper_status": "/api/v1/scraper/status",
            "list_sources": "/api/v1/scraper/sources",
            "run_scraper": "/api/v1/scraper/run"
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
        "database": "supabase",
        "sources_configured": 27,
        "features": [
            "Multi-source scraping",
            "Story clustering", 
            "Category classification",
            "TIME.mk style aggregation"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

# ---
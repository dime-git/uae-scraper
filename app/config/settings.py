import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # App Configuration
    app_name = "UAE News Scraper"
    app_version = "1.0.0"
    debug = os.getenv("DEBUG", "true").lower() == "true"
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8000"))
    
    # Database Configuration
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Your Node.js API Configuration
    nodejs_api_url = os.getenv("NODEJS_API_URL", "http://localhost:3000")
    
    # Scraping Configuration
    scraper_delay = float(os.getenv("SCRAPER_DELAY", "2.0"))
    scraper_timeout = int(os.getenv("SCRAPER_TIMEOUT", "30"))
    max_articles_per_source = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "20"))
    
    # Clustering Configuration
    similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.4"))
    clustering_hours_back = int(os.getenv("CLUSTERING_HOURS_BACK", "24"))
    
    # Logging Configuration
    log_level = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
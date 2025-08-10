# UAE News Scraper - Enhanced Edition

## Overview

This project is a comprehensive, production-ready web scraper designed to collect high-quality news articles from major sources across the UAE and Middle East region. Built with Python, it uses advanced asynchronous processing and intelligent content extraction to deliver rich, meaningful news data.

### Key Features

- **🚀 Enhanced Content Extraction**: Extracts actual article content from individual pages, not just headlines
- **🖼️ Smart Image Processing**: Advanced image extraction with lazy loading support for modern websites
- **📊 Rich Data Structure**: Provides headlines, source attribution, categories, text content, and images
- **⚡ Asynchronous Processing**: High-performance concurrent scraping with intelligent rate limiting
- **🛡️ Production-Ready**: Comprehensive error handling, retry logic, and detailed logging
- **🎯 Source Attribution**: Proper source tracking - no more "unknown" sources
- **📱 Modern Website Support**: Handles lazy loading, dynamic content, and various site architectures

## Recent Enhancements (Latest Update)

### 🎯 Fixed Source Attribution

- **Problem**: Articles were showing "unknown" source in the database
- **Solution**: Added proper `source` field transmission to API payload
- **Result**: All articles now show correct source names like "BBC Middle East", "Gulf News", etc.

### 📄 Enhanced Text Content Extraction

- **Problem**: `text_content` was empty or just repeated the headline
- **Solution**: Scraper now visits individual article pages to extract actual lead paragraphs
- **Example**: Instead of "News article: UAE President meets Putin", now extracts: "UAE President His Highness Sheikh Mohamed bin Zayed Al Nahyan met with His Excellency Vladimir Putin, President of the Russian Federation, to discuss enhancing the strategic partnership..."
- **Fallback System**: Smart fallback hierarchy (article content → meta description → headline-based content)

### 🖼️ Advanced Image Processing

- **Problem**: Time Out Dubai and Construction Week showed placeholder SVG images
- **Solution**: Enhanced lazy loading detection and extraction
- **Features**:
  - Detects and skips `data:image/svg+xml` placeholders
  - Extracts from `data-lazy-src`, `data-src`, `data-original` attributes
  - Works on both listing pages and individual article pages
  - Intelligent fallback system for various site architectures

### 🛠️ Technical Improvements

- **Enhanced Error Tracking**: Detailed categorization of network, parsing, and API errors
- **Smart Rate Limiting**: Adaptive delays based on success/failure rates
- **Comprehensive Logging**: Debug-level logging for troubleshooting lazy loading and content extraction
- **Robust Fallbacks**: Multiple extraction strategies ensure high success rates

## Source Coverage

The scraper provides comprehensive coverage across **29** UAE and regional news sources, organized by priority and category:

## Full List of Scraped Sources

### Tier 1: Must-Have (Regional & Business)

- The National
- Gulf News
- Khaleej Times
- WAM News
- Arabian Business
- Bloomberg ME
- Zawya
- Gulf Business
- BBC Middle East
- Reuters Middle East
- CNN Middle East

### Tier 2: Important (Regional & Niche)

- Al Arabiya
- Arab News
- Middle East Eye
- Trade Arabia
- Construction Week
- Emirates 24/7
- Wamda
- TechCrunch ME
- Time Out Dubai
- What's On Dubai

### Tier 3: Supplementary

- MEED
- Property Finder
- Bayut Blog
- Sport360
- Entrepreneur ME

### Tier 4: Official

- Dubai Media Office
- Abu Dhabi Media Office

## Data Structure

### Article Output Format

Each scraped article provides rich, structured data:

```json
{
  "timestamp": "2024-01-08T14:30:00.000Z",
  "title": "UAE, Russian Presidents discuss bilateral strategic partnership in Moscow",
  "text_content": "UAE President His Highness Sheikh Mohamed bin Zayed Al Nahyan met with His Excellency Vladimir Putin, President of the Russian Federation, to discuss enhancing the strategic partnership between the two countries, in addition to regional and international issues of common interest.",
  "source": "Emirates 24/7",
  "category": "regional",
  "link": "https://www.emirates247.com/news/2024/01/08/uae-russia-partnership",
  "image_url": "https://www.emirates247.com/images/articles/uae-russia-meeting.jpg"
}
```

### Key Improvements

- **title**: Clear, extracted headline from listing pages
- **text_content**: Actual article lead paragraph (not just headline repetition)
- **source**: Proper source attribution (no more "unknown")
- **image_url**: Real images (handles lazy loading for modern sites)
- **category**: Organized by topic (regional, economy, technology, lifestyle, official)

## How to Run

### Basic Usage

The main entry point for the scraper is within `app/scraper/enhanced_uae_scraper.py`:

```python
# Example from within an async context
from app.scraper.enhanced_uae_scraper import enhanced_scraper

async def main():
    results = await enhanced_scraper.run_enhanced_scrape()
    print(results)

# To run:
# asyncio.run(main())
```

### FastAPI Integration

Run the web application with endpoints for testing and monitoring:

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints:
# GET /test/scrape - Run enhanced scraper
# GET /test/api-connection - Test API connectivity
# POST /test/post-article - Test article posting
```

### Expected Output

The scraper provides comprehensive reporting:

```json
{
  "status": "completed",
  "summary": {
    "total_sources": 29,
    "successful_sources": 25,
    "total_articles_found": 156,
    "total_articles_posted": 142,
    "success_rate_percent": 86.2,
    "elapsed_time_seconds": 185.4
  },
  "by_category": {
    "regional": { "found": 45, "posted": 41 },
    "economy": { "found": 38, "posted": 35 },
    "technology": { "found": 23, "posted": 22 }
  },
  "error_analysis": {
    "network_errors": 2,
    "parsing_errors": 1,
    "api_errors": 0,
    "rate_limit_hits": 0
  },
  "recommendations": ["✅ Scraping performance looks good!"]
}
```

## Configuration

### Environment Settings

Key configuration options can be adjusted in `app/config/settings.py`:

- **Rate Limiting**: `scraper_delay` - Minimum delay between requests (default: 3 seconds)
- **Article Limits**: `max_articles_per_source` - Maximum articles per source per run
- **API Integration**: `nodejs_api_url` - Your Node.js API endpoint
- **Timeouts**: Individual source timeout settings for reliability

### Troubleshooting

#### Common Issues

**1. "Unknown" Sources**

- ✅ **Fixed**: Recent update ensures proper source attribution
- **Verification**: Check that articles show correct source names in your database

**2. Empty Text Content**

- ✅ **Fixed**: Enhanced content extraction from article pages
- **Verification**: Articles should now have meaningful lead paragraphs

**3. Missing Images (Time Out Dubai/Construction Week)**

- ✅ **Fixed**: Advanced lazy loading detection
- **Verification**: These sources should now show proper images instead of SVG placeholders

**4. Rate Limiting**

- **Solution**: The scraper automatically handles this with exponential backoff
- **Monitor**: Check logs for rate limit warnings and adjust delays if needed

#### Debug Mode

Enable debug logging to troubleshoot specific sources:

```python
import logging
logging.getLogger('app.scraper.enhanced_uae_scraper').setLevel(logging.DEBUG)
```

## Performance Metrics

### Typical Performance

- **Sources**: 29 total sources across 4 priority tiers
- **Articles**: 100-200 articles per run (varies by news volume)
- **Success Rate**: 85-95% typical success rate
- **Runtime**: 3-5 minutes for full scrape
- **API Posts**: Smart retry logic ensures high posting success

### Monitoring

The scraper provides detailed metrics for:

- Source-by-source success/failure rates
- Category-wise article distribution
- Error analysis and recommendations
- Performance timing and bottlenecks

---

**Enhanced UAE News Scraper** - Production-ready, intelligent news aggregation with rich content extraction and modern website support.

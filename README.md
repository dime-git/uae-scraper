# MENA News Scraper

## Overview

This project is a Python-based web scraper designed to collect news articles from various sources across the Middle East, with a primary focus on the UAE. It uses `aiohttp` for asynchronous HTTP requests and `BeautifulSoup` for parsing HTML content.

The scraper is built to be resilient, featuring:

- Detailed logging for each step of the process.
- Error handling with retry logic for network requests.
- Rate limiting to respect server policies.
- A comprehensive reporting summary after each run.

## What's Been Done

The scraper's source list has been significantly expanded to provide comprehensive coverage of UAE news across different sectors. We have completed the following:

1.  **Analyzed Existing Sources:** Reviewed the initial list of news sources to identify gaps.
2.  **Added 17 New Sources:** Integrated 17 new UAE-focused news sources, covering business, technology, lifestyle, real estate, and official government news.
3.  **Preserved International Sources:** Kept existing international sources like BBC, Reuters, and CNN for broader regional context.
4.  **Structured by Priority:** Organized all sources into a tiered system (Priority 1-4) to ensure the most critical news is scraped first.

The scraper now covers a total of **29** unique sources.

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

## How to Run

The main entry point for the scraper is within `app/scraper/enhanced_uae_scraper.py`. You can initiate a scrape by calling the `run_enhanced_scrape` method on the `enhanced_scraper` instance.

```python
# Example from within an async context
from app.scraper.enhanced_uae_scraper import enhanced_scraper

async def main():
    results = await enhanced_scraper.run_enhanced_scrape()
    print(results)

# To run:
# asyncio.run(main())
```

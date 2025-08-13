import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


async def extract_with_mcp_direct(
    page_url: str,
    selectors: Dict,
    wait_for: str | None = None,
    max_items: int = 20,
) -> Tuple[List[Dict], Dict]:
    """
    Use MCP Playwright tools directly to extract articles from a page.
    
    This handles lazy loading, JavaScript rendering, and SVG placeholder issues.
    
    Returns: (items, diag)
    """
    try:
        # Import MCP tools - these should be available in your MCP environment
        from mcp_playwright import playwright_navigate, playwright_evaluate
        
        logger.info(f"🧭 MCP: Navigating to {page_url}")
        
        # Navigate to the page
        nav_result = await playwright_navigate(
            url=page_url,
            browserType="chromium",
            width=1366,
            height=900,
            timeout=45000,
            waitUntil="domcontentloaded",
            headless=True
        )
        
        logger.info(f"🧭 MCP: Navigation result: {nav_result}")
        
        # Build extraction script
        extraction_script = f"""
        (() => {{
            const start = Date.now();
            const maxItems = {max_items};
            
            // Enhanced selectors for article containers
            const articleSelectors = [
                '{selectors.get("articles", "")}',
                'article',
                '[class*="card" i]',
                '[class*="Card" i]',
                '[class*="story" i]',
                '[class*="post" i]',
                '.news-item',
                '.article-item'
            ].filter(s => s);
            
            // Helper functions
            const getText = (el, sel) => {{
                if (!el) return '';
                const found = sel ? el.querySelector(sel) : el;
                return found ? found.textContent.trim().replace(/\\s+/g, ' ').slice(0, 200) : '';
            }};
            
            const getLink = (el) => {{
                const a = el.querySelector('a[href]');
                return a ? a.href : '';
            }};
            
            const getImage = (el) => {{
                const imgs = el.querySelectorAll('img');
                for (const img of imgs) {{
                    // Skip SVG placeholders (TimeOut, Construction Week issue)
                    const src = img.src || '';
                    if (src && !src.includes('data:image/svg+xml') && !src.includes('placeholder')) {{
                        return src;
                    }}
                    
                    // Check lazy loading attributes
                    for (const attr of ['data-src', 'data-lazy-src', 'data-original']) {{
                        const val = img.getAttribute(attr);
                        if (val && !val.includes('data:image/svg+xml')) {{
                            return val;
                        }}
                    }}
                }}
                return null;
            }};
            
            // Find containers using progressive selector testing
            let containers = [];
            let usedSelector = '';
            
            for (const selector of articleSelectors) {{
                try {{
                    const found = Array.from(document.querySelectorAll(selector));
                    if (found.length > 0) {{
                        containers = found;
                        usedSelector = selector;
                        break;
                    }}
                }} catch (e) {{
                    // Skip invalid selectors
                }}
            }}
            
            // Wait for lazy loading (scroll to trigger)
            window.scrollBy(0, 1000);
            
            // Extract items
            const items = containers.slice(0, maxItems).map(el => {{
                try {{
                    const headline = getText(el, 'h1, h2, h3, [class*="title" i], [class*="headline" i], a');
                    const link = getLink(el);
                    const summary = getText(el, 'p, [class*="summary" i], [class*="excerpt" i]');
                    const image_url = getImage(el);
                    
                    if (!headline || !link || headline.length < 10) {{
                        return null;
                    }}
                    
                    return {{
                        headline: headline,
                        link: link,
                        summary: summary,
                        image_url: image_url
                    }};
                }} catch (e) {{
                    return null;
                }}
            }}).filter(item => item !== null);
            
            const elapsed = Date.now() - start;
            
            return {{
                items: items,
                diag: {{
                    url: location.href,
                    found_containers: containers.length,
                    used_selector: usedSelector,
                    extracted_items: items.length,
                    elapsed_ms: elapsed
                }}
            }};
        }})()
        """
        
        logger.info(f"🧭 MCP: Executing extraction script")
        
        # Execute extraction
        result = await playwright_evaluate(script=extraction_script)
        
        if not result or 'items' not in result:
            return [], {"error": "mcp_no_result", "details": "No result from MCP evaluation"}
        
        items = result.get('items', [])
        diag = result.get('diag', {})
        
        logger.info(f"🧭 MCP: Extracted {len(items)} items in {diag.get('elapsed_ms', 0)}ms")
        
        return items, diag
        
    except ImportError:
        logger.error("🧭 MCP tools not available - install mcp_playwright package")
        return [], {"error": "mcp_import_error", "details": "MCP playwright tools not available"}
    
    except Exception as e:
        logger.error(f"🧭 MCP extraction error: {e}")
        return [], {"error": "mcp_exception", "details": str(e)}



import os
import aiohttp
from typing import Dict, List, Tuple


async def extract_with_mcp_via_http(
    page_url: str,
    selectors: Dict,
    wait_for: str | None = None,
    max_items: int = 20,
) -> Tuple[List[Dict], Dict]:
    """
    Call an HTTP bridge that talks to Playwright MCP and returns extracted items.

    Environment:
      - MCP_BRIDGE_URL: base URL of the bridge (e.g., http://localhost:8787)

    Returns: (items, diag)
    """
    bridge_url = os.getenv("MCP_BRIDGE_URL")
    if not bridge_url:
        return [], {"error": "bridge_url_missing", "hint": "Set MCP_BRIDGE_URL (e.g., http://localhost:8787)"}

    payload = {
        "url": page_url,
        "selectors": selectors or {},
        "waitFor": wait_for,
        "maxItems": max_items,
        "fetchArticleImage": True,
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.post(f"{bridge_url}/extract", json=payload) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    return [], {"error": f"bridge_http_{resp.status}", "details": text}
                data = await resp.json()
                return data.get("items", []), data.get("diag", {})
    except Exception as e:
        return [], {"error": "bridge_exception", "details": str(e)}



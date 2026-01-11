import logging
import asyncio
from typing import List, Dict, Any
from tavily import TavilyClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class WebSearchService:
    """
    Service enabling the Agent to perform Web Searches 
    to supplement missing local knowledge.
    """
    def __init__(self):
        secret_key_obj = settings.TAVILY_API_KEY
        tavily_api_key = secret_key_obj.get_secret_value()
        self.client = TavilyClient(api_key=tavily_api_key)

    async def search(self, query: str, search_depth: str = "basic") -> List[Dict[str, Any]]:
        """
        Executes a web search.
        Uses asyncio.to_thread to prevent blocking the event loop during I/O operations.
        """
        if not self.client:
            logger.error(" Web Search requested but client is not initialized.")
            return []

        try:
            logger.info(f" Searching the web for: {query[:50]}...")
            
            # sync => separate thread
            response = await asyncio.to_thread(
                self.client.search,
                query=query,
                search_depth=search_depth,
                max_results=settings.MAX_WEB_RESULTS if hasattr(settings, 'MAX_WEB_RESULTS') else 3,
                include_answer=True
            )
            
            results = []
            for res in response.get("results", []):
                content = (res.get("content") or res.get("snippet"))
                results.append({
                    "title": res.get("title"),
                    "url": res.get("url"),
                    "content": content
                })
            
            return results

        except Exception as e:
            logger.error(f" WebSearch API Error: {e}")
            return []

# Singleton
web_search_service = WebSearchService()
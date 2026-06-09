"""Tavily web search service for fallback"""
from typing import List, Dict, Optional
import httpx
from config import config
from utils import logger, TavilyError


async def search_tavily(
    query: str,
    max_results: int = None
) -> Optional[List[Dict]]:
    """
    Search web using Tavily API
    
    Args:
        query: Search query
        max_results: Maximum number of results (uses config default if None)
    
    Returns:
        List of search results or None if search fails
    """
    if max_results is None:
        max_results = config.TAVILY_MAX_RESULTS
    
    if not config.TAVILY_API_KEY:
        logger.warning("Tavily API key not configured, skipping web search")
        return None
    
    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": config.TAVILY_API_KEY,
                "query": query,
                "max_results": max_results,
                "include_answer": True
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            logger.info(f"Tavily search found {len(results)} results")
            return results
        else:
            logger.error(f"Tavily API error: {response.status_code}")
            return None
            
    except httpx.TimeoutException:
        logger.warning("Tavily search timed out")
        return None
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return None


async def should_search_tavily(confluence_confidence: str) -> bool:
    """
    Determine if we should search Tavily based on Confluence confidence
    
    Args:
        confluence_confidence: Confidence level from Confluence search
    
    Returns:
        True if we should search Tavily
    """
    # Only search Tavily if Confluence didn't return good results
    return confluence_confidence in ["medium", "low"]

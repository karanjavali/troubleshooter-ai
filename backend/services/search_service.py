"""BM25 search service via Supabase"""
from typing import List, Dict
from supabase import create_client, Client
from config import config
from utils import logger, SearchError


# Initialize Supabase client
supabase_client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


async def search_confluence_bm25(
    search_query: str, 
    limit: int = None
) -> tuple[List[Dict], str]:
    """
    Search Confluence using BM25 (PostgreSQL full-text search)
    
    Args:
        search_query: Search query string
        limit: Number of results to return (uses config default if None)
    
    Returns:
        Tuple of (results, confidence_level)
    """
    if limit is None:
        limit = config.BM25_RESULTS_LIMIT
    
    try:
        # Call BM25 search RPC function in Supabase
        response = supabase_client.rpc(
            "search_confluence_bm25",
            {
                "search_query": search_query,
                "limit": limit
            }
        ).execute()
        
        results = response.data if response.data else []
        
        # Calculate confidence based on results
        if len(results) > 0 and results[0].get("rank", 0) > 0.5:
            confidence = "high"
        elif len(results) > 0:
            confidence = "medium"
        else:
            confidence = "low"
        
        logger.info(f"Search returned {len(results)} results with {confidence} confidence")
        return results, confidence
        
    except Exception as e:
        error_msg = f"BM25 search failed: {e}"
        logger.error(error_msg)
        raise SearchError(error_msg)


async def index_chunk(
    page_id: str,
    title: str,
    space_key: str,
    chunk_index: int,
    chunk_text: str,
    url: str
) -> None:
    """
    Index a document chunk in Supabase
    
    Args:
        page_id: Confluence page ID
        title: Page title
        space_key: Confluence space key
        chunk_index: Index of this chunk
        chunk_text: Text content of chunk
        url: URL to the page
    """
    try:
        supabase_client.table("confluence_chunks").upsert({
            "page_id": page_id,
            "title": title,
            "space_key": space_key,
            "chunk_index": chunk_index,
            "chunk_text": chunk_text,
            "url": url,
            "team": space_key.lower()
        }).execute()
        
        logger.debug(f"Indexed chunk {chunk_index} for page {page_id}")
        
    except Exception as e:
        error_msg = f"Failed to index chunk: {e}"
        logger.error(error_msg)
        raise SearchError(error_msg)

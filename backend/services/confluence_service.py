"""Confluence integration service"""
from typing import List
from langchain_community.document_loaders import ConfluenceLoader
from config import config
from utils import logger, ConfluenceError
from models import ConfluencePage


async def fetch_confluence_pages(space_key: str) -> List[ConfluencePage]:
    """
    Fetch all pages from a Confluence space using LangChain ConfluenceLoader
    
    Args:
        space_key: Confluence space key (e.g., "PAYMENT", "AUTH")
    
    Returns:
        List of ConfluencePage objects
    """
    pages = []
    
    try:
        # Initialize ConfluenceLoader with environment variables
        loader = ConfluenceLoader(
            url=config.CONFLUENCE_BASE_URL,
            username=config.CONFLUENCE_EMAIL,
            api_key=config.CONFLUENCE_API_TOKEN,
            space_key=space_key
        )
        
        # Load documents (handles pagination automatically)
        documents = loader.load()
        
        # Convert LangChain documents to our format
        for doc in documents:
            page = ConfluencePage(
                id=doc.metadata.get("id", doc.metadata.get("page_id", "")),
                title=doc.metadata.get("title", "Untitled"),
                content=doc.page_content,
                url=doc.metadata.get("source", ""),
                updated=doc.metadata.get("updated_at", "")
            )
            pages.append(page)
        
        logger.info(f"Fetched {len(pages)} pages from space {space_key}")
        
    except Exception as e:
        error_msg = f"Failed to fetch Confluence pages from {space_key}: {e}"
        logger.error(error_msg)
        raise ConfluenceError(error_msg)
    
    return pages


async def sync_all_spaces() -> tuple[int, List[str]]:
    """
    Sync all configured Confluence spaces
    
    Returns:
        Tuple of (docs_added, errors)
    """
    total_docs = 0
    errors = []
    
    for space_key in config.CONFLUENCE_SPACES:
        try:
            pages = await fetch_confluence_pages(space_key)
            total_docs += len(pages)
            logger.info(f"Synced {len(pages)} pages from {space_key}")
        except ConfluenceError as e:
            error_msg = str(e)
            logger.error(error_msg)
            errors.append(error_msg)
    
    return total_docs, errors

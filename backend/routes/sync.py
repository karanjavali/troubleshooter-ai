"""Confluence synchronization API endpoints"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from models import SyncResponse
from services import sync_all_spaces, chunk_page, index_chunk, fetch_confluence_pages
from config import config
from utils import logger

router = APIRouter(prefix="/api", tags=["sync"])


@router.post("/sync-confluence", response_model=SyncResponse)
async def sync_confluence() -> SyncResponse:
    """
    Sync Confluence documentation to Supabase
    
    This endpoint:
    1. Fetches pages from all configured Confluence spaces
    2. Chunks each page (1000 chars, 100 char overlap)
    3. Indexes chunks in Supabase with BM25 full-text search
    
    Returns:
        SyncResponse with number of docs added and any errors
    """
    
    docs_added = 0
    errors = []
    
    try:
        logger.info(f"Starting Confluence sync for spaces: {config.CONFLUENCE_SPACES}")
        
        # Sync all configured spaces
        for space_key in config.CONFLUENCE_SPACES:
            if not space_key.strip():
                continue
            
            try:
                logger.info(f"Syncing space: {space_key}")
                
                # Fetch pages from Confluence
                pages = await fetch_confluence_pages(space_key)
                
                if not pages:
                    logger.warning(f"No pages found in space {space_key}")
                    continue
                
                # Process and index each page
                for page in pages:
                    try:
                        # Chunk the page
                        chunks = chunk_page(page.content)
                        
                        # Index each chunk
                        for chunk_idx, chunk_text in enumerate(chunks):
                            await index_chunk(
                                page_id=page.id,
                                title=page.title,
                                space_key=space_key,
                                chunk_index=chunk_idx,
                                chunk_text=chunk_text,
                                url=page.url
                            )
                        
                        docs_added += 1
                        logger.info(f"Indexed page: {page.title}")
                        
                    except Exception as e:
                        error_msg = f"Error indexing page {page.title}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
            except Exception as e:
                error_msg = f"Error syncing space {space_key}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        message = f"Synced {docs_added} documents successfully"
        if errors:
            message += f" with {len(errors)} errors"
        
        logger.info(message)
        
        return SyncResponse(
            message=message,
            docs_added=docs_added,
            docs_updated=0,
            errors=errors if errors else None
        )
        
    except Exception as e:
        logger.error(f"Sync endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

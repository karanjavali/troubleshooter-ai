"""Document chunking service"""
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import config
from utils import logger


def chunk_page(content: str, chunk_size: int = None, overlap: int = None) -> List[str]:
    """
    Split document content into chunks
    
    Args:
        content: Document content to chunk
        chunk_size: Size of each chunk (uses config default if None)
        overlap: Overlap between chunks (uses config default if None)
    
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE
    if overlap is None:
        overlap = config.CHUNK_OVERLAP
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    
    try:
        chunks = splitter.split_text(content)
        logger.info(f"Chunked content into {len(chunks)} chunks")
        return chunks if chunks else [content]
    except Exception as e:
        logger.error(f"Error chunking content: {e}")
        return [content]  # Return full content on error

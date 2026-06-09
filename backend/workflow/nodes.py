"""Langgraph workflow node functions"""
import re
from typing import List
from utils import logger
from services import (
    search_confluence_bm25,
    analyze_error_with_context,
    search_tavily,
    should_search_tavily
)
from workflow.state import TroubleshootState


async def parse_error_node(state: TroubleshootState) -> TroubleshootState:
    """
    Parse and extract keywords from error message
    
    Extracts:
    - Error codes (e.g., 500, 401, InvalidAccountId)
    - Service names (e.g., PaymentService, AuthService)
    - Keywords from error message
    """
    error = state["error_input"]
    
    # Extract error code/type
    error_codes = re.findall(
        r'\b(4\d{2}|5\d{2}|\w+Exception|\w+Error)\b',
        error
    )
    
    # Extract service names
    services = re.findall(
        r'\b(Payment|Auth|Account|Transaction|API|Service)\b',
        error,
        re.IGNORECASE
    )
    
    state["parsed_error"] = {
        "error_codes": list(set(error_codes)),
        "services": list(set(services)),
        "keywords": error.split()[:20],
        "full_error": error
    }
    
    logger.info(f"Parsed error: {state['parsed_error']}")
    return state


async def search_confluence_node(state: TroubleshootState) -> TroubleshootState:
    """
    Search Confluence using BM25 full-text search
    
    Builds query from parsed error and searches Supabase
    """
    parsed = state["parsed_error"]
    
    # Build search query
    search_terms = []
    search_terms.extend(parsed["error_codes"])
    search_terms.extend(parsed["services"])
    search_terms.extend(parsed["keywords"][:10])
    
    search_query = " & ".join(search_terms[:8])
    
    try:
        results, confidence = await search_confluence_bm25(search_query)
        state["confluence_results"] = results
        state["confluence_confidence"] = confidence
        logger.info(f"Found {len(results)} Confluence docs with confidence: {confidence}")
    except Exception as e:
        logger.error(f"Confluence search failed: {e}")
        state["confluence_results"] = []
        state["confluence_confidence"] = "low"
    
    return state


async def search_tavily_node(state: TroubleshootState) -> TroubleshootState:
    """
    Fallback to Tavily web search if Confluence is low confidence
    
    Only searches if Confluence didn't return good results
    """
    # Check if we should search Tavily
    if not await should_search_tavily(state["confluence_confidence"]):
        state["tavily_results"] = None
        return state
    
    # Build search query
    parsed = state["parsed_error"]
    search_query = f"{' '.join(parsed['error_codes'])} {' '.join(parsed['services'][:2])}"
    
    results = await search_tavily(search_query)
    state["tavily_results"] = results
    
    if results:
        logger.info(f"Tavily search found {len(results)} results")
    else:
        logger.info("Tavily search returned no results")
    
    return state


async def generate_response_node(state: TroubleshootState) -> TroubleshootState:
    """
    Use Claude to generate structured response with retrieved context
    
    Combines Confluence docs, Tavily results, and error analysis
    """
    try:
        response = await analyze_error_with_context(
            error=state["error_input"],
            confluence_docs=state["confluence_results"],
            tavily_results=state["tavily_results"]
        )
        state["llm_response"] = response
        logger.info("Generated response successfully")
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        # Return error response
        from models import TroubleshootResponse
        state["llm_response"] = TroubleshootResponse(
            error_explanation="Failed to analyze error",
            root_cause=None,
            confidence="low",
            resolution_steps=["Check Confluence manually", "Contact your team"],
            fallback_note=str(e)
        )
    
    return state

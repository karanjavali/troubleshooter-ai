"""Error troubleshooting API endpoints"""
from fastapi import APIRouter, HTTPException
from workflow.graph import graph
from models import TroubleshootRequest, TroubleshootResponse
from utils import logger

router = APIRouter(prefix="/api", tags=["troubleshoot"])


@router.post("/troubleshoot", response_model=TroubleshootResponse)
async def troubleshoot(request: TroubleshootRequest) -> TroubleshootResponse:
    """
    Analyze an error message and provide troubleshooting guidance
    
    The workflow:
    1. Parse error to extract keywords, error codes, services
    2. Search Confluence with BM25
    3. Fallback to Tavily web search if confidence is low
    4. Use Claude to analyze and generate recommendations
    
    Args:
        request: Contains the error message/logs to analyze
    
    Returns:
        Structured troubleshooting response with explanation, steps, and links
    """
    
    try:
        logger.info(f"Troubleshooting error: {request.error[:100]}...")
        
        # Initialize workflow state
        initial_state = {
            "error_input": request.error,
            "parsed_error": {},
            "confluence_results": [],
            "confluence_confidence": "low",
            "tavily_results": None,
            "llm_response": None
        }
        
        # Run Langgraph workflow
        final_state = graph.invoke(initial_state)
        
        response = final_state["llm_response"]
        logger.info(f"Response generated with confidence: {response.confidence}")
        
        return response
        
    except Exception as e:
        logger.error(f"Troubleshoot endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

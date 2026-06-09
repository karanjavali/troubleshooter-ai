"""Pydantic models for API requests and responses"""
from pydantic import BaseModel, Field
from typing import Optional, List
from typing_extensions import TypedDict

# ============ API REQUEST/RESPONSE MODELS ============

class TroubleshootRequest(BaseModel):
    """Request model for error analysis"""
    error: str = Field(..., description="Error message, stack trace, or logs to analyze")


class ConfluenceReference(BaseModel):
    """Reference to a Confluence document"""
    title: str
    url: str
    reason: Optional[str] = None


class TroubleshootResponse(BaseModel):
    """Response model for error analysis"""
    error_explanation: str
    root_cause: Optional[str] = None
    confidence: str  # "high", "medium", "low"
    resolution_steps: List[str]
    related_confluence: List[ConfluenceReference] = []
    fallback_note: Optional[str] = None
    tavily_results: Optional[List[dict]] = None


class SyncResponse(BaseModel):
    """Response model for Confluence sync"""
    message: str
    docs_added: int
    docs_updated: int
    errors: Optional[List[str]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str


# ============ LANGGRAPH STATE MODELS ============

class TroubleshootState(TypedDict):
    """State for Langgraph troubleshoot workflow"""
    error_input: str
    parsed_error: dict
    confluence_results: List[dict]
    confluence_confidence: str
    tavily_results: Optional[List[dict]]
    llm_response: Optional[TroubleshootResponse]


# ============ INTERNAL DATA MODELS ============

class ConfluencePage(BaseModel):
    """Internal model for Confluence page data"""
    id: str
    title: str
    content: str
    url: str
    updated: str


class ParsedError(BaseModel):
    """Parsed error information"""
    error_codes: List[str]
    services: List[str]
    keywords: List[str]
    full_error: str

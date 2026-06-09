"""Langgraph workflow state definitions"""
from typing_extensions import TypedDict
from typing import List, Dict, Optional
from models import TroubleshootResponse


class TroubleshootState(TypedDict):
    """State for troubleshoot workflow"""
    # Input
    error_input: str
    
    # Processing
    parsed_error: Dict
    confluence_results: List[Dict]
    confluence_confidence: str
    tavily_results: Optional[List[Dict]]
    
    # Output
    llm_response: Optional[TroubleshootResponse]

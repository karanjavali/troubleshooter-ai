from pydantic import BaseModel
from typing import Optional, List

class TroubleshootResponse(BaseModel):
    error_explanation: str
    root_cause: Optional[str] = None
    confidence: str
    resolution_steps: List[str]
    related_confluence: List[dict] = []
    fallback_note: Optional[str] = None
    tavily_results: Optional[List[dict]] = None

class SyncResponse(BaseModel):
    message: str
    docs_added: int
    docs_updated: int
    errors: Optional[List[str]] = None

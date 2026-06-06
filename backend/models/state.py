from typing import List, Optional
from typing_extensions import TypedDict

class TroubleshootState(TypedDict):
    error_input: str
    parsed_error: dict
    confluence_results: List[dict]
    confluence_confidence: str
    tavily_results: Optional[List[dict]]
    llm_response: dict

"""Custom exceptions"""

class APIError(Exception):
    """Base exception for API errors"""
    pass


class ConfluenceError(APIError):
    """Confluence integration error"""
    pass


class SearchError(APIError):
    """Search/retrieval error"""
    pass


class LLMError(APIError):
    """LLM service error"""
    pass


class TavilyError(APIError):
    """Tavily search error"""
    pass

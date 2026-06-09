"""LLM service for Claude API integration"""
import json
import re
from typing import Dict, Any
import anthropic
from config import config
from utils import logger, LLMError
from models import TroubleshootResponse


# Initialize Claude client
claude_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


async def analyze_error_with_context(
    error: str,
    confluence_docs: list,
    tavily_results: list = None
) -> TroubleshootResponse:
    """
    Use Claude to analyze error with retrieved context
    
    Args:
        error: Original error message
        confluence_docs: Retrieved Confluence documents
        tavily_results: Web search results from Tavily (optional)
    
    Returns:
        Structured troubleshooting response
    """
    
    # Build context for Claude
    context = f"""
Error Message:
{error}

Relevant Confluence Documentation:
"""
    
    if confluence_docs:
        for i, doc in enumerate(confluence_docs, 1):
            context += f"\n{i}. {doc.get('title', 'Untitled')} (Updated: {doc.get('last_updated')})\n"
            context += f"   Content: {doc.get('chunk_text', '')[:500]}...\n"
            context += f"   Link: {doc.get('url', '')}\n"
    else:
        context += "\n(No relevant Confluence docs found)\n"
    
    if tavily_results:
        context += "\nWeb Search Results (from Tavily):\n"
        for i, result in enumerate(tavily_results[:3], 1):
            context += f"\n{i}. {result.get('title', 'Untitled')}\n"
            context += f"   {result.get('content', '')[:300]}...\n"
    
    # System prompt
    system_prompt = """You are an expert API troubleshooter. Analyze the error and provide:

1. ERROR_EXPLANATION: What this error means in plain terms
2. ROOT_CAUSE: Why it's happening (based on context or educated guess)
3. CONFIDENCE: high/medium/low (based on how much context you found)
4. RESOLUTION_STEPS: Numbered list of exact steps to fix
5. FALLBACK_NOTE: If you had to guess without context, mention it

Format your response as JSON."""
    
    try:
        message = claude_client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=config.LLM_MAX_TOKENS,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": context
                }
            ]
        )
        
        response_text = message.content[0].text
        logger.info("Claude analysis completed")
        
        # Parse Claude's response
        parsed_response = _parse_claude_response(response_text, confluence_docs, tavily_results)
        return parsed_response
        
    except Exception as e:
        error_msg = f"Claude API error: {e}"
        logger.error(error_msg)
        raise LLMError(error_msg)


def _parse_claude_response(
    response_text: str,
    confluence_docs: list,
    tavily_results: list
) -> TroubleshootResponse:
    """
    Parse Claude's JSON response and build TroubleshootResponse
    
    Args:
        response_text: Raw text from Claude
        confluence_docs: Original confluence results
        tavily_results: Original tavily results
    
    Returns:
        Structured TroubleshootResponse
    """
    
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            # Fallback if no JSON found
            parsed = {
                "error_explanation": response_text,
                "root_cause": None,
                "confidence": "medium",
                "resolution_steps": ["Check the error message carefully", "Review related documentation"],
                "fallback_note": "Limited context available"
            }
        
        # Build related confluence links
        related_confluence = []
        if confluence_docs:
            for doc in confluence_docs[:3]:
                related_confluence.append({
                    "title": doc.get("title", "Untitled"),
                    "url": doc.get("url", ""),
                    "reason": f"Matches: {doc.get('matched_terms', 'error analysis')}"
                })
        
        return TroubleshootResponse(
            error_explanation=parsed.get("error_explanation", "Unable to explain"),
            root_cause=parsed.get("root_cause"),
            confidence=parsed.get("confidence", "medium").lower(),
            resolution_steps=parsed.get("resolution_steps", []),
            related_confluence=related_confluence,
            fallback_note=parsed.get("fallback_note"),
            tavily_results=tavily_results
        )
        
    except Exception as e:
        logger.error(f"Error parsing Claude response: {e}")
        # Return minimal response on error
        return TroubleshootResponse(
            error_explanation="Failed to analyze error",
            root_cause=None,
            confidence="low",
            resolution_steps=["Check Confluence manually", "Contact your team"],
            fallback_note=str(e)
        )

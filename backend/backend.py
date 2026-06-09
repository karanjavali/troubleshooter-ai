from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import logging
from datetime import datetime
import os

# Third-party imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import ConfluenceLoader
from langgraph.graph import StateGraph
from typing_extensions import TypedDict
import anthropic

# Database
import supabase
from supabase import create_client, Client

# Search & external APIs
import httpx

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="API Troubleshooter", version="1.0.0")

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Claude
claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Tavily API for web search fallback
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Confluence API config
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACES = os.getenv("CONFLUENCE_SPACES", "").split(",")  # comma-separated

# ============ PYDANTIC MODELS ============

class TroubleshootRequest(BaseModel):
    error: str

class TroubleshootResponse(BaseModel):
    error_explanation: str
    root_cause: Optional[str] = None
    confidence: str  # "high", "medium", "low"
    resolution_steps: List[str]
    related_confluence: List[dict] = []
    fallback_note: Optional[str] = None
    tavily_results: Optional[List[dict]] = None

class SyncResponse(BaseModel):
    message: str
    docs_added: int
    docs_updated: int
    errors: Optional[List[str]] = None

# ============ LANGGRAPH STATE & WORKFLOW ============

class TroubleshootState(TypedDict):
    error_input: str
    parsed_error: dict
    confluence_results: List[dict]
    confluence_confidence: str
    tavily_results: Optional[List[dict]]
    llm_response: TroubleshootResponse

def parse_error_node(state: TroubleshootState) -> TroubleshootState:
    """Parse and extract keywords from error message"""
    error = state["error_input"]
    
    # Extract error code/type (e.g., 500, NullPointerException, InvalidAccountId)
    import re
    error_codes = re.findall(r'\b(4\d{2}|5\d{2}|\w+Exception|\w+Error)\b', error)
    
    # Extract service names (common patterns)
    services = re.findall(r'\b(Payment|Auth|Account|Transaction|API|Service)\b', error, re.IGNORECASE)
    
    state["parsed_error"] = {
        "error_codes": list(set(error_codes)),
        "services": list(set(services)),
        "keywords": error.split()[:20],  # first 20 words
        "full_error": error
    }
    
    logger.info(f"Parsed error: {state['parsed_error']}")
    return state

def search_confluence_node(state: TroubleshootState) -> TroubleshootState:
    """Search Confluence using BM25 (PostgreSQL full-text search)"""
    parsed = state["parsed_error"]
    
    # Build search query (error codes + services + keywords)
    search_terms = []
    search_terms.extend(parsed["error_codes"])
    search_terms.extend(parsed["services"])
    search_terms.extend(parsed["keywords"][:10])
    
    search_query = " & ".join(search_terms[:8])  # Limit to 8 terms
    
    try:
        # BM25 search via PostgreSQL full-text search
        response = supabase_client.rpc(
            "search_confluence_bm25",
            {
                "search_query": search_query,
                "limit": 5
            }
        ).execute()
        
        results = response.data if response.data else []
        
        # Calculate confidence based on results
        if len(results) > 0 and results[0].get("rank", 0) > 0.5:
            confidence = "high"
        elif len(results) > 0:
            confidence = "medium"
        else:
            confidence = "low"
        
        state["confluence_results"] = results
        state["confluence_confidence"] = confidence
        
        logger.info(f"Found {len(results)} Confluence docs with confidence: {confidence}")
        
    except Exception as e:
        logger.error(f"Confluence search failed: {e}")
        state["confluence_results"] = []
        state["confluence_confidence"] = "low"
    
    return state

def search_tavily_fallback_node(state: TroubleshootState) -> TroubleshootState:
    """Fallback to Tavily web search if Confluence is low confidence"""
    if state["confluence_confidence"] == "high":
        state["tavily_results"] = None
        return state
    
    # Only search Tavily if Confluence didn't have good results
    error = state["error_input"]
    search_query = f"{' '.join(state['parsed_error']['error_codes'])} {' '.join(state['parsed_error']['services'][:2])}"
    
    try:
        tavily_response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_API_KEY,
                "query": search_query,
                "max_results": 3,
                "include_answer": True
            },
            timeout=10.0
        )
        
        if tavily_response.status_code == 200:
            data = tavily_response.json()
            state["tavily_results"] = data.get("results", [])
            logger.info(f"Tavily found {len(state['tavily_results'])} results")
        else:
            state["tavily_results"] = None
            
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        state["tavily_results"] = None
    
    return state

def generate_response_node(state: TroubleshootState) -> TroubleshootState:
    """Use Claude to generate response with retrieved context"""
    
    error = state["error_input"]
    confluence_docs = state["confluence_results"]
    tavily_results = state["tavily_results"]
    
    # Build context for Claude
    context = f"""
Error Message:
{error}

Relevant Confluence Documentation:
"""
    
    if confluence_docs:
        for i, doc in enumerate(confluence_docs, 1):
            context += f"\n{i}. {doc['title']} (Updated: {doc['last_updated']})\n"
            context += f"   Content: {doc['chunk_text'][:500]}...\n"
            context += f"   Link: {doc['url']}\n"
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
            model="claude-opus-4-1-20250805",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": context
                }
            ]
        )
        
        response_text = message.content[0].text
        
        # Parse Claude's response (expect JSON)
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed_response = json.loads(json_match.group())
        else:
            parsed_response = {
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
                    "title": doc["title"],
                    "url": doc["url"],
                    "reason": f"Matches: {doc.get('matched_terms', 'error analysis')}"
                })
        
        state["llm_response"] = TroubleshootResponse(
            error_explanation=parsed_response.get("error_explanation", "Unable to explain"),
            root_cause=parsed_response.get("root_cause"),
            confidence=parsed_response.get("confidence", "medium"),
            resolution_steps=parsed_response.get("resolution_steps", []),
            related_confluence=related_confluence,
            fallback_note=parsed_response.get("fallback_note"),
            tavily_results=tavily_results
        )
        
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        state["llm_response"] = TroubleshootResponse(
            error_explanation="Failed to analyze error",
            root_cause=None,
            confidence="low",
            resolution_steps=["Check Confluence manually", "Contact your team"],
            fallback_note=str(e)
        )
    
    return state

# Build Langgraph workflow
workflow = StateGraph(TroubleshootState)

workflow.add_node("parse_error", parse_error_node)
workflow.add_node("search_confluence", search_confluence_node)
workflow.add_node("search_tavily", search_tavily_fallback_node)
workflow.add_node("generate_response", generate_response_node)

# Define edges
workflow.add_edge("parse_error", "search_confluence")
workflow.add_edge("search_confluence", "search_tavily")
workflow.add_edge("search_tavily", "generate_response")

workflow.set_entry_point("parse_error")
workflow.set_finish_point("generate_response")

graph = workflow.compile()

# ============ API ENDPOINTS ============

@app.post("/api/troubleshoot", response_model=TroubleshootResponse)
async def troubleshoot(request: TroubleshootRequest):
    """
    Main endpoint: Accept error message and return analysis.
    Uses Langgraph workflow internally.
    """
    
    try:
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
        
        return final_state["llm_response"]
        
    except Exception as e:
        logger.error(f"Troubleshoot endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sync-confluence", response_model=SyncResponse)
async def sync_confluence():
    """
    Sync Confluence docs: Fetch from API, chunk, and index in Supabase.
    """
    
    docs_added = 0
    docs_updated = 0
    errors = []
    
    try:
        # Fetch pages from each Confluence space
        for space_key in CONFLUENCE_SPACES:
            if not space_key.strip():
                continue
            
            try:
                # Get pages from Confluence API
                pages = fetch_confluence_pages(space_key)
                
                for page in pages:
                    # Chunk the page
                    chunks = chunk_page(page)
                    
                    # Store in Supabase
                    for chunk_idx, chunk in enumerate(chunks):
                        result = supabase_client.table("confluence_chunks").upsert({
                            "doc_id": page["id"],
                            "page_id": page["id"],
                            "title": page["title"],
                            "space_key": space_key,
                            "team": space_key.lower(),
                            "chunk_index": chunk_idx,
                            "chunk_text": chunk,
                            "url": page["url"],
                            "last_updated": datetime.now().isoformat(),
                            "content": page["content"]
                        }).execute()
                    
                    docs_added += 1
                    logger.info(f"Indexed page: {page['title']}")
                    
            except Exception as e:
                error_msg = f"Error syncing space {space_key}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return SyncResponse(
            message=f"Synced {docs_added} documents successfully",
            docs_added=docs_added,
            docs_updated=docs_updated,
            errors=errors if errors else None
        )
        
    except Exception as e:
        logger.error(f"Sync endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============ HELPER FUNCTIONS ============

def fetch_confluence_pages(space_key: str) -> List[dict]:
    """Fetch all pages from a Confluence space using LangChain ConfluenceLoader"""
    pages = []
    
    try:
        # Initialize ConfluenceLoader with environment variables
        loader = ConfluenceLoader(
            url=CONFLUENCE_BASE_URL,
            username=CONFLUENCE_EMAIL,
            api_key=CONFLUENCE_API_TOKEN,
            space_key=space_key
        )
        
        # Load documents (handles pagination automatically)
        documents = loader.load()
        
        # Convert LangChain documents to our format
        for doc in documents:
            pages.append({
                "id": doc.metadata.get("id", doc.metadata.get("page_id")),
                "title": doc.metadata.get("title", "Untitled"),
                "content": doc.page_content,  # Full page content
                "url": doc.metadata.get("source", ""),
                "updated": doc.metadata.get("updated_at", datetime.now().isoformat())
            })
        
        logger.info(f"Fetched {len(pages)} pages from space {space_key}")
        
    except Exception as e:
        logger.error(f"Failed to fetch Confluence pages from {space_key}: {e}")
        # Return empty list on error (graceful degradation)
    
    return pages

def chunk_page(page: dict, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split page content into chunks"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = splitter.split_text(page["content"])
    return chunks if chunks else [page["content"]]

# ============ HEALTH CHECK ============

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

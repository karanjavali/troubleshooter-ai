# Backend Structure & Quick Start

## 📁 Directory Organization

```
backend/
├── main.py                          # FastAPI entry point
├── config.py                        # Configuration (env vars)
├── models.py                        # Pydantic models
├── __init__.py                      # Package init
│
├── services/                        # Business logic services
│   ├── __init__.py
│   ├── confluence_service.py        # Confluence API integration
│   ├── search_service.py            # BM25 search via Supabase
│   ├── llm_service.py               # Claude API integration
│   ├── tavily_service.py            # Tavily web search
│   └── chunking_service.py          # Document chunking logic
│
├── workflow/                        # Langgraph workflow
│   ├── __init__.py
│   ├── state.py                     # Workflow state definition
│   ├── nodes.py                     # Workflow node functions
│   └── graph.py                     # Graph compilation
│
├── routes/                          # API endpoints
│   ├── __init__.py
│   ├── troubleshoot.py              # Error analysis endpoint
│   ├── sync.py                      # Confluence sync endpoint
│   └── health.py                    # Health check endpoint
│
└── utils/                           # Utilities
    ├── __init__.py
    ├── logger.py                    # Logging setup
    └── errors.py                    # Custom exceptions
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the Server
```bash
python main.py
# Server runs on http://localhost:8000
```

### 4. Test the API
```bash
# Health check
curl http://localhost:8000/health

# Analyze an error
curl -X POST http://localhost:8000/api/troubleshoot \
  -H "Content-Type: application/json" \
  -d '{"error": "500 Internal Server Error"}'

# Sync Confluence
curl -X POST http://localhost:8000/api/sync-confluence
```

---

## 📦 Module Guide

### `config.py`
Centralized configuration management
- Loads environment variables
- Validates required config on startup
- Easy to override for testing

```python
from config import config
print(config.CONFLUENCE_SPACES)
print(config.BM25_RESULTS_LIMIT)
```

### `models.py`
Pydantic request/response models
- Type-safe API contracts
- Auto-generates OpenAPI docs
- Built-in validation

```python
from models import TroubleshootRequest, TroubleshootResponse
```

### `services/`
Business logic separated by concern

**confluence_service.py**
- Fetch pages from Confluence spaces
- Uses LangChain ConfluenceLoader
- Handles pagination automatically

**search_service.py**
- BM25 search via Supabase RPC
- Index chunks for fast retrieval
- Confidence scoring

**llm_service.py**
- Claude API integration
- Prompt engineering
- Response parsing and validation

**tavily_service.py**
- Web search fallback
- Conditional searching based on confidence
- Error handling

**chunking_service.py**
- Document splitting logic
- Configurable chunk size and overlap
- Uses LangChain RecursiveCharacterTextSplitter

### `workflow/`
Langgraph multi-step orchestration

**state.py**
- Defines workflow state schema
- Type-safe state management

**nodes.py**
- Individual workflow steps
- Async functions for parallelization
- Can add decision logic

**graph.py**
- Compiles workflow into executable graph
- Manages node connections
- Returns singleton instance

### `routes/`
API endpoint definitions

**troubleshoot.py**
- POST /api/troubleshoot
- Runs full workflow
- Returns structured response

**sync.py**
- POST /api/sync-confluence
- Syncs docs from all spaces
- Reports results

**health.py**
- GET /health
- Simple liveness check

### `utils/`
Helper utilities

**logger.py**
- Centralized logging setup
- Configurable log level
- Used throughout app

**errors.py**
- Custom exception classes
- Specific error types for different failures
- Better error handling

---

## 🔄 Request Flow

```
HTTP Request
    ↓
routes/troubleshoot.py (endpoint)
    ↓
workflow/graph.py (invoke Langgraph)
    ↓
workflow/nodes.py:
    1. parse_error_node() → Extract keywords
    2. search_confluence_node() → BM25 search
    3. search_tavily_node() → Web search fallback
    4. generate_response_node() → Claude analysis
    ↓
services/ (called by nodes):
    - search_service.search_confluence_bm25()
    - tavily_service.search_tavily()
    - llm_service.analyze_error_with_context()
    ↓
models.py (TroubleshootResponse)
    ↓
HTTP Response
```

---

## 🧪 Testing Individual Services

### Test Confluence Fetch
```python
from services import fetch_confluence_pages

pages = await fetch_confluence_pages("PAYMENT")
print(f"Fetched {len(pages)} pages")
```

### Test BM25 Search
```python
from services import search_confluence_bm25

results, confidence = await search_confluence_bm25("500 error PaymentService")
print(f"Found {len(results)} results with {confidence} confidence")
```

### Test LLM Analysis
```python
from services import analyze_error_with_context

response = await analyze_error_with_context(
    error="500 Internal Server Error",
    confluence_docs=[],
    tavily_results=None
)
print(response.error_explanation)
```

---

## 🛠️ Development Tips

### Add a New Endpoint
1. Create route in `routes/new_feature.py`
2. Import and include router in `main.py`
3. Use services for business logic

### Add a New Service
1. Create file in `services/new_service.py`
2. Export in `services/__init__.py`
3. Use in workflow nodes

### Add Logging
```python
from utils import logger

logger.info("Processing started")
logger.error("Error occurred")
logger.debug("Debug info")
```

### Handle Errors
```python
from utils import SearchError, ConfluenceError

try:
    results = await search_confluence_bm25(query)
except SearchError as e:
    logger.error(f"Search failed: {e}")
    # Handle gracefully
```

---

## 📊 Configuration Options

Edit `.env` to customize:

```
# Search settings
BM25_RESULTS_LIMIT=5
CHUNK_SIZE=1000
CHUNK_OVERLAP=100

# LLM settings
ANTHROPIC_MODEL=claude-opus-4-1-20250805
LLM_MAX_TOKENS=1024

# Logging
LOG_LEVEL=INFO

# Server
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

---

## 🚨 Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in backend directory
cd backend
python main.py
```

### Circular imports
- All imports use absolute paths from `backend/`
- Services import config, not vice versa
- Routes import services, not vice versa

### Async/await errors
- All service functions are async
- Call with `await` in routes/nodes
- Use `asyncio.run()` if testing directly

---

## 🎯 Next Steps

1. ✅ Run locally and test all endpoints
2. Add unit tests for each service
3. Add integration tests for workflows
4. Deploy to production (Docker, Railway, etc.)
5. Monitor with Langsmith
6. Optimize based on metrics


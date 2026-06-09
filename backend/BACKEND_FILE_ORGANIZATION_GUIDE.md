# Backend Setup Guide - File Organization

## 📥 How to Download and Organize

All the backend files are in `/outputs`. Here's how to organize them locally:

### Step 1: Create Directory Structure
```bash
# Create backend folder structure
mkdir -p api-troubleshooter/backend
cd api-troubleshooter/backend

mkdir -p services
mkdir -p routes
mkdir -p workflow
mkdir -p utils
```

### Step 2: Copy Root Files
Copy these files to `backend/`:
- `main.py` → Root of backend/
- `config.py` → Root of backend/
- `models.py` → Root of backend/
- `requirements.txt` → Root of backend/
- `.env.example` → Root of backend/

### Step 3: Copy Service Files
Copy to `backend/services/`:
- `confluence_service.py`
- `chunking_service.py`
- `search_service.py`
- `llm_service.py`
- `tavily_service.py`

Then create `backend/services/__init__.py`:
```python
"""Services package"""
from .confluence_service import fetch_confluence_pages, sync_all_spaces
from .chunking_service import chunk_page
from .search_service import search_confluence_bm25, index_chunk
from .llm_service import analyze_error_with_context
from .tavily_service import search_tavily, should_search_tavily

__all__ = [
    "fetch_confluence_pages",
    "sync_all_spaces",
    "chunk_page",
    "search_confluence_bm25",
    "index_chunk",
    "analyze_error_with_context",
    "search_tavily",
    "should_search_tavily"
]
```

### Step 4: Copy Workflow Files
Copy to `backend/workflow/`:
- `state.py`
- `nodes.py`
- `graph.py`

Then create `backend/workflow/__init__.py`:
```python
"""Workflow package"""
from .graph import graph
from .state import TroubleshootState

__all__ = ["graph", "TroubleshootState"]
```

### Step 5: Copy Utility Files
Copy to `backend/utils/`:
- `logger.py`
- `errors.py`

Then create `backend/utils/__init__.py`:
```python
"""Utils package"""
from .logger import logger
from .errors import (
    APIError,
    ConfluenceError,
    SearchError,
    LLMError,
    TavilyError
)

__all__ = [
    "logger",
    "APIError",
    "ConfluenceError",
    "SearchError",
    "LLMError",
    "TavilyError"
]
```

### Step 6: Copy Route Files
Copy to `backend/routes/`:
- `troubleshoot.py`
- `sync.py`
- `health.py`

Then create `backend/routes/__init__.py`:
```python
"""Routes package"""
from .troubleshoot import router as troubleshoot_router
from .sync import router as sync_router
from .health import router as health_router

__all__ = ["troubleshoot_router", "sync_router", "health_router"]
```

### Step 7: Create Backend Init
Create `backend/__init__.py`:
```python
"""API Troubleshooter Backend

A production-grade FastAPI backend for error analysis using:
- Langgraph for multi-step AI workflows
- PostgreSQL BM25 for vectorless RAG
- Claude API for intelligent analysis
- Confluence integration for documentation
- Tavily fallback for web search
"""

__version__ = "1.0.0"
```

### Step 8: Add .gitignore
Create `backend/.gitignore`:
```
# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp

# Testing
.pytest_cache/
.coverage

# Logs
*.log
```

---

## ✅ Final Structure

Your backend folder should look like:
```
backend/
├── main.py
├── config.py
├── models.py
├── requirements.txt
├── .env.example
├── .gitignore
├── __init__.py
│
├── services/
│   ├── __init__.py
│   ├── confluence_service.py
│   ├── chunking_service.py
│   ├── search_service.py
│   ├── llm_service.py
│   └── tavily_service.py
│
├── routes/
│   ├── __init__.py
│   ├── troubleshoot.py
│   ├── sync.py
│   └── health.py
│
├── workflow/
│   ├── __init__.py
│   ├── state.py
│   ├── nodes.py
│   └── graph.py
│
└── utils/
    ├── __init__.py
    ├── logger.py
    └── errors.py
```

---

## 🚀 Quick Start (After Organization)

```bash
cd backend

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py

# In another terminal, test it
curl http://localhost:8000/health
```

---

## 🔗 File Dependency Map

Understanding what imports what:

```
main.py
├── imports config
├── imports models
├── imports routes (all 3)
│   ├── troubleshoot.py
│   │   ├── imports models
│   │   ├── imports workflow.graph
│   │   └── imports utils.logger
│   ├── sync.py
│   │   ├── imports models
│   │   ├── imports services (all)
│   │   ├── imports config
│   │   └── imports utils.logger
│   └── health.py
│       └── imports models
│
services/
├── confluence_service.py
│   ├── imports config
│   ├── imports utils (logger, ConfluenceError)
│   └── imports models
├── chunking_service.py
│   ├── imports config
│   └── imports utils.logger
├── search_service.py
│   ├── imports config
│   ├── imports utils (logger, SearchError)
│   └── imports models
├── llm_service.py
│   ├── imports config
│   ├── imports utils (logger, LLMError)
│   └── imports models
└── tavily_service.py
    ├── imports config
    └── imports utils.logger

workflow/
├── state.py (no imports)
├── nodes.py
│   ├── imports utils.logger
│   ├── imports services (all)
│   └── imports workflow.state
└── graph.py
    ├── imports workflow.state
    └── imports workflow.nodes
```

---

## 💡 Key Points

✅ **No circular imports** - All dependencies flow downward  
✅ **Easy to test** - Import individual services and test them  
✅ **Easy to extend** - Add new services/routes/nodes easily  
✅ **Production-ready** - Follows FastAPI best practices  
✅ **Clean separation** - Config, business logic, API, utilities separate  

---

## 🎯 Next Steps

1. ✅ Organize files using this guide
2. Set up `.env` with your API keys
3. Run `pip install -r requirements.txt`
4. Test with `python main.py`
5. Test all endpoints
6. Deploy to production

Good luck! 🚀


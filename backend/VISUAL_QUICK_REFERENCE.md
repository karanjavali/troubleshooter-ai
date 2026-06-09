# 🎨 Visual Quick Reference - Organized Backend

## 📂 Complete Directory Tree

```
api-troubleshooter/
│
├── backend/
│   ├── main.py                          ⭐ App entry point
│   ├── config.py                        ⚙️  Environment config
│   ├── models.py                        📋 Pydantic schemas
│   ├── __init__.py                      
│   ├── requirements.txt                 📦 Dependencies
│   ├── .env.example                     🔑 Config template
│   ├── .gitignore
│   │
│   ├── services/                        🔧 Business Logic
│   │   ├── __init__.py
│   │   ├── confluence_service.py        (Fetch from Confluence)
│   │   ├── chunking_service.py          (Split documents)
│   │   ├── search_service.py            (BM25 search)
│   │   ├── llm_service.py               (Claude analysis)
│   │   └── tavily_service.py            (Web search fallback)
│   │
│   ├── routes/                          🛣️  API Endpoints
│   │   ├── __init__.py
│   │   ├── troubleshoot.py              (POST /api/troubleshoot)
│   │   ├── sync.py                      (POST /api/sync-confluence)
│   │   └── health.py                    (GET /health)
│   │
│   ├── workflow/                        🔄 Langgraph Orchestration
│   │   ├── __init__.py
│   │   ├── state.py                     (State definition)
│   │   ├── nodes.py                     (4 processing steps)
│   │   └── graph.py                     (Compiled workflow)
│   │
│   ├── utils/                           🛠️  Utilities
│   │   ├── __init__.py
│   │   ├── logger.py                    (Logging setup)
│   │   └── errors.py                    (Custom exceptions)
│   │
│   └── README.md                        📖 Backend docs
│
├── frontend/
│   ├── src/
│   │   └── App.jsx                      (React chat UI)
│   └── ...
│
├── .env                                 🔐 Actual config (Git ignored)
└── README.md                            📖 Project overview
```

---

## 🔗 Data Flow Through Backend

```
┌─────────────────────────────────────┐
│  User sends error (HTTP POST)       │
└──────────────┬──────────────────────┘
               │
               ▼
        ┌──────────────┐
        │ routes/      │
        │ troubleshoot │
        └──────┬───────┘
               │
               ▼
        ┌──────────────────┐
        │ workflow/graph.py│  (Orchestrates)
        └──────┬───────────┘
               │
               ▼
        ┌──────────────────────────────────────┐
        │      workflow/nodes.py (4 steps)     │
        ├──────────────────────────────────────┤
        │ 1. parse_error_node()                │
        │    ↓ Extracts keywords               │
        ├──────────────────────────────────────┤
        │ 2. search_confluence_node()          │
        │    ↓ Uses: services/search_service   │
        ├──────────────────────────────────────┤
        │ 3. search_tavily_node()              │
        │    ↓ Uses: services/tavily_service   │
        ├──────────────────────────────────────┤
        │ 4. generate_response_node()          │
        │    ↓ Uses: services/llm_service      │
        └──────┬───────────────────────────────┘
               │
               ▼
        ┌──────────────────────┐
        │ models.TroubleshootResponse
        │ (Structured output)  │
        └──────┬───────────────┘
               │
               ▼
        ┌──────────────────────┐
        │ HTTP Response (JSON) │
        └──────────────────────┘
```

---

## 🎯 Import Hierarchy

```
main.py (entry point)
  ├─ config.py ────────── .env variables
  ├─ models.py ────────── Type schemas
  └─ routes/
      ├─ troubleshoot.py
      │   ├─ models.py
      │   ├─ workflow/graph.py
      │   └─ utils/logger.py
      ├─ sync.py
      │   ├─ models.py
      │   ├─ services/
      │   │   ├─ confluence_service.py
      │   │   ├─ chunking_service.py
      │   │   └─ search_service.py
      │   └─ utils/logger.py
      └─ health.py
          └─ models.py

workflow/
  ├─ graph.py ─────────── Compiles workflow
  │   └─ nodes.py
  │       ├─ services/
  │       │   ├─ search_service.py
  │       │   ├─ tavily_service.py
  │       │   └─ llm_service.py
  │       └─ utils/logger.py
  └─ state.py ────────── Type definitions

services/
  ├─ confluence_service.py
  │   ├─ config.py
  │   └─ utils/
  ├─ search_service.py
  │   ├─ config.py
  │   └─ utils/
  ├─ llm_service.py
  │   ├─ config.py
  │   ├─ models.py
  │   └─ utils/
  └─ ... (other services)
```

---

## 📝 File Purposes at a Glance

| File | Purpose | Lines | Key Functions |
|------|---------|-------|---|
| `main.py` | FastAPI app init | ~70 | `app`, startup/shutdown |
| `config.py` | Configuration | ~60 | `Config` class, validation |
| `models.py` | Data schemas | ~80 | Pydantic models |
| `confluence_service.py` | Confluence fetch | ~60 | `fetch_confluence_pages()` |
| `chunking_service.py` | Document split | ~45 | `chunk_page()` |
| `search_service.py` | BM25 search | ~80 | `search_confluence_bm25()` |
| `llm_service.py` | Claude integration | ~150 | `analyze_error_with_context()` |
| `tavily_service.py` | Web search | ~65 | `search_tavily()` |
| `state.py` | State types | ~20 | `TroubleshootState` |
| `nodes.py` | Workflow steps | ~120 | 4 node functions |
| `graph.py` | Workflow compile | ~30 | `build_workflow()` |
| `troubleshoot.py` | Error endpoint | ~50 | `troubleshoot()` |
| `sync.py` | Sync endpoint | ~80 | `sync_confluence()` |
| `health.py` | Health endpoint | ~20 | `health_check()` |
| `logger.py` | Logging | ~20 | `setup_logging()` |
| `errors.py` | Exceptions | ~20 | Exception classes |

---

## 🎬 Request Flow Example

### Request: `POST /api/troubleshoot`
```
Body: {"error": "500 Internal Server Error"}
  │
  ├→ main.py (FastAPI receives)
  │    └→ routes/troubleshoot.py::troubleshoot()
  │         │
  │         ├→ Initialize state
  │         └→ Call workflow/graph.py::graph.invoke()
  │
  │              workflow/nodes.py:
  │              1. parse_error_node()
  │                 → extracts "500" as error_code
  │
  │              2. search_confluence_node()
  │                 → services/search_service.search_confluence_bm25("500")
  │                 → returns [doc1, doc2, doc3]
  │
  │              3. search_tavily_node()
  │                 → confidence = "medium" → run search
  │                 → services/tavily_service.search_tavily("500")
  │
  │              4. generate_response_node()
  │                 → services/llm_service.analyze_error_with_context()
  │                 → Claude analyzes with all context
  │
  │         └→ Returns TroubleshootResponse
  │
  └→ HTTP 200 with JSON response
```

---

## 🧩 Component Interactions

### Services Work Together
```
confluence_service
  ├─ Uses: config.CONFLUENCE_*
  └─ Returns: List[ConfluencePage]
       │
       └─→ chunking_service
           ├─ Uses: config.CHUNK_SIZE
           └─ Returns: List[str]
                │
                └─→ search_service
                    ├─ Indexes chunks
                    └─ Searches via BM25
```

### Workflow Orchestrates Services
```
workflow/graph.py
  │
  ├─→ parse_error_node()
  │   └─ Updates state["parsed_error"]
  │
  ├─→ search_confluence_node()
  │   └─ Calls: search_service.search_confluence_bm25()
  │      Updates: state["confluence_results"], state["confluence_confidence"]
  │
  ├─→ search_tavily_node()
  │   └─ Calls: tavily_service.search_tavily()
  │      Updates: state["tavily_results"]
  │
  └─→ generate_response_node()
      └─ Calls: llm_service.analyze_error_with_context()
         Updates: state["llm_response"]
```

---

## 🔑 Key Import Patterns

### In Routes
```python
from workflow.graph import graph          # Workflow execution
from models import TroubleshootResponse   # Type hints
from utils import logger                  # Logging
```

### In Workflow Nodes
```python
from services import search_confluence_bm25, search_tavily, analyze_error_with_context
from utils import logger
```

### In Services
```python
from config import config        # Never hardcode!
from utils import logger, SearchError
from models import TroubleshootResponse
```

### Never In Services
```python
# ❌ DON'T import routes
# ❌ DON'T import workflow
# ❌ DON'T import main
# Services are independent!
```

---

## ✅ Checklist After Setup

- [ ] All 17 Python files in correct folders
- [ ] All 4 `__init__.py` files created with proper exports
- [ ] `main.py` imports from `routes/`
- [ ] `routes/` import from `models`, `workflow`, `utils`
- [ ] `workflow/` imports from `services`
- [ ] `services/` import from `config`, `utils`, `models`
- [ ] No circular imports (test with `python -c "import main"`)
- [ ] `.env` created with API keys
- [ ] `pip install -r requirements.txt` works
- [ ] `python main.py` starts server without errors
- [ ] `curl http://localhost:8000/health` returns 200

---

## 🎓 This Structure Shows

When in interviews:
- ✅ You understand **separation of concerns**
- ✅ You think about **testability** (each service independently testable)
- ✅ You know **FastAPI best practices** (routers, dependency injection)
- ✅ You can **scale** (add features without touching existing code)
- ✅ You're **professional** (not a "my first project" structure)

---

## 💾 One-Liner Summary

**Monolithic:** 500 lines in `backend.py`  
**Organized:** 17 files, 800 lines total, clear separation, way more professional

That's the power of good organization! 🚀


"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import config
from utils import logger
from routes import troubleshoot_router, sync_router, health_router

# Validate configuration on startup
try:
    config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="API Troubleshooter",
    description="AI-powered API error analysis using Langgraph, RAG, and Claude",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL, "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(troubleshoot_router)
app.include_router(sync_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting API Troubleshooter in {config.ENVIRONMENT} mode")
    logger.info(f"Confluence spaces configured: {config.CONFLUENCE_SPACES}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down API Troubleshooter")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "API Troubleshooter",
        "version": "1.0.0",
        "status": "ready",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.DEBUG
    )

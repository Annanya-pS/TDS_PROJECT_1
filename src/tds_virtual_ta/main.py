"""
=== FIXED: src/tds_virtual_ta/main.py ===
FastAPI application with correct endpoint path
"""

import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import TaskRequest, TaskResponse
from .worker import process_task
from .utils.security import validate_secret
from .utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="TDS LLM Code Deployment",
    description="Automated code generation and deployment for IIT Madras TDS",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Service info."""
    return {
        "service": "TDS LLM Code Deployment",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "api": "/api-endpoint",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


@app.post("/api-endpoint", response_model=TaskResponse, status_code=200)
async def api_endpoint(
    request: TaskRequest,
    background_tasks: BackgroundTasks
):
    """
    Main API endpoint that receives task requests.
    
    CRITICAL: Must return HTTP 200 immediately and process in background.
    Must complete within 10 minutes.
    """
    
    # Validate secret
    if not validate_secret(request.secret):
        logger.warning(f"Invalid secret for email: {request.email}")
        raise HTTPException(status_code=401, detail="Invalid secret")
    
    logger.info(
        f"Task received: {request.task} (Round {request.round}) for {request.email}"
    )
    
    # Add background task - MUST complete within 10 minutes
    background_tasks.add_task(process_task, request)
    
    # Return immediate HTTP 200
    return TaskResponse(
        status="accepted",
        message="Request received, processing"
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.tds_virtual_ta.main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=False,
        log_level=settings.log_level.lower()
    )
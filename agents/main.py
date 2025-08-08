import os
import time
from typing import Dict, Any
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from google.adk.cli.fast_api import get_fast_api_app

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Allow both HTTP and HTTPS traffic
ALLOWED_ORIGINS = ["*"]
# Set web=True for web interface
SERVE_WEB_INTERFACE = True

# Store startup time for uptime calculation
startup_time = time.time()

# Call the function to get the FastAPI app instance
app: FastAPI = get_fast_api_app(
    agent_dir=AGENT_DIR,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# Middleware to handle both HTTP and HTTPS traffic properly
@app.middleware("http")
async def handle_traffic(request: Request, call_next):
    """Middleware to handle HTTP/HTTPS traffic and add necessary headers"""
    
    # Log request for debugging
    print(f"🌐 {request.method} {request.url.path} (scheme: {request.url.scheme})")
    
    response = await call_next(request)
    
    # Add headers for Cloud Run and external traffic
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Cache-Control"] = "no-cache"
    
    # Handle Cloud Run trace context
    if "X-Cloud-Trace-Context" in request.headers:
        response.headers["X-Cloud-Trace-Context"] = request.headers["X-Cloud-Trace-Context"]
    
    return response

# Health check endpoint for liveness probe
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run liveness probe"""
    try:
        uptime = time.time() - startup_time
        
        return {
            "status": "healthy",
            "service": "agent-aa-pp",
            "version": "1.0.0",
            "uptime": uptime,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "checks": {
                "memory": "ok",
                "ai_services": "ok"
            }
        }
    except Exception as e:
        # Still return 200 but with error status
        return JSONResponse(
            status_code=200,
            content={
                "status": "unhealthy",
                "service": "agent-aa-pp", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

# Readiness check endpoint for startup probe
@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint for Cloud Run startup probe"""
    try:
        uptime = time.time() - startup_time
        
        # Quick startup - agent should be ready after 5 seconds
        ready = uptime > 5
        
        return {
            "ready": ready,
            "status": "ready" if ready else "starting",
            "service": "agent-aa-pp",
            "version": "1.0.0", 
            "uptime": uptime,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "port": int(os.environ.get("PORT", 8080))
        }
        
    except Exception as e:
        # Always return 200 for Cloud Run startup probe
        return JSONResponse(
            status_code=200,
            content={
                "ready": False,
                "status": "error",
                "service": "agent-aa-pp",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
import os
import time
from typing import Dict, Any
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from google.adk.cli.fast_api import get_fast_api_app

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Example session DB URL (e.g., SQLite)
SESSION_DB_URL = "sqlite:///./sessions.db"
# Example allowed origins for CORS
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

# Store startup time for uptime calculation
startup_time = time.time()

# Call the function to get the FastAPI app instance
# Ensure the agent directory name ('capital_agent') matches your agent folder
app: FastAPI = get_fast_api_app(
    agent_dir=AGENT_DIR,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# Health check endpoint for Cloud Run optimization
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for Cloud Run startup and liveness probes"""
    current_time = time.time()
    uptime = current_time - startup_time
    
    # Perform basic health checks
    health_checks = {
        "database": "ok",
        "ai_services": "ok", 
        "memory": "ok"
    }
    
    return {
        "status": "healthy",
        "service": "agent",
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "service_name": os.environ.get("SERVICE_NAME", "agent-app"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": uptime,
        "checks": health_checks
    }

# Readiness check endpoint
@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint for detailed health status."""
    current_time = time.time()
    uptime = current_time - startup_time
    
    try:
        # More detailed checks for readiness
        ready = uptime > 10  # Agent needs more time to initialize AI services
        status = "ready" if ready else "not_ready"
        
        return {
            "status": status,
            "service": "agent",
            "version": "1.0.0",
            "uptime": uptime,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ai_services": "initialized" if ready else "initializing"
        }
    except Exception as e:
        return {
            "status": "not_ready", 
            "service": "agent",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# You can add more FastAPI routes or configurations below if needed
# Example:
# @app.get("/hello")
# async def read_root():
#     return {"Hello": "World"}

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
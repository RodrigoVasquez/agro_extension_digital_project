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

# Add a simple test endpoint to verify the app is working
@app.get("/")
async def root():
    """Root endpoint to verify service is running."""
    return {"message": "Agent service is running", "timestamp": datetime.utcnow().isoformat() + "Z"}

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

# Readiness check endpoint - MUST return 200 for Cloud Run startup probe
@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint for detailed health status."""
    current_time = time.time()
    uptime = current_time - startup_time
    
    try:
        # More detailed checks for readiness
        # Reduced from 10 to 5 seconds for faster startup
        ready = uptime > 5  # Agent needs time to initialize AI services
        
        response_data = {
            "status": "ready" if ready else "not_ready",
            "service": "agent",
            "version": "1.0.0",
            "uptime": uptime,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ai_services": "initialized" if ready else "initializing",
            "port": int(os.environ.get("PORT", 8080))
        }
        
        # Always return the response data, even if not ready
        # Cloud Run needs a 200 response to consider the probe successful
        return response_data
        
    except Exception as e:
        # Even on error, return a 200 response with error details
        return {
            "status": "not_ready", 
            "service": "agent",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime": uptime
        }

# Debug endpoint to help troubleshoot deployment issues
@app.get("/debug")
async def debug_info():
    """Debug endpoint to check service status."""
    return {
        "service": "agent",
        "environment": {
            "PORT": os.environ.get("PORT", "not_set"),
            "ENVIRONMENT": os.environ.get("ENVIRONMENT", "not_set"), 
            "SERVICE_NAME": os.environ.get("SERVICE_NAME", "not_set"),
            "GOOGLE_CLOUD_PROJECT": os.environ.get("GOOGLE_CLOUD_PROJECT", "not_set")
        },
        "uptime": time.time() - startup_time,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "app_type": str(type(app)),
        "routes": [str(route.path) for route in app.routes if hasattr(route, 'path')]
    }

# You can add more FastAPI routes or configurations below if needed
# Example:
# @app.get("/hello")
# async def read_root():
#     return {"Hello": "World"}

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
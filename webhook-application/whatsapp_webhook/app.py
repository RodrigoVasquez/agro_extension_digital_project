"""
FastAPI application factory and configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tomllib
import time
from datetime import datetime

from .api.webhooks import router as webhook_router
from .utils.logging import configure_app_logging
from .utils.app_config import config
from .models.api_models import HealthCheckResponse


def get_version() -> str:
    """Get version from pyproject.toml."""
    try:
        with open("pyproject.toml", "rb") as f:
            data = tomllib.load(f)
            return data["project"]["version"]
    except Exception:
        return "unknown"


async def _check_whatsapp_api_health() -> str:
    """Check if WhatsApp API configuration is available."""
    try:
        # Check if required environment variables are set
        required_vars = ["WSP_TOKEN", "WHATSAPP_BASE_URL"]
        for var in required_vars:
            if not os.getenv(var):
                return "error"
        return "ok"
    except Exception:
        return "error"


async def _check_agent_services_health() -> str:
    """Check if agent services configuration is available."""
    try:
        # Check if agent URL is configured
        if not os.getenv("APP_URL"):
            return "error"
        return "ok"
    except Exception:
        return "error"


def _check_environment_variables() -> str:
    """Check if critical environment variables are set."""
    try:
        critical_vars = ["VERIFY_TOKEN", "LOG_LEVEL"]
        for var in critical_vars:
            if not os.getenv(var):
                return "warning"
        return "ok"
    except Exception:
        return "error"


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Configure logging first
    app_logger = configure_app_logging()
    
    # Get version from pyproject.toml
    version = get_version()
    
    # Store startup time for uptime calculation
    startup_time = time.time()
    
    # Create FastAPI app with metadata
    app = FastAPI(
        title="WhatsApp Webhook Service",
        description="Modular WhatsApp webhook processor for handling various message types and integrating with AI agent services",
        version=version,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(webhook_router)
    
    # Add health check endpoint
    @app.get("/health", response_model=HealthCheckResponse)
    async def health_check():
        """Health check endpoint for Cloud Run startup and liveness probes."""
        current_time = time.time()
        uptime = current_time - startup_time
        
        # Perform basic health checks
        health_checks = {
            "whatsapp_api": await _check_whatsapp_api_health(),
            "agent_services": await _check_agent_services_health(),
            "memory": "ok",
            "environment_vars": _check_environment_variables()
        }
        
        # Determine overall status
        overall_status = "healthy" if all(
            check in ["ok", "healthy"] for check in health_checks.values()
        ) else "degraded"
        
        return HealthCheckResponse(
            status=overall_status,
            version=version,
            environment=config.environment,
            service="webhook",
            timestamp=datetime.utcnow().isoformat() + "Z",
            uptime=uptime,
            checks=health_checks
        )
    
    # Add readiness check endpoint
    @app.get("/ready", response_model=HealthCheckResponse)
    async def readiness_check():
        """Readiness check endpoint for detailed health status."""
        current_time = time.time()
        uptime = current_time - startup_time
        
        try:
            # More detailed checks for readiness
            ready = uptime > 5  # Webhook service is lighter, needs less startup time
            
            readiness_checks = {
                "configuration": "ok" if config.environment else "error",
                "logging": "ok",
                "uptime_sufficient": "ok" if ready else "warming_up"
            }
            
            status = "ready" if ready and all(
                check == "ok" for check in readiness_checks.values()
            ) else "not_ready"
            
            return HealthCheckResponse(
                status=status,
                version=version,
                environment=config.environment,
                service="webhook",
                timestamp=datetime.utcnow().isoformat() + "Z",
                uptime=uptime,
                checks=readiness_checks
            )
        except Exception as e:
            return HealthCheckResponse(
                status="not_ready",
                version=version,
                environment=config.environment,
                service="webhook",
                timestamp=datetime.utcnow().isoformat() + "Z",
                uptime=uptime,
                checks={"error": str(e)}
            )
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return JSONResponse(
            content={
                "service": "WhatsApp Webhook Service",
                "version": version,
                "status": "running",
                "environment": config.environment
            }
        )
    
    app_logger.info(f"FastAPI application created successfully", extra={
        "version": version,
        "environment": config.environment
    })
    
    return app

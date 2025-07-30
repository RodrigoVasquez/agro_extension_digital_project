"""
Pydantic models for API requests and responses.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class WebhookVerificationRequest(BaseModel):
    """Model for webhook verification GET request parameters."""
    
    hub_mode: Optional[str] = Field(None, alias="hub.mode", description="Verification mode")
    hub_verify_token: Optional[str] = Field(None, alias="hub.verify_token", description="Verification token")
    hub_challenge: Optional[str] = Field(None, alias="hub.challenge", description="Challenge string")


class WebhookVerificationResponse(BaseModel):
    """Model for webhook verification response."""
    
    challenge: int = Field(..., description="Challenge number to return")


class WebhookErrorResponse(BaseModel):
    """Model for webhook error responses."""
    
    status: str = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Error message")


class WebhookSuccessResponse(BaseModel):
    """Model for successful webhook responses."""
    
    status: str = Field(default="ok", description="Status of the request")


class WebhookPostRequest(BaseModel):
    """Model for webhook POST request body."""
    
    # Using Dict[str, Any] for flexibility as WhatsApp payload structure can vary
    body: Dict[str, Any] = Field(..., description="WhatsApp webhook payload")


class HealthCheckResponse(BaseModel):
    """Model for health check response."""
    
    status: str = Field(default="healthy", description="Service health status")
    version: str = Field(..., description="Application version")
    environment: Optional[str] = Field(None, description="Current environment")

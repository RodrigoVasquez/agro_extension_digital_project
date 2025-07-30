"""
Domain models for WhatsApp webhook processing using Pydantic v2.
"""

from .messages import (
    WhatsAppTextMessage,
    WhatsAppContact,
    WhatsAppMessageValue,
    WhatsAppChange,
    WhatsAppEntry,
    WhatsAppWebhookPayload,
    AgentMessage,
    AgentMessagePart,
    AgentResponse,
    WhatsAppOutgoingMessage,
    WhatsAppTextBody
)

from .api_models import (
    WebhookVerificationRequest,
    WebhookVerificationResponse,
    WebhookErrorResponse,
    WebhookSuccessResponse,
    WebhookPostRequest,
    HealthCheckResponse
)

__all__ = [
    # Domain models
    "WhatsAppTextMessage",
    "WhatsAppContact", 
    "WhatsAppMessageValue",
    "WhatsAppChange",
    "WhatsAppEntry",
    "WhatsAppWebhookPayload",
    "AgentMessage",
    "AgentMessagePart",
    "AgentResponse",
    "WhatsAppOutgoingMessage",
    "WhatsAppTextBody",
    # API models
    "WebhookVerificationRequest",
    "WebhookVerificationResponse",
    "WebhookErrorResponse",
    "WebhookSuccessResponse",
    "WebhookPostRequest",
    "HealthCheckResponse"
]
"""
Domain models for WhatsApp webhook processing using Pydantic v2.
Now supports all WhatsApp message types.
"""

from .messages import (
    # Main message models
    WhatsAppMessage,
    WhatsAppContact,
    WhatsAppMessageValue,
    WhatsAppChange,
    WhatsAppEntry,
    WhatsAppWebhookPayload,
    
    # Content type models
    WhatsAppTextContent,
    WhatsAppMediaContent,
    WhatsAppImageContent,
    WhatsAppAudioContent,
    WhatsAppVideoContent,
    WhatsAppDocumentContent,
    WhatsAppStickerContent,
    WhatsAppLocationContent,
    WhatsAppContactsContent,
    WhatsAppInteractiveContent,
    WhatsAppReactionContent,
    WhatsAppSystemContent,
    
    # Agent communication models
    AgentMessage,
    AgentMessagePart,
    AgentResponse,
    AgentRequestPayload,
    
    # Outgoing message models
    WhatsAppOutgoingMessage,
    WhatsAppOutgoingTextBody,
    
    # Processing context models
    MessageProcessingContext
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
    # Main message models
    "WhatsAppMessage",
    "WhatsAppContact", 
    "WhatsAppMessageValue",
    "WhatsAppChange",
    "WhatsAppEntry",
    "WhatsAppWebhookPayload",
    
    # Content type models
    "WhatsAppTextContent",
    "WhatsAppMediaContent",
    "WhatsAppImageContent",
    "WhatsAppAudioContent",
    "WhatsAppVideoContent",
    "WhatsAppDocumentContent",
    "WhatsAppStickerContent",
    "WhatsAppLocationContent",
    "WhatsAppContactsContent",
    "WhatsAppInteractiveContent",
    "WhatsAppReactionContent",
    "WhatsAppSystemContent",
    
    # Agent communication models
    "AgentMessage",
    "AgentMessagePart",
    "AgentResponse",
    "AgentRequestPayload",
    
    # Outgoing message models
    "WhatsAppOutgoingMessage",
    "WhatsAppOutgoingTextBody",
    
    # Processing context models
    "MessageProcessingContext",
    
    # API models
    "WebhookVerificationRequest",
    "WebhookVerificationResponse",
    "WebhookErrorResponse",
    "WebhookSuccessResponse",
    "WebhookPostRequest",
    "HealthCheckResponse"
]
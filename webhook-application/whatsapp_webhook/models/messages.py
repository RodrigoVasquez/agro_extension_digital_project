"""
Pydantic v2 models for WhatsApp webhook message processing.

These domain models provide type safety, validation, and clear structure
for handling WhatsApp webhook payloads, agent communications, and outgoing messages.
"""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


class WhatsAppTextBody(BaseModel):
    """Text content of a WhatsApp message."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    body: str = Field(..., min_length=1, max_length=4096, description="Message text content")


class WhatsAppTextMessage(BaseModel):
    """Represents a text message from WhatsApp webhook."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    id: str = Field(..., min_length=1, description="Unique message ID")
    type: Literal["text"] = Field(default="text", description="Message type")
    timestamp: str = Field(..., description="Message timestamp")
    text: WhatsAppTextBody = Field(..., description="Text content")
    from_: str = Field(..., alias="from", description="Sender phone number")
    
    @field_validator('from_')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format."""
        # Remove any whitespace and ensure it's a valid format
        phone = re.sub(r'\s+', '', v)
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise ValueError('Invalid phone number format')
        return phone


class WhatsAppContact(BaseModel):
    """Contact information from WhatsApp webhook."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    wa_id: str = Field(..., min_length=1, description="WhatsApp ID")
    profile: Optional[Dict[str, Any]] = Field(default=None, description="Profile information")


class WhatsAppMessageValue(BaseModel):
    """Value object containing messages and contacts from webhook."""
    
    model_config = ConfigDict(
        validate_default=True,
        extra="forbid"
    )
    
    messaging_product: Literal["whatsapp"] = Field(default="whatsapp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata information")
    contacts: List[WhatsAppContact] = Field(default_factory=list, description="Contact information")
    messages: List[WhatsAppTextMessage] = Field(default_factory=list, description="List of messages")
    
    @field_validator('contacts')
    @classmethod
    def validate_contacts_not_empty(cls, v: List[WhatsAppContact]) -> List[WhatsAppContact]:
        """Ensure at least one contact is present when messages exist."""
        return v
    
    def get_sender_wa_id(self) -> Optional[str]:
        """Get the sender's WhatsApp ID from contacts."""
        if self.contacts:
            return self.contacts[0].wa_id
        return None


class WhatsAppChange(BaseModel):
    """Change object from WhatsApp webhook."""
    
    model_config = ConfigDict(
        validate_default=True,
        extra="forbid"
    )
    
    field: Literal["messages"] = Field(default="messages", description="Change field type")
    value: WhatsAppMessageValue = Field(..., description="Change value containing messages")


class WhatsAppEntry(BaseModel):
    """Entry object from WhatsApp webhook."""
    
    model_config = ConfigDict(
        validate_default=True,
        extra="forbid"
    )
    
    id: str = Field(..., min_length=1, description="Entry ID")
    changes: List[WhatsAppChange] = Field(default_factory=list, description="List of changes")


class WhatsAppWebhookPayload(BaseModel):
    """Complete WhatsApp webhook payload."""
    
    model_config = ConfigDict(
        validate_default=True,
        extra="forbid"
    )
    
    object: Literal["whatsapp_business_account"] = Field(default="whatsapp_business_account")
    entry: List[WhatsAppEntry] = Field(default_factory=list, description="List of entries")
    
    def get_text_messages(self) -> List[tuple[str, WhatsAppTextMessage]]:
        """
        Extract all text messages with their sender WhatsApp IDs.
        
        Returns:
            List of tuples containing (sender_wa_id, message)
        """
        messages = []
        for entry in self.entry:
            for change in entry.changes:
                if change.field == "messages":
                    sender_wa_id = change.value.get_sender_wa_id()
                    if sender_wa_id:
                        for message in change.value.messages:
                            if message.type == "text":
                                messages.append((sender_wa_id, message))
        return messages


# Agent communication models

class AgentMessagePart(BaseModel):
    """Part of an agent message."""
    
    model_config = ConfigDict(extra="forbid")
    
    text: str = Field(..., min_length=1, description="Text content of the message part")


class AgentMessage(BaseModel):
    """Message structure for agent communication."""
    
    model_config = ConfigDict(extra="forbid")
    
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    parts: List[AgentMessagePart] = Field(..., min_items=1, description="Message parts")


class AgentResponse(BaseModel):
    """Response from the agent service."""
    
    model_config = ConfigDict(extra="ignore")  # Allow extra fields from agent
    
    content: Optional[Dict[str, Any]] = Field(default=None, description="Response content")
    
    def extract_text_response(self) -> Optional[str]:
        """
        Extract text response from agent response structure.
        
        Returns:
            Extracted text or None if not found
        """
        if not self.content:
            return None
            
        parts = self.content.get("parts")
        if not isinstance(parts, list) or not parts:
            return None
            
        first_part = parts[0]
        if isinstance(first_part, dict) and "text" in first_part:
            return first_part["text"].strip()
            
        return None


# Outgoing WhatsApp message models

class WhatsAppOutgoingTextBody(BaseModel):
    """Text body for outgoing WhatsApp message."""
    
    model_config = ConfigDict(extra="forbid")
    
    body: str = Field(..., min_length=1, max_length=4096, description="Message text")


class WhatsAppOutgoingMessage(BaseModel):
    """Outgoing message to WhatsApp API."""
    
    model_config = ConfigDict(extra="forbid")
    
    messaging_product: Literal["whatsapp"] = Field(default="whatsapp")
    recipient_type: Literal["individual"] = Field(default="individual")
    to: str = Field(..., description="Recipient phone number")
    type: Literal["text"] = Field(default="text")
    text: WhatsAppOutgoingTextBody = Field(..., description="Text content")
    
    @field_validator('to')
    @classmethod
    def validate_recipient_phone(cls, v: str) -> str:
        """Validate recipient phone number."""
        # Ensure proper format for WhatsApp API
        phone = v.strip()
        if not phone.startswith('+'):
            phone = f'+{phone}'
        return phone


# Processing context models

class MessageProcessingContext(BaseModel):
    """Context for message processing operations."""
    
    model_config = ConfigDict(extra="forbid")
    
    app_name: str = Field(..., min_length=1, description="Application name")
    user_wa_id: str = Field(..., min_length=1, description="User WhatsApp ID")
    session_id: str = Field(..., min_length=1, description="Session ID")
    whatsapp_api_url: str = Field(..., description="WhatsApp API URL")
    wsp_token: str = Field(..., min_length=1, description="WhatsApp token")
    
    @field_validator('whatsapp_api_url')
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Validate WhatsApp API URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('WhatsApp API URL must start with http:// or https://')
        return v.rstrip('/')


class AgentRequestPayload(BaseModel):
    """Payload for agent service requests."""
    
    model_config = ConfigDict(extra="forbid")
    
    app_name: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1) 
    session_id: str = Field(..., min_length=1)
    new_message: AgentMessage = Field(...)
    streaming: bool = Field(default=False)
    
    @classmethod
    def create_text_request(
        cls,
        app_name: str,
        user_id: str, 
        session_id: str,
        message_text: str,
        streaming: bool = False
    ) -> "AgentRequestPayload":
        """Create a text message request payload."""
        return cls(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            new_message=AgentMessage(
                role="user",
                parts=[AgentMessagePart(text=message_text)]
            ),
            streaming=streaming
        )

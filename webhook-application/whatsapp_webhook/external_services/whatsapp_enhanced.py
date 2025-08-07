"""
Enhanced WhatsApp messaging with typing indicators and UX improvements.
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from .whatsapp_client import send_whatsapp_message, create_text_message
from .whatsapp_actions import TypingContext, send_typing_indicator, mark_message_as_read
from ..utils.app_config import WhatsAppConfig
from ..utils.logging import get_logger


async def send_message_with_typing(
    user_wa_id: str,
    message_text: str,
    whatsapp_config: WhatsAppConfig,
    typing_duration: float = 2.0,
    auto_mark_read: bool = True
) -> bool:
    """
    Send a message with realistic typing indicator timing.
    
    Args:
        user_wa_id: WhatsApp ID of the recipient
        message_text: Text message to send
        whatsapp_config: WhatsApp configuration
        typing_duration: Minimum seconds to show typing indicator
        auto_mark_read: Whether to mark previous messages as read
        
    Returns:
        True if message was sent successfully
    """
    logger = get_logger("enhanced_messaging", {"app_name": whatsapp_config.app_type.value})
    
    if not whatsapp_config.api_url or not whatsapp_config.token:
        logger.error("WhatsApp API URL or token is not configured.")
        return False

    messages_url = f"{whatsapp_config.api_url}/messages"
    
    try:
        # Mark messages as read if requested
        if auto_mark_read:
            await mark_message_as_read(user_wa_id, messages_url, whatsapp_config.token)
            await asyncio.sleep(0.5)  # Small delay between read and typing
        
        # Send typing indicator
        await send_typing_indicator(user_wa_id, messages_url, whatsapp_config.token)
        
        # Calculate realistic typing time based on message length
        # Simulate human typing speed (approximately 40 WPM = 200 characters per minute)
        chars_per_second = 200 / 60  # ~3.33 characters per second
        calculated_time = max(len(message_text) / chars_per_second, typing_duration)
        
        # Cap maximum typing time to avoid too long delays
        typing_time = min(calculated_time, 8.0)
        
        logger.info(f"Typing indicator for {typing_time:.1f}s for message length {len(message_text)}")
        await asyncio.sleep(typing_time)
        
        # Send the actual message (this will stop the typing indicator)
        message = create_text_message(message_text)
        await send_whatsapp_message(user_wa_id, message, messages_url, whatsapp_config.token)
        
        logger.info(f"Message sent successfully to {user_wa_id} with typing UX")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send message with typing to {user_wa_id}: {e}", exc_info=True)
        return False


async def send_multi_message_sequence(
    user_wa_id: str,
    messages: List[str],
    whatsapp_config: WhatsAppConfig,
    delay_between: float = 1.5
) -> int:
    """
    Send multiple messages in sequence with natural timing and typing indicators.
    
    Args:
        user_wa_id: WhatsApp ID of the recipient
        messages: List of message texts to send
        whatsapp_config: WhatsApp configuration
        delay_between: Seconds to wait between messages
        
    Returns:
        Number of messages sent successfully
    """
    logger = get_logger("multi_message", {"app_name": whatsapp_config.app_type.value})
    successful_count = 0
    
    # Mark as read at the beginning
    if whatsapp_config.api_url and whatsapp_config.token:
        messages_url = f"{whatsapp_config.api_url}/messages"
        await mark_message_as_read(user_wa_id, messages_url, whatsapp_config.token)
    
    for i, message_text in enumerate(messages):
        try:
            # First message has minimal typing, subsequent messages have natural delays
            typing_duration = 1.0 if i == 0 else delay_between
            
            success = await send_message_with_typing(
                user_wa_id=user_wa_id,
                message_text=message_text,
                whatsapp_config=whatsapp_config,
                typing_duration=typing_duration,
                auto_mark_read=False  # Already marked read above
            )
            
            if success:
                successful_count += 1
                logger.info(f"Sent message {i+1}/{len(messages)} to {user_wa_id}")
            else:
                logger.error(f"Failed to send message {i+1}/{len(messages)} to {user_wa_id}")
                
            # Delay between messages (except for the last one)
            if i < len(messages) - 1:
                await asyncio.sleep(delay_between)
                
        except Exception as e:
            logger.error(f"Error sending message {i+1} to {user_wa_id}: {e}", exc_info=True)
    
    logger.info(f"Multi-message sequence completed: {successful_count}/{len(messages)} sent to {user_wa_id}")
    return successful_count


class ConversationManager:
    """
    Manager for handling conversation flow with enhanced UX features.
    """
    
    def __init__(self, whatsapp_config: WhatsAppConfig):
        self.whatsapp_config = whatsapp_config
        self.logger = get_logger("conversation_manager", {"app_name": whatsapp_config.app_type.value})
    
    async def send_thinking_message(
        self,
        user_wa_id: str,
        thinking_text: str = "Analizando tu consulta... 🤔"
    ) -> bool:
        """
        Send a quick thinking message while processing a complex request.
        """
        return await send_message_with_typing(
            user_wa_id=user_wa_id,
            message_text=thinking_text,
            whatsapp_config=self.whatsapp_config,
            typing_duration=0.8,
            auto_mark_read=True
        )
    
    async def send_agent_response_with_ux(
        self,
        user_wa_id: str,
        agent_response: str,
        show_thinking: bool = True
    ) -> bool:
        """
        Send agent response with enhanced UX including thinking indicator for long responses.
        """
        try:
            # For long responses, show thinking message first
            if show_thinking and len(agent_response) > 200:
                await self.send_thinking_message(user_wa_id)
                await asyncio.sleep(1.0)
            
            # Split very long messages into smaller chunks
            if len(agent_response) > 1500:
                # Split into chunks at sentence boundaries
                chunks = self._split_message_intelligently(agent_response)
                return await send_multi_message_sequence(
                    user_wa_id=user_wa_id,
                    messages=chunks,
                    whatsapp_config=self.whatsapp_config
                ) == len(chunks)
            else:
                # Send as single message with typing
                return await send_message_with_typing(
                    user_wa_id=user_wa_id,
                    message_text=agent_response,
                    whatsapp_config=self.whatsapp_config,
                    auto_mark_read=not show_thinking  # Don't mark read again if we already showed thinking
                )
                
        except Exception as e:
            self.logger.error(f"Error sending agent response to {user_wa_id}: {e}", exc_info=True)
            return False
    
    def _split_message_intelligently(self, text: str, max_length: int = 1500) -> List[str]:
        """
        Split a long message into smaller chunks at natural breakpoints.
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences first
        sentences = text.replace('. ', '.\n').replace('? ', '?\n').replace('! ', '!\n').split('\n')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed limit, start new chunk
            if current_chunk and len(current_chunk) + len(sentence) + 2 > max_length:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

"""Tests for audio processing functionality."""
import pytest
import asyncio
import io
from unittest.mock import patch, AsyncMock, MagicMock
from whatsapp_webhook.transcription import transcribe_audio_file
from whatsapp_webhook.external_services.whatsapp_client import download_media
from whatsapp_webhook.messages import handle_audio_message


class TestAudioProcessing:
    """Test suite for audio processing functionality."""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_with_mock_speech(self):
        """Test audio transcription with mocked Google Cloud Speech."""
        # Mock audio content (simulating OGG_OPUS)
        mock_audio_content = b"fake_ogg_opus_audio_data"
        
        # Mock Google Cloud Speech response
        mock_result = MagicMock()
        mock_result.alternatives = [MagicMock()]
        mock_result.alternatives[0].transcript = "Hola mundo"
        
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        
        # Mock the Speech client
        with patch('whatsapp_webhook.transcription.speech.SpeechClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.recognize.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            # Test transcription
            result = await transcribe_audio_file(mock_audio_content)
            
            # Assertions
            assert result == "Hola mundo"
            mock_client.recognize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_no_results(self):
        """Test audio transcription when no results are returned."""
        mock_audio_content = b"fake_audio_data"
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.results = []
        
        with patch('whatsapp_webhook.transcription.speech.SpeechClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.recognize.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            result = await transcribe_audio_file(mock_audio_content)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_download_media_success(self):
        """Test successful media download."""
        media_id = "test_media_id"
        whatsapp_api_url = "https://graph.facebook.com/v17.0"
        token = "test_token"
        
        # Mock responses
        media_url_response = {
            "url": "https://example.com/media/audio.ogg",
            "mime_type": "audio/ogg; codecs=opus"
        }
        
        audio_content = b"fake_audio_content"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            # Create mock client instance
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Mock the two HTTP calls
            mock_url_response = AsyncMock()
            mock_url_response.raise_for_status.return_value = None
            mock_url_response.json.return_value = media_url_response
            
            mock_content_response = AsyncMock()
            mock_content_response.raise_for_status.return_value = None
            mock_content_response.content = audio_content
            
            # Configure mock to return different responses for different calls
            mock_client.get.side_effect = [mock_url_response, mock_content_response]
            
            result = await download_media(media_id, whatsapp_api_url, token)
            
            assert result == audio_content
            assert mock_client.get.call_count == 2
    
    @pytest.mark.asyncio
    async def test_download_media_no_url(self):
        """Test media download when URL is not in response."""
        media_id = "test_media_id"
        whatsapp_api_url = "https://graph.facebook.com/v17.0"
        token = "test_token"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = AsyncMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {}  # No URL in response
            
            mock_client.get.return_value = mock_response
            
            result = await download_media(media_id, whatsapp_api_url, token)
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_full_flow(self):
        """Test complete audio message handling flow."""
        phone = "+56912345678"
        audio_id = "test_audio_id"
        app_name = "AA"
        session_id = "test_session"
        
        # Mock all external dependencies
        with patch('whatsapp_webhook.external_services.whatsapp_client.download_media') as mock_download, \
             patch('whatsapp_webhook.transcription.transcribe_audio_file') as mock_transcribe, \
             patch('whatsapp_webhook.messages.send_message') as mock_send_message, \
             patch('whatsapp_webhook.external_services.whatsapp_client.send_whatsapp_message') as mock_send_whatsapp, \
             patch('whatsapp_webhook.external_services.whatsapp_client.create_text_message') as mock_create_text, \
             patch('whatsapp_webhook.utils.config.get_whatsapp_config') as mock_get_config:
            
            # Configure mocks
            mock_download.return_value = b"fake_audio_content"
            mock_transcribe.return_value = "Hola mundo"
            mock_send_message.return_value = "¡Hola! ¿En qué puedo ayudarte?"
            mock_create_text.return_value = {"type": "text", "text": {"body": "¡Hola! ¿En qué puedo ayudarte?"}}
            mock_get_config.return_value = {
                "api_url": "https://graph.facebook.com/v17.0/test",
                "token": "test_token"
            }
            mock_send_whatsapp.return_value = None
            
            # Execute function
            await handle_audio_message(phone, audio_id, app_name, session_id)
            
            # Verify the flow
            mock_download.assert_called_once_with(
                audio_id, 
                "https://graph.facebook.com/v17.0/test", 
                "test_token"
            )
            mock_transcribe.assert_called_once_with(b"fake_audio_content")
            mock_send_message.assert_called_once_with(
                phone, app_name, session_id, "Hola mundo"
            )
            mock_send_whatsapp.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_download_fails(self):
        """Test audio handling when download fails."""
        phone = "+56912345678"
        audio_id = "test_audio_id"
        app_name = "AA"
        session_id = "test_session"
        
        with patch('whatsapp_webhook.external_services.whatsapp_client.download_media') as mock_download, \
             patch('whatsapp_webhook.external_services.whatsapp_client.send_whatsapp_message') as mock_send_whatsapp, \
             patch('whatsapp_webhook.external_services.whatsapp_client.create_text_message') as mock_create_text, \
             patch('whatsapp_webhook.utils.config.get_whatsapp_config') as mock_get_config:
            
            # Configure mocks
            mock_download.return_value = None  # Download fails
            mock_create_text.return_value = {"type": "text", "text": {"body": "No pude descargar tu audio."}}
            mock_get_config.return_value = {
                "api_url": "https://graph.facebook.com/v17.0/test",
                "token": "test_token"
            }
            mock_send_whatsapp.return_value = None
            
            # Execute function
            await handle_audio_message(phone, audio_id, app_name, session_id)
            
            # Verify error handling
            mock_download.assert_called_once()
            mock_send_whatsapp.assert_called_once()
            # Should send error message
            call_args = mock_send_whatsapp.call_args
            assert "No pude descargar tu audio." in str(call_args)
    
    @pytest.mark.asyncio
    async def test_handle_audio_message_transcription_fails(self):
        """Test audio handling when transcription fails."""
        phone = "+56912345678"
        audio_id = "test_audio_id"
        app_name = "AA"
        session_id = "test_session"
        
        with patch('whatsapp_webhook.external_services.whatsapp_client.download_media') as mock_download, \
             patch('whatsapp_webhook.transcription.transcribe_audio_file') as mock_transcribe, \
             patch('whatsapp_webhook.external_services.whatsapp_client.send_whatsapp_message') as mock_send_whatsapp, \
             patch('whatsapp_webhook.external_services.whatsapp_client.create_text_message') as mock_create_text, \
             patch('whatsapp_webhook.utils.config.get_whatsapp_config') as mock_get_config:
            
            # Configure mocks
            mock_download.return_value = b"fake_audio_content"
            mock_transcribe.return_value = None  # Transcription fails
            mock_create_text.return_value = {"type": "text", "text": {"body": "No pude entender tu audio."}}
            mock_get_config.return_value = {
                "api_url": "https://graph.facebook.com/v17.0/test",
                "token": "test_token"
            }
            mock_send_whatsapp.return_value = None
            
            # Execute function
            await handle_audio_message(phone, audio_id, app_name, session_id)
            
            # Verify error handling
            mock_download.assert_called_once()
            mock_transcribe.assert_called_once()
            mock_send_whatsapp.assert_called_once()
            # Should send error message about transcription
            call_args = mock_send_whatsapp.call_args
            assert "No pude entender tu audio." in str(call_args)


@pytest.mark.asyncio
async def test_integration_audio_processing():
    """Integration test for the complete audio processing pipeline."""
    # This test simulates a real audio processing scenario
    # but with mocked external services
    
    phone = "+56987654321"
    audio_id = "ABEGkYaYGDMREAGQ6YhWWZaYOCmSqmT6"
    app_name = "AA"
    session_id = "session_123"
    
    with patch('whatsapp_webhook.external_services.whatsapp_client.download_media') as mock_download, \
         patch('whatsapp_webhook.transcription.speech.SpeechClient') as mock_speech_client, \
         patch('whatsapp_webhook.messages.send_message') as mock_agent, \
         patch('whatsapp_webhook.external_services.whatsapp_client.send_whatsapp_message') as mock_send, \
         patch('whatsapp_webhook.utils.config.get_whatsapp_config') as mock_config:
        
        # Simulate audio download
        mock_download.return_value = b"simulated_ogg_opus_audio_data"
        
        # Simulate Speech-to-Text response
        mock_result = MagicMock()
        mock_result.alternatives = [MagicMock()]
        mock_result.alternatives[0].transcript = "Hola mundo, ¿cómo estás?"
        
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        
        mock_client = MagicMock()
        mock_client.recognize.return_value = mock_response
        mock_speech_client.return_value = mock_client
        
        # Simulate agent response
        mock_agent.return_value = "¡Hola! Estoy muy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?"
        
        # Simulate WhatsApp config
        mock_config.return_value = {
            "api_url": "https://graph.facebook.com/v17.0/123456789",
            "token": "EAAG1234567890"
        }
        
        # Execute the full flow
        from whatsapp_webhook.messages import handle_audio_message
        await handle_audio_message(phone, audio_id, app_name, session_id)
        
        # Verify the complete flow executed
        mock_download.assert_called_once_with(
            audio_id,
            "https://graph.facebook.com/v17.0/123456789", 
            "EAAG1234567890"
        )
        
        mock_client.recognize.assert_called_once()
        
        mock_agent.assert_called_once_with(
            phone, app_name, session_id, "Hola mundo, ¿cómo estás?"
        )
        
        mock_send.assert_called_once()
        
        print("✅ Integration test passed - Audio processing pipeline works!")


if __name__ == "__main__":
    # Run a simple test to verify the module works
    asyncio.run(test_integration_audio_processing())

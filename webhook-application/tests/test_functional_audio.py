"""
Simple functional test script to verify audio processing works.
This can be run independently to test the audio functionality.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set minimal environment
os.environ.setdefault("APP_URL", "https://test-agent.example.com")
os.environ.setdefault("ESTANDAR_AA_APP_NAME", "test_aa")
os.environ.setdefault("WSP_TOKEN", "test_token")


async def test_audio_flow():
    """Test the complete audio processing flow with mocks."""
    print("🎵 Testing Audio Processing Flow...")
    
    # Import here after setting up environment
    from unittest.mock import patch, MagicMock, AsyncMock
    
    phone = "+56912345678"
    audio_id = "test_audio_123"
    app_name = "AA"
    session_id = "test_session_456"
    
    print(f"📱 Phone: {phone}")
    print(f"🎤 Audio ID: {audio_id}")
    print(f"📱 App: {app_name}")
    
    # Mock all external services
    with patch('whatsapp_webhook.external_services.whatsapp_client.download_media') as mock_download, \
         patch('whatsapp_webhook.transcription.speech.SpeechClient') as mock_speech, \
         patch('whatsapp_webhook.messages.send_message') as mock_agent, \
         patch('whatsapp_webhook.external_services.whatsapp_client.send_whatsapp_message') as mock_send, \
         patch('whatsapp_webhook.utils.config.get_whatsapp_config') as mock_config:
        
        # 1. Mock audio download
        print("⬇️  Mocking audio download...")
        mock_download.return_value = b"fake_ogg_opus_audio_data_hello_world"
        
        # 2. Mock Speech-to-Text
        print("🗣️  Mocking Google Cloud Speech...")
        mock_result = MagicMock()
        mock_result.alternatives = [MagicMock()]
        mock_result.alternatives[0].transcript = "Hola mundo"
        
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        
        mock_client = MagicMock()
        mock_client.recognize.return_value = mock_response
        mock_speech.return_value = mock_client
        
        # 3. Mock agent response
        print("🤖 Mocking agent response...")
        mock_agent.return_value = "¡Hola! Recibí tu mensaje de audio que dice 'Hola mundo'. ¿En qué más puedo ayudarte?"
        
        # 4. Mock WhatsApp configuration
        print("⚙️  Mocking WhatsApp config...")
        mock_config.return_value = {
            "api_url": "https://graph.facebook.com/v17.0/123456789",
            "token": "EAAG_test_token_123"
        }
        
        # 5. Mock WhatsApp message sending
        mock_send.return_value = None
        
        print("\n🚀 Executing audio message handler...")
        
        # Execute the function
        from whatsapp_webhook.messages import handle_audio_message
        await handle_audio_message(phone, audio_id, app_name, session_id)
        
        print("\n✅ Verifying the flow...")
        
        # Verify each step was called
        assert mock_download.called, "❌ Audio download was not called"
        print("✅ Audio download: OK")
        
        assert mock_client.recognize.called, "❌ Speech recognition was not called"
        print("✅ Speech recognition: OK")
        
        assert mock_agent.called, "❌ Agent was not called"
        print("✅ Agent processing: OK")
        
        assert mock_send.called, "❌ WhatsApp send was not called"
        print("✅ WhatsApp response: OK")
        
        # Check the actual calls
        download_call = mock_download.call_args
        agent_call = mock_agent.call_args
        
        print(f"\n📋 Call Details:")
        print(f"   Download called with: audio_id={audio_id}")
        print(f"   Agent called with transcript: 'Hola mundo'")
        print(f"   Agent response: '{mock_agent.return_value[:50]}...'")
        
        print("\n🎉 SUCCESS! Audio processing flow works correctly!")
        return True


async def test_transcription_only():
    """Test just the transcription function."""
    print("\n🎵 Testing Transcription Function...")
    
    from unittest.mock import patch, MagicMock
    
    # Mock audio content
    fake_audio = b"fake_ogg_opus_data_hola_mundo"
    
    with patch('whatsapp_webhook.transcription.speech.SpeechClient') as mock_speech:
        # Setup mock
        mock_result = MagicMock()
        mock_result.alternatives = [MagicMock()]
        mock_result.alternatives[0].transcript = "Hola mundo desde el test"
        
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        
        mock_client = MagicMock()
        mock_client.recognize.return_value = mock_response
        mock_speech.return_value = mock_client
        
        # Test transcription
        from whatsapp_webhook.transcription import transcribe_audio_file
        result = await transcribe_audio_file(fake_audio)
        
        print(f"📝 Transcription result: '{result}'")
        assert result == "Hola mundo desde el test"
        print("✅ Transcription test: OK")


async def main():
    """Run all functional tests."""
    print("🧪 Starting Functional Tests for Audio Processing\n")
    
    try:
        # Test 1: Transcription only
        await test_transcription_only()
        
        # Test 2: Full flow
        await test_audio_flow()
        
        print("\n🎊 ALL TESTS PASSED! Audio processing is working correctly.")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

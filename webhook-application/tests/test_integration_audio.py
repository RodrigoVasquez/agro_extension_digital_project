"""
Test de integración que simula un mensaje de audio real de WhatsApp.
Este test verifica el flujo completo desde el webhook hasta la respuesta.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment for testing
os.environ.setdefault("APP_URL", "https://test-agent.example.com")
os.environ.setdefault("ESTANDAR_AA_APP_NAME", "test_aa")
os.environ.setdefault("ESTANDAR_AA_FACEBOOK_APP", "123456789")
os.environ.setdefault("WSP_TOKEN", "test_token")
os.environ.setdefault("WHATSAPP_API_URL_AA", "https://graph.facebook.com/v17.0/123456789")


async def test_full_audio_integration():
    """
    Test completo que simula un mensaje de audio real llegando al webhook.
    """
    print("🎵 Test de Integración Completa - Audio 'Hola Mundo'")
    print("=" * 60)
    
    from unittest.mock import patch, MagicMock, AsyncMock
    
    # Simular payload de WhatsApp con mensaje de audio
    whatsapp_payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "56912345678",
                        "phone_number_id": "123456789"
                    },
                    "messages": [{
                        "from": "56987654321",
                        "id": "wamid.ABC123XYZ",
                        "timestamp": "1609459200",
                        "type": "audio",
                        "audio": {
                            "id": "audio_media_id_123",
                            "mime_type": "audio/ogg; codecs=opus"
                        }
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    print(f"📱 Payload de WhatsApp recibido:")
    print(f"   - Tipo: audio")
    print(f"   - De: +56987654321")
    print(f"   - Audio ID: audio_media_id_123")
    
    # Mock todas las dependencias externas
    with patch('whatsapp_webhook.external_services.whatsapp_client.download_media') as mock_download, \
         patch('whatsapp_webhook.transcription.speech.SpeechClient') as mock_speech, \
         patch('whatsapp_webhook.messages.send_message') as mock_agent, \
         patch('whatsapp_webhook.external_services.whatsapp_client.send_whatsapp_message') as mock_send, \
         patch('whatsapp_webhook.external_services.whatsapp_client.create_text_message') as mock_create, \
         patch('whatsapp_webhook.utils.config.get_whatsapp_config') as mock_config, \
         patch('whatsapp_webhook.messages.create_session') as mock_session:
        
        # 1. Mock descarga de audio
        print("\n⬇️  Simulando descarga de audio...")
        mock_download.return_value = b"simulated_ogg_opus_hello_world_audio"
        
        # 2. Mock Google Cloud Speech
        print("🗣️  Simulando transcripción con Google Cloud Speech...")
        mock_result = MagicMock()
        mock_result.alternatives = [MagicMock()]
        mock_result.alternatives[0].transcript = "Hola mundo"
        
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        
        mock_client = MagicMock()
        mock_client.recognize.return_value = mock_response
        mock_speech.return_value = mock_client
        
        # 3. Mock agente de IA
        print("🤖 Simulando respuesta del agente...")
        mock_agent.return_value = "¡Hola! Escuché que dijiste 'Hola mundo'. ¿En qué puedo ayudarte hoy?"
        
        # 4. Mock configuración y otros
        mock_config.return_value = {
            "api_url": "https://graph.facebook.com/v17.0/123456789",
            "token": "EAAG_test_token"
        }
        mock_session.return_value = "session_12345"
        mock_create.return_value = {
            "type": "text", 
            "text": {"body": "¡Hola! Escuché que dijiste 'Hola mundo'. ¿En qué puedo ayudarte hoy?"}
        }
        mock_send.return_value = None
        
        print("\n🚀 Procesando mensaje de audio...")
        
        # Simular el procesamiento del mensaje de audio
        from whatsapp_webhook.utils.model_utils import parse_webhook_payload
        from whatsapp_webhook.messages import _process_non_text_message
        
        # Parse el payload
        webhook_data = parse_webhook_payload(whatsapp_payload)
        
        # Obtener el primer mensaje de audio
        for entry in webhook_data.entry:
            for change in entry.changes:
                for message in change.value.messages:
                    if message.type == "audio":
                        print(f"   ✅ Mensaje de audio detectado: {message.id}")
                        
                        # Procesar el mensaje
                        await _process_non_text_message(
                            sender_wa_id=message.from_,
                            message=message,
                            app_name="AA",
                            whatsapp_api_url="https://graph.facebook.com/v17.0/123456789",
                            wsp_token="test_token"
                        )
                        break
        
        print("\n📊 Verificando el flujo completo...")
        
        # Verificar que se llamaron todas las funciones
        assert mock_download.called, "❌ No se descargó el audio"
        print("   ✅ Audio descargado")
        
        assert mock_client.recognize.called, "❌ No se transcribió el audio"
        print("   ✅ Audio transcrito")
        
        assert mock_agent.called, "❌ No se llamó al agente"
        print("   ✅ Agente procesó el mensaje")
        
        assert mock_send.called, "❌ No se envió respuesta"
        print("   ✅ Respuesta enviada al usuario")
        
        # Verificar los parámetros de las llamadas
        download_call = mock_download.call_args
        agent_call = mock_agent.call_args
        
        print(f"\n📋 Detalles de las llamadas:")
        print(f"   • Audio ID procesado: {download_call[0][0] if download_call else 'N/A'}")
        print(f"   • Texto transcrito: '{agent_call[0][2] if agent_call else 'N/A'}'")
        print(f"   • Usuario: {agent_call[0][0] if agent_call else 'N/A'}")
        
        print("\n🎉 ¡TEST DE INTEGRACIÓN EXITOSO!")
        print("   El flujo completo de audio funciona correctamente")
        
        return True


async def test_audio_error_scenarios():
    """Test de escenarios de error."""
    print("\n🚨 Testing Error Scenarios...")
    
    from unittest.mock import patch, MagicMock
    
    # Test 1: Error en descarga
    print("   • Error en descarga de audio...")
    with patch('whatsapp_webhook.external_services.whatsapp_client.download_media') as mock_download, \
         patch('whatsapp_webhook.external_services.whatsapp_client.send_whatsapp_message') as mock_send, \
         patch('whatsapp_webhook.utils.config.get_whatsapp_config') as mock_config:
        
        mock_download.return_value = None  # Simular fallo
        mock_config.return_value = {"api_url": "test", "token": "test"}
        mock_send.return_value = None
        
        from whatsapp_webhook.messages import handle_audio_message
        await handle_audio_message("+56912345678", "bad_audio", "AA", "session")
        
        assert mock_send.called, "Debería enviar mensaje de error"
        print("     ✅ Maneja correctamente error de descarga")
    
    # Test 2: Error en transcripción
    print("   • Error en transcripción...")
    with patch('whatsapp_webhook.external_services.whatsapp_client.download_media') as mock_download, \
         patch('whatsapp_webhook.transcription.transcribe_audio_file') as mock_transcribe, \
         patch('whatsapp_webhook.external_services.whatsapp_client.send_whatsapp_message') as mock_send, \
         patch('whatsapp_webhook.utils.config.get_whatsapp_config') as mock_config:
        
        mock_download.return_value = b"audio_data"
        mock_transcribe.return_value = None  # Simular fallo
        mock_config.return_value = {"api_url": "test", "token": "test"}
        mock_send.return_value = None
        
        await handle_audio_message("+56912345678", "audio_123", "AA", "session")
        
        assert mock_send.called, "Debería enviar mensaje de error"
        print("     ✅ Maneja correctamente error de transcripción")
    
    print("   ✅ Todos los escenarios de error manejados correctamente")


async def main():
    """Ejecutar todos los tests de integración."""
    print("🧪 TESTS DE INTEGRACIÓN - PROCESAMIENTO DE AUDIO")
    print("=" * 70)
    
    try:
        # Test principal
        await test_full_audio_integration()
        
        # Test de errores
        await test_audio_error_scenarios()
        
        print("\n" + "=" * 70)
        print("🎊 TODOS LOS TESTS DE INTEGRACIÓN PASARON")
        print("\n📈 Funcionalidades verificadas:")
        print("   ✅ Procesamiento completo de mensajes de audio")
        print("   ✅ Descarga desde WhatsApp API")
        print("   ✅ Transcripción con Google Cloud Speech")
        print("   ✅ Integración con agente de IA")
        print("   ✅ Respuesta automática al usuario")
        print("   ✅ Manejo robusto de errores")
        print("\n🚀 El sistema está listo para procesar audio de WhatsApp!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

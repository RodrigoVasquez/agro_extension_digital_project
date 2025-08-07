"""Transcripción de audio usando Google Cloud Speech."""
import logging
from typing import Optional
from google.cloud import speech

logger = logging.getLogger(__name__)

async def transcribe_audio_file(audio_content: bytes) -> Optional[str]:
    """Transcribe audio OGG_OPUS de WhatsApp."""
    try:
        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            sample_rate_hertz=16000,
            language_code="es-CL"
        )
        audio = speech.RecognitionAudio(content=audio_content)
        response = client.recognize(config=config, audio=audio)
        
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            logger.info(f"Successfully transcribed audio: {transcript[:50]}...")
            return transcript.strip()
        
        logger.warning("Audio transcription returned no results.")
        return None
    except Exception as e:
        logger.error(f"Error during audio transcription: {e}", exc_info=True)
        return None

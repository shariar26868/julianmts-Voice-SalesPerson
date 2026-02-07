import asyncio
from openai import AsyncOpenAI
from app.config.settings import settings
import base64
import io

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class WhisperService:
    """Handle real-time speech-to-text using OpenAI Whisper"""
    
    def __init__(self):
        self.model = "whisper-1"
    
    async def transcribe_audio(self, audio_bytes: bytes, language: str = "en") -> str:
        """
        Transcribe audio to text using Whisper
        
        Args:
            audio_bytes: Audio data in bytes (MP3, WAV, etc.)
            language: Language code (default: en)
            
        Returns:
            Transcribed text
        """
        
        try:
            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.mp3"  # Whisper needs a filename
            
            # Transcribe using Whisper
            transcript = await client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                response_format="text"
            )
            
            return transcript.strip()
            
        except Exception as e:
            print(f"Error in Whisper transcription: {e}")
            raise
    
    async def transcribe_audio_stream(self, audio_chunks: list) -> str:
        """
        Transcribe multiple audio chunks (for streaming)
        
        Args:
            audio_chunks: List of audio byte chunks
            
        Returns:
            Complete transcription
        """
        
        try:
            # Combine all chunks
            combined_audio = b''.join(audio_chunks)
            
            # Transcribe combined audio
            return await self.transcribe_audio(combined_audio)
            
        except Exception as e:
            print(f"Error in streaming transcription: {e}")
            raise


# Singleton instance
whisper_service = WhisperService()
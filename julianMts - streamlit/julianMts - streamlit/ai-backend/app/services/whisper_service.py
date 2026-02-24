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
            if not audio_bytes or len(audio_bytes) == 0:
                print("⚠️ Empty audio bytes received")
                return ""
            
            print(f"📝 Transcribing {len(audio_bytes)} bytes of audio...")
            
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.webm"
            
            print(f"🔄 Calling Whisper API...")
            
            transcript = await asyncio.wait_for(
                client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=language,
                    response_format="text"
                ),
                timeout=30.0
            )
            
            result = transcript.strip() if transcript else ""
            print(f"✅ Transcription successful: '{result}'")
            
            return result
            
        except asyncio.TimeoutError:
            print(f"❌ Whisper API timeout (30s)")
            raise Exception("Transcription timeout - audio might be too long or API is slow")
        except Exception as e:
            print(f"❌ Error in Whisper transcription: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def transcribe_audio_stream(self, audio_chunks: list) -> str:
        """
        Transcribe multiple audio chunks (for streaming)
        
        Args:
            audio_chunks: List of audio bytes chunks (from audio_stream_service)
            
        Returns:
            Complete transcription
        """
        
        try:
            if not audio_chunks or len(audio_chunks) == 0:
                print("⚠️ No audio chunks to transcribe")
                return ""
            
            print(f"🎙️ Processing {len(audio_chunks)} audio chunks...")
            print(f"🔍 First chunk type: {type(audio_chunks[0])}")
            print(f"🔍 First chunk size: {len(audio_chunks[0])} bytes")
            
            combined_audio = b''.join(audio_chunks)
            
            print(f"📦 Combined audio size: {len(combined_audio)} bytes")
            
            if len(combined_audio) < 100:
                print("⚠️ Audio too short, might be invalid")
                return "Sorry, the audio was too short."
            
            return await self.transcribe_audio(combined_audio)
            
        except Exception as e:
            print(f"❌ Error in streaming transcription: {e}")
            import traceback
            traceback.print_exc()
            raise


whisper_service = WhisperService()
import asyncio
from openai import AsyncOpenAI
from app.config.settings import settings
import base64
import io

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# Minimum combined audio size to attempt transcription.
# Audio below this threshold is too short to contain real speech and Whisper
# is known to hallucinate common filler phrases on near-silent input.
# ~0.25 seconds of audio at typical WebM/Opus bitrates.
MIN_AUDIO_BYTES = 4000

# Known phrases that Whisper hallucinates on near-silent or very short audio.
# Normalized to lowercase for comparison.
HALLUCINATION_PATTERNS = {
    "thank you", "thanks", "bye", "goodbye",
    "you too", "see you", "okay", "ok",
    "sure", "alright", "uh", "um", "hmm",
    "you", "the", "a", "i",
}


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
            
            # Pre-call guard: skip Whisper on audio that is too short to contain
            # real speech. The old < 100 threshold was far too low and allowed
            # near-silent audio through, causing Whisper hallucinations.
            if len(combined_audio) < MIN_AUDIO_BYTES:
                print(f"⚠️ Audio below minimum threshold ({len(combined_audio)} < {MIN_AUDIO_BYTES} bytes), skipping Whisper")
                return ""

            result = await self.transcribe_audio(combined_audio)

            # Post-call hallucination filter: discard known filler phrases that
            # Whisper produces on near-silent audio above the byte threshold.
            # Strip trailing punctuation before comparing against the pattern set.
            normalized = result.lower().strip().rstrip(".,!?")
            if normalized in HALLUCINATION_PATTERNS or (
                len(normalized.split()) <= 1 and len(normalized) < 10
            ):
                print(f"⚠️ Hallucination detected, discarding: '{result}'")
                return ""

            return result
            
        except Exception as e:
            print(f"❌ Error in streaming transcription: {e}")
            import traceback
            traceback.print_exc()
            raise


whisper_service = WhisperService()
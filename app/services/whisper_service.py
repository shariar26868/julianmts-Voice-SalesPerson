# import asyncio
# from openai import AsyncOpenAI
# from app.config.settings import settings
# import base64
# import io

# client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


# class WhisperService:
#     """Handle real-time speech-to-text using OpenAI Whisper"""
    
#     def __init__(self):
#         self.model = "whisper-1"
    
#     async def transcribe_audio(self, audio_bytes: bytes, language: str = "en") -> str:
#         """
#         Transcribe audio to text using Whisper
        
#         Args:
#             audio_bytes: Audio data in bytes (MP3, WAV, etc.)
#             language: Language code (default: en)
            
#         Returns:
#             Transcribed text
#         """
        
#         try:
#             if not audio_bytes or len(audio_bytes) == 0:
#                 print("⚠️ Empty audio bytes received")
#                 return ""
            
#             print(f"📝 Transcribing {len(audio_bytes)} bytes of audio...")
            
#             audio_file = io.BytesIO(audio_bytes)
#             audio_file.name = "audio.webm"
            
#             print(f"🔄 Calling Whisper API...")
            
#             transcript = await asyncio.wait_for(
#                 client.audio.transcriptions.create(
#                     model=self.model,
#                     file=audio_file,
#                     language=language,
#                     response_format="text"
#                 ),
#                 timeout=30.0
#             )
            
#             result = transcript.strip() if transcript else ""
#             print(f"✅ Transcription successful: '{result}'")
            
#             return result
            
#         except asyncio.TimeoutError:
#             print(f"❌ Whisper API timeout (30s)")
#             raise Exception("Transcription timeout - audio might be too long or API is slow")
#         except Exception as e:
#             print(f"❌ Error in Whisper transcription: {e}")
#             import traceback
#             traceback.print_exc()
#             raise
    
#     async def transcribe_audio_stream(self, audio_chunks: list) -> str:
#         """
#         Transcribe multiple audio chunks (for streaming)
        
#         Args:
#             audio_chunks: List of audio bytes chunks (from audio_stream_service)
            
#         Returns:
#             Complete transcription
#         """
        
#         try:
#             if not audio_chunks or len(audio_chunks) == 0:
#                 print("⚠️ No audio chunks to transcribe")
#                 return ""
            
#             print(f"🎙️ Processing {len(audio_chunks)} audio chunks...")
#             print(f"🔍 First chunk type: {type(audio_chunks[0])}")
#             print(f"🔍 First chunk size: {len(audio_chunks[0])} bytes")
            
#             combined_audio = b''.join(audio_chunks)
            
#             print(f"📦 Combined audio size: {len(combined_audio)} bytes")
            
#             if len(combined_audio) < 100:
#                 print("⚠️ Audio too short, might be invalid")
#                 return "Sorry, the audio was too short."
            
#             return await self.transcribe_audio(combined_audio)
            
#         except Exception as e:
#             print(f"❌ Error in streaming transcription: {e}")
#             import traceback
#             traceback.print_exc()
#             raise


# whisper_service = WhisperService()




import asyncio
from openai import AsyncOpenAI
from app.config.settings import settings
import io
import struct

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class WhisperService:
    """Handle real-time speech-to-text using OpenAI Whisper"""
    
    def __init__(self):
        self.model = "whisper-1"
    
    def _create_wav_from_pcm(self, pcm_bytes: bytes, sample_rate: int = 48000, channels: int = 1, sample_width: int = 2) -> bytes:
        """
        Wrap raw PCM bytes in a proper WAV header so Whisper accepts it.
        Browser MediaRecorder sends PCM-like data — this makes it valid WAV.
        """
        num_frames = len(pcm_bytes) // (channels * sample_width)
        wav_buffer = io.BytesIO()
        
        # WAV header
        data_size = len(pcm_bytes)
        wav_buffer.write(b'RIFF')
        wav_buffer.write(struct.pack('<I', 36 + data_size))  # file size - 8
        wav_buffer.write(b'WAVE')
        wav_buffer.write(b'fmt ')
        wav_buffer.write(struct.pack('<I', 16))              # chunk size
        wav_buffer.write(struct.pack('<H', 1))               # PCM format
        wav_buffer.write(struct.pack('<H', channels))
        wav_buffer.write(struct.pack('<I', sample_rate))
        wav_buffer.write(struct.pack('<I', sample_rate * channels * sample_width))
        wav_buffer.write(struct.pack('<H', channels * sample_width))
        wav_buffer.write(struct.pack('<H', sample_width * 8))
        wav_buffer.write(b'data')
        wav_buffer.write(struct.pack('<I', data_size))
        wav_buffer.write(pcm_bytes)
        
        return wav_buffer.getvalue()

    def _detect_audio_format(self, audio_bytes: bytes) -> str:
        """Detect audio format from magic bytes"""
        if audio_bytes[:4] == b'RIFF':
            return 'wav'
        elif audio_bytes[:3] == b'ID3' or (audio_bytes[:2] == b'\xff\xfb') or (audio_bytes[:2] == b'\xff\xf3'):
            return 'mp3'
        elif audio_bytes[:4] == b'OggS':
            return 'ogg'
        elif audio_bytes[:4] == b'fLaC':
            return 'flac'
        elif audio_bytes[4:8] == b'ftyp':
            return 'm4a'
        elif audio_bytes[:4] == b'\x1a\x45\xdf\xa3':
            return 'webm'
        else:
            return 'unknown'

    async def transcribe_audio(self, audio_bytes: bytes, language: str = "en") -> str:
        """
        Transcribe audio to text using Whisper.
        ✅ Auto-detects format and wraps raw PCM in WAV if needed.
        """
        
        try:
            if not audio_bytes or len(audio_bytes) == 0:
                print("⚠️ Empty audio bytes received")
                return ""
            
            print(f"📝 Transcribing {len(audio_bytes)} bytes of audio...")
            
            # Detect format
            fmt = self._detect_audio_format(audio_bytes)
            print(f"🔍 Detected audio format: {fmt}")
            
            if fmt in ('wav', 'mp3', 'ogg', 'flac', 'm4a', 'webm'):
                # Already a valid format — use directly
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = f"audio.{fmt}"
                print(f"✅ Using detected format: {fmt}")
            else:
                # Unknown/raw format — wrap in WAV
                print("⚠️ Unknown format — wrapping PCM in WAV header...")
                wav_bytes = self._create_wav_from_pcm(audio_bytes)
                audio_file = io.BytesIO(wav_bytes)
                audio_file.name = "audio.wav"
                print(f"✅ Wrapped as WAV: {len(wav_bytes)} bytes")
            
            print("🔄 Calling Whisper API...")
            
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
            print("❌ Whisper API timeout (30s)")
            raise Exception("Transcription timeout - audio might be too long")
        except Exception as e:
            print(f"❌ Error in Whisper transcription: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def transcribe_audio_stream(self, audio_chunks: list) -> str:
        """
        Transcribe multiple audio chunks (for streaming).
        ✅ Handles both bytes and base64 string chunks.
        """
        
        try:
            if not audio_chunks or len(audio_chunks) == 0:
                print("⚠️ No audio chunks to transcribe")
                return ""
            
            print(f"🎙️ Processing {len(audio_chunks)} audio chunks...")
            
            # ✅ Handle both bytes and base64 string chunks
            processed_chunks = []
            for chunk in audio_chunks:
                if isinstance(chunk, bytes):
                    processed_chunks.append(chunk)
                elif isinstance(chunk, str):
                    # base64 string → bytes
                    import base64 as b64
                    try:
                        processed_chunks.append(b64.b64decode(chunk))
                    except Exception:
                        pass  # skip invalid chunks
            
            if not processed_chunks:
                print("⚠️ No valid audio chunks after processing")
                return ""
            
            combined_audio = b''.join(processed_chunks)
            print(f"📦 Combined audio size: {len(combined_audio)} bytes")
            
            if len(combined_audio) < 10000:  # 10KB এর কম হলে skip
                print("⚠️ Audio too short/noise, skipping")
                return ""
            
            return await self.transcribe_audio(combined_audio)
            
        except Exception as e:
            print(f"❌ Error in streaming transcription: {e}")
            import traceback
            traceback.print_exc()
            raise


whisper_service = WhisperService()
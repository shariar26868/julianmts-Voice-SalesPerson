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

# Minimum combined audio size to attempt transcription.
# ~0.25 seconds of audio at typical WebM/Opus bitrates.
MIN_AUDIO_BYTES = 4000

# Phrases Whisper is known to hallucinate on TRULY silent / near-empty audio.
# Keep this list TIGHT — do NOT add real conversational words.
# The filter is also gated on audio length (see transcribe_audio_stream).
HALLUCINATION_PATTERNS = {
    # Whisper's most common silent-audio hallucinations (confirmed empirically)
    "thank you for watching",
    "thanks for watching",
    "thank you for listening",
    "please subscribe",
    "subtitles by",
    "www.",
    ".",
    "",
}


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
        """
        Detect audio format from magic bytes.
        
        ⚠️ Browser MediaRecorder quirk: on the 2nd+ recording the WebM
        initialization segment (EBML magic: \x1a\x45\xdf\xa3) may NOT be
        at offset 0 — it can appear anywhere in the first ~512 bytes because
        the browser appends it after one or more continuation chunks.
        We therefore scan the entire header region instead of checking only
        the very first 4 bytes.
        """
        header = audio_bytes[:512]  # scan first 512 bytes

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
        elif b'\x1a\x45\xdf\xa3' in header:
            # WebM EBML magic found anywhere in the header region
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
                # Browser MediaRecorder ALWAYS produces WebM/Opus.
                # If magic bytes weren't found (e.g. truncated or mid-stream
                # chunk without EBML header), treat as webm — never as raw PCM.
                # Wrapping as fake WAV causes Whisper to return empty strings.
                print("⚠️ Unknown format — defaulting to webm (browser MediaRecorder always produces WebM)")
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = "audio.webm"
                print(f"✅ Treating as webm: {len(audio_bytes)} bytes")
            
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
            
            # ── WebM chunk reordering ──────────────────────────────────────────
            # Browser MediaRecorder quirk: on the 2nd+ recording the WebM
            # initialization segment (containing the EBML magic \x1a\x45\xdf\xa3)
            # may NOT be the first chunk delivered — it can arrive at index 1 or 2.
            # Concatenating chunks in arrival order produces a structurally invalid
            # WebM file (header not at offset 0), which Whisper rejects with 400.
            #
            # Fix: find whichever chunk contains the EBML magic and move it to
            # the front so the combined bytes form a valid WebM container.
            WEBM_MAGIC = b'\x1a\x45\xdf\xa3'
            init_idx = None
            for i, chunk in enumerate(processed_chunks):
                if WEBM_MAGIC in chunk[:64]:   # magic is always within first 64 bytes of the init chunk
                    init_idx = i
                    break

            if init_idx is not None and init_idx != 0:
                print(f"🔧 WebM init chunk found at index {init_idx} — moving to front for valid container")
                processed_chunks = (
                    [processed_chunks[init_idx]]
                    + processed_chunks[:init_idx]
                    + processed_chunks[init_idx + 1:]
                )
            elif init_idx == 0:
                print("✅ WebM init chunk already at front")
            else:
                print("⚠️ WebM init chunk not found in first 64 bytes of any chunk — sending as-is")
            # ──────────────────────────────────────────────────────────────────

            combined_audio = b''.join(processed_chunks)
            print(f"📦 Combined audio size: {len(combined_audio)} bytes")
            
            if len(combined_audio) < MIN_AUDIO_BYTES:
                print(f"⚠️ Audio below minimum threshold ({len(combined_audio)} < {MIN_AUDIO_BYTES} bytes), skipping Whisper")
                return ""
            
            result = await self.transcribe_audio(combined_audio)

            # Post-call hallucination filter
            # Only discard known Whisper silent-audio artifacts.
            # Do NOT discard short but valid replies like "okay", "sure", "hmm".
            normalized = result.lower().strip().rstrip(".,!?")
            if normalized in HALLUCINATION_PATTERNS:
                print(f"⚠️ Hallucination detected, discarding: '{result}'")
                return ""

            return result
            
        except Exception as e:
            print(f"❌ Error in streaming transcription: {e}")
            import traceback
            traceback.print_exc()
            raise


whisper_service = WhisperService()
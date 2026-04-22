# import asyncio
# import logging
# from typing import Optional, Dict, Any

# from app.config.settings import settings

# logger = logging.getLogger(__name__)

# # =====================================================
# # Safe fallback dummy classes (SDK না থাকলেও app উঠবে)
# # =====================================================

# class _DummyVoiceSettings:
#     def __init__(
#         self,
#         stability: float = 0.5,
#         similarity_boost: float = 0.75,
#         style: float = 0.0,
#         use_speaker_boost: bool = True,
#     ):
#         self.stability = stability
#         self.similarity_boost = similarity_boost
#         self.style = style
#         self.use_speaker_boost = use_speaker_boost


# class _DummyVoice:
#     def __init__(self, voice_id: str, settings: Any = None):
#         self.voice_id = voice_id
#         self.settings = settings


# VoiceSettings = _DummyVoiceSettings
# Voice = _DummyVoice

# CLIENT_MODE = "none"
# client = None
# generate = None
# voices = None

# # =====================================================
# # Try NEW ElevenLabs SDK (v1.x)
# # =====================================================
# try:
#     from elevenlabs.client import ElevenLabs
#     from elevenlabs import VoiceSettings as _VoiceSettings, Voice as _Voice

#     VoiceSettings = _VoiceSettings
#     Voice = _Voice

#     client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
#     CLIENT_MODE = "new"
#     logger.info("✅ Using ElevenLabs NEW SDK")
#     print("✅ Using ElevenLabs NEW SDK")

# except Exception as new_sdk_error:
#     # =================================================
#     # Try OLD ElevenLabs SDK (v0.x)
#     # =================================================
#     try:
#         from elevenlabs import (
#             generate as _generate,
#             voices as _voices,
#             Voice as _Voice,
#             VoiceSettings as _VoiceSettings,
#             set_api_key,
#         )

#         set_api_key(settings.ELEVENLABS_API_KEY)

#         generate = _generate
#         voices = _voices
#         Voice = _Voice
#         VoiceSettings = _VoiceSettings

#         CLIENT_MODE = "old"
#         logger.info("✅ Using ElevenLabs OLD SDK")
#         print("✅ Using ElevenLabs OLD SDK")

#     except Exception as old_sdk_error:
#         logger.warning(
#             "⚠️ ElevenLabs SDK not available, fallback mode enabled",
#             exc_info=True,
#         )
#         print("⚠️ ElevenLabs SDK not available, fallback mode enabled")
#         CLIENT_MODE = "none"


# # =====================================================
# # ElevenLabs Service
# # =====================================================

# class ElevenLabsService:
#     """Unified ElevenLabs TTS Service (NEW + OLD SDK supported)"""

#     def __init__(self):
#         self.available_voices: Dict[str, str] = {}
#         self.default_voice_id = "21m00Tcm4TlvDq8ikWAM"
#         self._load_voices()

#     # -------------------------------------------------
#     # Load available voices safely
#     # -------------------------------------------------
#     def _load_voices(self):
#         try:
#             if CLIENT_MODE == "new" and client:
#                 all_voices = client.voices.get_all()
#                 for i, v in enumerate(all_voices.voices[:10]):
#                     self.available_voices[f"voice_{i}"] = v.voice_id

#             elif CLIENT_MODE == "old" and voices:
#                 all_voices = voices()
#                 for i, v in enumerate(all_voices[:10]):
#                     self.available_voices[f"voice_{i}"] = v.voice_id

#         except Exception:
#             logger.warning("⚠️ Voice loading failed, using defaults", exc_info=True)

#         # Absolute fallback voices
#         if not self.available_voices:
#             self.available_voices = {
#                 "voice_0": "21m00Tcm4TlvDq8ikWAM",
#                 "voice_1": "AZnzlk1XvdvUeBnXmlld",
#                 "voice_2": "EXAVITQu4vr4xnSDxMaL",
#                 "voice_3": "ErXwobaYiN019PkySvjV",
#                 "voice_4": "MF3mGyEYCl7XYWbV9V6O",
#                 "voice_5": "TxGEqnHWrfWFTfGW9XjX",
#             }

#     # -------------------------------------------------
#     # Personality → Voice settings (✅ FIXED - Using keyword arguments)
#     # -------------------------------------------------
#     def _get_voice_settings(self, personality: str) -> VoiceSettings:
#         """Get voice settings based on personality with keyword arguments"""
        
#         presets = {
#             "angry": VoiceSettings(
#                 stability=0.3,
#                 similarity_boost=0.8,
#                 style=0.6,
#                 use_speaker_boost=True
#             ),
#             "arrogant": VoiceSettings(
#                 stability=0.6,
#                 similarity_boost=0.9,
#                 style=0.7,
#                 use_speaker_boost=True
#             ),
#             "soft": VoiceSettings(
#                 stability=0.7,
#                 similarity_boost=0.7,
#                 style=0.3,
#                 use_speaker_boost=True
#             ),
#             "cold_hearted": VoiceSettings(
#                 stability=0.6,
#                 similarity_boost=0.8,
#                 style=0.2,
#                 use_speaker_boost=False
#             ),
#             "nice": VoiceSettings(
#                 stability=0.8,
#                 similarity_boost=0.8,
#                 style=0.5,
#                 use_speaker_boost=True
#             ),
#             "analytical": VoiceSettings(
#                 stability=0.75,
#                 similarity_boost=0.7,
#                 style=0.3,
#                 use_speaker_boost=True
#             ),
#             "neutral": VoiceSettings(
#                 stability=0.5,
#                 similarity_boost=0.75,
#                 style=0.0,
#                 use_speaker_boost=True
#             ),
#         }

#         return presets.get(
#             personality.lower(), 
#             presets["neutral"]
#         )

#     # -------------------------------------------------
#     # Text to Speech (ASYNC SAFE)
#     # -------------------------------------------------
#     async def text_to_speech(
#         self,
#         text: str,
#         voice_id: Optional[str] = None,
#         personality: str = "neutral",
#     ) -> bytes:
#         """
#         Convert text to speech using ElevenLabs
        
#         Args:
#             text: Text to convert
#             voice_id: Optional custom voice ID
#             personality: Personality type for voice modulation
            
#         Returns:
#             Audio bytes (MP3)
#         """

#         if not text or not text.strip():
#             logger.warning("⚠️ Empty text provided to TTS")
#             return b""

#         # Resolve voice ID
#         resolved_voice = self.available_voices.get(
#             voice_id, self.default_voice_id
#         )

#         # Get voice settings
#         settings_obj = self._get_voice_settings(personality)
        
#         print(f"🔊 Generating TTS: '{text[:50]}...' with voice {resolved_voice}")

#         try:
#             # ---------- NEW SDK ----------
#             if CLIENT_MODE == "new" and client:
#                 print(f"📡 Using NEW SDK with voice settings: {settings_obj.__dict__}")
                
#                 audio = await asyncio.to_thread(
#                     client.text_to_speech.convert,
#                     text=text,
#                     voice_id=resolved_voice,
#                     model_id="eleven_multilingual_v2",
#                     voice_settings=settings_obj
#                 )

#             # ---------- OLD SDK ----------
#             elif CLIENT_MODE == "old" and generate:
#                 print(f"📡 Using OLD SDK with voice {resolved_voice}")
                
#                 audio = await asyncio.to_thread(
#                     generate,
#                     text=text,
#                     voice=Voice(
#                         voice_id=resolved_voice,
#                         settings=settings_obj
#                     ),
#                     model="eleven_multilingual_v2",
#                 )

#             else:
#                 raise RuntimeError("ElevenLabs SDK not available")

#             # Ensure bytes
#             audio_bytes = audio if isinstance(audio, bytes) else b"".join(audio)
            
#             print(f"✅ TTS generated: {len(audio_bytes)} bytes")
#             return audio_bytes

#         except Exception as e:
#             logger.error(f"❌ ElevenLabs TTS failed: {e}", exc_info=True)
#             print(f"❌ TTS Error: {e}")
#             raise RuntimeError(f"Text-to-speech generation failed: {str(e)}")

#     # -------------------------------------------------
#     # Assign voice per representative
#     # -------------------------------------------------
#     def get_voice_for_representative(
#         self,
#         rep_index: int,
#         custom_voice_id: Optional[str] = None,
#     ) -> str:
#         """Get voice ID for a representative"""

#         if custom_voice_id and custom_voice_id in self.available_voices:
#             return self.available_voices[custom_voice_id]

#         key = f"voice_{rep_index % len(self.available_voices)}"
#         return self.available_voices.get(key, self.default_voice_id)

#     # -------------------------------------------------
#     # Speech-to-text placeholder
#     # -------------------------------------------------
#     async def speech_to_text(self, audio_bytes: bytes) -> str:
#         """Speech to text - Use OpenAI Whisper instead"""
#         raise NotImplementedError("Use OpenAI Whisper for STT")

#     # -------------------------------------------------
#     # Get available voices
#     # -------------------------------------------------
#     async def get_available_voices(self):
#         """Fetch all available voices from ElevenLabs"""
#         try:
#             if CLIENT_MODE == "new" and client:
#                 result = await asyncio.to_thread(client.voices.get_all)
#                 return result.voices
#             elif CLIENT_MODE == "old" and voices:
#                 return await asyncio.to_thread(voices)
#             return []
#         except Exception as e:
#             logger.error(f"❌ Failed to fetch voices: {e}", exc_info=True)
#             return []


# # =====================================================
# # Singleton
# # =====================================================
# elevenlabs_service = ElevenLabsService()





import asyncio
import logging
from typing import Optional, Dict, Any

from app.config.settings import settings

logger = logging.getLogger(__name__)

# =====================================================
# Safe fallback dummy classes
# =====================================================

class _DummyVoiceSettings:
    def __init__(
        self,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True,
    ):
        self.stability = stability
        self.similarity_boost = similarity_boost
        self.style = style
        self.use_speaker_boost = use_speaker_boost


class _DummyVoice:
    def __init__(self, voice_id: str, settings: Any = None):
        self.voice_id = voice_id
        self.settings = settings


VoiceSettings = _DummyVoiceSettings
Voice = _DummyVoice

CLIENT_MODE = "none"
client = None
generate = None
voices = None

# =====================================================
# Try NEW ElevenLabs SDK (v1.x)
# =====================================================
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings as _VoiceSettings, Voice as _Voice

    VoiceSettings = _VoiceSettings
    Voice = _Voice

    client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
    CLIENT_MODE = "new"
    logger.info("✅ Using ElevenLabs NEW SDK")
    print("✅ Using ElevenLabs NEW SDK")

except Exception as new_sdk_error:
    # =================================================
    # Try OLD ElevenLabs SDK (v0.x)
    # =================================================
    try:
        from elevenlabs import (
            generate as _generate,
            voices as _voices,
            Voice as _Voice,
            VoiceSettings as _VoiceSettings,
            set_api_key,
        )

        set_api_key(settings.ELEVENLABS_API_KEY)

        generate = _generate
        voices = _voices
        Voice = _Voice
        VoiceSettings = _VoiceSettings

        CLIENT_MODE = "old"
        logger.info("✅ Using ElevenLabs OLD SDK")
        print("✅ Using ElevenLabs OLD SDK")

    except Exception as old_sdk_error:
        logger.warning("⚠️ ElevenLabs SDK not available, fallback mode enabled")
        print("⚠️ ElevenLabs SDK not available, fallback mode enabled")
        CLIENT_MODE = "none"


# =====================================================
# ElevenLabs Service
# =====================================================

class ElevenLabsService:
    """Unified ElevenLabs TTS Service (NEW + OLD SDK supported)"""

    def __init__(self):
        self.available_voices: Dict[str, str] = {}
        self.default_voice_id = "21m00Tcm4TlvDq8ikWAM"
        self.api_key = settings.ELEVENLABS_API_KEY or ""
        # WebSocket streaming enabled only if we have API key and websockets package
        try:
            import websockets
            self.enabled_ws = bool(self.api_key)
        except ImportError:
            print("⚠️ websockets package not found - install with: pip install websockets")
            self.enabled_ws = False
        self._load_voices()

    def _load_voices(self):
        try:
            if CLIENT_MODE == "new" and client:
                all_voices = client.voices.get_all()
                for i, v in enumerate(all_voices.voices[:10]):
                    self.available_voices[f"voice_{i}"] = v.voice_id

            elif CLIENT_MODE == "old" and voices:
                all_voices = voices()
                for i, v in enumerate(all_voices[:10]):
                    self.available_voices[f"voice_{i}"] = v.voice_id

        except Exception:
            logger.warning("⚠️ Voice loading failed, using defaults")

        if not self.available_voices:
            self.available_voices = {
                "voice_0": "21m00Tcm4TlvDq8ikWAM",
                "voice_1": "AZnzlk1XvdvUeBnXmlld",
                "voice_2": "EXAVITQu4vr4xnSDxMaL",
                "voice_3": "ErXwobaYiN019PkySvjV",
                "voice_4": "MF3mGyEYCl7XYWbV9V6O",
                "voice_5": "TxGEqnHWrfWFTfGW9XjX",
            }

    def _get_voice_settings(self, personality: str) -> VoiceSettings:
        """Get voice settings based on personality"""
        
        presets = {
            "angry": VoiceSettings(
                stability=0.3,
                similarity_boost=0.8,
                style=0.6,
                use_speaker_boost=True
            ),
            "arrogant": VoiceSettings(
                stability=0.6,
                similarity_boost=0.9,
                style=0.7,
                use_speaker_boost=True
            ),
            "soft": VoiceSettings(
                stability=0.7,
                similarity_boost=0.7,
                style=0.3,
                use_speaker_boost=True
            ),
            "cold_hearted": VoiceSettings(
                stability=0.6,
                similarity_boost=0.8,
                style=0.2,
                use_speaker_boost=False
            ),
            "nice": VoiceSettings(
                stability=0.8,
                similarity_boost=0.8,
                style=0.5,
                use_speaker_boost=True
            ),
            "analytical": VoiceSettings(
                stability=0.75,
                similarity_boost=0.7,
                style=0.3,
                use_speaker_boost=True
            ),
            "neutral": VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            ),
        }

        return presets.get(personality.lower(), presets["neutral"])

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        personality: str = "neutral",
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs.
        ✅ Uses eleven_turbo_v2 for faster generation.
        ✅ Returns complete bytes in one call — no chunking.
        """

        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided to TTS")
            return b""

        # ✅ If voice_id is a real ElevenLabs voice ID (long string), use directly
        # Otherwise look up from available_voices dict
        if voice_id and len(voice_id) > 10:
            resolved_voice = voice_id
        else:
            resolved_voice = self.available_voices.get(
                voice_id or "voice_0", self.default_voice_id
            )

        settings_obj = self._get_voice_settings(personality)

        print(f"🔊 TTS: '{text[:60]}...' | voice={resolved_voice} | personality={personality}")

        try:
            # ---------- NEW SDK ----------
            if CLIENT_MODE == "new" and client:
                print("📡 Using NEW SDK (turbo model)...")

                # ✅ eleven_turbo_v2 = ~3x faster than eleven_multilingual_v2
                # ✅ mp3_22050_32 = lower bitrate = faster transfer, still good quality
                audio_generator = await asyncio.to_thread(
                    client.text_to_speech.convert,
                    text=text,
                    voice_id=resolved_voice,
                    model_id="eleven_turbo_v2_5",
                    output_format="mp3_22050_32",
                    voice_settings=settings_obj
                )

                # Collect all bytes at once
                if isinstance(audio_generator, bytes):
                    audio_bytes = audio_generator
                else:
                    audio_bytes = b"".join(audio_generator)

            # ---------- OLD SDK ----------
            elif CLIENT_MODE == "old" and generate:
                print("📡 Using OLD SDK...")

                audio = await asyncio.to_thread(
                    generate,
                    text=text,
                    voice=Voice(
                        voice_id=resolved_voice,
                        settings=settings_obj
                    ),
                    model="eleven_turbo_v2",  # ✅ turbo here too
                )

                audio_bytes = audio if isinstance(audio, bytes) else b"".join(audio)

            else:
                raise RuntimeError("ElevenLabs SDK not available")

            if not audio_bytes:
                raise RuntimeError("ElevenLabs returned empty audio")

            print(f"✅ TTS complete: {len(audio_bytes)} bytes")
            return audio_bytes

        except Exception as e:
            logger.error(f"❌ ElevenLabs TTS failed: {e}", exc_info=True)
            print(f"❌ TTS Error: {e}")
            raise RuntimeError(f"Text-to-speech generation failed: {str(e)}")

    def get_voice_for_representative(
        self,
        rep_index: int,
        custom_voice_id: Optional[str] = None,
    ) -> str:
        """Get voice ID for a representative"""

        if custom_voice_id and custom_voice_id in self.available_voices:
            return self.available_voices[custom_voice_id]

        key = f"voice_{rep_index % len(self.available_voices)}"
        return self.available_voices.get(key, self.default_voice_id)

    async def speech_to_text(self, audio_bytes: bytes) -> str:
        """Speech to text - Use OpenAI Whisper instead"""
        raise NotImplementedError("Use OpenAI Whisper for STT")

    async def get_available_voices(self):
        """Fetch all available voices from ElevenLabs"""
        try:
            if CLIENT_MODE == "new" and client:
                result = await asyncio.to_thread(client.voices.get_all)
                return result.voices
            elif CLIENT_MODE == "old" and voices:
                return await asyncio.to_thread(voices)
            return []
        except Exception as e:
            logger.error(f"❌ Failed to fetch voices: {e}")
            return []
            
    from typing import AsyncGenerator
    
    async def stream_tts_from_sentences(
        self,
        sentences_stream,
        voice_id: Optional[str] = None,
        personality: str = "neutral",
    ):
        """
        Consumes an async generator of sentences and yields audio chunks.
        Each sentence is generated and yielded sequentially to preserve order.
        """
        async for sentence in sentences_stream:
            try:
                audio_bytes = await self.text_to_speech(
                    text=sentence,
                    voice_id=voice_id,
                    personality=personality
                )
                if audio_bytes:
                    yield (sentence, audio_bytes)
            except Exception as e:
                print(f"❌ TTS stream error for sentence '{sentence[:20]}...': {e}")
                yield (sentence, b"")

    async def stream_tts_websocket(
        self,
        token_stream,
        voice_id: Optional[str] = None,
        personality: str = "neutral",
    ):
        """
        Ultra-low latency TTS using ElevenLabs WebSocket input streaming.
        Pipes OpenAI token stream directly into ElevenLabs WS and yields
        (text_chunk, audio_bytes) tuples as audio arrives.
        
        Flow:
          OpenAI tokens → ElevenLabs WS input → audio chunks → yield to client
        """
        import websockets
        import base64
        import asyncio
        import json as _json

        if not self.enabled_ws:
            # Fallback to sentence-based TTS
            from app.utils.stream_helpers import sentence_buffer
            async for item in self.stream_tts_from_sentences(
                sentence_buffer(token_stream), voice_id=voice_id, personality=personality
            ):
                yield item
            return

        # Resolve voice
        if voice_id and len(str(voice_id)) > 10:
            resolved_voice = voice_id
        else:
            resolved_voice = self.available_voices.get(voice_id or "voice_0", self.default_voice_id)

        settings_obj = self._get_voice_settings(personality)
        model_id = "eleven_turbo_v2_5"

        uri = (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{resolved_voice}"
            f"/stream-input?model_id={model_id}&output_format=mp3_22050_32"
        )

        full_text = ""
        audio_queue: asyncio.Queue = asyncio.Queue()
        DONE_SENTINEL = None

        async def _send_tokens(ws):
            nonlocal full_text
            try:
                # Initialize connection with voice settings
                await ws.send(_json.dumps({
                    "text": " ",
                    "voice_settings": {
                        "stability": settings_obj.stability,
                        "similarity_boost": settings_obj.similarity_boost,
                        "style": getattr(settings_obj, 'style', 0.0),
                        "use_speaker_boost": getattr(settings_obj, 'use_speaker_boost', True),
                    },
                    "generation_config": {
                        "chunk_length_schedule": [80, 120, 180]
                    },
                    "xi_api_key": self.api_key,
                }))

                # Stream tokens from OpenAI
                async for token in token_stream:
                    full_text += token
                    await ws.send(_json.dumps({"text": token}))

                # Flush remaining buffer
                await ws.send(_json.dumps({"text": "", "flush": True}))
                # Close ElevenLabs WS
                await ws.send(_json.dumps({"text": ""}))
            except Exception as e:
                print(f"❌ ElevenLabs WS send error: {e}")
            finally:
                await audio_queue.put(DONE_SENTINEL)

        async def _receive_audio(ws):
            try:
                async for message in ws:
                    data = _json.loads(message)
                    if data.get("audio"):
                        audio_bytes = base64.b64decode(data["audio"])
                        await audio_queue.put(audio_bytes)
                    if data.get("isFinal"):
                        break
            except Exception as e:
                print(f"❌ ElevenLabs WS receive error: {e}")
            finally:
                await audio_queue.put(DONE_SENTINEL)

        try:
            async with websockets.connect(uri) as ws:
                # Run sender and receiver concurrently
                sender_task = asyncio.create_task(_send_tokens(ws))
                receiver_task = asyncio.create_task(_receive_audio(ws))

                done_count = 0
                accumulated_text = ""
                while done_count < 2:
                    chunk = await audio_queue.get()
                    if chunk is DONE_SENTINEL:
                        done_count += 1
                        continue
                    # yield current accumulated text snapshot + audio chunk
                    yield (full_text, chunk)

                await asyncio.gather(sender_task, receiver_task, return_exceptions=True)

        except Exception as e:
            print(f"❌ ElevenLabs WS connection error: {e}, falling back to HTTP TTS")
            # Fallback: generate full audio via HTTP
            try:
                audio_bytes = await self.text_to_speech(
                    text=full_text or "I understand.",
                    voice_id=voice_id,
                    personality=personality
                )
                if audio_bytes:
                    yield (full_text, audio_bytes)
            except Exception as fe:
                print(f"❌ Fallback TTS also failed: {fe}")

# =====================================================
# Singleton
# =====================================================
elevenlabs_service = ElevenLabsService()
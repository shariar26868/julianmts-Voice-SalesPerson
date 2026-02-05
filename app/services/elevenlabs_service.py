# try:
#     from elevenlabs import ElevenLabs, Voice, VoiceSettings
#     client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
# except ImportError:
#     # Fallback for older versions
#     from elevenlabs import generate, voices, Voice, VoiceSettings
#     from elevenlabs import set_api_key
#     from app.config.settings import settings
#     set_api_key(settings.ELEVENLABS_API_KEY)
#     client = None

# from app.config.settings import settings
# from typing import Optional


# class ElevenLabsService:
#     """Handle text-to-speech and speech-to-text using ElevenLabs"""
    
#     def __init__(self):
#         self.available_voices = {}
#         self._load_voices()
    
#     def _load_voices(self):
#         """Load available ElevenLabs voices"""
#         try:
#             # Try newer API
#             if client:
#                 all_voices = client.voices.get_all()
#                 for i, voice in enumerate(all_voices.voices[:10]):
#                     self.available_voices[f"voice_{i}"] = voice.voice_id
#             else:
#                 # Fallback for older API
#                 from elevenlabs import voices as get_voices
#                 all_voices = get_voices()
#                 for i, voice in enumerate(all_voices[:10]):
#                     self.available_voices[f"voice_{i}"] = voice.voice_id
#         except Exception as e:
#             print(f"Error loading voices: {e}")
#             # Fallback voice IDs (common ElevenLabs voices)
#             self.available_voices = {
#                 "voice_0": "21m00Tcm4TlvDq8ikWAM",  # Rachel
#                 "voice_1": "AZnzlk1XvdvUeBnXmlld",  # Domi
#                 "voice_2": "EXAVITQu4vr4xnSDxMaL",  # Bella
#                 "voice_3": "ErXwobaYiN019PkySvjV",  # Antoni
#                 "voice_4": "MF3mGyEYCl7XYWbV9V6O",  # Elli
#                 "voice_5": "TxGEqnHWrfWFTfGW9XjX",  # Josh
#             }
    
#     async def text_to_speech(
#         self,
#         text: str,
#         voice_id: Optional[str] = None,
#         personality: str = "neutral"
#     ) -> bytes:
#         """
#         Convert text to speech audio
        
#         Args:
#             text: Text to convert
#             voice_id: ElevenLabs voice ID or key from available_voices
#             personality: Adjust voice settings based on personality
            
#         Returns:
#             Audio bytes (MP3)
#         """
        
#         # Get voice ID
#         if not voice_id or voice_id not in self.available_voices:
#             voice_id = self.available_voices["voice_0"]
#         else:
#             voice_id = self.available_voices.get(voice_id, voice_id)
        
#         # Adjust voice settings based on personality
#         voice_settings = self._get_voice_settings(personality)
        
#         try:
#             # Try newer API first
#             if client:
#                 audio = client.generate(
#                     text=text,
#                     voice=Voice(
#                         voice_id=voice_id,
#                         settings=voice_settings
#                     ),
#                     model="eleven_multilingual_v2"
#                 )
#             else:
#                 # Fallback to older API
#                 from elevenlabs import generate
#                 audio = generate(
#                     text=text,
#                     voice=voice_id,
#                     model="eleven_multilingual_v2"
#                 )
            
#             # Convert generator to bytes
#             audio_bytes = b''.join(audio)
#             return audio_bytes
            
#         except Exception as e:
#             print(f"Error in text_to_speech: {e}")
#             raise
    
#     def _get_voice_settings(self, personality: str) -> VoiceSettings:
#         """Get voice settings based on personality"""
        
#         personality_settings = {
#             "angry": VoiceSettings(
#                 stability=0.3,
#                 similarity_boost=0.8,
#                 style=0.6,
#                 use_speaker_boost=True
#             ),
#             "arrogant": VoiceSettings(
#                 stability=0.7,
#                 similarity_boost=0.7,
#                 style=0.5,
#                 use_speaker_boost=True
#             ),
#             "soft": VoiceSettings(
#                 stability=0.8,
#                 similarity_boost=0.6,
#                 style=0.3,
#                 use_speaker_boost=True
#             ),
#             "cold_hearted": VoiceSettings(
#                 stability=0.9,
#                 similarity_boost=0.5,
#                 style=0.2,
#                 use_speaker_boost=False
#             ),
#             "nice": VoiceSettings(
#                 stability=0.6,
#                 similarity_boost=0.7,
#                 style=0.4,
#                 use_speaker_boost=True
#             ),
#             "analytical": VoiceSettings(
#                 stability=0.8,
#                 similarity_boost=0.6,
#                 style=0.3,
#                 use_speaker_boost=True
#             ),
#         }
        
#         return personality_settings.get(
#             personality.lower(),
#             VoiceSettings(
#                 stability=0.5,
#                 similarity_boost=0.75,
#                 style=0.0,
#                 use_speaker_boost=True
#             )
#         )
    
#     def get_voice_for_representative(
#         self,
#         rep_index: int,
#         custom_voice_id: Optional[str] = None
#     ) -> str:
#         """Get appropriate voice ID for a representative"""
        
#         if custom_voice_id and custom_voice_id in self.available_voices:
#             return self.available_voices[custom_voice_id]
        
#         # Assign voice based on index
#         voice_key = f"voice_{rep_index % len(self.available_voices)}"
#         return self.available_voices.get(voice_key, self.available_voices["voice_0"])
    
#     async def speech_to_text(self, audio_bytes: bytes) -> str:
#         """
#         Convert speech audio to text
#         Note: ElevenLabs doesn't have built-in STT, use OpenAI Whisper instead
#         This is a placeholder for integration
#         """
#         # This would use OpenAI Whisper API or another STT service
#         # For now, returning placeholder
#         raise NotImplementedError(
#             "Use OpenAI Whisper API for speech-to-text conversion"
#         )


# # Singleton instance
# elevenlabs_service = ElevenLabsService()



from typing import Optional, Dict, Any
from app.config.settings import settings

# -------------------------
# Safe placeholders (fallback)
# -------------------------

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

# -------------------------
# Try NEW SDK
# -------------------------
try:
    from elevenlabs.client import ElevenLabs, Voice as _Voice, VoiceSettings as _VoiceSettings

    Voice = _Voice
    VoiceSettings = _VoiceSettings
    client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
    CLIENT_MODE = "new"
    print("✅ Using ElevenLabs NEW SDK")

except Exception:
    # -------------------------
    # Try OLD SDK
    # -------------------------
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
        print("✅ Using ElevenLabs OLD SDK")

    except Exception as e:
        print("⚠️ ElevenLabs SDK unavailable, running in fallback mode:", e)
        CLIENT_MODE = "none"


# -------------------------
# ElevenLabs Service
# -------------------------

class ElevenLabsService:
    """Handle text-to-speech and speech-to-text using ElevenLabs"""

    def __init__(self):
        self.available_voices: Dict[str, str] = {}
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

        except Exception as e:
            print("⚠️ Voice loading failed, using defaults:", e)

        # Absolute fallback
        if not self.available_voices:
            self.available_voices = {
                "voice_0": "21m00Tcm4TlvDq8ikWAM",
                "voice_1": "AZnzlk1XvdvUeBnXmlld",
                "voice_2": "EXAVITQu4vr4xnSDxMaL",
                "voice_3": "ErXwobaYiN019PkySvjV",
                "voice_4": "MF3mGyEYCl7XYWbV9V6O",
                "voice_5": "TxGEqnHWrfWFTfGW9XjX",
            }

    # -------------------------
    # Text-to-Speech
    # -------------------------

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        personality: str = "neutral",
    ) -> bytes:

        resolved_voice = self.available_voices.get(
            voice_id, self.available_voices["voice_0"]
        )

        settings_obj = self._get_voice_settings(personality)

        if CLIENT_MODE == "new" and client:
            audio = client.text_to_speech.convert(
                text=text,
                voice=Voice(
                    voice_id=resolved_voice,
                    settings=settings_obj,
                ),
                model_id="eleven_multilingual_v2",
            )

        elif CLIENT_MODE == "old" and generate:
            audio = generate(
                text=text,
                voice=resolved_voice,
                model="eleven_multilingual_v2",
            )

        else:
            raise RuntimeError("ElevenLabs SDK not available")

        # Ensure bytes
        audio_bytes = audio if isinstance(audio, bytes) else b"".join(audio)
        return audio_bytes

    # -------------------------
    # Personality voice settings
    # -------------------------

    def _get_voice_settings(self, personality: str) -> VoiceSettings:
        presets = {
            "angry": VoiceSettings(0.3, 0.8, 0.6, True),
            "arrogant": VoiceSettings(0.7, 0.7, 0.5, True),
            "soft": VoiceSettings(0.8, 0.6, 0.3, True),
            "cold_hearted": VoiceSettings(0.9, 0.5, 0.2, False),
            "nice": VoiceSettings(0.6, 0.7, 0.4, True),
            "analytical": VoiceSettings(0.8, 0.6, 0.3, True),
        }

        return presets.get(
            personality.lower(),
            VoiceSettings(0.5, 0.75, 0.0, True),
        )

    # -------------------------
    # Assign voice to representative
    # -------------------------

    def get_voice_for_representative(
        self, rep_index: int, custom_voice_id: Optional[str] = None
    ) -> str:
        if custom_voice_id and custom_voice_id in self.available_voices:
            return self.available_voices[custom_voice_id]

        key = f"voice_{rep_index % len(self.available_voices)}"
        return self.available_voices.get(key, self.available_voices["voice_0"])

    # -------------------------
    # Speech-to-Text (placeholder)
    # -------------------------

    async def speech_to_text(self, audio_bytes: bytes) -> str:
        raise NotImplementedError("Use OpenAI Whisper for STT")


# -------------------------
# Singleton instance
# -------------------------

elevenlabs_service = ElevenLabsService()

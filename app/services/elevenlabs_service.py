


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

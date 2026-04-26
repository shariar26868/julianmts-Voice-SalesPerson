"""
Bug Condition Exploration Tests — Bug 1: Whisper Hallucinations

These tests are EXPECTED TO FAIL on unfixed code.
Failure confirms the bug exists.

Sub-condition A: The < 100 byte guard does NOT catch 500-byte audio.
  Whisper is called and may return a hallucination. The test asserts "" — FAILS.

Sub-condition B: There is no post-call hallucination filter.
  When transcribe_audio returns "Thank you." (or similar), the result is
  passed through as-is. The test asserts "" — FAILS.

DO NOT fix the code. These tests document the bug.
"""

import asyncio
import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ---------------------------------------------------------------------------
# Patch the OpenAI client at module level so whisper_service can be imported
# without a real API key in the test environment.
# ---------------------------------------------------------------------------

# We patch 'openai.AsyncOpenAI' before importing whisper_service so the
# module-level `client = AsyncOpenAI(api_key=...)` call succeeds.
_mock_openai_client = MagicMock()

openai_patcher = patch("openai.AsyncOpenAI", return_value=_mock_openai_client)
openai_patcher.start()

# Also patch settings so the import of app.config.settings doesn't fail
# if OPENAI_API_KEY is not set in the environment.
with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
    from app.services.whisper_service import WhisperService

openai_patcher.stop()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(coro):
    """Run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


def make_service(mock_transcription_return: str) -> WhisperService:
    """
    Create a WhisperService instance with transcribe_audio mocked to return
    the given string. This avoids any real API calls.
    """
    service = WhisperService()
    service.transcribe_audio = AsyncMock(return_value=mock_transcription_return)
    return service


# ---------------------------------------------------------------------------
# Sub-condition A — Pre-call size guard is too low (< 100 instead of < 4000)
# ---------------------------------------------------------------------------

class TestSubConditionA:
    """
    Bug Sub-condition A: combined audio < MIN_AUDIO_BYTES (4000 bytes) should
    return "" without calling Whisper.

    On UNFIXED code the guard is `< 100`, so 500 bytes passes through and
    transcribe_audio is called. The test asserts "" — this FAILS on unfixed code.

    Validates: Requirements 1.1, 1.2
    """

    def test_500_bytes_silence_returns_empty(self):
        """
        500 bytes of silence (b'\\x00' * 500) is above the broken < 100 guard.
        On unfixed code, transcribe_audio is called and returns a hallucination.
        Expected: "" — FAILS on unfixed code.

        Counterexample: transcribe_audio_stream([b'\\x00' * 500]) returns "Thank you."
        instead of "".
        """
        service = make_service("Thank you.")
        result = run(service.transcribe_audio_stream([b'\x00' * 500]))

        # On unfixed code this assertion FAILS because the code returns "Thank you."
        assert result == "", (
            f"BUG CONFIRMED (Sub-condition A): transcribe_audio_stream([b'\\x00' * 500]) "
            f"returned {result!r} instead of ''. "
            f"The < 100 byte guard does not catch 500-byte audio."
        )

    def test_200_bytes_silence_returns_empty(self):
        """
        200 bytes of silence is above the broken < 100 guard.
        On unfixed code, transcribe_audio is called.
        Expected: "" — FAILS on unfixed code.
        """
        service = make_service("Bye.")
        result = run(service.transcribe_audio_stream([b'\x00' * 200]))

        assert result == "", (
            f"BUG CONFIRMED (Sub-condition A): transcribe_audio_stream([b'\\x00' * 200]) "
            f"returned {result!r} instead of ''. "
            f"The < 100 byte guard does not catch 200-byte audio."
        )

    def test_3999_bytes_returns_empty(self):
        """
        3999 bytes is just below MIN_AUDIO_BYTES (4000) but well above the broken < 100 guard.
        On unfixed code, transcribe_audio is called.
        Expected: "" — FAILS on unfixed code.
        """
        service = make_service("Okay.")
        result = run(service.transcribe_audio_stream([b'\x00' * 3999]))

        assert result == "", (
            f"BUG CONFIRMED (Sub-condition A): transcribe_audio_stream([b'\\x00' * 3999]) "
            f"returned {result!r} instead of ''. "
            f"The < 100 byte guard does not catch 3999-byte audio."
        )


# ---------------------------------------------------------------------------
# Sub-condition B — No post-call hallucination filter
# ---------------------------------------------------------------------------

class TestSubConditionB:
    """
    Bug Sub-condition B: when transcribe_audio returns a known hallucination
    phrase, transcribe_audio_stream should return "" (discard the result).

    On UNFIXED code there is no hallucination filter, so the phrase is returned
    as-is. The test asserts "" — this FAILS on unfixed code.

    Validates: Requirements 1.3
    """

    def _run_with_mock_transcription(self, mock_return: str, audio_size: int = 5000) -> str:
        """Helper: run transcribe_audio_stream with mocked transcribe_audio."""
        service = make_service(mock_return)
        return run(service.transcribe_audio_stream([b'\x00' * audio_size]))

    def test_thank_you_is_discarded(self):
        """
        Whisper returns "Thank you." on 5000 bytes of near-silent audio.
        Expected: "" — FAILS on unfixed code (no hallucination filter).

        Counterexample: transcribe_audio_stream([b'\\x00' * 5000]) with
        transcribe_audio mocked to return "Thank you." returns "Thank you."
        instead of "".
        """
        result = self._run_with_mock_transcription("Thank you.")
        assert result == "", (
            f"BUG CONFIRMED (Sub-condition B): transcribe_audio_stream returned "
            f"{result!r} instead of ''. No hallucination filter for 'Thank you.'."
        )

    def test_bye_is_discarded(self):
        """
        Whisper returns "Bye." — a known hallucination phrase.
        Expected: "" — FAILS on unfixed code.

        Counterexample: returns "Bye." instead of "".
        """
        result = self._run_with_mock_transcription("Bye.")
        assert result == "", (
            f"BUG CONFIRMED (Sub-condition B): transcribe_audio_stream returned "
            f"{result!r} instead of ''. No hallucination filter for 'Bye.'."
        )

    def test_okay_is_discarded(self):
        """
        Whisper returns "Okay." — a known hallucination phrase.
        Expected: "" — FAILS on unfixed code.

        Counterexample: returns "Okay." instead of "".
        """
        result = self._run_with_mock_transcription("Okay.")
        assert result == "", (
            f"BUG CONFIRMED (Sub-condition B): transcribe_audio_stream returned "
            f"{result!r} instead of ''. No hallucination filter for 'Okay.'."
        )

    def test_uh_is_discarded(self):
        """
        Whisper returns "uh" — a single short word (word_count=1, len<10).
        Expected: "" — FAILS on unfixed code.

        Counterexample: returns "uh" instead of "".
        """
        result = self._run_with_mock_transcription("uh")
        assert result == "", (
            f"BUG CONFIRMED (Sub-condition B): transcribe_audio_stream returned "
            f"{result!r} instead of ''. No hallucination filter for 'uh'."
        )

    def test_thanks_is_discarded(self):
        """
        Whisper returns "Thanks." — a known hallucination phrase.
        Expected: "" — FAILS on unfixed code.

        Counterexample: returns "Thanks." instead of "".
        """
        result = self._run_with_mock_transcription("Thanks.")
        assert result == "", (
            f"BUG CONFIRMED (Sub-condition B): transcribe_audio_stream returned "
            f"{result!r} instead of ''. No hallucination filter for 'Thanks.'."
        )

    def test_you_too_is_discarded(self):
        """
        Whisper returns "You too." — a known hallucination phrase.
        Expected: "" — FAILS on unfixed code.

        Counterexample: returns "You too." instead of "".
        """
        result = self._run_with_mock_transcription("You too.")
        assert result == "", (
            f"BUG CONFIRMED (Sub-condition B): transcribe_audio_stream returned "
            f"{result!r} instead of ''. No hallucination filter for 'You too.'."
        )

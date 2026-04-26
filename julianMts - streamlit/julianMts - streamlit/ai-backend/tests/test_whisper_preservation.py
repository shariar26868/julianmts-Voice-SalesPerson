"""
Preservation Property Tests — Task 2

These tests MUST PASS on the current (unfixed) code.
They document the baseline behavior that must be preserved after the fix.

Property 3: Normal audio (>= MIN_AUDIO_BYTES) with a non-hallucination
transcription passes through transcribe_audio_stream unchanged.

Property 5: _build_orchestrator_prompt retains all existing routing rules,
personality rules, JSON format requirements, and representative information.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
"""

import asyncio
import os
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# ---------------------------------------------------------------------------
# Patch OpenAI client at module level so services can be imported without
# a real API key in the test environment.
# ---------------------------------------------------------------------------

_mock_openai_client = MagicMock()

openai_patcher = patch("openai.AsyncOpenAI", return_value=_mock_openai_client)
openai_patcher.start()

with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
    from app.services.whisper_service import WhisperService
    from app.services.openai_service import OpenAIService

openai_patcher.stop()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(coro):
    """Run a coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


def make_whisper_service(mock_transcription_return: str) -> WhisperService:
    """
    Create a WhisperService with transcribe_audio mocked to return the given
    string. Avoids any real API calls.
    """
    service = WhisperService()
    service.transcribe_audio = AsyncMock(return_value=mock_transcription_return)
    return service


def make_minimal_representatives():
    return [
        {
            "id": "rep_001",
            "name": "Alice Johnson",
            "role": "CFO",
            "personality_traits": ["Arrogant", "analytical"],
            "is_decision_maker": True,
            "tenure_months": 36,
            "notes": "Focused on ROI",
        }
    ]


def make_minimal_salesperson_data():
    return {
        "product_name": "SalesBot Pro",
        "description": "AI-powered sales training platform",
    }


def make_minimal_company_data():
    return {
        "company_url": "https://example.com",
        "company_data": {
            "industry": "Technology",
            "company_size": "200-500",
            "revenue": "$50M",
        },
    }


# ---------------------------------------------------------------------------
# Preservation tests for transcribe_audio_stream
# ---------------------------------------------------------------------------

class TestTranscribeAudioStreamPreservation:
    """
    Property 3: For audio_chunks where combined len >= MIN_AUDIO_BYTES and
    transcribe_audio returns a non-hallucination string, transcribe_audio_stream
    MUST return that same string unchanged.

    These tests PASS on unfixed code because the unfixed code has no
    hallucination filter — it simply returns whatever transcribe_audio returns.

    Validates: Requirements 3.1, 3.2
    """

    def test_exactly_4000_bytes_passes_through(self):
        """
        Audio of exactly 4000 bytes with transcribe_audio returning
        "What is your budget?" → result must be "What is your budget?".

        On unfixed code: combined_audio (4000 bytes) > 100 byte guard, so
        transcribe_audio is called and its return value is passed through.
        PASSES on unfixed code.
        """
        service = make_whisper_service("What is your budget?")
        result = run(service.transcribe_audio_stream([b'\x00' * 4000]))
        assert result == "What is your budget?", (
            f"Expected 'What is your budget?' but got {result!r}"
        )

    def test_5000_bytes_passes_through(self):
        """
        Audio of 5000 bytes with transcribe_audio returning
        "What is your budget?" → result must be "What is your budget?".

        PASSES on unfixed code.
        """
        service = make_whisper_service("What is your budget?")
        result = run(service.transcribe_audio_stream([b'\x00' * 5000]))
        assert result == "What is your budget?", (
            f"Expected 'What is your budget?' but got {result!r}"
        )

    def test_18000_bytes_revenue_statement_passes_through(self):
        """
        Audio of 18000 bytes with transcribe_audio returning
        "Our revenue is $5M annually." → result must be that same string.

        PASSES on unfixed code.
        """
        service = make_whisper_service("Our revenue is $5M annually.")
        result = run(service.transcribe_audio_stream([b'\x00' * 18000]))
        assert result == "Our revenue is $5M annually.", (
            f"Expected 'Our revenue is $5M annually.' but got {result!r}"
        )

    def test_10000_bytes_long_question_passes_through(self):
        """
        Audio of 10000 bytes with transcribe_audio returning
        "Can you tell me more about your pricing model?" → result must be
        that same string.

        PASSES on unfixed code.
        """
        transcription = "Can you tell me more about your pricing model?"
        service = make_whisper_service(transcription)
        result = run(service.transcribe_audio_stream([b'\x00' * 10000]))
        assert result == transcription, (
            f"Expected {transcription!r} but got {result!r}"
        )

    @pytest.mark.parametrize("audio_size,transcription", [
        (4000,  "What is your budget?"),
        (5000,  "What is your budget?"),
        (6000,  "Tell me about your current solution."),
        (8000,  "How many employees do you have?"),
        (10000, "Can you tell me more about your pricing model?"),
        (12000, "What are your main pain points right now?"),
        (15000, "Our revenue is $5M annually."),
        (18000, "Our revenue is $5M annually."),
        (20000, "We are looking for a scalable solution."),
        (50000, "This is a longer audio clip with substantive content."),
    ])
    def test_various_sizes_non_hallucination_passes_through(
        self, audio_size: int, transcription: str
    ):
        """
        Property-based parametrize: for various audio sizes >= 4000 bytes
        with non-hallucination transcription results, the result passes
        through unchanged.

        Validates: Requirements 3.1, 3.2
        """
        service = make_whisper_service(transcription)
        result = run(service.transcribe_audio_stream([b'\x00' * audio_size]))
        assert result == transcription, (
            f"audio_size={audio_size}: expected {transcription!r} but got {result!r}"
        )


# ---------------------------------------------------------------------------
# Preservation tests for _build_orchestrator_prompt
# ---------------------------------------------------------------------------

class TestBuildOrchestratorPromptPreservation:
    """
    Property 5: _build_orchestrator_prompt retains all existing routing rules,
    personality rules, JSON format requirements, and representative information.

    These tests PASS on unfixed code because the prompt already contains all
    these strings. After the fix, they must still pass.

    Validates: Requirements 3.3, 3.4, 3.5
    """

    def _build_prompt(self) -> str:
        service = OpenAIService()
        return service._build_orchestrator_prompt(
            representatives=make_minimal_representatives(),
            salesperson_data=make_minimal_salesperson_data(),
            company_data=make_minimal_company_data(),
        )

    def test_prompt_contains_critical_output_format(self):
        """
        The prompt must contain the 'CRITICAL - OUTPUT FORMAT' section header.
        PASSES on unfixed code.
        """
        prompt = self._build_prompt()
        assert "CRITICAL - OUTPUT FORMAT" in prompt, (
            "Prompt is missing 'CRITICAL - OUTPUT FORMAT' section"
        )

    def test_prompt_contains_responding_rep_id(self):
        """
        The prompt must contain 'responding_rep_id' (JSON output field).
        PASSES on unfixed code.
        """
        prompt = self._build_prompt()
        assert "responding_rep_id" in prompt, (
            "Prompt is missing 'responding_rep_id' JSON field"
        )

    def test_prompt_contains_arrogant_personalities(self):
        """
        The prompt must contain 'Arrogant personalities' (personality rule).
        PASSES on unfixed code.
        """
        prompt = self._build_prompt()
        assert "Arrogant personalities" in prompt, (
            "Prompt is missing 'Arrogant personalities' personality rule"
        )

    def test_prompt_contains_decision_makers(self):
        """
        The prompt must contain 'Decision makers' (routing rule).
        PASSES on unfixed code.
        """
        prompt = self._build_prompt()
        assert "Decision makers" in prompt, (
            "Prompt is missing 'Decision makers' routing rule"
        )

    def test_prompt_contains_responding_rep_name(self):
        """
        The prompt must contain 'responding_rep_name' (JSON output field).
        PASSES on unfixed code.
        """
        prompt = self._build_prompt()
        assert "responding_rep_name" in prompt, (
            "Prompt is missing 'responding_rep_name' JSON field"
        )

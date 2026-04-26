# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Whisper Hallucination on Short/Silent Audio
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate both sub-conditions of Bug 1
  - **Scoped PBT Approach**: Scope the property to concrete failing cases — audio chunks whose combined length is < 4000 bytes (MIN_AUDIO_BYTES), and audio above the threshold where `transcribe_audio` is mocked to return a known hallucination phrase
  - Sub-condition A: Call `transcribe_audio_stream` with `[b'\x00' * 500]` (500 bytes). On unfixed code, Whisper is called and may return a hallucination. Assert result is `""` — this assertion FAILS on unfixed code.
  - Sub-condition B: Mock `transcribe_audio` to return `"Thank you."`. Call `transcribe_audio_stream` with audio of 5000 bytes. Assert result is `""` — this assertion FAILS on unfixed code.
  - Also test: mock `transcribe_audio` to return `"Bye."`, `"Okay."`, `"uh"` — all should return `""`.
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct — it proves the bug exists)
  - Document counterexamples found (e.g., `transcribe_audio_stream([b'\x00' * 500])` returns `"Thank you."` instead of `""`)
  - Mark task complete when tests are written, run, and failures are documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Normal Audio Passes Through Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: `transcribe_audio_stream` with audio ≥ 4000 bytes and a substantive Whisper result (e.g. `"What is your budget?"`) returns `"What is your budget?"` on unfixed code
  - Observe: `transcribe_audio_stream` with audio of exactly 4000 bytes and a non-hallucination result passes through unchanged on unfixed code
  - Write property-based test: for all byte arrays with `len >= MIN_AUDIO_BYTES` where `transcribe_audio` is mocked to return a non-hallucination string, `transcribe_audio_stream` returns that same string (from Preservation Requirements 3.1, 3.2 in design)
  - Also write unit test: `_build_orchestrator_prompt` still contains `"CRITICAL - OUTPUT FORMAT"`, `"responding_rep_id"`, `"Arrogant personalities"`, and `"Decision makers"` (from Preservation Requirements 3.3–3.5 in design)
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for Whisper hallucinations and AI silent rephrasing

  - [x] 3.1 Add module-level constants and replace size guard in `whisper_service.py`
    - Add `MIN_AUDIO_BYTES = 4000` constant after imports in `app/services/whisper_service.py`
    - Add `HALLUCINATION_PATTERNS` set with: `"thank you"`, `"thanks"`, `"bye"`, `"goodbye"`, `"you too"`, `"see you"`, `"okay"`, `"ok"`, `"sure"`, `"alright"`, `"uh"`, `"um"`, `"hmm"`, `"you"`, `"the"`, `"a"`, `"i"`
    - In `transcribe_audio_stream`, replace the existing `len(combined_audio) < 100` check with `len(combined_audio) < MIN_AUDIO_BYTES` — return `""` (empty string) without calling Whisper
    - _Bug_Condition: isBugCondition_Whisper(audio_chunks) where len(join(audio_chunks)) < MIN_AUDIO_BYTES_
    - _Expected_Behavior: transcribe_audio_stream returns "" without calling transcribe_audio_
    - _Preservation: audio_chunks with combined len >= MIN_AUDIO_BYTES must still be sent to Whisper unchanged_
    - _Requirements: 2.1, 2.2, 3.1_

  - [x] 3.2 Add post-call hallucination filter in `transcribe_audio_stream`
    - After `result = await self.transcribe_audio(combined_audio)`, normalize the result: `normalized = result.lower().strip()`
    - Check if `normalized` is in `HALLUCINATION_PATTERNS`
    - Also check: `len(normalized.split()) <= 1 AND len(normalized) < 10`
    - If either condition is true, log a warning (e.g. `print(f"⚠️ Hallucination detected, discarding: '{result}'")`), and return `""`
    - Otherwise return `result` unchanged
    - _Bug_Condition: isHallucination(transcription) — normalized result in HALLUCINATION_PATTERNS or (word_count <= 1 and len < 10)_
    - _Expected_Behavior: transcribe_audio_stream returns "" when hallucination is detected_
    - _Preservation: non-hallucination transcriptions (e.g. "What is your budget?") must be returned unchanged_
    - _Requirements: 2.3, 3.2_

  - [x] 3.3 Add acknowledgment and anti-repetition rules to `_build_orchestrator_prompt`
    - In `app/services/openai_service.py`, locate the `RESPONSE RULES` section of the prompt string inside `_build_orchestrator_prompt`
    - Add the following two rules immediately before the `CRITICAL - OUTPUT FORMAT` block:
      - "If you do NOT understand the salesperson's message or need clarification, you MUST explicitly acknowledge the confusion first with a natural phrase such as \"I'm not sure I followed that — could you give me a bit more detail?\" or \"I didn't quite catch that — could you clarify?\" before asking your question. Do NOT silently rephrase or repeat a question you have already asked."
      - "If a question you want to ask already appears in the recent conversation history, do NOT repeat it verbatim or paraphrase it without first acknowledging that you are returning to it."
    - No other changes to `_build_orchestrator_prompt` — all existing sections remain identical
    - _Bug_Condition: isBugCondition_AIRephrasing — AI has no instruction to acknowledge confusion before rephrasing_
    - _Expected_Behavior: prompt contains explicit acknowledgment instruction and anti-repetition instruction_
    - _Preservation: all existing routing rules, personality rules, JSON format requirements, and representative info remain unchanged_
    - _Requirements: 2.4, 2.5, 3.3, 3.4, 3.5_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Whisper Hallucination Guards Active
    - **IMPORTANT**: Re-run the SAME tests from task 1 — do NOT write new tests
    - The tests from task 1 encode the expected behavior for both sub-conditions
    - When these tests pass, it confirms the size guard and hallucination filter are working correctly
    - Run bug condition exploration tests from step 1
    - **EXPECTED OUTCOME**: Tests PASS (confirms Bug 1 is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Normal Audio and Prompt Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions in audio passthrough or prompt structure)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint — Ensure all tests pass
  - Run the full test suite for `whisper_service.py` and `openai_service.py`
  - Confirm Property 1 (Bug Condition) tests pass — size guard and hallucination filter active
  - Confirm Property 2 (Preservation) tests pass — normal audio and prompt structure unchanged
  - Confirm all unit tests pass: size guard, hallucination filter, prompt acknowledgment rule, prompt anti-repetition rule, prompt existing sections preserved
  - Ensure all tests pass; ask the user if questions arise

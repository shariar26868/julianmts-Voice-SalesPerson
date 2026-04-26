# Conversation Quality Fix — Bugfix Design

## Overview

Two bugs degrade the realism of real-time voice conversations on the sales training platform.

**Bug 1** — `WhisperService.transcribe_audio_stream` in `whisper_service.py` calls the Whisper API unconditionally, even when the combined audio is too small to contain real speech. Whisper is known to hallucinate common filler phrases ("Thank you.", "Bye.", "Okay.") on near-silent or very short audio. The result is that the AI responds to words the salesperson never said.

**Bug 2** — `OpenAIService._build_orchestrator_prompt` in `openai_service.py` contains no instruction telling the AI to acknowledge confusion before asking for clarification. When the AI does not understand the salesperson, it silently rephrases the same question, making the conversation feel robotic.

The fix strategy is minimal and targeted:
- Add two guards inside `transcribe_audio_stream`: a pre-call byte-size check and a post-call hallucination filter.
- Add two prompt instructions inside `_build_orchestrator_prompt`: one requiring an explicit acknowledgment phrase when confused, and one prohibiting silent verbatim repetition of a prior question.

---

## Glossary

- **Bug_Condition (C)**: The condition that triggers a bug — either audio that is too short to contain real speech, or a Whisper result that matches a known hallucination pattern, or an AI response that silently rephrases a prior unanswered question.
- **Property (P)**: The desired correct behavior when the bug condition holds — an empty transcription (Bug 1) or a response that explicitly acknowledges confusion (Bug 2).
- **Preservation**: Existing behaviors that must remain unchanged — normal audio transcription, substantive AI responses, representative routing, and all other conversation logic.
- **`transcribe_audio_stream`**: The method in `app/services/whisper_service.py` that joins audio chunks and calls `transcribe_audio`. This is where both Bug 1 guards are added.
- **`transcribe_audio`**: The method in `app/services/whisper_service.py` that calls the Whisper API. It is called by `transcribe_audio_stream` and is not modified.
- **`_build_orchestrator_prompt`**: The method in `app/services/openai_service.py` that constructs the system prompt for the GPT orchestrator. The Bug 2 instructions are added here.
- **`MIN_AUDIO_BYTES`**: The minimum combined byte size below which audio is considered too short to contain real speech. Set to `4000` bytes.
- **`HALLUCINATION_PATTERNS`**: A set of lowercase normalized strings that Whisper is known to produce on near-silent audio (e.g. `"thank you"`, `"bye"`, `"okay"`).
- **`audio_chunks`**: A `List[bytes]` collected by `audio_stream_service` while the salesperson is speaking, passed to `transcribe_audio_stream`.

---

## Bug Details

### Bug 1 — Whisper Hallucinations

#### Bug Condition

The bug manifests in two distinct sub-conditions inside `transcribe_audio_stream`:

- **Sub-condition A (pre-call)**: The combined audio is below `MIN_AUDIO_BYTES`. Whisper is called anyway and returns a hallucinated phrase.
- **Sub-condition B (post-call)**: The combined audio is above the threshold but contains only silence or noise. Whisper returns a known hallucination phrase. The result is passed to the AI as a valid utterance.

**Formal Specification:**

```
FUNCTION isBugCondition_Whisper(audio_chunks)
  INPUT: audio_chunks of type List[bytes]
  OUTPUT: boolean

  combined ← join(audio_chunks)

  // Sub-condition A: audio too short to contain real speech
  IF len(combined) < MIN_AUDIO_BYTES THEN RETURN true

  // Sub-condition B: evaluated after Whisper call
  // (see isHallucination below)
  RETURN false
END FUNCTION

FUNCTION isHallucination(transcription)
  INPUT: transcription of type string
  OUTPUT: boolean

  KNOWN_HALLUCINATIONS ← {
    "thank you", "thanks", "bye", "goodbye",
    "you too", "see you", "okay", "ok",
    "sure", "alright", "uh", "um", "hmm"
  }

  normalized ← lowercase(strip(transcription))
  IF normalized IN KNOWN_HALLUCINATIONS THEN RETURN true
  IF word_count(normalized) <= 1 AND len(normalized) < 10 THEN RETURN true
  RETURN false
END FUNCTION
```

#### Examples

| Scenario | Combined bytes | Whisper result | Current behavior | Expected behavior |
|---|---|---|---|---|
| Salesperson accidentally taps mic | 800 bytes | "Thank you." | AI responds to "Thank you." | Empty transcription, no AI response |
| Background noise burst | 1 200 bytes | "Bye." | AI responds to "Bye." | Empty transcription, no AI response |
| Near-silent audio above threshold | 5 000 bytes | "Okay." | AI responds to "Okay." | Empty transcription (hallucination filtered) |
| Normal speech | 18 000 bytes | "What's your budget?" | AI responds correctly | AI responds correctly (unchanged) |

---

### Bug 2 — AI Silent Rephrasing

#### Bug Condition

The bug manifests when the AI representative does not understand the salesperson's message. The system prompt contains no instruction to acknowledge confusion, so the model silently rephrases the same question it already asked.

**Formal Specification:**

```
FUNCTION isBugCondition_AIRephrasing(conversation_history, current_message)
  INPUT: conversation_history of type List[Turn], current_message of type string
  OUTPUT: boolean

  last_ai_turn ← last turn in conversation_history WHERE speaker != "salesperson"
  IF last_ai_turn contains a question
     AND is_unclear(current_message)   // short, vague, or off-topic reply
  THEN RETURN true
  RETURN false
END FUNCTION
```

#### Examples

| Scenario | Salesperson message | Current AI behavior | Expected AI behavior |
|---|---|---|---|
| Vague reply to a question | "Uh, I don't know" | "So, what I was asking is — what is your current budget?" | "I'm not sure I followed that — could you give me a bit more detail?" |
| Off-topic reply | "Can we talk about something else?" | "Right, but going back to my earlier question about budget…" | "Of course — I'm not sure I understood where you were going. Could you clarify?" |
| Clear, on-topic reply | "Our budget is $50k" | "Great, that helps." | "Great, that helps." (unchanged) |

---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- Audio chunks above `MIN_AUDIO_BYTES` that produce a non-hallucination transcription MUST continue to be passed to the AI unchanged.
- The Whisper API call path (`transcribe_audio`) MUST remain unmodified.
- All AI response routing logic (representative selection, personality, directed-address handling) MUST remain unchanged.
- When the AI clearly understands the salesperson, responses MUST remain direct and on-topic with no added clarification preamble.
- The WebSocket conversation loop in `conversation.py` MUST NOT be modified.
- All other prompt instructions in `_build_orchestrator_prompt` (JSON format, personality rules, routing rules) MUST remain unchanged.

**Scope:**

All inputs that do NOT satisfy `isBugCondition_Whisper` or `isBugCondition_AIRephrasing` must be completely unaffected by this fix. This includes:

- Normal speech audio above the byte threshold with substantive transcription results
- Clear, unambiguous salesperson messages that the AI can answer directly
- All non-audio message types (ping, disconnect, etc.)
- The HTTP `send_message` endpoint (no changes required there)

---

## Hypothesized Root Cause

### Bug 1

1. **No minimum-size guard before the Whisper call**: `transcribe_audio_stream` only checks `len(combined_audio) < 100` (a near-zero threshold that catches nothing meaningful). Any audio above 100 bytes is sent to Whisper unconditionally, including mic noise and accidental taps.

2. **No post-call hallucination filter**: After Whisper returns, the result is used as-is. There is no check against known hallucination phrases. Whisper's documented behavior of producing filler phrases on near-silent audio is not accounted for.

3. **Threshold too low**: The existing `< 100` byte check was intended as a guard but is set far too low to catch real-world short/silent audio. A meaningful threshold is in the range of 4 000–8 000 bytes (roughly 0.25–0.5 seconds of audio at typical WebM bitrates).

### Bug 2

1. **No acknowledgment instruction in the system prompt**: `_build_orchestrator_prompt` has no rule telling the model what to do when it does not understand the salesperson. The model defaults to rephrasing, which is a common GPT behavior in the absence of explicit guidance.

2. **No anti-repetition instruction**: There is no instruction prohibiting the model from repeating a question already present in the conversation history. The model has no signal that silent repetition is undesirable.

---

## Correctness Properties

Property 1: Bug Condition A — Pre-call Size Guard

_For any_ `audio_chunks` list where the combined byte length is less than `MIN_AUDIO_BYTES` (4 000 bytes), the fixed `transcribe_audio_stream` SHALL return an empty string `""` without calling the Whisper API.

**Validates: Requirements 2.1, 2.2**

---

Property 2: Bug Condition B — Post-call Hallucination Filter

_For any_ transcription string returned by Whisper where `isHallucination(transcription)` is true (matches a known hallucination pattern or is a single short word), the fixed `transcribe_audio_stream` SHALL discard the result and return an empty string `""`.

**Validates: Requirements 2.3**

---

Property 3: Preservation — Normal Audio Passes Through Unchanged

_For any_ `audio_chunks` list where the combined byte length is ≥ `MIN_AUDIO_BYTES` AND the Whisper result does not match any hallucination pattern, the fixed `transcribe_audio_stream` SHALL return the same transcription as the original function.

**Validates: Requirements 3.1, 3.2**

---

Property 4: Bug Condition — Prompt Contains Acknowledgment Instruction

_For any_ call to `_build_orchestrator_prompt`, the returned prompt string SHALL contain an explicit instruction requiring the AI to acknowledge confusion with a natural phrase (e.g. "I'm not sure I followed that") before asking for clarification, and SHALL contain an instruction prohibiting silent verbatim repetition of a prior question.

**Validates: Requirements 2.4, 2.5**

---

Property 5: Preservation — Prompt Retains All Existing Instructions

_For any_ call to `_build_orchestrator_prompt`, the returned prompt string SHALL continue to contain all existing routing rules, personality rules, JSON format requirements, and representative information that were present before the fix.

**Validates: Requirements 3.3, 3.4, 3.5**

---

## Fix Implementation

### Changes Required

#### File: `app/services/whisper_service.py`

**Function**: `transcribe_audio_stream`

**Specific Changes**:

1. **Add module-level constants** at the top of the file (after imports):
   ```python
   MIN_AUDIO_BYTES = 4000  # ~0.25s of audio at typical WebM bitrates

   HALLUCINATION_PATTERNS = {
       "thank you", "thanks", "bye", "goodbye",
       "you too", "see you", "okay", "ok",
       "sure", "alright", "uh", "um", "hmm",
       "you", "the", "a", "i",
   }
   ```

2. **Replace the existing `< 100` byte check** with the new `MIN_AUDIO_BYTES` pre-call guard. The guard must run after `combined_audio = b''.join(audio_chunks)` and before `return await self.transcribe_audio(combined_audio)`. It must return `""` (empty string) without calling Whisper.

3. **Add a post-call hallucination filter** after the `transcribe_audio` call returns. Normalize the result (lowercase + strip), check against `HALLUCINATION_PATTERNS`, and also check the single-short-word condition (`word_count <= 1 AND len < 10`). If either matches, log a warning and return `""`.

4. **Keep all other logic unchanged**: the `audio_chunks` empty check, the `print` statements, and the exception handling remain as-is.

**Pseudocode for the fixed `transcribe_audio_stream`:**

```
FUNCTION transcribe_audio_stream(audio_chunks)
  IF audio_chunks is empty THEN RETURN ""

  combined ← join(audio_chunks)
  LOG combined size

  // Pre-call guard (replaces the old < 100 check)
  IF len(combined) < MIN_AUDIO_BYTES THEN
    LOG "Audio below minimum threshold, skipping Whisper"
    RETURN ""
  END IF

  result ← AWAIT transcribe_audio(combined)

  // Post-call hallucination filter
  IF isHallucination(result) THEN
    LOG "Hallucination detected, discarding: " + result
    RETURN ""
  END IF

  RETURN result
END FUNCTION
```

---

#### File: `app/services/openai_service.py`

**Function**: `_build_orchestrator_prompt`

**Specific Changes**:

1. **Add two new rules to the `RESPONSE RULES` section** of the prompt string, immediately after the existing personality/decision-maker rules and before the `CRITICAL - OUTPUT FORMAT` block:

   ```
   - If you do NOT understand the salesperson's message or need clarification, you MUST
     explicitly acknowledge the confusion first with a natural phrase such as
     "I'm not sure I followed that — could you give me a bit more detail?" or
     "I didn't quite catch that — could you clarify?" before asking your question.
     Do NOT silently rephrase or repeat a question you have already asked.
   - If a question you want to ask already appears in the recent conversation history,
     do NOT repeat it verbatim or paraphrase it without first acknowledging that you
     are returning to it.
   ```

2. **No other changes** to `_build_orchestrator_prompt`. All existing sections (COMPANY INFORMATION, PRODUCT, REPRESENTATIVES, TASK, existing RESPONSE RULES, OUTPUT FORMAT) remain identical.

---

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate each bug on the unfixed code, then verify the fix works correctly and preserves existing behavior.

---

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm or refute the root cause analysis.

**Test Plan**: Write unit tests that call `transcribe_audio_stream` with short/silent audio and assert the result is empty. Run on UNFIXED code to observe that the guard is missing. Write a test that calls `_build_orchestrator_prompt` and checks for the acknowledgment instruction. Run on UNFIXED code to observe it is absent.

**Test Cases**:

1. **Short audio test** (Bug 1A): Call `transcribe_audio_stream` with `[b'\x00' * 500]` (500 bytes of silence). On unfixed code, Whisper is called and may return a hallucination. (will fail on unfixed code)
2. **Hallucination filter test** (Bug 1B): Mock `transcribe_audio` to return `"Thank you."`. Call `transcribe_audio_stream` with audio above the threshold. On unfixed code, `"Thank you."` is returned as-is. (will fail on unfixed code)
3. **Prompt acknowledgment test** (Bug 2): Call `_build_orchestrator_prompt` and assert the returned string contains `"acknowledge"` or `"I'm not sure I followed"`. On unfixed code, this assertion fails. (will fail on unfixed code)

**Expected Counterexamples**:
- `transcribe_audio_stream` returns a non-empty hallucination string for short audio
- `_build_orchestrator_prompt` returns a prompt with no acknowledgment instruction

---

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**

```
// Bug 1A
FOR ALL audio_chunks WHERE len(join(audio_chunks)) < MIN_AUDIO_BYTES DO
  result ← transcribe_audio_stream_fixed(audio_chunks)
  ASSERT result = ""
END FOR

// Bug 1B
FOR ALL transcription WHERE isHallucination(transcription) DO
  // with transcribe_audio mocked to return transcription
  result ← transcribe_audio_stream_fixed(audio_above_threshold)
  ASSERT result = ""
END FOR

// Bug 2
prompt ← _build_orchestrator_prompt_fixed(representatives, salesperson, company)
ASSERT prompt CONTAINS acknowledgment_instruction
ASSERT prompt CONTAINS anti_repetition_instruction
```

---

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**

```
// Bug 1 preservation
FOR ALL audio_chunks WHERE len(join(audio_chunks)) >= MIN_AUDIO_BYTES
                       AND NOT isHallucination(transcribe_audio(audio_chunks)) DO
  ASSERT transcribe_audio_stream(audio_chunks) = transcribe_audio_stream_fixed(audio_chunks)
END FOR

// Bug 2 preservation
FOR ALL (representatives, salesperson, company) DO
  original_prompt ← _build_orchestrator_prompt(representatives, salesperson, company)
  fixed_prompt    ← _build_orchestrator_prompt_fixed(representatives, salesperson, company)
  // All sections except the two new rules must be identical
  ASSERT original_prompt SUBSET_OF fixed_prompt
END FOR
```

**Testing Approach**: Property-based testing is recommended for Bug 1 preservation because:
- It generates many random byte arrays automatically across the input domain
- It catches edge cases near the threshold boundary
- It provides strong guarantees that normal audio is unaffected

**Test Cases**:

1. **Normal audio preservation**: Mock `transcribe_audio` to return `"What is your budget?"`. Call `transcribe_audio_stream_fixed` with audio ≥ `MIN_AUDIO_BYTES`. Assert result equals `"What is your budget?"`.
2. **Threshold boundary**: Audio of exactly `MIN_AUDIO_BYTES` bytes must be sent to Whisper (not blocked).
3. **Prompt existing rules preserved**: Assert the fixed prompt still contains `"CRITICAL - OUTPUT FORMAT"`, `"Arrogant personalities"`, `"Decision makers"`, and all representative data.

---

### Unit Tests

- Test `transcribe_audio_stream` with combined audio < `MIN_AUDIO_BYTES` → returns `""`
- Test `transcribe_audio_stream` with combined audio = `MIN_AUDIO_BYTES` → calls Whisper (not blocked)
- Test `transcribe_audio_stream` with combined audio > `MIN_AUDIO_BYTES` and mocked Whisper returning `"Thank you."` → returns `""`
- Test `transcribe_audio_stream` with combined audio > `MIN_AUDIO_BYTES` and mocked Whisper returning `"What is your budget?"` → returns `"What is your budget?"`
- Test `isHallucination` for each entry in `HALLUCINATION_PATTERNS` → returns `True`
- Test `isHallucination` for a single short word not in the list (e.g. `"hi"`) → returns `True` (len < 10, word count = 1)
- Test `isHallucination` for a substantive phrase → returns `False`
- Test `_build_orchestrator_prompt` returns a string containing the acknowledgment instruction
- Test `_build_orchestrator_prompt` returns a string containing the anti-repetition instruction
- Test `_build_orchestrator_prompt` still contains `"CRITICAL - OUTPUT FORMAT"` and `"responding_rep_id"`

---

### Property-Based Tests

- **Property 1 (PBT)**: Generate random byte arrays with `len < MIN_AUDIO_BYTES`. For all such inputs, `transcribe_audio_stream_fixed` returns `""` without calling Whisper.
- **Property 2 (PBT)**: Generate random strings from `HALLUCINATION_PATTERNS` (and single-word strings < 10 chars). For all such inputs, `isHallucination` returns `True`.
- **Property 3 (PBT)**: Generate random byte arrays with `len >= MIN_AUDIO_BYTES` and mock Whisper to return a non-hallucination string. For all such inputs, `transcribe_audio_stream_fixed` returns the same value as the original.
- **Property 5 (PBT)**: Generate random representative/salesperson/company data. For all such inputs, the fixed prompt contains all the same sections as the original prompt plus the two new instructions.

---

### Integration Tests

- Full WebSocket conversation flow: send a short audio chunk (< `MIN_AUDIO_BYTES`) and verify no `transcription` event is emitted to the client (or an empty one is).
- Full WebSocket conversation flow: send normal audio and verify the conversation proceeds as before.
- End-to-end AI response test: send a vague salesperson message after the AI has asked a question and verify the AI response contains an acknowledgment phrase.
- Regression test: send a clear salesperson message and verify the AI response does NOT contain an unnecessary clarification preamble.

# Bugfix Requirements Document

## Introduction

Two related bugs degrade the quality of real-time voice conversations between a salesperson and AI company representatives on the sales training platform.

**Bug 1 — Whisper hallucinations on short/silent audio**: The Whisper STT service is called unconditionally on every audio chunk, regardless of size or content. Whisper is known to hallucinate common phrases (e.g. "Thank you.", "You too.", "Bye.") when given near-silent or very short audio. This causes the AI to respond to words the salesperson never said, breaking the realism of the conversation.

**Bug 2 — AI silently rephrasing unanswered questions**: When the AI representative does not understand the salesperson's input, it silently rephrases the same question instead of acknowledging the confusion. This makes the conversation feel unnatural and robotic — the opposite of a genuine business meeting.

Both bugs must be fixed together because they share the same goal: making the conversation feel smooth, clean, and real.

---

## Bug Analysis

### Current Behavior (Defect)

**Bug 1 — Whisper hallucinations**

1.1 WHEN the combined audio chunks are smaller than a meaningful minimum byte threshold THEN the system sends the audio to Whisper and returns a hallucinated transcription (e.g. "Thank you.", "Bye.", "You too.")

1.2 WHEN the audio contains only silence or background noise THEN the system sends it to Whisper and returns a hallucinated phrase as if the salesperson spoke

1.3 WHEN Whisper returns a transcription that matches a known hallucination pattern (very short, common filler phrase, no meaningful content) THEN the system treats it as a valid utterance and passes it to the AI for a response

**Bug 2 — AI silently rephrasing questions**

1.4 WHEN the AI representative does not understand the salesperson's message THEN the system generates a response that rephrases the same question in different words without acknowledging the confusion

1.5 WHEN the AI representative needs clarification THEN the system produces a response that gives no signal to the salesperson that their message was unclear

### Expected Behavior (Correct)

**Bug 1 — Whisper hallucinations**

2.1 WHEN the combined audio chunks are smaller than a meaningful minimum byte threshold THEN the system SHALL discard the audio and return an empty transcription without calling Whisper

2.2 WHEN the audio contains only silence or background noise THEN the system SHALL detect this before calling Whisper and return an empty transcription

2.3 WHEN Whisper returns a transcription that matches a known hallucination pattern THEN the system SHALL discard the result and return an empty transcription, preventing a spurious AI response

**Bug 2 — AI silently rephrasing questions**

2.4 WHEN the AI representative does not understand the salesperson's message THEN the system SHALL generate a response that explicitly acknowledges the confusion with a natural phrase such as "I'm not sure I understood that — could you give me a bit more detail?" before asking for clarification

2.5 WHEN the AI representative needs clarification THEN the system SHALL produce a response that clearly signals to the salesperson that their message was unclear, so the conversation feels like a genuine business meeting

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the audio chunks contain a sufficient amount of audio data above the minimum threshold THEN the system SHALL CONTINUE TO send the audio to Whisper and return the transcription as before

3.2 WHEN Whisper returns a substantive transcription that does not match any hallucination pattern THEN the system SHALL CONTINUE TO pass it to the AI unchanged

3.3 WHEN the AI representative clearly understands the salesperson's message THEN the system SHALL CONTINUE TO generate a direct, on-topic response without any unnecessary clarification preamble

3.4 WHEN the salesperson addresses a specific representative by name THEN the system SHALL CONTINUE TO route the response to that representative

3.5 WHEN the conversation is proceeding normally with clear audio and clear messages THEN the system SHALL CONTINUE TO behave exactly as before, with no change in response quality, latency, or routing logic

---

## Bug Condition Pseudocode

### Bug 1 — Whisper Hallucination

**Bug Condition Function:**
```pascal
FUNCTION isBugCondition_Whisper(audio_chunks)
  INPUT: audio_chunks of type List[bytes]
  OUTPUT: boolean

  combined ← join(audio_chunks)

  // Condition A: audio is too short to contain real speech
  IF len(combined) < MIN_AUDIO_BYTES THEN RETURN true

  // Condition B: transcription result is a known hallucination
  // (evaluated after Whisper call — used for post-call filtering)
  RETURN false
END FUNCTION

FUNCTION isHallucination(transcription)
  INPUT: transcription of type string
  OUTPUT: boolean

  KNOWN_HALLUCINATIONS ← ["thank you", "thanks", "bye", "goodbye",
                           "you too", "see you", "okay", "ok",
                           "sure", "alright", "uh", "um", "hmm"]

  normalized ← lowercase(strip(transcription))
  IF normalized IN KNOWN_HALLUCINATIONS THEN RETURN true
  IF len(normalized.split()) <= 1 AND len(normalized) < 10 THEN RETURN true
  RETURN false
END FUNCTION
```

**Fix Checking Property:**
```pascal
// Property: Whisper is not called on short/silent audio
FOR ALL audio_chunks WHERE isBugCondition_Whisper(audio_chunks) DO
  result ← transcribe_audio_stream'(audio_chunks)
  ASSERT result = ""   // empty — Whisper was never called
END FOR

// Property: Hallucinated transcriptions are discarded
FOR ALL transcription WHERE isHallucination(transcription) DO
  result ← filter_transcription'(transcription)
  ASSERT result = ""
END FOR
```

**Preservation Property:**
```pascal
// Property: Normal audio is unaffected
FOR ALL audio_chunks WHERE NOT isBugCondition_Whisper(audio_chunks) DO
  ASSERT transcribe_audio_stream(audio_chunks) = transcribe_audio_stream'(audio_chunks)
END FOR
```

---

### Bug 2 — AI Silent Rephrasing

**Bug Condition Function:**
```pascal
FUNCTION isBugCondition_AIRephrasing(conversation_history, current_message)
  INPUT: conversation_history of type List[Turn], current_message of type string
  OUTPUT: boolean

  // Bug triggers when the AI has already asked a question
  // and the salesperson's reply is unclear or very short
  last_ai_turn ← last turn in conversation_history WHERE speaker != "salesperson"
  IF last_ai_turn contains a question AND is_unclear(current_message) THEN
    RETURN true
  RETURN false
END FUNCTION
```

**Fix Checking Property:**
```pascal
// Property: AI explicitly acknowledges confusion instead of silently rephrasing
FOR ALL (history, message) WHERE isBugCondition_AIRephrasing(history, message) DO
  response ← generate_multi_agent_response'(history, message)
  ASSERT response.response_text contains acknowledgment phrase
         (e.g. "I'm not sure I understood", "could you clarify", "could you give me more detail")
  ASSERT response.response_text does NOT silently repeat the previous question verbatim
END FOR
```

**Preservation Property:**
```pascal
// Property: Clear messages are answered directly without clarification preamble
FOR ALL (history, message) WHERE NOT isBugCondition_AIRephrasing(history, message) DO
  ASSERT generate_multi_agent_response(history, message).response_text
       = generate_multi_agent_response'(history, message).response_text
       // (functionally equivalent — no spurious clarification added)
END FOR
```

# Requirements Document

## Introduction

This feature adds a Gender field (Male/Female) to the Salesperson profile. When a salesperson is created or updated, their gender is stored in MongoDB. During AI-driven sales practice conversations, the ElevenLabs TTS voice assigned to each AI representative is selected based on the salesperson's gender — male salesperson profiles receive male AI voices, female profiles receive female AI voices. Currently all AI representative voices default to female voices regardless of the salesperson's gender.

## Glossary

- **Salesperson**: The user who is practicing sales skills. Identified by a `salesperson_id` stored in MongoDB.
- **Gender**: A binary attribute (`male` or `female`) stored on the Salesperson document that controls which pool of ElevenLabs voices is used for AI representatives in that salesperson's conversations.
- **AI Representative (Rep)**: An AI-controlled participant in a practice meeting, whose speech is synthesized via ElevenLabs TTS.
- **Voice_Pool**: A predefined set of ElevenLabs voice IDs grouped by gender. The Male_Voice_Pool contains male voices; the Female_Voice_Pool contains female voices.
- **Voice_Resolver**: The component inside `ElevenLabsService` responsible for selecting a voice ID from the correct pool based on salesperson gender.
- **SalespersonCreate**: The Pydantic model in `app/models/schemas.py` used to validate salesperson creation input.
- **SalespersonResponse**: The Pydantic model in `app/models/schemas.py` used to serialize salesperson data in API responses.
- **TTS**: Text-to-Speech synthesis performed by ElevenLabs.
- **Default_Gender**: The gender value applied when no gender is provided. Defaults to `female` to preserve backward compatibility with existing salesperson records.

---

## Requirements

### Requirement 1: Gender Field on Salesperson Profile

**User Story:** As a user creating a salesperson profile, I want to specify the salesperson's gender, so that the system can select appropriately gendered AI voices during practice conversations.

#### Acceptance Criteria

1. THE `SalespersonCreate` model SHALL include an optional `gender` field whose accepted values are exactly `"male"` and `"female"` (case-sensitive).
2. WHEN a salesperson creation request is received without a `gender` value, THE System SHALL store `"female"` as the default gender for that salesperson.
3. WHEN a salesperson creation request is received with a `gender` value that is not `"male"` or `"female"`, THE System SHALL return an HTTP 422 response containing a `detail` array with at least one entry whose `loc` includes `"gender"` and whose `msg` states the value is not a valid gender.
4. THE `SalespersonResponse` model SHALL include the `gender` field so that clients can read the stored gender value.
5. WHEN a salesperson profile is retrieved via `GET /api/salesperson/{salesperson_id}`, THE System SHALL include the `gender` field in the response body.

---

### Requirement 2: Persist Gender During Salesperson Creation

**User Story:** As a developer, I want the gender field to be saved to MongoDB when a salesperson is created, so that it is available for voice selection during conversations.

#### Acceptance Criteria

1. WHEN `POST /api/salesperson/with-files` is called with a `gender` form field whose value is `"male"` or `"female"`, THE System SHALL store exactly that value in the `gender` field of the salesperson MongoDB document.
2. WHEN `POST /api/salesperson/with-files` is called without a `gender` form field, THE System SHALL store `"female"` in the `gender` field of the salesperson MongoDB document.
3. WHEN `POST /api/salesperson/with-files` is called with a `gender` value that is not `"male"` or `"female"`, THE System SHALL return an HTTP 422 response and SHALL NOT insert any document into the salesperson collection.
4. THE System SHALL include `gender` in the OpenAPI schema for the `POST /api/salesperson/with-files` multipart form body so that API clients can discover and send the field.

---

### Requirement 3: Gender-Based Voice Pool Selection

**User Story:** As a user practicing sales, I want the AI representatives to speak with voices that match my salesperson's gender, so that the practice scenario feels consistent and realistic.

#### Acceptance Criteria

1. THE `ElevenLabsService` SHALL define a `Male_Voice_Pool` as a non-empty list of at least two distinct ElevenLabs voice IDs that correspond to male voices.
2. THE `ElevenLabsService` SHALL define a `Female_Voice_Pool` as a non-empty list of at least two distinct ElevenLabs voice IDs that correspond to female voices.
3. WHEN `text_to_speech()` is called with `gender="male"` and no explicit `voice_id`, THE `Voice_Resolver` SHALL select a voice ID at random from the `Male_Voice_Pool`.
4. WHEN `text_to_speech()` is called with `gender="male"`, no explicit `voice_id`, and the `Male_Voice_Pool` contains zero entries, THE System SHALL raise a `RuntimeError` with a message indicating the male voice pool is empty.
5. WHEN `text_to_speech()` is called with `gender="female"` and no explicit `voice_id`, THE `Voice_Resolver` SHALL select a voice ID at random from the `Female_Voice_Pool`.
6. WHEN `text_to_speech()` is called with `gender="female"`, no explicit `voice_id`, and the `Female_Voice_Pool` contains zero entries, THE System SHALL raise a `RuntimeError` with a message indicating the female voice pool is empty.
7. WHEN `text_to_speech()` is called with an explicit `voice_id` whose length is greater than 10 characters, THE `Voice_Resolver` SHALL use that explicit `voice_id` regardless of the `gender` parameter.
8. WHEN `text_to_speech()` is called with an explicit `voice_id` whose length is 10 characters or fewer, THE `Voice_Resolver` SHALL ignore the `voice_id` and select from the pool determined by the `gender` parameter.
9. WHEN `text_to_speech()` is called without a `gender` parameter, THE `Voice_Resolver` SHALL default to selecting a voice ID at random from the `Female_Voice_Pool`.
10. WHEN `text_to_speech()` is called with a `gender` value that is neither `"male"` nor `"female"`, THE `Voice_Resolver` SHALL select a voice ID at random from the `Female_Voice_Pool`.

---

### Requirement 4: Pass Salesperson Gender Through the Conversation Flow

**User Story:** As a developer, I want the salesperson's gender to be retrieved and forwarded to the TTS service during every conversation turn, so that voice selection is always gender-consistent.

#### Acceptance Criteria

1. WHEN a conversation turn is processed in `POST /api/conversation/send-message`, THE System SHALL retrieve the `gender` field from the salesperson's MongoDB document identified by `meeting.salesperson_id`.
2. WHEN generating TTS audio for the AI-selected responding representative in `POST /api/conversation/send-message`, THE System SHALL pass the salesperson's `gender` value as the `gender` argument to `elevenlabs_service.text_to_speech()`.
3. IF the salesperson document does not contain a `gender` field, THEN THE System SHALL pass `"female"` as the `gender` argument to `elevenlabs_service.text_to_speech()`.
4. WHEN the WebSocket live conversation endpoint generates TTS audio via `elevenlabs_service.text_to_speech()`, THE System SHALL pass the salesperson's `gender` value (or `"female"` if absent) as the `gender` argument.
5. WHEN the WebSocket live conversation endpoint generates TTS audio via `elevenlabs_service.stream_tts_websocket()`, THE System SHALL pass the salesperson's `gender` value (or `"female"` if absent) as the `gender` argument.

---

### Requirement 5: Gender Persistence on Salesperson Update

**User Story:** As a user, I want to be able to update the gender on an existing salesperson profile, so that I can correct it if it was set incorrectly.

#### Acceptance Criteria

1. WHEN `PUT /api/salesperson/{salesperson_id}` is called with a `gender` form field whose value is `"male"` or `"female"`, THE System SHALL update the `gender` field in the salesperson MongoDB document to exactly that value.
2. WHEN `PUT /api/salesperson/{salesperson_id}` is called without a `gender` form field, THE System SHALL leave the existing `gender` value in the MongoDB document unchanged.
3. WHEN `PUT /api/salesperson/{salesperson_id}` is called with a `gender` value that is not `"male"` or `"female"`, THE System SHALL return an HTTP 422 response containing a `detail` array with at least one entry whose `loc` includes `"gender"` and SHALL NOT modify the salesperson document.

---

### Requirement 6: Backward Compatibility for Existing Salesperson Records

**User Story:** As a system operator, I want existing salesperson records without a gender field to continue working without errors, so that the deployment of this feature does not break any active sessions.

#### Acceptance Criteria

1. WHEN the System reads a salesperson document from MongoDB whose `gender` field is absent, THE System SHALL use `"female"` as the gender value for all voice pool selection calls.
2. WHEN the System reads a salesperson document from MongoDB whose `gender` field is `null`, THE System SHALL use `"female"` as the gender value for all voice pool selection calls.
3. THE System SHALL NOT require any database migration, index creation, or document backfill to operate correctly after deployment of this feature.
4. WHEN `GET /api/salesperson/{salesperson_id}` is called for a salesperson document that has no `gender` field, THE System SHALL return `"female"` as the `gender` value in the response body.

# Domain Boundaries Planning

## 🎯 Question: Where should competition demo analysis live?

### Current Structure:
```
app/domains/
├── gladia/          # STT transcription domain
└── competition/     # Competition-specific logic?
```

## 🤔 Domain Analysis

### Option 1: Keep Competition Separate
```
app/domains/
├── gladia/
│   ├── entities/stt_session.py
│   ├── value_objects/transcript.py
│   └── services/stt_domain_service.py
├── competition/
│   ├── entities/demo_session.py
│   ├── entities/leaderboard.py
│   ├── services/scoring_service.py
│   └── mcp/competition_mcp_handler.py
└── feedback/
    ├── entities/feedback_report.py
    └── services/ai_feedback_service.py
```

**Pros:**
- Clear separation between STT technology and business domain
- Competition domain owns its own entities and rules
- Could be reused for different STT providers (not just Gladia)
- Business logic separate from infrastructure

**Cons:**
- More domains to manage
- Potential circular dependencies
- Competition demo is tightly coupled to transcription

### Option 2: Everything in Gladia Domain
```
app/domains/
└── gladia/
    ├── entities/
    │   ├── stt_session.py
    │   └── demo_session.py      # Competition-specific
    ├── value_objects/
    │   ├── transcript.py
    │   └── demo_score.py        # Competition-specific
    ├── services/
    │   ├── stt_domain_service.py
    │   ├── demo_analysis_service.py
    │   └── leaderboard_service.py
    └── mcp/
        └── gladia_mcp_handler.py  # All MCP tools here
```

**Pros:**
- Single domain for all transcription + analysis
- Simpler structure
- Direct access to transcript data
- All MCP tools in one place

**Cons:**
- Mixed infrastructure (Gladia API) with business logic
- Less modular
- Harder to swap STT providers
- Domain becomes too broad

### Option 3: Pitch Analysis Domain
```
app/domains/
├── gladia/
│   ├── entities/stt_session.py
│   ├── value_objects/transcript.py
│   └── services/stt_domain_service.py
└── pitch_analysis/              # NEW: Core business domain
    ├── entities/
    │   ├── pitch_session.py     # Business entity
    │   ├── pitch_score.py
    │   └── leaderboard.py
    ├── services/
    │   ├── pitch_recording_service.py
    │   ├── pitch_scoring_service.py
    │   └── pitch_feedback_service.py
    ├── repositories/
    │   └── pitch_session_repository.py
    └── mcp/
        └── pitch_analysis_mcp_handler.py
```

**Pros:**
- Clean business domain focused on pitch analysis
- Technology-agnostic (could use any STT service)
- Clear business terminology
- MCP tools focused on pitch analysis workflow

**Cons:**
- Need integration layer between domains
- More complex

## 🎯 Recommended Approach: Option 3

### Why Pitch Analysis Domain?

1. **Business-Focused**: The core value is analyzing pitches, not STT technology
2. **Technology Independence**: Could work with Whisper, Azure STT, etc.
3. **Clear Boundaries**: 
   - Gladia = Speech-to-Text infrastructure
   - Pitch Analysis = Business logic for competition
4. **MCP Alignment**: MCP tools should be business-focused

### Domain Responsibilities:

#### `domains/gladia/`
- **Purpose**: STT technology integration
- **Owns**: Audio processing, transcription, Gladia API
- **Entities**: STTSession, TranscriptSegment
- **Services**: STT processing, WebSocket management

#### `domains/pitch_analysis/`
- **Purpose**: Competition pitch analysis business logic
- **Owns**: Scoring, feedback, leaderboards, competitions
- **Entities**: PitchSession, PitchScore, Leaderboard
- **Services**: Recording workflow, scoring, feedback generation
- **MCP**: Business workflow tools

### Integration Pattern:
```python
# pitch_analysis domain uses gladia domain
class PitchRecordingService:
    def __init__(self, stt_service: STTDomainService):
        self.stt_service = stt_service
    
    async def process_pitch_audio(self, pitch_session: PitchSession):
        # Use Gladia STT
        transcript = await self.stt_service.transcribe_audio(audio_file)
        
        # Apply business logic
        pitch_session.set_transcript(transcript)
        score = await self.score_pitch(transcript)
        pitch_session.set_score(score)
```

## 🚀 Proposed Structure

```
app/domains/
├── gladia/
│   ├── entities/stt_session.py
│   ├── value_objects/
│   │   ├── audio_configuration.py
│   │   ├── session_id.py
│   │   └── transcript.py
│   ├── services/stt_domain_service.py
│   ├── repositories/
│   │   ├── gladia_api_repository.py
│   │   └── stt_session_repository.py
│   └── infrastructure/
│       └── gladia_api_client.py
└── pitch_analysis/
    ├── entities/
    │   ├── pitch_session.py
    │   ├── pitch_score.py
    │   ├── pitch_feedback.py
    │   └── leaderboard.py
    ├── value_objects/
    │   ├── pitch_id.py
    │   └── scoring_criteria.py
    ├── services/
    │   ├── pitch_recording_service.py
    │   ├── pitch_scoring_service.py
    │   ├── pitch_feedback_service.py
    │   └── leaderboard_service.py
    ├── repositories/
    │   └── pitch_session_repository.py
    ├── mcp/
    │   ├── pitch_mcp_handler.py
    │   └── mcp_schemas.py
    └── application/
        └── pitch_workflow_service.py
```

## 🎪 MCP Flow in Pitch Analysis Domain

### MCP Tools:
1. `record_pitch_demo()` - Start recording
2. `stop_pitch_recording()` - Stop and process
3. `score_pitch()` - Generate scores  
4. `get_leaderboard()` - Show rankings
5. `generate_pitch_feedback()` - Individual feedback

### Flow:
```
MCP: record_pitch_demo("Team Alpha", "FinTech Solution")
  → pitch_analysis creates PitchSession
  → Uses gladia domain for STT
  → Returns session_id

MCP: stop_pitch_recording(session_id)  
  → pitch_analysis coordinates transcription
  → Automatically triggers scoring
  → Updates leaderboard
  → Generates feedback

MCP: get_leaderboard()
  → Returns ranked list of all pitches

MCP: generate_pitch_feedback(session_id)
  → Returns detailed individual feedback
```

Does this domain structure make more sense? Should we go with `pitch_analysis` as the main business domain?
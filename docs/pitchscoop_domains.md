# PitchScoop Domain Architecture

## 🏗️ Domain Structure

```
app/domains/
├── gladia/              # STT transcription infrastructure
├── scoop_score/         # Scoring and evaluation logic
├── leaderboard/         # Rankings and competition standings  
├── team_feedback/       # Individual team feedback and reports
└── chat/               # Chat and communication features
```

## 🎯 Domain Responsibilities

### 1. `domains/gladia/`
**Purpose**: Speech-to-text transcription infrastructure
- **Entities**: STTSession, WebSocketConnection
- **Value Objects**: AudioConfiguration, TranscriptSegment, TranscriptCollection
- **Services**: STTDomainService, AudioProcessingService
- **Infrastructure**: GladiaAPIClient, WebSocketManager
- **Responsibilities**:
  - Audio recording and processing
  - Real-time transcription via Gladia API
  - Transcript storage and retrieval
  - Audio quality validation

### 2. `domains/scoop_score/`
**Purpose**: Pitch scoring and evaluation logic
- **Entities**: PitchScore, ScoringCriteria, ScoreCalculation
- **Value Objects**: ScoreBreakdown, EvaluationMetrics
- **Services**: ScoringService, CriteriaEvaluationService
- **Responsibilities**:
  - Define scoring criteria (technical clarity, presentation skills, etc.)
  - Calculate scores from transcripts and metadata
  - AI-powered content analysis
  - Score validation and normalization
  - Historical scoring trends

### 3. `domains/leaderboard/`
**Purpose**: Competition rankings and standings
- **Entities**: Leaderboard, LeaderboardEntry, Competition
- **Value Objects**: Ranking, CompetitionPeriod
- **Services**: LeaderboardService, RankingCalculationService
- **Responsibilities**:
  - Maintain real-time leaderboards
  - Calculate rankings based on scores
  - Handle tie-breaking logic
  - Competition lifecycle management
  - Historical leaderboard snapshots

### 4. `domains/team_feedback/`
**Purpose**: Individual team feedback and reporting
- **Entities**: FeedbackReport, Team, PitchSession
- **Value Objects**: FeedbackCategory, Recommendation, ImprovementArea
- **Services**: FeedbackGenerationService, ReportGenerationService
- **Responsibilities**:
  - Generate personalized feedback reports
  - AI-powered improvement suggestions
  - Comparative analysis vs other teams
  - Progress tracking over time
  - Report delivery and formatting

### 5. `domains/chat/`
**Purpose**: Communication and interaction features
- **Entities**: ChatSession, Message, Participant
- **Value Objects**: MessageContent, ChatContext
- **Services**: ChatService, NotificationService
- **Responsibilities**:
  - Team communication during events
  - Judge/organizer messaging
  - Real-time notifications
  - Chat history and search
  - Integration with other domains for context

## 🔄 Domain Interactions & Flow

### **Record → Score → Leaderboard → Individual Feedback Flow**

```
1. RECORD (gladia domain)
   ├── Audio recording starts
   ├── Real-time transcription via Gladia
   └── Transcript stored

2. SCORE (scoop_score domain)  
   ├── Retrieves transcript from gladia
   ├── AI analysis of content
   ├── Calculates scores across criteria
   └── Stores PitchScore

3. LEADERBOARD (leaderboard domain)
   ├── Receives score from scoop_score
   ├── Updates real-time rankings
   ├── Recalculates positions
   └── Publishes leaderboard updates

4. INDIVIDUAL FEEDBACK (team_feedback domain)
   ├── Gets transcript from gladia
   ├── Gets score breakdown from scoop_score
   ├── Gets ranking context from leaderboard
   ├── Generates personalized feedback
   └── Delivers report to team
```

### **Domain Dependencies**

```
team_feedback → depends on → gladia, scoop_score, leaderboard
leaderboard   → depends on → scoop_score
scoop_score   → depends on → gladia
chat          → depends on → team_feedback (for context)
gladia        → independent (pure infrastructure)
```

## 🎪 MCP Integration Strategy

### **MCP Tools Distribution**

Each domain exposes its own MCP tools:

#### `gladia/mcp/`
```python
@mcp_tool("start_transcription")
@mcp_tool("stop_transcription") 
@mcp_tool("get_transcript")
```

#### `scoop_score/mcp/`
```python
@mcp_tool("calculate_pitch_score")
@mcp_tool("get_scoring_breakdown")
@mcp_tool("analyze_presentation_quality")
```

#### `leaderboard/mcp/`
```python
@mcp_tool("get_current_leaderboard")
@mcp_tool("get_team_ranking")
@mcp_tool("create_competition_event")
```

#### `team_feedback/mcp/`
```python
@mcp_tool("generate_team_feedback")
@mcp_tool("get_feedback_report")
@mcp_tool("compare_team_performance")
```

#### `chat/mcp/`
```python
@mcp_tool("send_team_message")
@mcp_tool("broadcast_announcement")
@mcp_tool("get_chat_history")
```

### **Orchestration MCP Handler**
```python
# app/mcp/pitch_scoop_orchestrator.py
@mcp_tool("record_and_analyze_pitch")
async def record_and_analyze_pitch(team_name, demo_title):
    """Complete flow: Record → Score → Update Leaderboard → Generate Feedback"""
    
    # 1. Start recording (gladia domain)
    session = await gladia_handler.start_transcription(team_name, demo_title)
    
    # 2. Calculate score (scoop_score domain) 
    score = await scoop_score_handler.calculate_pitch_score(session.transcript)
    
    # 3. Update leaderboard (leaderboard domain)
    await leaderboard_handler.update_team_score(team_name, score)
    
    # 4. Generate feedback (team_feedback domain)
    feedback = await team_feedback_handler.generate_team_feedback(session, score)
    
    return {
        "session_id": session.id,
        "score": score.overall_score,
        "rank": await leaderboard_handler.get_team_rank(team_name),
        "feedback_generated": True
    }
```

## 📁 Proposed Directory Structure

```
app/domains/
├── gladia/
│   ├── entities/
│   │   ├── stt_session.py
│   │   └── websocket_connection.py
│   ├── value_objects/
│   │   ├── audio_configuration.py
│   │   ├── session_id.py
│   │   └── transcript.py
│   ├── services/
│   │   └── stt_domain_service.py
│   ├── repositories/
│   │   └── gladia_api_repository.py
│   ├── infrastructure/
│   │   └── gladia_api_client.py
│   └── mcp/
│       └── gladia_mcp_handler.py
├── scoop_score/
│   ├── entities/
│   │   ├── pitch_score.py
│   │   └── scoring_criteria.py
│   ├── value_objects/
│   │   └── score_breakdown.py
│   ├── services/
│   │   └── scoring_service.py
│   └── mcp/
│       └── scoring_mcp_handler.py
├── leaderboard/
│   ├── entities/
│   │   ├── leaderboard.py
│   │   ├── leaderboard_entry.py
│   │   └── competition.py
│   ├── value_objects/
│   │   └── ranking.py
│   ├── services/
│   │   └── leaderboard_service.py
│   └── mcp/
│       └── leaderboard_mcp_handler.py
├── team_feedback/
│   ├── entities/
│   │   ├── feedback_report.py
│   │   ├── team.py
│   │   └── pitch_session.py
│   ├── value_objects/
│   │   ├── feedback_category.py
│   │   └── improvement_area.py
│   ├── services/
│   │   └── feedback_generation_service.py
│   └── mcp/
│       └── feedback_mcp_handler.py
└── chat/
    ├── entities/
    │   ├── chat_session.py
    │   ├── message.py
    │   └── participant.py
    ├── services/
    │   └── chat_service.py
    └── mcp/
        └── chat_mcp_handler.py
```

## 🚀 Implementation Order

1. **gladia** - Core STT infrastructure ✅ (already started)
2. **scoop_score** - Scoring logic (depends on gladia)
3. **leaderboard** - Rankings (depends on scoop_score)  
4. **team_feedback** - Feedback generation (depends on all above)
5. **chat** - Communication features (independent)
6. **MCP orchestration** - Tie it all together

Should I start implementing this structure, beginning with completing the `gladia` domain and then moving to `scoop_score`?
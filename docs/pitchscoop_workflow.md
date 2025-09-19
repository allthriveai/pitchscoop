# PitchScoop Complete Workflow Documentation

## 🎯 Overview
PitchScoop is an AI-powered competition platform that records, transcribes, scores, and provides feedback on pitch presentations using MCP (Model Context Protocol) tools.

## 🔄 Complete Workflow Steps

### 1. **Pick Organizer vs Individual**
| Field | Value |
|-------|--------|
| **Things that happen** | Two selection boxes for role selection |
| **Criteria to next step** | Role saved in session/database |
| **Sponsor tools used** | Redis |
| **MCP tool** | `auth.set_role` → save `{user_id, role}` |
| **Other tools** | SPA, Nginx |
| **Domain** | `auth` (shared) |

**Implementation Details:**
- Simple role selection UI (Organizer/Individual)
- Store role in Redis session with user_id
- Role determines available features and permissions

---

### 2. **Add a Link** 
| Field | Value |
|-------|--------|
| **Things that happen** | User adds event/pitch URL |
| **Criteria to next step** | Record created in Redis |
| **Sponsor tools used** | Redis |
| **MCP tool** | `events.link_upsert` → crawl + upsert link |
| **Other tools** | Apify client container |
| **Domain** | `events` (shared) |

**Implementation Details:**
- URL input field for event/pitch links
- Apify crawls and extracts event information
- Store event metadata in Redis
- Validate URL and extract relevant content

---

### 3. **Event Criteria Onboarding**
| Field | Value |
|-------|--------|
| **Things that happen** | Add judges, rubric, goals, sponsor tools; index rubric/rules |
| **Criteria to next step** | Event record complete |
| **Sponsor tools used** | Redis, Apify, LlamaIndex |
| **MCP tool** | `events.upsert` → persist; `index.event_materials` → embed rubric/rules |
| **Other tools** | None |
| **Domain** | `events` (shared) + `scoop_score` |

**Implementation Details:**
- Form for judges, scoring rubric, goals, sponsor tools
- Embed rubric/rules using LlamaIndex for later RAG retrieval
- Store complete event configuration
- Validate all required fields are populated

---

### 4. **Team / Individual Setup**
| Field | Value |
|-------|--------|
| **Things that happen** | Organizer enters team name, members, bios, focus; index bios |
| **Criteria to next step** | Team saved & linked |
| **Sponsor tools used** | Redis, LlamaIndex |
| **MCP tool** | `teams.upsert`; `index.team_profile` |
| **Other tools** | None |
| **Domain** | `team_feedback` |

**Implementation Details:**
- Team registration form (name, members, bios, focus area)
- Index team bios for context in feedback generation
- Link teams to event
- Support both individual participants and teams

---

### 5. **Record Demo Pitches** ⭐ **CORE FLOW STARTS HERE**
| Field | Value |
|-------|--------|
| **Things that happen** | Start recording, live transcript; optionally save audio file |
| **Criteria to next step** | Transcript captured & stored |
| **Sponsor tools used** | Gladia, Redis, LlamaIndex |
| **MCP tool** | `pitches.start_ws` • `pitches.record_chunk` • `index.transcript_realtime` |
| **Other tools** | MinIO |
| **Domain** | `gladia` |

**Implementation Details:**
```python
@mcp_tool("pitches.start_ws")
async def start_pitch_recording(team_name: str, pitch_title: str) -> dict:
    """Start WebSocket recording session for a team's pitch"""
    # Creates STT session with Gladia
    # Returns WebSocket URL for real-time audio streaming
    
@mcp_tool("pitches.record_chunk") 
async def record_audio_chunk(session_id: str, audio_data: bytes) -> dict:
    """Process real-time audio chunk through Gladia STT"""
    
@mcp_tool("index.transcript_realtime")
async def index_transcript_segment(session_id: str, transcript_segment: str) -> dict:
    """Index transcript segments in real-time for search/RAG"""
```

---

### 6. **Audio Intelligence Metrics**
| Field | Value |
|-------|--------|
| **Things that happen** | Compute WPM, pauses, fillers, sentiment |
| **Criteria to next step** | Metrics computed & attached |
| **Sponsor tools used** | Gladia Audio Intelligence |
| **MCP tool** | `metrics.compute_delivery` |
| **Other tools** | None |
| **Domain** | `gladia` → `scoop_score` |

**Implementation Details:**
```python
@mcp_tool("metrics.compute_delivery")
async def compute_delivery_metrics(session_id: str) -> dict:
    """Analyze speech delivery metrics from Gladia transcript"""
    # - Words per minute (WPM)
    # - Pause analysis 
    # - Filler word detection ("um", "uh", "like")
    # - Sentiment analysis
    # - Speaking confidence indicators
```

---

### 7. **Scoop Score** ⭐ **SCORING ENGINE**
| Field | Value |
|-------|--------|
| **Things that happen** | Retrieve rules + pitch; score + feedback (RAG) |
| **Criteria to next step** | Scores saved |
| **Sponsor tools used** | Gladia, Redis, LlamaIndex |
| **MCP tool** | `scores.evaluate` → RAG over (rubric+transcript) + LLM |
| **Other tools** | Azure OpenAI |
| **Domain** | `scoop_score` |

**Implementation Details:**
```python
@mcp_tool("scores.evaluate")
async def evaluate_pitch_score(session_id: str) -> dict:
    """Score pitch using RAG over rubric + transcript with LLM analysis"""
    # 1. Retrieve transcript from gladia domain
    # 2. Retrieve event rubric from LlamaIndex
    # 3. Use Azure OpenAI to score against criteria:
    #    - Technical clarity
    #    - Presentation skills  
    #    - Problem-solution fit
    #    - Market opportunity
    #    - Innovation factor
    # 4. Return structured scores + reasoning
```

---

### 8. **Leaderboard** ⭐ **RANKINGS**
| Field | Value |
|-------|--------|
| **Things that happen** | Generate leaderboard by total score |
| **Criteria to next step** | All scored demos visible |
| **Sponsor tools used** | Redis |
| **MCP tool** | `leaderboard.generate` |
| **Other tools** | Plain React table |
| **Domain** | `leaderboard` |

**Implementation Details:**
```python
@mcp_tool("leaderboard.generate")
async def generate_leaderboard(event_id: str) -> dict:
    """Generate real-time leaderboard for competition"""
    # 1. Get all scores for event
    # 2. Rank by total score
    # 3. Handle tie-breaking logic
    # 4. Return sorted leaderboard with rankings
    
@mcp_tool("leaderboard.get_team_rank")
async def get_team_rank(team_name: str, event_id: str) -> dict:
    """Get specific team's current ranking"""
```

---

### 9. **Team Pages** ⭐ **INDIVIDUAL FEEDBACK**
| Field | Value |
|-------|--------|
| **Things that happen** | Show team's demos, feedback, transcript, scores, **and replay audio** |
| **Criteria to next step** | Team pages available; if audio exists, show Play button |
| **Sponsor tools used** | Redis |
| **MCP tool** | `teams.get_detail` → return bios, pitches, scores; `pitches.get_media_url` → presigned MinIO URL if audio exists |
| **Other tools** | HTML5 `<audio>` player, MinIO |
| **Domain** | `team_feedback` |

**Implementation Details:**
```python
@mcp_tool("teams.get_detail")
async def get_team_details(team_name: str, event_id: str) -> dict:
    """Get comprehensive team information and performance data"""
    # Returns: bios, pitch sessions, scores, feedback, rankings
    
@mcp_tool("pitches.get_media_url")
async def get_pitch_media_url(session_id: str) -> dict:
    """Get presigned URL for audio playback if audio was recorded"""
    # Returns MinIO presigned URL for audio file access

@mcp_tool("feedback.generate_report")
async def generate_team_feedback(session_id: str) -> dict:
    """Generate comprehensive feedback report for team"""
    # Combines: transcript analysis, score breakdown, improvement suggestions
```

---

### 10. **Chat with Transcripts**
| Field | Value |
|-------|--------|
| **Things that happen** | Q&A over rules + bios + transcripts |
| **Criteria to next step** | Answers returned |
| **Sponsor tools used** | Sensio, LlamaIndex |
| **MCP tool** | `chat.query` → LlamaIndex chat engine |
| **Other tools** | Weaviate |
| **Domain** | `chat` |

**Implementation Details:**
```python
@mcp_tool("chat.query")
async def query_competition_data(question: str, event_id: str) -> dict:
    """RAG-powered Q&A over event rules, team bios, and transcripts"""
    # Uses LlamaIndex + Weaviate for semantic search
    # Provides context-aware answers about the competition
```

---

## 🎪 **Core MCP Flow: Record → Score → Leaderboard → Individual Feedback**

### **Orchestration Tool**
```python
@mcp_tool("pitchscoop.complete_demo_analysis")
async def complete_demo_analysis(team_name: str, pitch_title: str) -> dict:
    """Execute complete demo analysis workflow"""
    
    # 1. RECORD (gladia domain)
    session = await pitches.start_ws(team_name, pitch_title)
    # ... recording happens via WebSocket ...
    await pitches.stop_recording(session.id)
    
    # 2. SCORE (scoop_score domain)
    await metrics.compute_delivery(session.id)
    score = await scores.evaluate(session.id)
    
    # 3. LEADERBOARD (leaderboard domain)  
    leaderboard = await leaderboard.generate(event_id)
    team_rank = await leaderboard.get_team_rank(team_name, event_id)
    
    # 4. INDIVIDUAL FEEDBACK (team_feedback domain)
    feedback = await feedback.generate_report(session.id)
    
    return {
        "session_id": session.id,
        "score": score.overall_score,
        "rank": team_rank.position,
        "leaderboard": leaderboard.top_10,
        "feedback_url": f"/teams/{team_name}/feedback"
    }
```

---

## 🏗️ **Domain Integration Map**

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   gladia    │───▶│  scoop_score │───▶│  leaderboard    │
│ (Record)    │    │  (Score)     │    │  (Rank)         │
└─────────────┘    └──────────────┘    └─────────────────┘
                            │                     │
                            ▼                     ▼
                   ┌─────────────────┐   ┌─────────────────┐
                   │  team_feedback  │◀──│     chat        │
                   │  (Feedback)     │   │  (Q&A)          │
                   └─────────────────┘   └─────────────────┘
```

---

## 🚀 **Implementation Priority**

### **Phase 1: Core Flow (MVP)**
1. ✅ `gladia` domain - Recording & transcription 
2. 🔨 `scoop_score` domain - Basic scoring
3. 🔨 `leaderboard` domain - Simple rankings
4. 🔨 `team_feedback` domain - Basic feedback

### **Phase 2: Enhanced Features**
1. Audio intelligence metrics
2. Advanced feedback generation
3. Audio playback functionality
4. Enhanced RAG-based scoring

### **Phase 3: Full Platform**
1. `chat` domain - Q&A functionality
2. Complete UI integration
3. Multi-event support
4. Advanced analytics

---

## 📋 **MCP Tools Summary**

| Domain | MCP Tools | Purpose |
|--------|-----------|---------|
| `gladia` | `pitches.start_ws`, `pitches.record_chunk`, `pitches.stop_recording` | Audio recording & STT |
| `scoop_score` | `scores.evaluate`, `metrics.compute_delivery` | AI-powered scoring |
| `leaderboard` | `leaderboard.generate`, `leaderboard.get_team_rank` | Competition rankings |
| `team_feedback` | `feedback.generate_report`, `teams.get_detail` | Individual feedback |
| `chat` | `chat.query` | RAG-powered Q&A |
| **Orchestration** | `pitchscoop.complete_demo_analysis` | **End-to-end workflow** |

This documentation serves as our implementation blueprint. Each step is clearly defined with inputs, outputs, and dependencies. Should we start implementing the core flow (Steps 5-9) first?
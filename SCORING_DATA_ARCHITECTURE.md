# 🏗️ PitchScoop: Event → User → Recording → Scoring Data Architecture

## 📊 **Current Data Relationship Overview**

Your scoring system follows a clear hierarchy that ensures **multi-tenant isolation** and **proper data relationships**:

```
EVENT
├── Users/Participants (teams)
├── Recording Sessions 
└── Scoring Results
    ├── AI Analysis
    ├── Audio Intelligence  
    └── Judge Scores
```

## 🔑 **Redis Key Structure**

### **1. Event Level (Multi-Tenant Root)**
```bash
event:{event_id}                          # Event configuration
event:{event_id}:participants             # Event participants list
event:{event_id}:sessions                 # All sessions for this event
```

### **2. Recording Session Level**
```bash
event:{event_id}:session:{session_id}     # Individual recording session
```

**Session Data Structure:**
```json
{
  "session_id": "uuid-123",
  "event_id": "hackathon-2024", 
  "event_name": "AI Agent Hackathon",
  "event_type": "hackathon",
  "team_name": "Team Innovators",      # ← USER IDENTIFIER
  "pitch_title": "Smart AI Assistant",
  "status": "completed",
  "created_at": "2024-01-15T10:00:00Z",
  "final_transcript": {
    "total_text": "Our AI agent solves...",
    "segments": [...]
  },
  "gladia_session_id": "gladia-xyz-789",
  "has_audio": true
}
```

### **3. Scoring Results Level**
```bash
event:{event_id}:scoring:{session_id}           # Main scoring results
event:{event_id}:judge:{judge_id}:scoring:{session_id}  # Judge-specific scores
event:{event_id}:tool_analysis:{session_id}     # Tool usage analysis
event:{event_id}:audio_intelligence:{session_id} # Audio Intelligence cache
event:{event_id}:presentation_analysis:{session_id} # Presentation delivery analysis
```

## 🔄 **Data Flow: Event → User → Recording → Scoring**

### **Step 1: Event Creation**
```bash
# MCP Tool: events.create_event
Redis Key: event:{event_id}
Data: Event configuration, criteria, duration, status
```

### **Step 2: User Participation**
```bash
# MCP Tool: events.join_event  
Redis Key: event:{event_id}:participants
Data: List of teams/users participating in event
```

### **Step 3: Recording Session**
```bash
# MCP Tool: pitches.start_recording
Redis Key: event:{event_id}:session:{session_id}
Data: User (team_name), recording, transcript, audio
Links: event_id → session_id → team_name
```

### **Step 4: Scoring Analysis**
```bash
# MCP Tool: analysis.score_pitch
Redis Key: event:{event_id}:scoring:{session_id}
Data: AI scores, analysis, timestamps
Links: event_id → session_id → team_name → scores
```

## 🎯 **Multi-Tenant Isolation Strategy**

### **Event-Scoped Data**
- **All data prefixed with `event:{event_id}`**
- **Complete isolation between competitions**
- **Judge scores scoped to specific events**
- **Audio Intelligence cached per event**

### **Session-to-User Mapping**
```python
# Session contains user identity
session_data = {
    "session_id": "session-123",
    "event_id": "hackathon-2024",
    "team_name": "Team Alpha",      # ← USER IDENTITY
    "pitch_title": "AI Innovation"
}

# Scoring results include user context
scoring_data = {
    "session_id": "session-123", 
    "event_id": "hackathon-2024",
    "team_name": "Team Alpha",      # ← PRESERVED FROM SESSION
    "scores": {...},
    "judge_id": "judge-001"         # ← OPTIONAL JUDGE CONTEXT
}
```

## 📋 **Key Relationships Explained**

### **1. Event → Recording Relationship**
```python
# Recording MUST belong to an event
session_key = f"event:{event_id}:session:{session_id}"

# Event validates recording permissions
if event_data["status"] not in ["active"]:
    return {"error": "Event is not active"}
```

### **2. Recording → User Relationship**
```python
# Session contains user identity
session_data = {
    "team_name": "Team Innovators",  # ← PRIMARY USER IDENTIFIER
    "pitch_title": "Smart Assistant", # ← PITCH CONTEXT
}

# No separate user table - team_name IS the user identifier
```

### **3. Recording → Scoring Relationship**
```python
# Scoring reads from session data
session_key = f"event:{event_id}:session:{session_id}"
scoring_key = f"event:{event_id}:scoring:{session_id}"

# Scoring inherits user context from session
scoring_record = {
    "session_id": session_id,
    "event_id": event_id,          # ← INHERITED
    "team_name": session_data["team_name"],  # ← INHERITED  
    "pitch_title": session_data["pitch_title"], # ← INHERITED
    "scores": {...}
}
```

### **4. Multiple Judges Per Session**
```python
# Main scoring (official)
f"event:{event_id}:scoring:{session_id}"

# Judge-specific scoring
f"event:{event_id}:judge:{judge_001}:scoring:{session_id}"
f"event:{event_id}:judge:{judge_002}:scoring:{session_id}"
f"event:{event_id}:judge:{judge_003}:scoring:{session_id}"
```

## 🔍 **Query Patterns**

### **Get All Scores for an Event**
```python
# Pattern: event:{event_id}:scoring:*
scoring_keys = redis.keys(f"event:{event_id}:scoring:*")
```

### **Get All Sessions for a Team**
```python
# Scan all sessions in event, filter by team_name
sessions = []
async for key in redis.scan_iter(match=f"event:{event_id}:session:*"):
    session_data = json.loads(await redis.get(key))
    if session_data["team_name"] == target_team:
        sessions.append(session_data)
```

### **Get Leaderboard for Event**
```python
# Get all scoring results for event
scores = []
async for key in redis.scan_iter(match=f"event:{event_id}:scoring:*"):
    score_data = json.loads(await redis.get(key))
    scores.append({
        "team_name": score_data["team_name"],
        "total_score": score_data["analysis"]["overall"]["total_score"]
    })
scores.sort(key=lambda x: x["total_score"], reverse=True)
```

## 📊 **Audio Intelligence Integration**

### **Enhanced Data Flow**
```python
# 1. Recording Session (has audio + transcript)
session_data = {
    "gladia_session_id": "gladia-123",
    "has_audio": True,
    "final_transcript": {...}
}

# 2. Audio Intelligence Analysis (new layer)
audio_intelligence_key = f"event:{event_id}:audio_intelligence:{session_id}"
audio_data = {
    "speech_metrics": {"words_per_minute": 145, ...},
    "filler_analysis": {"filler_percentage": 2.1, ...},
    "confidence_metrics": {"confidence_score": 0.87, ...}
}

# 3. Enhanced Scoring (uses both transcript + audio)
enhanced_scoring_key = f"event:{event_id}:presentation_analysis:{session_id}"
enhanced_score = {
    "content_analysis": {...},      # From transcript
    "audio_intelligence": {...},   # From Gladia AI
    "combined_score": 22.3         # Weighted combination
}
```

## 🏆 **Strengths of Current Architecture**

### ✅ **Multi-Tenant by Design**
- Complete event isolation with `event:{event_id}` prefix
- No cross-event data leakage possible
- Easy to scale across multiple competitions

### ✅ **Clear Data Hierarchy**  
- Event → Session → Scoring relationship is explicit
- User identity (team_name) preserved through all layers
- Audit trail from recording to final scores

### ✅ **Flexible Judge System**
- Support for multiple judges per session
- Main scoring vs judge-specific scoring
- Easy aggregation for consensus scoring

### ✅ **Caching Strategy**
- Session data cached for quick access
- Audio Intelligence results cached to avoid re-processing
- TTL-based expiry for cleanup

## 🎯 **Summary: Data Relationships**

```
EVENT (hackathon-2024)
├── PARTICIPANTS
│   ├── Team Alpha
│   ├── Team Beta  
│   └── Team Gamma
├── RECORDING SESSIONS
│   ├── session-001 (Team Alpha → "AI Assistant")
│   ├── session-002 (Team Beta → "Smart Tools") 
│   └── session-003 (Team Gamma → "Agent Platform")
└── SCORING RESULTS
    ├── session-001 → Score: 87.5 (Judge A: 85, Judge B: 90)
    ├── session-002 → Score: 82.3 (Judge A: 80, Judge B: 84)
    └── session-003 → Score: 91.2 (Judge A: 92, Judge B: 90)
```

**The relationship flow is:**
1. **Event** defines the competition scope and rules
2. **Teams** (users) participate in the event
3. **Sessions** capture each team's pitch recording + transcript
4. **Scoring** analyzes the session data to produce scores
5. **Audio Intelligence** enhances scoring with delivery metrics

**Every piece of data is event-scoped, ensuring complete multi-tenant isolation while maintaining clear relationships between events, users, recordings, and scores.**
# 🚀 PitchScoop Hackathon Day 2 Plan

## 📋 Current Status (End of Day 1)

### ✅ What's Working
- **Recording Domain**: Complete MCP implementation with Redis caching, MinIO audio storage
- **Infrastructure**: Docker setup with Redis, MinIO, API services running on correct ports
- **Tests**: All unit tests (19/19), integration tests, and mock flows passing
- **Browser Test UI**: Working test interface accessible at http://localhost:8000/test (inside Docker)
- **Multi-tenant Isolation**: Proper event_id scoping with `event:{event_id}:session:{session_id}` keys
- **MCP Tools**: 6 tools ready for AI assistant use (start/stop recording, sessions, playback, etc.)

### ⚠️ Key Constraints to Honor
- **Ports**: Frontend 3000, Backend 8000 (always use Docker)
- **No venv**, no `git push --no-verify`, never bypass pre-commit
- **Never use**: `localStorage.getItem('access_token')`, certain words, placeholders
- **Always generate thumbnails** when possible
- **Keep all services in `/services` subfolder**
- **Use `event_id` for multi-tenant isolation** (not org_id) across endpoints, data, logs
- **PostgreSQL preferred** for structured data
- **TypeScript for frontend**

### 🔧 Current Gaps
- No frontend UI yet
- No scoring/leaderboard system
- No PostgreSQL integration
- Missing comprehensive event_id enforcement
- No thumbnail generation for audio

---

## 🎯 Day 2 Execution Plan (Priority Order)

### **Track A: Demo-Ready Product (MUST SHIP)**

#### 1. **TypeScript Frontend** (2-3 hours) 🎨
**Goal**: Minimal React/Next.js app that demonstrates core workflow

**Implementation**:
```bash
# Structure
/services/web/
├── Dockerfile
├── package.json (Next.js + TypeScript)
├── src/
│   ├── pages/
│   │   ├── index.tsx (home/event selector)
│   │   ├── record.tsx (recording interface)
│   │   ├── playback.tsx (session playback)
│   │   └── leaderboard.tsx (scores table)
│   ├── components/
│   │   ├── AudioRecorder.tsx
│   │   ├── SessionList.tsx
│   │   └── WaveformThumbnail.tsx
│   └── lib/
│       └── api.ts (fetch wrapper, NO localStorage)
```

**Key Features**:
- **Record Page**: Start/stop recording, show WebSocket status, upload audio, list sessions
- **Playback Page**: Show session details, transcript, audio player with waveform thumbnail
- **Leaderboard Page**: Simple table with team rankings (stub initially)
- **Auth**: Use HttpOnly cookies or in-memory state (never `localStorage.getItem('access_token')`)
- **CORS**: Ensure backend allows `http://localhost:3000`

**Docker Setup**:
```dockerfile
# /services/web/Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

#### 2. **LlamaIndex Integration** (1.5 hours) 🦙
**Goal**: Set up RAG-powered indexing and context-aware scoring

**Quick Setup**:
```bash
# 1. Build with new dependencies (LlamaIndex + Qdrant)
docker-compose build api

# 2. Start with Qdrant service
docker-compose up -d qdrant redis minio api

# 3. Test LlamaIndex connection
docker-compose exec api python -c "from domains.indexing.services.llamaindex_service import llamaindex_service; print('✅ LlamaIndex ready!')"
```

**New MCP Tools** (already implemented):
```python
# Available immediately:
- index.add_rubric(event_id, rubric_data)
- index.add_transcript(event_id, session_id, transcript_data) 
- index.add_team_profile(event_id, team_data)
- index.health_check()
```

#### 3. **Scoring Engine MVP** (2 hours) 🏆
**Goal**: RAG-powered scoring using LlamaIndex + Azure OpenAI

**Context-Aware Scoring**:
```python
# domains/scoring/mcp/scoring_tools.py
@mcp_tool("scores.evaluate")
async def evaluate_pitch(session_id: str, event_id: str) -> dict:
    """RAG-powered pitch scoring using rubric context"""
    # 1. Query indexed rubric for scoring criteria
    # 2. Query indexed transcript for pitch content
    # 3. Use Azure OpenAI to score with context:
    #    - Technical clarity vs rubric criteria
    #    - Content quality vs examples
    #    - Delivery metrics (WPM, fillers, duration)
    # 4. Return structured scores with reasoning
```

**Auto-Indexing Integration**:
- Transcripts auto-indexed after recording
- Rubrics indexed when events created
- Context-aware scoring uses RAG retrieval

#### 3. **Audio Thumbnails** (1 hour) 🎵
**Goal**: Generate waveform visualizations for recorded audio

**Implementation**:
```python
# domains/recordings/services/thumbnail_service.py
def generate_waveform_thumbnail(audio_data: bytes) -> dict:
    """Generate waveform thumbnail from audio data"""
    # Use pydub + matplotlib or simple amplitude analysis
    # Return base64 PNG or JSON data points for frontend
```

**Integration**:
- Generate thumbnail when audio is uploaded in `stop_recording`
- Store thumbnail URL/data in session metadata
- Display in frontend playback interface

#### 4. **Event_ID Enforcement** (1 hour) 🔒
**Goal**: Comprehensive event_id isolation across all endpoints

**Updates Needed**:
- **Redis Keys**: Ensure all keys follow `event:{event_id}:*` pattern
- **MCP Schemas**: Make event_id required (remove default fallback in production)
- **Logging**: Add event_id to all log entries
- **Validation**: Reject requests without valid event_id

**Key Changes**:
```python
# Update all MCP tools to require event_id
@mcp_tool("pitches.start_recording")
async def start_recording(team_name: str, pitch_title: str, event_id: str):
    # event_id is now required, no default
    
# Logging format
logger.info("Session started", extra={
    "event_id": event_id,
    "session_id": session_id,
    "team_name": team_name
})
```

---

### **Track B: Backend Hardening (SHOULD HAVE)**

#### 5. **PostgreSQL Integration** (2 hours) 💾
**Goal**: Structured data persistence for events, teams, scores

**Setup**:
```yaml
# docker-compose.yml addition
postgres:
  image: postgres:15-alpine
  ports:
    - "5432:5432"
  environment:
    POSTGRES_DB: pitchscoop
    POSTGRES_USER: pitchscoop
    POSTGRES_PASSWORD: pitchscoop123
  volumes:
    - postgres-data:/var/lib/postgresql/data
```

**Schema**:
```sql
-- /services/db/migrations/001_initial.sql
CREATE TABLE events (
    event_id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    rubric JSONB,
    duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR REFERENCES events(event_id),
    session_id VARCHAR NOT NULL,
    team_name VARCHAR NOT NULL,
    total_score DECIMAL(5,2),
    breakdown JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 6. **Pre-push Hook** (30 minutes) ⚡
**Goal**: Ensure code quality before push

**Implementation**:
```bash
#!/bin/bash
# .git/hooks/pre-push
set -e

echo "🧪 Running tests..."
docker-compose run --rm api pytest

echo "🔍 Running linters..."
docker-compose run --rm api ruff check .
docker-compose run --rm api black --check .

echo "🎯 Running type checks..."
docker-compose run --rm api mypy domains/

echo "✅ All checks passed!"
```

---

### **Track C: Differentiators (NICE TO HAVE)**

#### 7. **Real-time Features** (if time permits) ⚡
- **WebSocket Integration**: Real-time transcript streaming during recording
- **Live Leaderboard**: Auto-refresh rankings as teams complete pitches
- **Judge Interface**: Real-time scoring during presentations

#### 8. **Enhanced Audio Processing** (if time permits) 🎧
- **Speech Analysis**: Confidence, pace, sentiment using Gladia Audio Intelligence
- **Multi-speaker Detection**: Identify different speakers in team presentations
- **Audio Quality Metrics**: Volume levels, background noise detection

#### 9. **Advanced Search** (stretch goal) 🔍
- **Qdrant Integration**: Vector search through all transcripts
- **AI Chat**: Ask questions about any pitch using RAG + Azure OpenAI

---

## ⏰ Recommended Schedule (8-hour day)

### Morning (4 hours)
- **8:00-10:00**: TypeScript Frontend setup + basic recording UI
- **10:00-11:00**: Audio thumbnail generation
- **11:00-12:00**: Scoring engine MVP

### Afternoon (4 hours)  
- **1:00-2:00**: PostgreSQL integration + data persistence
- **2:00-3:00**: Event_ID enforcement + logging cleanup
- **3:00-4:00**: Frontend polish + leaderboard UI
- **4:00-5:00**: Integration testing + demo preparation

---

## 🎯 Demo Script

### Core Demo Flow (3 minutes)
1. **Show Event Setup**: Create event with rubric in UI
2. **Record Pitch**: Use browser to record 30-second demo pitch
3. **View Results**: Show transcript, waveform thumbnail, playback
4. **See Scoring**: Display scores broken down by criteria  
5. **Check Leaderboard**: Show team rankings with multiple entries

### Technical Highlights
- **Multi-tenant Isolation**: All data scoped by event_id
- **Audio Pipeline**: Browser → WebSocket → Gladia → MinIO → Playback
- **AI Scoring**: Transcript analysis + rubric matching
- **Real Architecture**: Docker + Redis + PostgreSQL + MinIO

---

## 🚨 Critical Success Factors

### Must Work for Demo
1. **End-to-end recording flow**: Browser → API → Storage → Playback
2. **Scoring system**: At least basic heuristics working
3. **Multi-event support**: Can switch between different events
4. **Audio playback**: Recorded audio accessible via presigned URLs
5. **Visual polish**: Clean UI that doesn't look like a dev tool

### Technical Debt to Avoid
- Don't break existing tests - run them before each major change
- Keep Docker setup working - everything must run in containers
- Maintain MCP tool compatibility - AI assistants should still work
- Follow logging/security rules - never bypass established patterns

---

## 🎉 Success Metrics

### MVP Success (Must Have)
- [ ] Complete recording workflow works in browser
- [ ] Basic scoring system produces meaningful results
- [ ] Leaderboard updates when new pitches are scored
- [ ] Multiple teams can use the system simultaneously
- [ ] Audio thumbnails enhance the playback experience

### Stretch Success (Wow Factor)
- [ ] Real-time transcript streaming during recording
- [ ] AI-powered content analysis in scoring
- [ ] Beautiful, professional-looking UI
- [ ] Advanced audio processing metrics
- [ ] Search/query functionality across all pitches

---

**Let's ship it! 🚢**

Focus on Track A first - get the demo working end-to-end, then polish and add features. The foundation is solid, now we build the experience that wins the hackathon!
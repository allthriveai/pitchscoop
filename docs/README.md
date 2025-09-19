# PitchScoop Backend

A pitch competition platform backend built with FastAPI, Redis, MinIO, and AI-powered analysis. The system uses MCP (Model Context Protocol) for AI assistant interactions and follows Domain-Driven Design principles with multi-tenant architecture.

## Tech Stack

- **Backend**: Python 3.11 + FastAPI
- **Database**: Redis for caching and session storage
- **Storage**: MinIO for audio file storage
- **AI**: Azure OpenAI + LangChain for pitch analysis and scoring
- **STT**: Gladia API for speech-to-text transcription
- **Vector DB**: Qdrant for document processing and RAG
- **Containerization**: Docker & Docker Compose
- **AI Integration**: MCP tools for assistant interactions

## Quick Start for New Team Members

### Prerequisites
- Docker and Docker Compose installed
- Git installed
- (Optional) Azure OpenAI access for AI features
- (Optional) Gladia API key for speech-to-text

### 🚀 One-Command Setup

1. **Clone and start the project**:
   ```bash
   git clone <repository-url>
   cd pitchscoop
   cp .env.example .env
   docker compose up --build
   ```

2. **Verify everything is working**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001 (user: `pitchscoop`, password: `pitchscoop123`)
   - Redis: localhost:6379
   - Qdrant: http://localhost:6333

3. **Test the API**:
   ```bash
   curl localhost:8000/api/healthz
   ```
   Should return: `{"ok": true}`

### 🔧 Development Workflow

```bash
# Start all services (Redis, MinIO, Qdrant, API)
docker compose up --build

# Start in detached mode
docker compose up -d --build

# View logs
docker compose logs -f api

# Run tests
docker compose exec api pytest tests/

# Stop services
docker compose down
```

### 🧪 Running Tests

```bash
# Run all tests
docker compose exec api pytest tests/

# Run with coverage
docker compose exec api pytest tests/ --cov=domains --cov-report=html

# Run specific domain tests
docker compose exec api pytest tests/unit/domains/recordings/
docker compose exec api pytest tests/unit/domains/scoring/

# Run integration tests
docker compose exec api python tests/test_mcp_integration.py
```

### 🎯 Key Services and Ports

| Service | Port | Purpose | Credentials |
|---------|------|---------|--------------|
| FastAPI API | 8000 | Main backend API | - |
| MinIO API | 9000 | File storage API | Access: `pitchscoop`<br>Secret: `pitchscoop123` |
| MinIO Console | 9001 | Storage admin UI | User: `pitchscoop`<br>Password: `pitchscoop123` |
| Redis | 6379 | Cache and sessions | - |
| Qdrant | 6333 | Vector database | - |

### 🔑 Environment Configuration

The `.env.example` file contains all necessary environment variables. For basic development, you only need to copy it:

```bash
cp .env.example .env
```

**Optional: Enable AI Features**
To enable AI-powered pitch analysis, add your Azure OpenAI credentials to `.env`:

```bash
SYSTEM_LLM_AZURE_ENDPOINT=https://your-resource.openai.azure.com/
SYSTEM_LLM_AZURE_API_KEY=your_api_key_here
SYSTEM_LLM_AZURE_DEPLOYMENT=your_deployment_name
SYSTEM_LLM_AZURE_API_VERSION=2024-02-15-preview
```

**Optional: Enable Speech-to-Text**
To enable real speech-to-text (instead of mock mode), add your Gladia API key:

```bash
GLADIA_API_KEY=your_gladia_api_key_here
```

## 📚 Project Structure

```
pitchscoop/
├── api/                          # Main FastAPI application
│   ├── domains/                  # Domain-driven architecture
│   │   ├── events/               # ✅ Event management
│   │   ├── recordings/           # ✅ Audio recording & STT
│   │   ├── scoring/              # ✅ AI-powered analysis
│   │   ├── leaderboards/         # ⚠️  Rankings (in progress)
│   │   ├── feedback/             # ⚠️  Feedback generation
│   │   └── shared/               # Shared infrastructure
│   ├── tests/                    # Comprehensive test suite
│   ├── main.py                   # FastAPI app entry point
│   └── requirements.txt          # Python dependencies
├── docker-compose.yml            # Multi-service orchestration
├── .env.example                  # Environment template
└── README.md                     # This file
```

## 🎯 MCP Tools Available

The system provides comprehensive MCP (Model Context Protocol) tools:

### Events Domain
- `events.create_event` - Create hackathon, VC pitch, or practice events
- `events.list_events` - List events with filtering
- `events.join_event` - Add participants to events
- `events.start_event` - Begin competitions
- `events.end_event` - Finalize events

### Recordings Domain
- `pitches.start_recording` - Initialize recording session
- `pitches.stop_recording` - Finalize and store audio/transcript
- `pitches.get_session` - Retrieve session details
- `pitches.get_playback_url` - Generate audio URLs

### Scoring Domain
- `analysis.score_pitch` - Complete AI-powered pitch scoring
- `analysis.score_idea` - Analyze idea uniqueness
- `analysis.score_technical` - Analyze technical implementation
- `analysis.score_presentation` - Analyze presentation delivery

## 🚀 API Examples

### Health Check
```bash
curl localhost:8000/api/healthz
# Response: {"ok": true}
```

### Create an Event
```bash
curl -X POST localhost:8000/api/events.create_event \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "hackathon",
    "name": "My Hackathon",
    "description": "A great hackathon",
    "judges": ["judge1", "judge2"],
    "sponsor_tools": ["Redis", "FastAPI"]
  }'
```

### Start a Recording
```bash
curl -X POST localhost:8000/api/pitches.start_recording \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "your-event-id",
    "team_name": "Team Alpha"
  }'
```

### Score a Pitch (AI-powered)
```bash
curl -X POST localhost:8000/api/analysis.score_pitch \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "your-event-id",
    "session_id": "your-session-id"
  }'
```

## 📖 API Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs (recommended for testing)
- **ReDoc**: http://localhost:8000/redoc (great for reading)

## 🏗️ Architecture Overview

### Event-Driven Workflow
1. **Create Event** → Set up competition
2. **Add Participants** → Register teams  
3. **Start Event** → Begin competition
4. **Record Pitches** → Audio recording + STT
5. **Score Pitches** → AI analysis
6. **Generate Leaderboard** → Rankings
7. **Individual Feedback** → Personalized reports

### Multi-Tenant Design
- All data is scoped by `event_id`
- Redis keys: `event:{event_id}:*`
- MinIO storage: `sessions/{session_id}/`
- Ensures complete data isolation between events

### Database Schema (Redis)
- `event:{event_id}` - Event configuration
- `event:{event_id}:participants` - Team list
- `event:{event_id}:sessions` - Recording sessions
- `event:{event_id}:scoring:{session_id}` - AI analysis results

## 🤝 Contributing

For new team members:
1. Follow the setup instructions above
2. Run tests to ensure everything works: `docker compose exec api pytest tests/`
3. Check the FastAPI docs at http://localhost:8000/docs
4. Look at domain structure in `api/domains/` for code organization
5. See `WARP.md` for detailed development guidelines

## 🆘 Troubleshooting

**Docker issues?**
```bash
# Clean up and restart
docker compose down -v
docker compose up --build
```

**API not responding?**
```bash
# Check API logs
docker compose logs api
```

**MinIO connection issues?**
- Check MinIO console: http://localhost:9001
- Verify credentials in `.env` match docker-compose.yml

**Tests failing?**
```bash
# Run with verbose output
docker compose exec api pytest tests/ -v
```

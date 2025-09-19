# PitchScoop

A pitch competition platform backend built with FastAPI, Redis, MinIO, and AI-powered analysis. The system uses MCP (Model Context Protocol) for AI assistant interactions and follows Domain-Driven Design principles with multi-tenant architecture.

## 🚀 Quick Start (New Team Members)

**One-command setup** - Get up and running in under 2 minutes:

```bash
git clone git@github.com:allthriveai/pitchscoop.git
cd pitchscoop
./setup.sh
```

That's it! The script will:
- ✅ Validate Docker is installed and running
- ✅ Copy environment template to `.env`
- ✅ Build and start all services (FastAPI, Redis, MinIO, Qdrant)
- ✅ Run health checks to verify everything is working
- ✅ Show you all the important URLs and commands

### Manual Setup (if you prefer)

```bash
cp .env.example .env
docker compose up --build
```

### Verify Setup

```bash
# Test API health
curl localhost:8000/api/healthz
# Should return: {"ok": true}
```

**Key URLs:**
- 🌐 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🗄️ **MinIO Console**: http://localhost:9001 (`pitchscoop` / `pitchscoop123`)

## 🔧 Development Workflow

```bash
# Start services in background
docker compose up -d --build

# View API logs
docker compose logs -f api

# Run tests
docker compose exec api pytest tests/

# Stop services
docker compose down
```

## 🎯 Tech Stack

- **Backend**: Python 3.11 + FastAPI
- **Database**: Redis for caching and session storage
- **Storage**: MinIO for audio file storage
- **AI**: Azure OpenAI + LangChain for pitch analysis and scoring
- **STT**: Gladia API for speech-to-text transcription
- **Vector DB**: Qdrant for document processing and RAG
- **Containerization**: Docker & Docker Compose
- **AI Integration**: MCP tools for assistant interactions

## 🏗️ Architecture

### Event-Driven Workflow
1. **Create Event** → Set up competition
2. **Add Participants** → Register teams  
3. **Start Event** → Begin competition
4. **Record Pitches** → Audio recording + STT
5. **Score Pitches** → AI analysis
6. **Generate Leaderboard** → Rankings
7. **Individual Feedback** → Personalized reports

### Project Structure

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
│   └── main.py                   # FastAPI app entry point
├── docs/                         # All project documentation
├── setup.sh                     # ✨ One-command setup script
├── docker-compose.yml            # Multi-service orchestration
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

## 📚 Documentation

**New Team Member?** Start with [`ONBOARDING.md`](./ONBOARDING.md) for a detailed checklist.

All project documentation is in the [`/docs`](./) folder:

- **[ONBOARDING.md](./ONBOARDING.md)** - 🎆 New team member checklist
- **[WARP.md](./WARP.md)** - Development guidelines and architecture
- **[MCP_BUSINESS_CASE.md](./MCP_BUSINESS_CASE.md)** - Business strategy and positioning
- **[IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)** - Complete implementation plan
- **[Domain Documentation](./)** - Technical architecture and APIs

## 🆘 Troubleshooting

**API not starting?**
```bash
docker compose logs api
```

**Port conflicts?**
```bash
# Check what's using the ports
lsof -i :8000  # API
lsof -i :6379  # Redis
lsof -i :9000  # MinIO
```

**Clean restart?**
```bash
docker compose down -v
docker compose up --build
```

## 🤝 Contributing

1. Run `./setup.sh` to get started
2. Check that tests pass: `docker compose exec api pytest tests/`
3. Explore the API at http://localhost:8000/docs
4. Read [`WARP.md`](./WARP.md) for development guidelines

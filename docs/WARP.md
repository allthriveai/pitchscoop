# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

PitchScoop is a pitch competition platform backend built with FastAPI, Redis, MinIO, and AI-powered analysis. The system uses MCP (Model Context Protocol) for AI assistant interactions and follows Domain-Driven Design principles with multi-tenant architecture.

## Architecture

### Core Stack
- **Backend**: Python 3.11 + FastAPI
- **Database**: Redis for caching and session storage
- **Storage**: MinIO for audio file storage
- **AI**: Azure OpenAI + LangChain for pitch analysis and scoring
- **STT**: Gladia API for speech-to-text transcription
- **Containerization**: Docker & Docker Compose
- **AI Integration**: MCP tools for assistant interactions

### Domain Structure
The application follows Domain-Driven Design with these domains:

#### Core Domains
- `domains/events/` - Event management (hackathons, VC pitches, practice sessions)
- `domains/recordings/` - Audio recording, STT, and session management
- `domains/scoring/` - AI-powered pitch analysis and scoring
- `domains/leaderboards/` - Competition rankings and standings
- `domains/feedback/` - Individual team feedback generation
- `domains/chat/` - Communication features
- `domains/shared/` - Shared infrastructure and utilities

#### Domain Status
- **events**: ✅ Fully implemented with MCP tools
- **recordings**: ✅ Fully implemented with MCP tools
- **scoring**: ✅ Fully implemented with AI analysis
- **leaderboards**: ⚠️ Structure exists, implementation in progress
- **feedback**: ⚠️ Structure exists, implementation in progress
- **chat**: ⚠️ Structure exists, implementation in progress

## Development Commands

### Environment Setup
```bash
# Copy environment variables
cp .env.example .env

# Start all services (Redis, MinIO, API)
docker compose up --build

# Start in detached mode
docker compose up -d --build

# View logs
docker compose logs -f api

# Stop services
docker compose down
```

### Testing
```bash
# Run all tests from /tests directory
docker compose exec api pytest tests/

# Run with coverage
docker compose exec api pytest tests/ --cov=domains --cov-report=html

# Run specific domain tests
docker compose exec api pytest tests/unit/domains/recordings/
docker compose exec api pytest tests/unit/domains/scoring/

# Run integration tests
docker compose exec api python tests/test_mcp_integration.py

# Run Azure integration tests
docker compose exec api python tests/test_azure_integration.py

# Run complete workflow tests
docker compose exec api pytest tests/test_complete_recording_flow.py -v

# Run specific integration test files
docker compose exec api python tests/test_mcp_direct.py
docker compose exec api python tests/simple_azure_test.py
```

### Development Server
```bash
# API runs on http://localhost:8000 with auto-reload
# FastAPI docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc

# MinIO console: http://localhost:9001 
# Credentials: pitchscoop / pitchscoop123

# Redis available on localhost:6379
```

## MCP Tools Available

The system provides comprehensive MCP tools across domains:

### Events Domain (`domains/events/mcp/`)
- `events.create_event` - Create hackathon, VC pitch, or practice events
- `events.list_events` - List events with filtering
- `events.get_event_details` - Complete event information
- `events.join_event` - Add participants to events
- `events.start_event` - Begin competitions
- `events.end_event` - Finalize events
- `events.delete_event` - Clean up test events

### Recordings Domain (`domains/recordings/mcp/`)
- `pitches.start_recording` - Initialize recording session
- `pitches.stop_recording` - Finalize and store audio/transcript
- `pitches.get_session` - Retrieve session details
- `pitches.get_playback_url` - Generate audio URLs
- `pitches.list_sessions` - Browse recordings
- `pitches.delete_session` - Clean up sessions

### Scoring Domain (`domains/scoring/mcp/`)
- `analysis.score_pitch` - Complete AI-powered pitch scoring
- `analysis.score_idea` - Analyze idea uniqueness
- `analysis.score_technical` - Analyze technical implementation
- `analysis.score_tools` - Analyze sponsor tool integration
- `analysis.score_presentation` - Analyze presentation delivery
- `analysis.compare_pitches` - Compare multiple pitch sessions

## Key Files and Directories

### Configuration
- `docker-compose.yml` - Multi-service orchestration (Redis, MinIO, API)
- `api/requirements.txt` - Python dependencies including LangChain, Azure OpenAI
- `api/Dockerfile` - API container configuration
- `.env.example` - Environment variable template

### Core Application
- `api/main.py` - FastAPI application entry point
- `api/domains/` - Domain-driven architecture implementation
  - Each domain has: `entities/`, `mcp/`, `repositories/`, `services/`, `value_objects/`

### Shared Infrastructure
- `api/domains/shared/infrastructure/` - Shared services
  - `azure_openai_client.py` - Azure OpenAI integration
  - `langchain_config.py` - LangChain analysis chains
  - `audio_utils.py` - Audio processing utilities
  - `logging.py` - Centralized logging

### Testing Infrastructure
- `tests/` - Comprehensive test suite with mocks
  - `tests/unit/` - Unit tests organized by domain
  - `tests/integration/` - Integration test framework
  - `tests/mocks/` - Mock implementations for external services
  - `tests/fixtures/` - Test data and fixtures
- `TEST_SUMMARY.md` - Integration test documentation
- Mock implementations for Redis, MinIO, Gladia, and Azure OpenAI

## Database Schema

### Redis Key Patterns
- `event:{event_id}` - Event data with configuration and status
- `event:{event_id}:participants` - Event participant list
- `event:{event_id}:sessions` - Recording sessions for event
- `event:{event_id}:session:{session_id}` - Individual session data
- `event:{event_id}:scoring:{session_id}` - AI scoring results
- `event:{event_id}:tool_analysis:{session_id}` - Sponsor tool analysis
- `event:{event_id}:judge:{judge_id}:scoring:{session_id}` - Judge-specific scores

### MinIO Storage
- Audio files: `sessions/{session_id}/recording.wav`
- Presigned URLs for playback with configurable expiration

## Multi-Tenant Architecture

Always use `{event_id}` in endpoints and data structures to ensure proper tenant isolation:
- Scoring and analysis results include event_id prefix
- API endpoints should include event context
- Database keys are prefixed with event_id for sensitive data
- Log entries must include event_id for filtering

## AI Integration

### Azure OpenAI Configuration
The system uses Azure OpenAI for pitch analysis:
- Environment variables: `SYSTEM_LLM_AZURE_*` configuration
- LangChain integration for structured analysis
- Multi-criteria scoring: idea, technical, tools, presentation
- Comparative analysis between pitches

### Analysis Capabilities
- Complete pitch scoring with structured criteria
- Sponsor tool usage analysis
- Presentation delivery assessment
- Comparative ranking of multiple pitches
- AI-powered feedback generation

## Development Guidelines

### Port Configuration
- Frontend: Port 3000 (when implemented)
- Backend API: Port 8000
- Redis: Port 6379
- MinIO API: Port 9000
- MinIO Console: Port 9001

### Environment Variables
Critical environment variables:
```bash
# Redis
REDIS_URL=redis://redis:6379/0

# MinIO Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=pitchscoop
MINIO_SECRET_KEY=pitchscoop123
MINIO_BUCKET_NAME=pitchscoop

# Azure OpenAI (for AI analysis)
SYSTEM_LLM_AZURE_ENDPOINT=${SYSTEM_LLM_AZURE_ENDPOINT}
SYSTEM_LLM_AZURE_API_KEY=${SYSTEM_LLM_AZURE_API_KEY}
SYSTEM_LLM_AZURE_DEPLOYMENT=${SYSTEM_LLM_AZURE_DEPLOYMENT}
SYSTEM_LLM_AZURE_API_VERSION=${SYSTEM_LLM_AZURE_API_VERSION}

# Gladia STT (optional, mock mode available)
GLADIA_API_KEY=your_api_key_here
```

### Event-Driven Workflow
1. **Create Event**: `events.create_event` - Set up competition
2. **Add Participants**: `events.join_event` - Register teams
3. **Start Event**: `events.start_event` - Begin competition
4. **Record Pitches**: `pitches.start_recording` → `pitches.stop_recording`
5. **Score Pitches**: `analysis.score_pitch` - AI analysis
6. **Generate Leaderboard**: Rankings based on scores
7. **Individual Feedback**: Personalized team reports

### Testing Strategy
- Unit tests for each domain's entities and services in `tests/unit/domains/`
- Integration tests with mocked external services (Redis, MinIO, Azure OpenAI) in `tests/`
- End-to-end workflow testing via `tests/test_complete_recording_flow.py`
- MCP integration validation via `tests/test_mcp_integration.py`
- Azure AI integration testing via `tests/test_azure_integration.py`
- Direct MCP tool testing via `tests/test_mcp_direct.py`
- Simple Azure connection testing via `tests/simple_azure_test.py`

### Development Flow
1. Make changes to domain code
2. Run domain-specific tests: `pytest tests/unit/domains/{domain}/`
3. Run integration tests: `python tests/test_mcp_integration.py`
4. Test AI features: `python tests/test_azure_integration.py`
5. Test via FastAPI docs at http://localhost:8000/docs
6. Use pre-push hooks to validate before deployment

## Documentation Locations
- Domain architecture: `docs/pitchscoop_domains.md`
- Domain boundaries: `docs/domain_boundaries.md`
- MCP implementation status: `docs/GLADIA_MCP_STATUS.md`
- Integration test results: `docs/TEST_SUMMARY.md`
- Various planning docs: `docs/*.md`

## Project Rules

### Code Quality
- Never bypass pre-commit hooks
- Run all validations in pre-push git hooks
- Never commit .env files to version control
- Use PostgreSQL for production database needs when scaling
- Always include thumbnails in media features
- Keep all services in domain structure

### TypeScript and Frontend
- Use TypeScript for frontend development (when implemented)
- Never use localStorage.getItem('access_token') patterns
- Avoid placeholder content, especially for file uploads

### Language and Terminology
- Application name is "CanaryQA" in user-facing content
- Never use the word "compliance" in any text or communication
- Avoid "REFACTORED" or "legacy" in commit messages or documentation

### Multi-tenancy and Security
- Always ensure multi-tenant isolation using {event_id}
- Include event_id in endpoints, data access, and logging
- AI analysis results must be scoped to event
- Judge-specific data isolation for scoring

### AI Integration
- Use Azure OpenAI through LangChain for structured analysis
- Mock mode available for development without API keys
- Always include event_id in AI requests for proper tenant isolation
- Store analysis results with appropriate TTL in Redis

# API Domain Structure

## Overview

The PitchScoop API has been refactored to follow Domain-Driven Design (DDD) principles, where each business domain owns its complete vertical slice including:
- REST endpoints (routers)
- Business logic
- MCP tools
- Data models
- Infrastructure concerns

## Directory Structure

```
api/
├── main.py                     # App initialization, router registration, MCP aggregation
├── domains/
│   ├── events/
│   │   ├── router.py          # REST endpoints for events (/api/events/*)
│   │   ├── mcp/               # MCP tools for events domain
│   │   └── models.py          # Pydantic models (to be added)
│   │
│   ├── recordings/
│   │   ├── router.py          # REST endpoints for sessions (/api/sessions/*)
│   │   ├── mcp/               # MCP tools for recordings/pitches
│   │   └── value_objects/     # Domain value objects
│   │
│   ├── scoring/
│   │   ├── router.py          # REST endpoints for analysis (/api/analysis/*)
│   │   └── mcp/               # MCP tools for scoring/analysis
│   │
│   ├── leaderboards/
│   │   ├── router.py          # REST endpoints for leaderboards (/api/leaderboard/*)
│   │   └── mcp/               # MCP tools for rankings
│   │
│   └── users/
│       ├── router.py          # REST endpoints for users/auth (/api/users/*, /api/auth/*)
│       └── mcp/               # MCP tools for user management
```

## Key Changes

### Before
- All REST endpoints were in `main.py` (300+ lines)
- Models scattered in `/api/models/` folder
- No clear domain boundaries
- Difficult to understand which endpoints belonged to which domain

### After
- Each domain has its own `router.py` with related endpoints
- Models co-located with their domains (in progress)
- Clear separation of concerns
- Easy to find and modify domain-specific logic

## API Routes by Domain

### Events Domain (`/api/events/*`)
- `POST /api/events/create` - Create new event
- `POST /api/events/upsert` - Legacy create/update
- `GET /api/events/list` - List events with filters
- `GET /api/events/{event_id}` - Get event details
- `POST /api/events/{event_id}/join` - Join event
- `POST /api/events/{event_id}/start` - Start event
- `POST /api/events/{event_id}/end` - End event
- `DELETE /api/events/{event_id}` - Delete event

### Recordings Domain (`/api/sessions/*`)
- `GET /api/sessions/` - List sessions
- `POST /api/sessions/start` - Start recording
- `POST /api/sessions/{session_id}/stop` - Stop recording
- `POST /api/sessions/{session_id}/upload` - Upload audio
- `GET /api/sessions/{session_id}` - Get session details
- `GET /api/sessions/{session_id}/transcript` - Get transcript
- `GET /api/sessions/{session_id}/audio-intelligence` - Get audio analysis
- `POST /api/sessions/{session_id}/process` - Process session
- `DELETE /api/sessions/{session_id}` - Delete session
- `GET /api/sessions/{session_id}/scoring` - Get presentation scoring

### Scoring Domain (`/api/analysis/*`)
- `POST /api/analysis/score` - Score a pitch
- `POST /api/analysis/presentation-delivery` - Analyze delivery
- `POST /api/analysis/batch-score` - Batch scoring
- `POST /api/analysis/judge-feedback` - Generate feedback
- `GET /api/analysis/session/{session_id}` - Get session scoring
- `GET /api/analysis/event/{event_id}/stats` - Event statistics
- `POST /api/analysis/compare` - Compare pitches
- `POST /api/analysis/feedback/{session_id}/improve` - Improvement suggestions

### Leaderboards Domain (`/api/leaderboard/*`)
- `GET /api/leaderboard/{event_id}` - Get leaderboard
- `GET /api/leaderboard/{event_id}/team/{session_id}` - Team rank
- `GET /api/leaderboard/{event_id}/stats` - Leaderboard stats
- `GET /api/leaderboard/{event_id}/top` - Top teams
- `POST /api/leaderboard/{event_id}/compare` - Compare teams
- `GET /api/leaderboard/{event_id}/changes` - Recent changes
- `GET /api/leaderboard/{event_id}/category/{category}` - Category leaders
- `POST /api/leaderboard/{event_id}/refresh` - Refresh leaderboard
- `GET /api/leaderboard/{event_id}/export` - Export data
- `GET /api/leaderboard/generate` - Legacy endpoint

### Users Domain (`/api/users/*`, `/api/auth/*`)
- `POST /api/auth.set_role` - Legacy set role
- `POST /api/users/create` - Create user
- `POST /api/users/{user_id}/role` - Set user role
- `GET /api/users/{user_id}` - Get user profile
- `GET /api/users` - List users
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `DELETE /api/users/{user_id}` - Delete user
- `GET /api/users/{user_id}/sessions` - User's sessions
- `GET /api/users/{user_id}/events` - User's events
- `PUT /api/users/{user_id}` - Update profile

### MCP Endpoints (Centralized in `main.py`)
- `GET /mcp/health` - MCP health check
- `GET /mcp/tools` - List all MCP tools
- `POST /mcp/execute` - Execute any MCP tool

## Benefits of This Structure

1. **Domain Isolation**: Each domain is self-contained with its own router, models, and business logic
2. **Easier Testing**: Can test each domain independently
3. **Better Organization**: Clear where to find and add new features
4. **Scalability**: Domains can be easily extracted into microservices if needed
5. **Team Collaboration**: Different teams can work on different domains without conflicts
6. **MCP-First Design**: REST endpoints wrap MCP tools, ensuring consistency

## Next Steps

1. Move remaining Pydantic models from `/api/models/` to their respective domains
2. Add domain-specific services and repositories
3. Implement domain events for cross-domain communication
4. Add comprehensive tests for each domain router
5. Consider adding OpenAPI schemas per domain

## Running the API

```bash
# Using Docker (recommended)
./setup.sh

# Using uvicorn directly
cd pitchscoop
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
http://localhost:8000/docs  # Swagger UI
http://localhost:8000/redoc  # ReDoc
```

## Architecture Principles

1. **MCP Tools First**: All business logic exposed as MCP tools
2. **REST as Interface**: REST endpoints are thin wrappers around MCP tools
3. **Domain Boundaries**: Each domain owns its complete vertical slice
4. **Redis for Everything**: Single data platform for all storage needs
5. **AI-Native**: Designed for AI assistants to operate the business logic directly
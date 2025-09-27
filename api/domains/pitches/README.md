# Pitches Domain

## Overview

The Pitches domain provides video pitch presentation analysis using Hume AI emotion detection. This domain replaces the legacy recordings domain with a clean, modern implementation focused specifically on pitch presentation coaching and feedback.

## Features

- **Video Emotion Analysis**: Upload pitch videos for Hume AI emotion detection and sentiment analysis
- **Presentation Scoring**: Get comprehensive delivery scores based on confidence, engagement, authenticity, and energy
- **Coaching Feedback**: Receive actionable insights and improvement suggestions
- **Category-Specific Tips**: Tailored advice for investor pitches, sales pitches, and elevator pitches
- **Real-time Session Management**: Track analysis progress and manage multiple pitch sessions

## Architecture

This domain follows Domain-Driven Design (DDD) principles with clean separation of concerns:

```
api/domains/pitches/
├── entities/           # Core business entities
│   └── pitch_session.py
├── value_objects/      # Immutable value objects
│   └── video_intelligence.py
├── repositories/       # Data access layer
│   └── hume_api_repository.py
├── services/          # Domain services
│   └── pitch_analysis_service.py
├── mcp/              # MCP tools for AI assistants
│   └── pitch_tools.py
├── application/      # Application layer (future)
├── infrastructure/   # Infrastructure concerns (future)
└── router.py         # FastAPI REST endpoints
```

## MCP Tools

The domain provides 6 MCP tools for AI assistant integration:

1. **pitch_health_check** - Check system health and capabilities
2. **create_pitch_session** - Create new pitch analysis sessions
3. **analyze_pitch_video** - Upload and analyze pitch videos
4. **get_coaching_insights** - Get detailed coaching feedback
5. **get_session_status** - Check session status and basic info
6. **list_active_sessions** - List all active sessions (with optional user filtering)

## Usage Examples

### REST API

```python
# Create a new pitch session
POST /api/pitches/sessions
{
  "user_id": "user123",
  "title": "My Startup Pitch",
  "pitch_category": "investor_pitch",
  "target_duration": 180
}

# Upload and analyze video
POST /api/pitches/sessions/{session_id}/analyze
# Upload video file as multipart/form-data

# Get coaching insights
GET /api/pitches/sessions/{session_id}/insights
```

### MCP Integration

```json
{
  "tool": "create_pitch_session",
  "arguments": {
    "user_id": "user123",
    "title": "Investor Pitch Practice",
    "pitch_category": "investor_pitch"
  }
}
```

## Video Analysis Pipeline

1. **Upload**: Video is uploaded and encoded as base64
2. **Processing**: Hume AI analyzes facial expressions and emotions
3. **Intelligence**: Raw emotion data is converted to presentation metrics
4. **Scoring**: Overall delivery score calculated with weighted factors
5. **Coaching**: Actionable insights generated based on analysis results

## Scoring System

The presentation scoring system uses weighted factors:

- **Confidence** (35%): Projected confidence through facial expressions
- **Engagement Consistency** (25%): Emotional consistency throughout presentation  
- **Authenticity** (20%): Natural vs forced expressions
- **Energy Level** (15%): Enthusiasm and energy
- **Emotional Range** (5%): Variety of expressions

Maximum score: 25 points

## Pitch Categories

- **investor_pitch**: VC/funding presentations
- **sales_pitch**: Customer/client presentations  
- **elevator_pitch**: Brief networking presentations

Each category provides tailored coaching insights based on the specific context and goals.

## Dependencies

- **Hume AI API**: Video emotion analysis
- **FastAPI**: REST API framework
- **Pydantic**: Data validation
- **AsyncIO**: Asynchronous processing

## Integration Points

- **MCP Server**: Exposes tools for AI assistant integration
- **Main Application**: Registered in main.py router
- **Health Checks**: System status monitoring
- **Error Handling**: Comprehensive error reporting

## Future Enhancements

- Persistent storage for sessions and results
- Video streaming analysis for real-time feedback
- Integration with scoring and leaderboard domains
- Advanced analytics and trend analysis
- Multi-language support for international pitches

## Migration Notes

This domain completely replaces the legacy recordings domain which was focused on audio transcription with Gladia. The new implementation is video-first with Hume AI integration, providing much richer analysis capabilities for pitch presentation coaching.
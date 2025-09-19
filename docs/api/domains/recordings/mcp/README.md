# Gladia MCP Tools - Pitch Recording for CanaryQA

This module provides Model Context Protocol (MCP) tools for AI assistants to manage pitch recording sessions with Gladia Speech-to-Text integration, MinIO audio storage, and Redis session caching.

## Overview

The Gladia MCP Tools enable AI assistants to:
- Start and stop pitch recording sessions
- Store audio files for playback
- Cache transcripts in real-time
- Generate playback URLs for website integration
- Manage session lifecycle with error handling

## Architecture

```
AI Assistant → MCP Tools → GladiaMCPHandler → Infrastructure
                                           ├── Gladia STT API
                                           ├── Redis (session cache)
                                           └── MinIO (audio storage)
```

## Available Tools

### 1. `pitches.start_recording`
**Purpose**: Initialize a new pitch recording session

**Parameters**:
- `team_name` (required): Name of the team/participant
- `pitch_title` (required): Title of the pitch presentation
- `audio_config` (optional): Audio configuration overrides

**Returns**:
```json
{
    "session_id": "uuid-string",
    "status": "ready_to_record",
    "websocket_url": "wss://api.gladia.io/v2/live/...",
    "team_name": "Team Name",
    "pitch_title": "Pitch Title",
    "gladia_session_id": "gladia-id",
    "audio_config": {...},
    "instructions": {
        "next_step": "Connect to WebSocket and start sending audio chunks",
        "websocket_format": "Send raw audio bytes or base64 encoded chunks",
        "stop_method": "Call pitches.stop_recording when demo is complete"
    }
}
```

### 2. `pitches.stop_recording`
**Purpose**: Finalize recording and store audio/transcript

**Parameters**:
- `session_id` (required): Session identifier from start_recording
- `audio_data_base64` (optional): Base64-encoded audio data to store

**Returns**:
```json
{
    "session_id": "uuid-string",
    "status": "completed", 
    "transcript": {
        "segments_count": 5,
        "total_text": "Full transcript text",
        "segments": [...]
    },
    "audio": {
        "has_audio": true,
        "playback_url": "https://minio/...",
        "audio_size": 12345
    },
    "duration_seconds": 180.5,
    "completed_at": "2024-01-01T10:05:30"
}
```

### 3. `pitches.get_session`
**Purpose**: Get complete session details and status

**Parameters**:
- `session_id` (required): Session identifier

**Returns**: Complete session data with fresh playback URLs

### 4. `pitches.get_playback_url`
**Purpose**: Generate fresh playback URL for audio

**Parameters**:
- `session_id` (required): Session identifier
- `expires_hours` (optional): URL expiry time (default: 1 hour)

**Returns**:
```json
{
    "session_id": "uuid-string",
    "playback_url": "https://minio/presigned-url",
    "expires_in_seconds": 3600,
    "team_name": "Team Name",
    "pitch_title": "Pitch Title"
}
```

### 5. `pitches.list_sessions`
**Purpose**: Browse all recording sessions with filtering

**Parameters**:
- `team_name` (optional): Filter by team name
- `status` (optional): Filter by session status

**Returns**:
```json
{
    "sessions": [
        {
            "session_id": "uuid-string",
            "team_name": "Team A",
            "pitch_title": "AI Demo",
            "status": "completed",
            "created_at": "2024-01-01T10:00:00",
            "has_audio": true,
            "transcript_segments": 8,
            "duration_seconds": 120.0
        }
    ],
    "total_count": 1,
    "filters_applied": {...}
}
```

### 6. `pitches.delete_session`
**Purpose**: Remove session and audio files

**Parameters**:
- `session_id` (required): Session identifier to delete

**Returns**:
```json
{
    "session_id": "uuid-string",
    "deleted": true,
    "redis_deleted": true,
    "audio_deleted": true
}
```

## Usage Examples

### Basic Recording Workflow

```python
# 1. Start recording
result = await execute_mcp_tool("pitches.start_recording", {
    "team_name": "AI Innovators",
    "pitch_title": "Revolutionary ML Platform"
})
session_id = result["session_id"]
websocket_url = result["websocket_url"]

# 2. [Connect to WebSocket and stream audio...]

# 3. Stop recording
result = await execute_mcp_tool("pitches.stop_recording", {
    "session_id": session_id
})

# 4. Get playback URL for website
result = await execute_mcp_tool("pitches.get_playback_url", {
    "session_id": session_id,
    "expires_hours": 24
})
playback_url = result["playback_url"]
```

### Session Management

```python
# List all completed sessions
sessions = await execute_mcp_tool("pitches.list_sessions", {
    "status": "completed"
})

# Get detailed session info
details = await execute_mcp_tool("pitches.get_session", {
    "session_id": "some-uuid"
})

# Clean up test sessions
await execute_mcp_tool("pitches.delete_session", {
    "session_id": "test-uuid"
})
```

## Configuration

### Environment Variables

```bash
# Gladia API (required for real STT)
GLADIA_API_KEY=your_gladia_api_key

# Redis (session caching)
REDIS_URL=redis://redis:6379/0

# MinIO (audio storage)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=pitchscoop
MINIO_SECRET_KEY=pitchscoop123
MINIO_BUCKET_NAME=pitchscoop
```

### Docker Compose Setup

The tools are designed to work with the existing docker-compose setup:
- Redis on port 6379
- MinIO on ports 9000 (API) and 9001 (console)
- API container with environment variables

## Testing

### Integration Test
```bash
cd /Users/allierays/Sites/pitchscoop
docker-compose exec api python test_mcp_integration.py
```

This tests:
- ✅ Infrastructure connectivity (Redis, MinIO)
- ✅ Tool registry and schemas
- ✅ Error handling 
- ✅ Complete recording workflow
- ✅ Session cleanup

### Mock Mode
When `GLADIA_API_KEY` is not set, the tools run in mock mode:
- Simulated Gladia responses for testing
- Full Redis and MinIO integration
- Complete session lifecycle validation

## Session Status Flow

```
initializing → ready_to_record → recording → processing → completed
                                         ↘            ↗
                                           → error ←
```

## Error Handling

The tools provide comprehensive error handling:

1. **Infrastructure Errors**: Redis/MinIO connectivity issues
2. **Validation Errors**: Missing required parameters
3. **API Errors**: Gladia API failures (falls back to mock mode)
4. **Session Errors**: Invalid session IDs, missing sessions
5. **Storage Errors**: Audio upload/retrieval failures

All errors return structured responses with error messages and context.

## Audio Storage

- **Format**: WAV files (configurable)
- **Storage**: MinIO object storage with versioning
- **Access**: Presigned URLs with configurable expiry
- **Path**: `sessions/{session_id}/recording.wav`
- **Metadata**: Size, timestamps, content type

## Session Caching

- **Store**: Redis with TTL expiry
- **Key Format**: `session:{session_id}`
- **TTL**: 1 hour for active sessions, 24 hours for completed
- **Data**: JSON-serialized session metadata and transcript segments

## Next Steps

1. **Gladia Integration**: Set up real Gladia API key for production STT
2. **WebSocket Client**: Implement audio streaming from frontend/recording device
3. **Frontend Integration**: Add audio playback components using playback URLs
4. **Scoring System**: Build scoring domain to analyze transcripts
5. **Leaderboard**: Create leaderboard domain for competitive rankings

## API Integration

The MCP tools are ready for use by AI assistants through the Model Context Protocol. Each tool has well-defined schemas and can be called directly by compatible AI systems.

For manual testing and development, use the integration test script or call tools directly through the `execute_mcp_tool` function.
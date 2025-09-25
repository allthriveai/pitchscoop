# PitchScoop Recording & Scoring Endpoints

## Base URL
```
http://localhost:8000
```

## Recording Endpoints

### 1. Start Recording

**Endpoint:** `POST /mcp/execute`

**Request:**
```json
{
  "tool": "pitches.start_recording",
  "arguments": {
    "team_name": "Your Team Name",
    "pitch_title": "Your Pitch Title",
    "event_id": "optional-event-id"
  }
}
```

**Response:**
```json
{
  "session_id": "session-abc-123",
  "event_id": "event-456",
  "team_name": "Your Team Name",
  "pitch_title": "Your Pitch Title",
  "status": "ready_to_record",
  "websocket_url": "wss://gladia-websocket-url",
  "created_at": "2024-01-15T10:00:00Z",
  "success": true
}
```

### 2. Stop Recording

**Endpoint:** `POST /mcp/execute`

**Request:**
```json
{
  "tool": "pitches.stop_recording",
  "arguments": {
    "session_id": "session-abc-123",
    "audio_data_base64": "optional-base64-audio-data"
  }
}
```

**Response:**
```json
{
  "session_id": "session-abc-123",
  "status": "completed",
  "transcript": {
    "total_text": "Hi, I'm presenting our AI agent...",
    "segments_count": 5
  },
  "audio": {
    "has_audio": true,
    "audio_size": 1024000,
    "playback_url": "https://minio-url/audio.wav?expires=..."
  },
  "completed_at": "2024-01-15T10:03:00Z",
  "success": true
}
```

### 3. Get Session Details

**Endpoint:** `POST /mcp/execute`

**Request:**
```json
{
  "tool": "pitches.get_session",
  "arguments": {
    "session_id": "session-abc-123"
  }
}
```

**Response:**
```json
{
  "session_id": "session-abc-123",
  "event_id": "event-456",
  "team_name": "Your Team Name",
  "pitch_title": "Your Pitch Title",
  "status": "completed",
  "has_audio": true,
  "has_transcript": true,
  "current_playback_url": "https://minio-url/audio.wav?expires=...",
  "created_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:03:00Z",
  "success": true
}
```

### 4. List All Sessions

**Endpoint:** `GET /api/sessions`

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "session-abc-123",
      "event_id": "event-456",
      "team_name": "Your Team Name",
      "pitch_title": "Your Pitch Title",
      "status": "completed",
      "has_audio": true,
      "has_transcript": true,
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:03:00Z"
    }
  ],
  "total_count": 1
}
```

## Scoring Endpoints

### Score a Pitch

**Endpoint:** `POST /mcp/execute`

**Request:**
```json
{
  "tool": "analysis.score_pitch",
  "arguments": {
    "session_id": "your-session-id",
    "event_id": "your-event-id",
    "judge_id": "optional-judge-id"
  }
}
```

**Response:**
```json
{
  "session_id": "your-session-id",
  "event_id": "your-event-id", 
  "team_name": "Demo Team",
  "pitch_title": "AI Document Analysis Agent",
  "scores": {
    "idea": {
      "score": 22.5,
      "max_score": 25,
      "strengths": ["Clear value proposition", "Specific use case"],
      "areas_of_improvement": ["More details needed"]
    },
    "technical_implementation": {
      "score": 20.0,
      "max_score": 25,
      "strengths": ["Multi-tool integration", "Clear architecture"],
      "areas_of_improvement": ["More technical depth"]
    },
    "tool_use": {
      "score": 23.0,
      "max_score": 25,
      "sponsor_tools_used": ["OpenAI", "Qdrant", "MinIO"],
      "tool_count": 3,
      "strengths": ["Meets 3+ tool requirement"],
      "areas_of_improvement": ["More sophisticated behaviors"]
    },
    "presentation_delivery": {
      "score": 21.0,
      "max_score": 25,
      "strengths": ["Clear delivery", "Good timing"],
      "areas_of_improvement": ["More interactive demo"]
    },
    "overall": {
      "total_score": 86.5,
      "max_total": 100,
      "percentage": 86.5,
      "ranking_tier": "very_good",
      "judge_recommendation": "Excellent foundation with clear market focus."
    }
  },
  "scoring_timestamp": "2024-01-15T10:05:00Z",
  "success": true
}
```

**Key Points:**
- Always check `success: true` before using data
- Total score is out of 100, each criterion out of 25
- Rankings: `excellent` > `very_good` > `good` > `needs_improvement`
- Include `event_id` for proper isolation
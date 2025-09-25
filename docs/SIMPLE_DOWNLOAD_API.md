# Simple Download API for Frontend

## Get a Recording + Its Score

**Step 1: Get the recording session**
```bash
GET http://localhost:8000/api/sessions
```

**Step 2: Download the audio file**
```bash
# Use the playback_url from the session response
GET {playback_url}
```

**Step 3: Get the score**
```bash
POST http://localhost:8000/mcp/execute
{
  "tool": "analysis.get_scores",
  "arguments": {
    "session_id": "session-123",
    "event_id": "event-456"
  }
}
```

## Example Response

**Sessions list:**
```json
{
  "sessions": [{
    "session_id": "session-123",
    "team_name": "Demo Team",
    "pitch_title": "AI Document Analysis",
    "current_playback_url": "http://localhost:9000/audio.wav?expires=...",
    "status": "completed"
  }]
}
```

**Score response:**
```json
{
  "team_name": "Demo Team",
  "scores": {
    "overall": {
      "total_score": 86.5,
      "ranking_tier": "very_good"
    },
    "idea": {"score": 22.5},
    "technical_implementation": {"score": 20.0},
    "tool_use": {"score": 23.0},
    "presentation_delivery": {"score": 21.0}
  },
  "success": true
}
```

That's it. Three endpoints, done.
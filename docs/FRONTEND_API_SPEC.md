# PitchScoop Recording & Scoring API Specification for Frontend

## Overview
This document provides the exact API endpoints and response formats for integrating pitch recording and scoring into the frontend.

## Base URL
```
http://localhost:8000
```

---

## Recording Endpoints

### 1. Start Recording

#### Endpoint
```
POST /mcp/execute
```

#### Request Body
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

#### Response Format
```json
{
  "session_id": "session-abc-123",
  "event_id": "event-456",
  "team_name": "Your Team Name",
  "pitch_title": "Your Pitch Title",
  "status": "ready_to_record",
  "websocket_url": "wss://gladia-websocket-url-or-mock",
  "created_at": "2024-01-15T10:00:00Z",
  "success": true
}
```

### 2. Stop Recording

#### Endpoint
```
POST /mcp/execute
```

#### Request Body
```json
{
  "tool": "pitches.stop_recording",
  "arguments": {
    "session_id": "session-abc-123",
    "audio_data_base64": "optional-base64-encoded-audio-file"
  }
}
```

#### Response Format
```json
{
  "session_id": "session-abc-123",
  "status": "completed",
  "transcript": {
    "total_text": "Hi, I'm presenting our AI agent for document analysis. We use OpenAI, Qdrant, and MinIO...",
    "segments_count": 5
  },
  "audio": {
    "has_audio": true,
    "audio_size": 1024000,
    "minio_object_key": "sessions/session-abc-123/recording.wav",
    "playback_url": "https://localhost:9000/pitchscoop/sessions/session-abc-123/recording.wav?expires=..."
  },
  "completed_at": "2024-01-15T10:03:00Z",
  "success": true
}
```

### 3. Get Session Details

#### Endpoint
```
POST /mcp/execute
```

#### Request Body
```json
{
  "tool": "pitches.get_session",
  "arguments": {
    "session_id": "session-abc-123"
  }
}
```

#### Response Format
```json
{
  "session_id": "session-abc-123",
  "event_id": "event-456",
  "team_name": "Your Team Name",
  "pitch_title": "Your Pitch Title",
  "status": "completed",
  "has_audio": true,
  "has_transcript": true,
  "current_playback_url": "https://localhost:9000/pitchscoop/sessions/session-abc-123/recording.wav?expires=...",
  "created_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:03:00Z",
  "final_transcript": {
    "total_text": "Complete transcript text here...",
    "segments_count": 5
  },
  "success": true
}
```

### 4. List All Sessions

#### Endpoint
```
GET /api/sessions
```

#### Response Format
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
      "completed_at": "2024-01-15T10:03:00Z",
      "current_playback_url": "https://localhost:9000/pitchscoop/sessions/session-abc-123/recording.wav?expires=..."
    }
  ],
  "total_count": 1,
  "filtered_count": 1
}
```

---

## Scoring Endpoints

### 1. Score a Pitch

### Endpoint
```
POST /mcp/execute
```

### Request Body
```json
{
  "tool": "analysis.score_pitch",
  "arguments": {
    "session_id": "session-123",
    "event_id": "event-456", 
    "judge_id": "judge-789"
  }
}
```

### Response Format
```json
{
  "session_id": "session-123",
  "event_id": "event-456",
  "judge_id": "judge-789",
  "team_name": "Demo Team",
  "pitch_title": "AI Document Analysis Agent",
  "scores": {
    "idea": {
      "score": 22.5,
      "max_score": 25,
      "unique_value_proposition": "Document quality analysis with AI reasoning",
      "vertical_focus": "Enterprise document management",
      "reasoning_capabilities": "Advanced NLP analysis of document structure",
      "action_capabilities": "Automated issue detection and report generation",
      "tool_integration": "Seamless OpenAI, Qdrant, MinIO pipeline",
      "strengths": [
        "Clear value proposition for enterprise market",
        "Specific vertical focus on document quality"
      ],
      "areas_of_improvement": [
        "More details on reasoning sophistication needed",
        "Expand on competitive advantages"
      ]
    },
    "technical_implementation": {
      "score": 20.0,
      "max_score": 25,
      "novel_tool_use": "Multi-stage document processing pipeline",
      "technical_sophistication": "Good integration architecture",
      "surprise_factor": "Innovative document quality metrics",
      "implementation_quality": "Clean tool integration approach",
      "strengths": [
        "Multi-tool integration shows technical depth",
        "Clear architectural thinking"
      ],
      "areas_of_improvement": [
        "More technical implementation details",
        "Demonstrate more novel tool usage patterns"
      ]
    },
    "tool_use": {
      "score": 23.0,
      "max_score": 25,
      "sponsor_tools_used": ["OpenAI", "Qdrant", "MinIO"],
      "tool_count": 3,
      "integration_quality": "Well-integrated tool stack with clear purpose",
      "agentic_behavior": "Document analysis, quality assessment, report generation",
      "tool_synergy": "Tools complement each other for complete workflow",
      "strengths": [
        "Meets 3+ sponsor tool requirement",
        "Clear synergy between tool choices"
      ],
      "areas_of_improvement": [
        "Could demonstrate more sophisticated agentic behaviors",
        "Show more tool interaction complexity"
      ]
    },
    "presentation_delivery": {
      "score": 21.0,
      "max_score": 25,
      "demo_clarity": "Clear explanation of agent capabilities and workflow",
      "impact_demonstration": "Good explanation of business impact",
      "time_management": "Stayed within 3-minute limit effectively",
      "delivery_quality": "Professional presentation style",
      "agent_impact_shown": "Clear demonstration of value proposition",
      "strengths": [
        "Clear and professional delivery",
        "Good time management"
      ],
      "areas_of_improvement": [
        "More interactive live demo elements",
        "Show real-time agent actions"
      ]
    },
    "overall": {
      "total_score": 86.5,
      "max_total": 100,
      "percentage": 86.5,
      "ranking_tier": "very_good",
      "standout_features": [
        "Strong tool integration strategy",
        "Clear enterprise value proposition"
      ],
      "critical_improvements": [
        "Enhanced technical depth demonstration",
        "More sophisticated agentic behavior showcase"
      ],
      "judge_recommendation": "Excellent foundation with clear market focus. Strengthen technical demonstration and show more complex agent behaviors to reach top tier."
    }
  },
  "scoring_timestamp": "2024-01-15T10:05:00Z",
  "success": true
}
```

---

## 2. Get Existing Scores

### Endpoint
```
POST /mcp/execute
```

### Request Body
```json
{
  "tool": "analysis.get_scores",
  "arguments": {
    "session_id": "session-123",
    "event_id": "event-456",
    "include_details": true
  }
}
```

### Response Format (Same as Score Pitch)
```json
{
  "session_id": "session-123",
  "event_id": "event-456",
  "team_name": "Demo Team",
  "pitch_title": "AI Document Analysis Agent", 
  "scoring_timestamp": "2024-01-15T10:05:00Z",
  "judge_id": "judge-789",
  "has_scoring": true,
  "has_tool_analysis": true,
  "scores": {
    // Same structure as above
  }
}
```

---

## 3. List All Sessions

### Endpoint
```
GET /api/sessions
```

### Response Format
```json
{
  "sessions": [
    {
      "session_id": "session-123",
      "event_id": "event-456",
      "team_name": "Demo Team",
      "pitch_title": "AI Document Analysis Agent",
      "status": "completed",
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:03:00Z",
      "has_audio": true,
      "has_transcript": true,
      "current_playback_url": "https://minio-url/audio.wav?expires=..."
    }
  ],
  "total_count": 1,
  "filtered_count": 1
}
```

---

## 4. Get Presentation Analysis (with Audio Intelligence)

### Endpoint
```
GET /api/sessions/{session_id}/scoring?event_id={event_id}
```

### Response Format
```json
{
  "session_id": "session-123",
  "event_id": "event-456",
  "team_name": "Demo Team",
  "pitch_title": "AI Document Analysis Agent",
  "analysis_timestamp": "2024-01-15T10:05:00Z",
  "analysis_type": "presentation_delivery",
  
  "content_analysis": {
    "demo_clarity": "Clear demo explanation with 5 demo references",
    "impact_demonstration": "Impact shown with 3 impact indicators",
    "technical_depth": "Technical content with 4 technical terms",
    "time_management": "Duration: 180s (target: 180s)",
    "estimated_wpm": 150.5,
    "content_score": 8.5
  },
  
  "audio_intelligence": {
    "available": true,
    "speech_pace": {
      "words_per_minute": 152,
      "speaking_rate_assessment": "optimal",
      "pace_vs_target": 2
    },
    "delivery_quality": {
      "filler_percentage": 2.1,
      "professionalism_grade": "excellent",
      "filler_words_detected": ["um", "uh"]
    },
    "confidence_energy": {
      "confidence_score": 0.85,
      "confidence_assessment": "high",
      "energy_level": "engaging"
    },
    "overall_audio_score": 22.5
  },
  
  "presentation_delivery_score": {
    "content_score": 8.5,
    "audio_delivery_score": 22.5,
    "combined_score": 18.9,
    "max_score": 25.0,
    "final_score": 18.9
  },
  
  "insights": {
    "strengths": [
      "Clear focus on demonstrating the agent's capabilities",
      "Excellent speaking pace at optimal rate",
      "High vocal confidence throughout presentation"
    ],
    "areas_of_improvement": [
      "Include more explicit demonstrations of the agent in action",
      "Reduce usage of filler words like 'um'"
    ],
    "coaching_recommendations": [
      "Maintain current excellent pace",
      "Practice eliminating filler words",
      "Structure: Problem → Solution → Demo → Impact"
    ]
  },
  
  "success": true
}
```

---

## 5. Error Responses

### Format
```json
{
  "error": "Error message describing what went wrong",
  "session_id": "session-123",
  "event_id": "event-456", 
  "error_type": "session_not_found|missing_transcript|ai_analysis_error|etc"
}
```

### Common Errors
- `"No transcript available for scoring"` - Recording not completed
- `"Session not found"` - Invalid session_id
- `"AI analysis system error"` - Azure OpenAI connectivity issues
- `"Missing required parameters"` - Invalid request format

---

## Frontend Integration Examples

### React/JavaScript Example
```javascript
// Score a pitch
const scoreResponse = await fetch('http://localhost:8000/mcp/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tool: 'analysis.score_pitch',
    arguments: {
      session_id: sessionId,
      event_id: eventId,
      judge_id: judgeId
    }
  })
});

const scores = await scoreResponse.json();

if (scores.success) {
  // Display scores
  console.log(`Total Score: ${scores.scores.overall.total_score}/100`);
  console.log(`Ranking: ${scores.scores.overall.ranking_tier}`);
  
  // Individual criteria
  console.log(`Idea: ${scores.scores.idea.score}/25`);
  console.log(`Technical: ${scores.scores.technical_implementation.score}/25`);
  console.log(`Tools: ${scores.scores.tool_use.score}/25`);
  console.log(`Presentation: ${scores.scores.presentation_delivery.score}/25`);
} else {
  console.error('Scoring failed:', scores.error);
}
```

### TypeScript Interfaces
```typescript
interface ScoreResponse {
  session_id: string;
  event_id: string;
  judge_id?: string;
  team_name: string;
  pitch_title: string;
  scores: {
    idea: CriterionScore;
    technical_implementation: CriterionScore;
    tool_use: ToolUseScore;
    presentation_delivery: PresentationScore;
    overall: OverallScore;
  };
  scoring_timestamp: string;
  success: boolean;
}

interface CriterionScore {
  score: number;
  max_score: number;
  strengths: string[];
  areas_of_improvement: string[];
}

interface OverallScore {
  total_score: number;
  max_total: number;
  percentage: number;
  ranking_tier: 'excellent' | 'very_good' | 'good' | 'needs_improvement';
  standout_features: string[];
  critical_improvements: string[];
  judge_recommendation: string;
}
```

---

## Complete Workflow Example

### Frontend Integration Flow
```javascript
// 1. Start Recording
const startResponse = await fetch('http://localhost:8000/mcp/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tool: 'pitches.start_recording',
    arguments: {
      team_name: 'Demo Team',
      pitch_title: 'AI Document Analysis Agent',
      event_id: 'demo-event-456'
    }
  })
});
const startData = await startResponse.json();
const sessionId = startData.session_id;

// 2. Record audio (via WebSocket or audio capture)
// ... recording implementation ...

// 3. Stop Recording
const stopResponse = await fetch('http://localhost:8000/mcp/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tool: 'pitches.stop_recording',
    arguments: {
      session_id: sessionId,
      audio_data_base64: audioBase64 // optional
    }
  })
});
const stopData = await stopResponse.json();

// 4. Score the Pitch
const scoreResponse = await fetch('http://localhost:8000/mcp/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tool: 'analysis.score_pitch',
    arguments: {
      session_id: sessionId,
      event_id: 'demo-event-456',
      judge_id: 'judge-001'
    }
  })
});
const scores = await scoreResponse.json();

if (scores.success) {
  // Display results
  console.log(`Total Score: ${scores.scores.overall.total_score}/100`);
  console.log(`Ranking: ${scores.scores.overall.ranking_tier}`);
}
```

### Session Status Flow
```
initializing → ready_to_record → recording → processing → completed
                                                     ↓
                                                  error (if failed)
```

---

## Key Points for Frontend Development

### Recording
1. **Always check `success: true`** before using response data
2. **Session ID** is returned from start_recording - save it for all subsequent calls
3. **WebSocket URL** is provided for real-time audio streaming (Gladia integration)
4. **Audio upload** via base64 in stop_recording is optional
5. **Status tracking** through session status field

### Scoring  
1. **All scores are on 0-100 scale** with 25 points per criterion
2. **`ranking_tier`** provides easy categorization for UI display
3. **Detailed feedback** available in `strengths` and `areas_of_improvement` arrays
4. **Multi-tenant isolation** via `event_id` - always include it
5. **Timestamps** in ISO 8601 format for easy parsing
6. **Error handling** via `error` field in responses

### Audio Playback
1. **Playback URLs** expire after 1-24 hours (configurable)
2. **MinIO URLs** format: `https://localhost:9000/pitchscoop/sessions/{session_id}/recording.wav`
3. **Refresh URLs** using `pitches.get_playback_url` tool when expired

This specification covers everything your frontend developer needs to integrate both pitch recording and scoring functionality!

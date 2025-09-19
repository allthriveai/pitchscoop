# Recording Progression Analysis System

A Domain-Driven Design (DDD) implementation for tracking and analyzing how teams' pitch recordings evolve over time, built using LlamaIndex for semantic analysis and Redis for storage.

## 📋 Overview

The Recording Progression Analysis System allows you to:
- Track multiple versions of team recordings over time
- Analyze how recordings improve or change between versions  
- Get AI-powered insights about progression patterns
- Compare specific recording versions
- Perform semantic search across all recordings

## 🏗️ Architecture

The system follows DDD principles within the `recordings` domain:

```
domains/recordings/
├── entities/
│   ├── recording_version.py          # Core domain entity
│   └── stt_session.py               # Existing STT session entity
├── value_objects/
│   ├── recording_version_id.py      # Version identifier
│   ├── team_id.py                   # Team identifier  
│   ├── recording_scores.py          # Scoring data
│   ├── audio_intelligence.py        # Audio analysis data (existing)
│   └── ...
├── services/
│   └── recording_progression_service.py  # Domain service
├── repositories/
│   └── recording_version_repository.py   # Repository interface
├── infrastructure/
│   └── redis_recording_version_repository.py  # Redis implementation
└── mcp/
    └── recording_progression_mcp_tools.py     # MCP tools
```

## 🎯 Core Concepts

### RecordingVersion Entity
Represents a single version of a team's pitch recording:
- **Version ID**: Unique identifier for this specific version
- **Team ID**: Identifies which team owns this recording
- **Version Number**: Sequential number (1, 2, 3, etc.)
- **Transcripts**: Complete transcript data from STTSession
- **Scores**: Optional pitch scoring data
- **Audio Intelligence**: Optional audio analysis data
- **Metadata**: Additional contextual information

### Key Domain Services

#### RecordingProgressionService
- **Add Recording Version**: Create new versions from STT sessions
- **Analyze Progression**: Compare how recordings evolve over time
- **Generate Insights**: AI-powered analysis of improvement patterns
- **Compare Versions**: Detailed comparison between specific versions

## 🚀 Getting Started

### Prerequisites

Install required dependencies:
```bash
pip install llama-index llama-index-vector-stores-redis redis
```

### Basic Usage

#### 1. Initialize the Service
```python
from domains.recordings.services.recording_progression_service import RecordingProgressionService
from domains.recordings.infrastructure.redis_recording_version_repository import RedisRecordingVersionRepository

# Create repository and service
repository = RedisRecordingVersionRepository()
await repository.initialize()

service = RecordingProgressionService(repository)
```

#### 2. Add a Recording Version
```python
from domains.recordings.value_objects.team_id import TeamId

# After a team completes a recording session
team_id = TeamId.from_string("team_healthai_001")
recording_version = await service.add_recording_version(
    team_id=team_id,
    team_name="HealthAI Solutions",
    recording_title="MedAssist - AI Healthcare Diagnosis", 
    stt_session=completed_stt_session,
    scores=pitch_scores,  # Optional
    audio_intelligence=audio_analysis  # Optional
)
```

#### 3. Analyze Team Progression
```python
# Analyze how a team has improved over time
analysis = await service.analyze_team_progression(team_id)
print(f"Team has {analysis['version_count']} versions")
print(f"Score improvement: {analysis['progression_metrics']['score_changes']}")
```

#### 4. Get AI Insights
```python
# Get strategic insights about progression
insights = await service.get_progression_insights(team_id)
print(insights['insights'])  # AI-generated analysis
```

## 🔧 MCP Tools Integration

The system provides MCP tools for integration with the broader PitchScoop platform:

### Available Tools

1. **add_recording_version** - Add a new recording version for progression tracking
2. **analyze_team_progression** - Get comprehensive progression analysis
3. **get_progression_insights** - Get AI-powered strategic insights
4. **compare_recording_versions** - Compare two specific versions
5. **get_team_recordings** - List all recordings for a team
6. **semantic_search_recordings** - Search recordings using semantic similarity

### Using MCP Tools
```python
from domains.recordings.mcp.recording_progression_mcp_tools import create_recording_progression_mcp_tools

# Initialize MCP tools
tools = await create_recording_progression_mcp_tools(server, event_id="hackathon_2024")
```

## 📊 Features

### Semantic Search with LlamaIndex
- Vector embeddings of transcript content
- Similarity search across all recording versions
- Team-filtered searches
- Metadata-enriched results

### AI-Powered Analysis
- Uses Azure OpenAI for progression analysis
- Identifies key improvements and regressions
- Provides strategic recommendations
- Contextual insights based on scoring data

### Quantitative Metrics
- Score progression tracking
- Word count and duration changes
- Audio intelligence evolution (confidence, filler words, pace)
- Version frequency analysis

### Data Storage
- Redis for fast key-value storage
- LlamaIndex Redis vector store for semantic search
- 30-day TTL for automatic cleanup
- Team and event indexing for quick retrieval

## 🎯 Use Cases

1. **Team Coaching**: Track how teams improve their pitch over multiple attempts
2. **Event Analytics**: Analyze progression patterns across all teams in an event
3. **Scoring Insights**: Understand which aspects of pitches improve most over time
4. **Content Analysis**: Find similar pitches or identify common improvement patterns
5. **Judge Feedback**: Provide data-driven insights for more effective feedback

## 🔮 Future Enhancements

- Integration with real-time STT sessions
- Advanced visualization dashboards
- Benchmark comparisons against successful pitches
- Automated coaching recommendations
- Export capabilities for external analysis tools

## 🏷️ Domain Rules & Constraints

Following your existing DDD rules:
- Never use `localStorage.getItem('access_token')`
- Always use TypeScript for frontend development
- Keep services in `/services` subfolder
- Use PostgreSQL as the database (for future persistence layer)
- Never bypass or disable pre-commits
- Run all checks in pre-push git hooks

## 📝 Next Steps

To complete the integration:

1. **Connect with STTSession**: Update the service to automatically create recording versions when STT sessions complete
2. **Add Frontend Integration**: Create TypeScript interfaces for the progression data
3. **Database Persistence**: Add PostgreSQL repository implementation alongside Redis
4. **Visualization Components**: Build React components to display progression timelines and insights
5. **Testing Suite**: Add comprehensive unit and integration tests

The foundation is now in place following proper DDD principles within your existing codebase structure!
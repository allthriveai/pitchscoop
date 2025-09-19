# PitchScoop MCP Implementation Plan - Next Steps

Based on the documentation review and current codebase analysis, here's your prioritized implementation roadmap for completing the pitchscoop MCP application.

## Current State Summary

### ✅ **Fully Implemented Domains**
- **Events Domain**: Complete with MCP tools (create_event, list_events, join_event, etc.)
- **Recordings Domain**: Complete with MCP tools (start_recording, stop_recording, get_session, etc.)
- **Scoring Domain**: Complete with AI-powered analysis (score_pitch, compare_pitches, etc.)
- **Chat Domain**: Complete with RAG-powered conversational AI (start_conversation, send_message, etc.)

### ⚠️ **Partially Implemented (Structure Only)**
- **Leaderboards Domain**: Empty structure exists, needs full implementation
- **Feedback Domain**: Empty structure exists, needs full implementation

### 🔴 **Missing Critical Components**
- **MCP Server**: No actual MCP protocol server implementation
- **End-to-End Workflow**: Domains aren't connected in a complete pipeline

---

## Phase 1: Complete Core Domains (2-3 weeks)

### Priority 1: Leaderboards Domain Implementation

#### 1.1 Value Objects
```
api/domains/leaderboards/value_objects/
├── ranking.py              # Ranking and RankingPosition classes
├── leaderboard_entry.py    # Individual team entries with scores
└── competition_period.py   # Time-based competition phases
```

**Key Components:**
- `Ranking`: Overall competition rankings with tie-breaking
- `RankingPosition`: Individual team position with score breakdown
- `LeaderboardEntry`: Team entry with scores, timestamps, metadata
- `CompetitionPeriod`: Time windows for scoring phases

#### 1.2 Entities
```
api/domains/leaderboards/entities/
├── leaderboard.py      # Main leaderboard entity with ranking logic
├── competition.py      # Competition lifecycle management
└── leaderboard_entry.py # Team participation tracking
```

**Key Features:**
- Real-time ranking calculations
- Multi-criteria sorting (overall, idea, technical, tools, presentation)
- Tie-breaking logic with fallback criteria
- Historical snapshots for competition phases
- Event-scoped isolation using `event_id`

#### 1.3 Services
```
api/domains/leaderboards/services/
├── leaderboard_service.py         # Core leaderboard operations
├── ranking_calculation_service.py # Advanced ranking algorithms
└── competition_lifecycle_service.py # Competition state management
```

**Core Logic:**
- Score aggregation from scoring domain
- Real-time ranking updates
- Competition phase transitions
- Leaderboard finalization and archiving

#### 1.4 MCP Tools
```
api/domains/leaderboards/mcp/
├── leaderboard_mcp_handler.py # Handler implementation
└── leaderboard_mcp_tools.py   # Tool definitions
```

**Required MCP Tools:**
```python
# Core leaderboard operations
leaderboards.generate_leaderboard(event_id, criteria="overall_score")
leaderboards.get_team_ranking(event_id, session_id)
leaderboards.update_team_score(event_id, session_id, scores)

# Competition management  
leaderboards.create_competition(event_id, title, config)
leaderboards.finalize_leaderboard(event_id)
leaderboards.get_leaderboard_snapshot(event_id, snapshot_id)

# Statistics and analysis
leaderboards.get_competition_stats(event_id)
leaderboards.compare_team_rankings(event_id, session_ids)
```

#### 1.5 Repository
```
api/domains/leaderboards/repositories/
└── leaderboard_repository.py  # Redis-based persistence
```

**Redis Storage Patterns:**
- `event:{event_id}:leaderboard` - Main leaderboard data
- `event:{event_id}:rankings` - Current ranking positions
- `event:{event_id}:leaderboard:snapshots` - Historical snapshots
- `event:{event_id}:competition:config` - Competition settings

### Priority 2: Feedback Domain Implementation

#### 2.1 Value Objects
```
api/domains/feedback/value_objects/
├── feedback_category.py    # Categorized feedback (idea, technical, etc.)
├── improvement_area.py     # Specific improvement suggestions
├── feedback_score.py       # Scored feedback with ratings
└── report_template.py      # Customizable report formats
```

#### 2.2 Entities
```
api/domains/feedback/entities/
├── feedback_report.py      # Complete feedback document
├── team_performance.py     # Team performance analysis
└── comparative_analysis.py # Comparison with other teams
```

**Key Features:**
- AI-powered feedback generation using Azure OpenAI
- Multi-criteria analysis (idea, technical, tools, presentation)
- Comparative context (how team performed vs others)
- Actionable improvement recommendations
- Personalized coaching insights

#### 2.3 Services
```
api/domains/feedback/services/
├── feedback_generation_service.py # AI-powered feedback creation
├── report_generation_service.py   # Report formatting and delivery
└── comparative_analysis_service.py # Cross-team analysis
```

#### 2.4 MCP Tools
```
api/domains/feedback/mcp/
├── feedback_mcp_handler.py # Handler implementation
└── feedback_mcp_tools.py   # Tool definitions
```

**Required MCP Tools:**
```python
# Core feedback operations
feedback.generate_team_report(event_id, session_id, criteria=[])
feedback.get_feedback_report(event_id, session_id)
feedback.generate_comparative_feedback(event_id, session_ids)

# Analysis and insights
feedback.analyze_team_performance(event_id, session_id)
feedback.suggest_improvements(event_id, session_id, focus_areas=[])
feedback.compare_team_progress(event_id, session_id, comparison_sessions=[])

# Report management
feedback.customize_report_template(event_id, template_config)
feedback.export_feedback_report(event_id, session_id, format="pdf")
```

---

## Phase 2: MCP Server Implementation (1-2 weeks)

### Critical Missing Component: Actual MCP Protocol Server

Currently, you have MCP tools defined but no actual MCP server to serve them.

#### 2.1 MCP Server Core
```
api/mcp/
├── server.py              # Main MCP protocol server
├── transport.py           # WebSocket/HTTP transport layers
├── tool_registry.py       # Central tool registration
└── authentication.py      # API key and auth management
```

**Implementation Requirements:**
- Use official MCP SDK for protocol compliance
- WebSocket transport for real-time interactions
- HTTP transport for REST-like operations
- Tool discovery and schema serving
- Rate limiting and authentication
- Error handling and logging

#### 2.2 Tool Registration System
```python
# Centralized tool registry
from domains.events.mcp.events_mcp_tools import EVENT_MCP_TOOLS
from domains.recordings.mcp.recordings_mcp_tools import RECORDING_MCP_TOOLS
from domains.scoring.mcp.scoring_mcp_tools import SCORING_MCP_TOOLS
from domains.leaderboards.mcp.leaderboard_mcp_tools import LEADERBOARD_MCP_TOOLS
from domains.feedback.mcp.feedback_mcp_tools import FEEDBACK_MCP_TOOLS
from domains.chat.mcp.chat_mcp_tools import CHAT_MCP_TOOLS

# Register all tools with MCP server
ALL_MCP_TOOLS = {
    **EVENT_MCP_TOOLS,
    **RECORDING_MCP_TOOLS,
    **SCORING_MCP_TOOLS,
    **LEADERBOARD_MCP_TOOLS,
    **FEEDBACK_MCP_TOOLS,
    **CHAT_MCP_TOOLS
}
```

#### 2.3 Server Configuration
```
api/config/
├── mcp_server_config.py   # MCP server settings
├── tool_permissions.py    # Tool access control
└── rate_limits.py         # Rate limiting configuration
```

---

## Phase 3: End-to-End Workflow Integration (1 week)

### 3.1 Complete Pipeline Implementation

Create orchestration tools that connect all domains:

```python
# Complete workflow MCP tool
@mcp_tool("pitchscoop.complete_pitch_analysis")
async def complete_pitch_analysis(
    event_id: str,
    session_id: str,
    generate_feedback: bool = True
) -> dict:
    """Execute complete pitch analysis workflow"""
    
    # 1. Get pitch session data (recordings domain)
    session = await recordings_handler.get_session(session_id, event_id)
    
    # 2. Score the pitch (scoring domain)
    scores = await scoring_handler.score_pitch(session_id, event_id)
    
    # 3. Update leaderboard (leaderboards domain)
    ranking = await leaderboards_handler.update_team_score(
        event_id, session_id, scores
    )
    
    # 4. Generate feedback (feedback domain)
    feedback = None
    if generate_feedback:
        feedback = await feedback_handler.generate_team_report(
            event_id, session_id
        )
    
    return {
        "session_id": session_id,
        "scores": scores,
        "ranking": ranking,
        "feedback": feedback,
        "pipeline_success": True
    }
```

### 3.2 Integration Testing
```
tests/integration/
├── test_complete_workflow.py     # End-to-end pipeline testing
├── test_cross_domain_integration.py # Domain interaction testing
└── test_mcp_server_integration.py   # MCP protocol testing
```

---

## Phase 4: Environment and Configuration (3-5 days)

### 4.1 Complete Environment Setup
The `.env.example` is missing critical variables:

```bash
# Add to .env.example
SYSTEM_LLM_AZURE_ENDPOINT=your_azure_endpoint
SYSTEM_LLM_AZURE_API_KEY=your_api_key
SYSTEM_LLM_AZURE_DEPLOYMENT=your_deployment
SYSTEM_LLM_AZURE_API_VERSION=2024-02-15-preview
GLADIA_API_KEY=your_gladia_key

# MCP Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8001
MCP_SERVER_AUTH_REQUIRED=true
MCP_MAX_CONCURRENT_CONNECTIONS=100

# Rate Limiting
MCP_RATE_LIMIT_REQUESTS_PER_MINUTE=60
MCP_RATE_LIMIT_BURST_SIZE=10
```

### 4.2 Docker Configuration Updates
Update `docker-compose.yml` to include MCP server:

```yaml
services:
  mcp-server:
    build: .
    command: python -m api.mcp.server
    ports:
      - "8001:8001"
    depends_on:
      - redis
      - api
    environment:
      - MCP_SERVER_PORT=8001
```

---

## Implementation Timeline

### Week 1-2: Leaderboards Domain
- [ ] Value objects and entities (3-4 days)
- [ ] Services and business logic (2-3 days)  
- [ ] MCP tools and handlers (2 days)
- [ ] Unit tests (1 day)

### Week 3: Feedback Domain  
- [ ] Core entities and services (3-4 days)
- [ ] AI-powered feedback generation (2 days)
- [ ] MCP tools integration (1 day)

### Week 4: MCP Server Implementation
- [ ] Core MCP protocol server (3-4 days)
- [ ] Tool registration and discovery (1-2 days)
- [ ] Authentication and rate limiting (1 day)

### Week 5: Integration and Testing
- [ ] End-to-end workflow implementation (2-3 days)
- [ ] Integration testing (2 days)
- [ ] Documentation and deployment (1-2 days)

---

## Success Criteria

### Functional Requirements
- [ ] Complete Event → Recording → Scoring → Leaderboard → Feedback pipeline
- [ ] All domains have functional MCP tools
- [ ] MCP server serves tools via WebSocket/HTTP
- [ ] Real-time leaderboard updates
- [ ] AI-powered feedback generation
- [ ] Multi-tenant isolation with `event_id`

### Technical Requirements
- [ ] All tests pass (unit + integration)
- [ ] MCP protocol compliance
- [ ] Redis persistence for all domains
- [ ] Proper error handling and logging
- [ ] Rate limiting and authentication
- [ ] Docker containerization works

### Documentation Requirements
- [ ] API documentation updated
- [ ] MCP tool schemas documented
- [ ] Deployment guide completed
- [ ] Usage examples provided

---

## Next Immediate Action

**Start with Priority 1.1**: Implement the leaderboards value objects (`ranking.py`, `leaderboard_entry.py`) as they're the foundation for the entire leaderboards domain and are required for the core workflow to function.

This plan provides a clear path to complete your pitchscoop MCP application with all the missing pieces identified and prioritized.
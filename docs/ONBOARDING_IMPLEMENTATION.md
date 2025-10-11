# Onboarding Implementation Status

## Overview

Building the onboarding flow from `docs/ONBOARDING_FLOW.md` that works for **both MCP (Claude Desktop) and Web UI**.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Claude Desktop │    │  Web Frontend   │
│   (MCP Client)   │    │  (Coming Later) │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          │ MCP Tools            │ REST API
          │                      │
          ▼                      ▼
┌─────────────────────────────────────────┐
│      Onboarding MCP Tools / API Router  │
│     (Thin interface layer)              │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│      OnboardingService                  │
│      (Business logic - shared!)         │
│  - start_onboarding()                   │
│  - process_step()                       │
│  - create_participant_profile()         │
│  - configure_event_judging()            │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│      OnboardingRepository               │
│      (Database operations)              │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────┐
│      PostgreSQL Database                │
│  - onboarding_sessions                  │
│  - user_profiles                        │
│  - event_customizations                 │
└─────────────────────────────────────────┘
```

## ✅ Completed

### 1. Database Layer
- ✅ PostgreSQL added to docker-compose
- ✅ SQLAlchemy async setup
- ✅ Database models:
  - `OnboardingSession` - tracks progress through onboarding
  - `UserProfile` - participant information
  - `EventCustomization` - event-specific judging criteria

### 2. Configuration
- ✅ Default judging criteria (Idea, Technical, Tools, Presentation)
- ✅ Weight validation and normalization
- ✅ Help text configuration
- ✅ Required fields definition

### 3. Repository Layer  
- ✅ `OnboardingRepository` - CRUD operations for all entities
- ✅ Session management (create, get, update, complete)
- ✅ Profile operations
- ✅ Event customization operations

## 🚧 In Progress

### 4. Service Layer (Next)
Need to create `OnboardingService` with these methods:

```python
class OnboardingService:
    # Initial decision
    async def start_onboarding(user_id: str, role: str) -> dict
    
    # Organizer flow
    async def create_event_details(session_id: str, event_data: dict) -> dict
    async def configure_judging_criteria(session_id: str, categories: list) -> dict
    async def add_custom_judging_category(session_id: str, category: dict) -> dict
    
    # Participant flow
    async def create_participant_profile(session_id: str, profile_data: dict) -> dict
    async def join_event(session_id: str, event_id: str) -> dict
    
    # Common
    async def get_current_step(session_id: str) -> dict
    async def process_step(session_id: str, step_data: dict) -> dict
    async def get_help(session_id: str, topic: str) -> dict
```

### 5. MCP Tools (Next)
Need to create thin wrappers that call the service:

```python
ONBOARDING_MCP_TOOLS = {
    "onboarding.start": "Start onboarding flow",
    "onboarding.process_step": "Submit data for current step",
    "onboarding.get_help": "Get contextual help",
    # ... more tools
}
```

### 6. Validation Logic (Next)
Field validation based on requirements:

```python
class OnboardingValidator:
    def validate_profile_data(data: dict, required_fields: list) -> ValidationResult
    def validate_judging_categories(categories: list) -> ValidationResult
    def validate_event_details(data: dict) -> ValidationResult
```

## 📋 Next Steps

### Step 1: Create OnboardingService
**File**: `api/domains/onboarding/services/onboarding_service.py`

This is the core business logic that both MCP and web will use.

### Step 2: Create Validation Logic
**File**: `api/domains/onboarding/services/validation_service.py`

Validates user input for each step.

### Step 3: Create MCP Tools
**File**: `api/domains/onboarding/mcp/onboarding_mcp_tools.py`

Exposes onboarding to Claude Desktop.

### Step 4: Test MCP Flow
Use Claude Desktop to test the complete onboarding flow.

### Step 5: Add Web API (Later)
**File**: `api/domains/onboarding/router.py`

REST API endpoints for web frontend.

## User Flows

### Flow A: Event Organizer (via MCP)

```
User in Claude: "I want to create a hackathon"

Claude: [Calls onboarding.start with role="organizer"]
"Great! Let's set up your competition. 

What's the name of your event?"

User: "AI Innovation Challenge"

Claude: [Calls onboarding.process_step with event_name]
"Perfect! When does it start?"

User: "Next Friday"

Claude: [Processes date, moves to judging criteria]
"Now let's set up judging. I'll start with standard categories:
- Idea (25%)
- Technical (25%)
- Tools (20%)
- Presentation (30%)

Would you like to adjust these weights or add custom categories?"

User: "Add a Sustainability category worth 15%"

Claude: [Adds custom category, normalizes weights]
"Added! Updated categories:
- Idea (21%)
- Technical (21%)
- Tools (17%)
- Presentation (26%)
- Sustainability (15%)

Your event is ready! Event ID: ai-challenge-2025"
```

### Flow B: Participant (via MCP)

```
User in Claude: "Join the AI Innovation Challenge"

Claude: [Calls onboarding.start with role="participant", event_id]
"Welcome to AI Innovation Challenge! 🚀

Let's set up your profile. What's your name?"

User: "Alex Chen"

Claude: "Hi Alex! Team name?"

User: "Team Rocket"

Claude: [Collects all required fields]
"Great! You're all set. 

Available options:
- Upload your pitch video
- Record a practice pitch
- See past events"
```

## Key Design Decisions

### Why This Architecture?

1. **Shared Service Layer**: MCP and web use identical business logic
2. **Database-Driven**: Content comes from database, not hard-coded
3. **Event-Specific**: Each event can have custom judging criteria
4. **Stateful**: Onboarding session tracks progress
5. **Validation**: Input validation happens once, works everywhere

### Content Source

**NOT using YAML** because:
- ❌ Event organizers need to customize per-event
- ❌ Can't A/B test or analyze
- ❌ Changes require deployment

**Using PostgreSQL** because:
- ✅ Event organizers can customize their own events
- ✅ Changes are instant
- ✅ Can track analytics
- ✅ Same data for MCP and web

## Testing Strategy

### 1. Unit Tests
Test service methods in isolation

### 2. Integration Tests
Test database operations

### 3. MCP Flow Tests
Test via Claude Desktop

### 4. Web Flow Tests (Later)
Test via web UI

## Documentation for Frontend Team

When the web frontend is ready, they'll:

1. Call the same `OnboardingService` methods
2. Use REST API endpoints that wrap the service
3. Get identical behavior to MCP
4. Share validation logic

Example web endpoint:

```python
@router.post("/onboarding/start")
async def start_onboarding(
    request: StartOnboardingRequest,
    db: AsyncSession = Depends(get_db)
):
    service = OnboardingService(db)
    return await service.start_onboarding(
        user_id=request.user_id,
        role=request.role
    )
```

Same logic, different interface!

## Current File Structure

```
api/domains/onboarding/
├── config/
│   └── default_judging_criteria.py  ✅ Default categories and help text
├── entities/
│   ├── __init__.py                  ✅ Model exports
│   ├── onboarding_session.py        ✅ Session tracking
│   ├── user_profile.py              ✅ Participant profiles
│   └── event_customization.py       ✅ Event-specific config
├── repositories/
│   └── onboarding_repository.py     ✅ Database operations
├── services/
│   ├── onboarding_service.py        🚧 TODO: Business logic
│   └── validation_service.py        🚧 TODO: Input validation
└── mcp/
    └── onboarding_mcp_tools.py      🚧 TODO: MCP interface
```

## Ready to Continue?

The foundation is solid. Next step is to implement the `OnboardingService` with all the business logic from the onboarding flow document.

This service will power both MCP and the future web UI!

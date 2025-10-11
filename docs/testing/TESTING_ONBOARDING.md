# Testing PitchScoop Onboarding

Multiple ways to test the onboarding flow, from simple to complex.

## Option 1: Quick Test Script (Recommended)

Run the comprehensive test suite:

```bash
# Make sure Docker services are running
docker compose ps

# Run all tests
docker compose exec api python /app/../test_onboarding.py
```

This tests:
- ✅ Complete organizer onboarding flow (4 steps)
- ✅ Complete participant onboarding flow (4 steps)
- ✅ Validation of required fields
- ✅ Resuming existing sessions

Expected output:
```
🚀 ========================================================
🚀  PitchScoop Onboarding Test Suite
🚀 ========================================================

🎯 Testing Organizer Onboarding Flow
====================================

📝 Step 1: Starting onboarding as organizer...
✅ Session ID: xxx-xxx-xxx
   Current step: Event Details
   Message: Welcome! Let's create your pitch competition...

[... more steps ...]

🎉 ONBOARDING COMPLETE!

📊 Test Summary
====================================
✅ PASS  Organizer Onboarding
✅ PASS  Participant Onboarding  
✅ PASS  Validation Errors
✅ PASS  Resume Onboarding

4/4 tests passed

🎉 All tests passed!
```

## Option 2: Interactive Python Session

Test step-by-step in a Python shell:

```bash
docker compose exec api python
```

Then:

```python
import asyncio
import sys
sys.path.insert(0, '/app')

from domains.shared.infrastructure.database import AsyncSessionLocal
from domains.onboarding.services.onboarding_service import OnboardingService

async def test():
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        # Start onboarding
        result = await service.start_onboarding(
            user_id="allie_123",
            role="organizer"
        )
        
        print(f"Session ID: {result['session_id']}")
        print(f"Current step: {result['current_step']['title']}")
        
        # Submit first step
        result = await service.process_step(
            session_id=result['session_id'],
            step_data={
                "event_name": "My Hackathon",
                "event_type": "hackathon",
                "event_description": "An awesome hackathon",
                "start_date": "2024-12-01",
                "end_date": "2024-12-02"
            }
        )
        
        print(f"Next step: {result['next_step']['title']}")
        return result

# Run it
asyncio.run(test())
```

## Option 3: Via MCP Tools (Claude Desktop)

Once you install the MCP config:

```bash
# Install MCP config
./install_mcp.sh

# Restart Claude Desktop
```

Then in Claude Desktop, ask:

**"Start onboarding for me as an organizer"**

Claude will call `onboarding_start()` and guide you through the flow interactively!

## Option 4: Direct Database Check

Verify onboarding data was saved:

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U postgres -d pitchscoop

# Check onboarding sessions
SELECT id, user_id, role, current_step, status 
FROM onboarding_sessions 
ORDER BY created_at DESC 
LIMIT 5;

# Check user profiles
SELECT id, user_id, display_name, role 
FROM user_profiles 
ORDER BY created_at DESC 
LIMIT 5;

# Exit
\q
```

## What Each Test Validates

### Organizer Flow
1. **Event Details** - Name, type, dates, description
2. **Judging Configuration** - Default or custom criteria
3. **Review** - Summary of event setup
4. **Confirmation** - Create event in database

### Participant Flow
1. **Team Information** - Name, size, members
2. **Project Details** - Name, description, tech stack
3. **Review** - Summary of team/project
4. **Confirmation** - Register team for event

### Validation
- Required fields enforced
- Type checking (strings, dates, lists)
- Enum validation (event_type, role)
- Business rules (dates, team size)

### Resume Capability
- Same user can resume unfinished session
- Progress is preserved
- Can continue from last step

## Common Issues

### Database Connection Error
```bash
# Make sure PostgreSQL is running
docker compose ps postgres

# Should show "running (healthy)"
```

### Import Errors
```bash
# Make sure you're in the api container
docker compose exec api python test_onboarding.py
```

### No Tables Exist
```bash
# Run migrations
docker compose exec api alembic upgrade head
```

## Next Steps

After testing works:
1. **Try via MCP** - Test with Claude Desktop
2. **Add Web UI** - Build the minimal web onboarding interface
3. **Add Tests** - Write pytest unit tests
4. **Deploy** - Push to production

Happy testing! 🚀

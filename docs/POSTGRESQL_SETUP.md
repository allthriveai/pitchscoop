# PostgreSQL Setup for PitchScoop

## Overview

PostgreSQL has been added to PitchScoop for relational data storage, complementing Redis which handles caching and real-time data.

## What PostgreSQL Stores

### Onboarding Domain
- **User Profiles**: Participant information (name, team, project details)
- **Event Customizations**: Event organizer configurations for judging criteria and onboarding flows  
- **Onboarding Sessions**: Track user progress through multi-step onboarding

### Data Model

```sql
-- User profiles for participants
user_profiles:
  - user_id, user_name, team_name
  - project_name, project_description, github_repo
  
-- Event-specific customizations by organizers  
event_customizations:
  - event_id, welcome_message, required_fields
  - judging_categories (JSON with weights)
  - custom_category_name, custom_category_description

-- Session state for onboarding flows
onboarding_sessions:
  - user_id, role (organizer/participant)
  - current_flow, current_step, completed_steps
  - session_data (accumulated form inputs)
```

## Architecture: Hybrid Redis + PostgreSQL

**Redis**: Fast access for temporary data
- Events (with TTL)
- Real-time leaderboards
- Session recordings metadata
- Cache layer

**PostgreSQL**: Persistent relational data
- User profiles
- Event customizations
- Onboarding state
- Analytics data

## Getting Started

### 1. Start Services

```bash
docker compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379  
- MinIO on ports 9000/9001
- API on port 8002

### 2. Database Connection

The API automatically connects using the `DATABASE_URL` environment variable:

```
postgresql://pitchscoop:pitchscoop123@postgres:5432/pitchscoop
```

### 3. Tables are Auto-Created

Tables are automatically created when the API starts (for now). In production, we'll use Alembic migrations.

## Using the Database

### In MCP Tools

```python
from domains.shared.infrastructure.database import get_db
from domains.onboarding.entities import UserProfile

async def create_profile_mcp_tool(tool_name: str, arguments: dict):
    async with get_db() as db:
        profile = UserProfile(
            user_id=arguments["user_id"],
            user_name=arguments["user_name"],
            team_name=arguments["team_name"],
            # ...
        )
        db.add(profile)
        await db.commit()
        return profile.to_dict()
```

### In Web API (FastAPI)

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from domains.shared.infrastructure.database import get_db

@app.post("/profiles")
async def create_profile(
    request: CreateProfileRequest,
    db: AsyncSession = Depends(get_db)
):
    profile = UserProfile(**request.dict())
    db.add(profile)
    await db.commit()
    return profile.to_dict()
```

## Database Management

### Access PostgreSQL Directly

```bash
# Connect to database
docker compose exec postgres psql -U pitchscoop -d pitchscoop

# View tables
\dt

# Query data
SELECT * FROM user_profiles;
SELECT * FROM event_customizations;
```

### Reset Database (Development Only)

```bash
# Stop services
docker compose down

# Remove volume
docker volume rm pitchscoop_postgres-data

# Restart
docker compose up -d
```

## Future Enhancements

### Phase 2: Migrations with Alembic
- Proper migration system
- Version-controlled schema changes
- Rollback capability

### Phase 3: Additional Tables
- User authentication
- Event analytics
- Submission history
- Judge assignments

### Phase 4: Optimization
- Connection pooling
- Read replicas
- Query optimization
- Indexes for common queries

## Benefits of PostgreSQL + Redis Hybrid

1. **Best of Both Worlds**
   - PostgreSQL: Reliable, relational, queryable
   - Redis: Fast, real-time, scalable

2. **Clean Separation**
   - PostgreSQL: User data, configurations
   - Redis: Temporary data, caching, real-time

3. **Flexibility**
   - Complex queries in PostgreSQL
   - Simple key-value in Redis
   - Right tool for each job

4. **Scalability**  
   - Can scale PostgreSQL and Redis independently
   - Offload reads to Redis cache
   - Write to PostgreSQL for durability

## Troubleshooting

### Connection Issues

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# View logs
docker compose logs postgres

# Test connection
docker compose exec postgres pg_isready -U pitchscoop
```

### Common Issues

**"Database does not exist"**
- The database is created automatically on first start
- If issues persist, recreate the container

**"Connection refused"**
- Ensure PostgreSQL container is healthy
- Check `docker compose ps` for container status

**"Tables not found"**
- Tables are created on API startup
- Check API logs for migration errors

## Next Steps

With PostgreSQL set up, you can now:
1. Implement onboarding services that use these models
2. Create MCP tools for onboarding flows
3. Build web API endpoints for event customization
4. Add analytics queries for event organizers

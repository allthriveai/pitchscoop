"""
Events domain REST API router
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime
import json
import redis.asyncio as redis
from typing import Literal

# Import MCP handlers
from .mcp.events_mcp_tools import EVENTS_MCP_TOOLS
from .mcp.events_mcp_handler import events_mcp_handler

router = APIRouter(prefix="/api/events", tags=["events"])


# ============= Models =============
# These should eventually be in a models.py file within this domain

class CreateEventRequest(BaseModel):
    """Request to create a new event"""
    event_type: Literal["hackathon", "vc_pitch", "individual_practice"]
    event_name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    max_participants: int = Field(50, gt=0, le=1000)
    duration_minutes: int = Field(5, gt=0, le=60)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_config: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "hackathon",
                "event_name": "AI Innovation Challenge 2024",
                "description": "Build innovative AI applications using MCP tools",
                "max_participants": 50,
                "duration_minutes": 5
            }
        }


class UpsertEventRequest(BaseModel):
    """Request to create or update an event (legacy)"""
    event_id: str = Field(..., min_length=1)
    judges: List[str]
    rules: Dict[str, Any]
    goals: List[str]
    sponsor_tools: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "hackathon-2024",
                "judges": ["judge1", "judge2"],
                "rules": {"max_duration": 5, "team_size": 4},
                "goals": ["Innovation", "Technical Excellence"],
                "sponsor_tools": ["OpenAI", "Redis", "MinIO"]
            }
        }


class EventResponse(BaseModel):
    """Event information response"""
    event_id: str
    event_type: str
    event_name: str
    description: str
    status: Literal["upcoming", "active", "completed", "cancelled"]
    max_participants: int
    duration_minutes: int
    participant_count: int = 0
    session_count: int = 0
    created_at: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_config: Dict[str, Any]


class EventSummary(BaseModel):
    """Event summary for listing"""
    event_id: str
    event_name: str
    event_type: str
    status: str
    participant_count: int
    created_at: datetime


class EventListResponse(BaseModel):
    """Response for event listing"""
    events: List[EventSummary]
    total_count: int
    filters_applied: Dict[str, Any]


class UpsertEventResponse(BaseModel):
    """Response for event creation/update"""
    ok: bool
    event_id: str
    message: str = "Event created successfully"


# ============= Helper functions =============

async def execute_events_tool(tool_name: str, args: Dict[str, Any]):
    """Execute events MCP tool."""
    if tool_name in EVENTS_MCP_TOOLS:
        handler_name = EVENTS_MCP_TOOLS[tool_name]["handler"]
        handler = getattr(events_mcp_handler, handler_name)
        return await handler(**args)
    else:
        raise HTTPException(status_code=404, detail=f"Unknown events tool: {tool_name}")


# ============= Endpoints =============

@router.post("/create", response_model=EventResponse)
async def create_event(request: CreateEventRequest):
    """Create a new event"""
    try:
        result = await execute_events_tool("events.create_event", request.dict())
        return EventResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upsert", response_model=UpsertEventResponse)
async def upsert_event(request: UpsertEventRequest):
    """Legacy endpoint: Create or update an event"""
    # Get Redis connection (this should be injected via dependency)
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    r = await redis.from_url(REDIS_URL, decode_responses=True)
    
    event_key = f"event:{request.event_id}"
    
    event_data = {
        "judges": json.dumps(request.judges),
        "rules": json.dumps(request.rules),
        "goals": json.dumps(request.goals),
        "sponsor_tools": json.dumps(request.sponsor_tools)
    }
    
    await r.hset(event_key, mapping=event_data)
    await r.close()
    
    return UpsertEventResponse(ok=True, event_id=request.event_id)


@router.get("/list", response_model=EventListResponse)
async def list_events(
    event_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=500)
):
    """List all events with optional filters"""
    try:
        filters = {}
        if event_type:
            filters["event_type"] = event_type
        if status:
            filters["status"] = status
            
        result = await execute_events_tool("events.list_events", {
            "filters": filters,
            "limit": limit
        })
        return EventListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: str):
    """Get details for a specific event"""
    try:
        result = await execute_events_tool("events.get_event_details", {
            "event_id": event_id
        })
        return EventResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{event_id}/join")
async def join_event(
    event_id: str,
    team_name: str = Query(...),
    members: List[str] = Query([])
):
    """Join an event as a participant"""
    try:
        result = await execute_events_tool("events.join_event", {
            "event_id": event_id,
            "team_name": team_name,
            "members": members
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{event_id}/start")
async def start_event(event_id: str):
    """Start an event"""
    try:
        result = await execute_events_tool("events.start_event", {
            "event_id": event_id
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{event_id}/end")
async def end_event(event_id: str):
    """End an event"""
    try:
        result = await execute_events_tool("events.end_event", {
            "event_id": event_id
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{event_id}")
async def delete_event(event_id: str):
    """Delete an event"""
    try:
        result = await execute_events_tool("events.delete_event", {
            "event_id": event_id
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
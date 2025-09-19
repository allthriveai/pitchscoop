from typing import Dict, List, Literal, Any
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import redis.asyncio as redis
import json
import os
from dotenv import load_dotenv

# Import MCP tools
try:
    from domains.recordings.mcp.mcp_tools import execute_mcp_tool as recordings_execute, list_available_tools as recordings_tools
    from domains.events.mcp.events_mcp_tools import EVENTS_MCP_TOOLS
    from domains.events.mcp.events_mcp_handler import events_mcp_handler
    from domains.users.mcp.users_mcp_tools import USERS_TOOLS, handle_users_tool_call
    
    async def execute_events_tool(tool_name, args):
        """Execute events MCP tool."""
        if tool_name in EVENTS_MCP_TOOLS:
            handler_name = EVENTS_MCP_TOOLS[tool_name]["handler"]
            handler = getattr(events_mcp_handler, handler_name)
            if handler_name == "create_event":
                return await handler(**args)
            elif handler_name == "list_events":
                return await handler(**args)
            elif handler_name == "get_event_details":
                return await handler(**args) 
            elif handler_name == "join_event":
                return await handler(**args)
            elif handler_name == "start_event":
                return await handler(**args)
            elif handler_name == "end_event":
                return await handler(**args)
            elif handler_name == "delete_event":
                return await handler(**args)
            else:
                return {"error": f"Unknown handler: {handler_name}"}
        else:
            return {"error": f"Unknown events tool: {tool_name}"}
    
    async def execute_mcp_tool(tool, args):
        # Try recordings domain first
        if tool.startswith('pitches.'):
            return await recordings_execute(tool, args)
        # Try events domain 
        elif tool.startswith('events.'):
            return await execute_events_tool(tool, args)
        # Try users domain
        elif tool.startswith('users.'):
            return await handle_users_tool_call(tool, args)
        else:
            return {"error": f"Unknown tool: {tool}"}
    
    def list_available_tools():
        tools = []
        tools.extend(recordings_tools())
        tools.extend(list(EVENTS_MCP_TOOLS.keys()))
        tools.extend([tool["name"] for tool in USERS_TOOLS])
        return tools
        
except ImportError as e:
    print(f"Warning: Could not import MCP tools: {e}")
    import traceback
    traceback.print_exc()
    async def execute_mcp_tool(tool, args):
        return {"error": "MCP tools not available"}
    def list_available_tools():
        return []

load_dotenv()

app = FastAPI(title="PitchScoop Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = None


async def get_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client


class SetRoleRequest(BaseModel):
    user_id: str
    role: Literal["organizer", "individual"]


class SetRoleResponse(BaseModel):
    ok: bool


class UpsertEventRequest(BaseModel):
    event_id: str
    judges: List[str]
    rules: Dict[str, Any]
    goals: List[str]
    sponsor_tools: List[str]


class UpsertEventResponse(BaseModel):
    ok: bool


class LeaderboardResponse(BaseModel):
    leaderboard: List[Dict[str, Any]]


class MCPExecuteRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any]


class MCPExecuteResponse(BaseModel):
    result: Dict[str, Any] = None
    error: str = None


class HealthResponse(BaseModel):
    ok: bool


@app.on_event("startup")
async def startup_event():
    await get_redis()


@app.on_event("shutdown")
async def shutdown_event():
    global redis_client
    if redis_client:
        await redis_client.close()


@app.get("/")
async def root():
    return {"message": "Hackathon MCP Backend", "docs": "/docs", "health": "/api/healthz"}


@app.get("/api/healthz", response_model=HealthResponse)
async def health_check():
    return HealthResponse(ok=True)


@app.post("/api/auth.set_role", response_model=SetRoleResponse)
async def set_role(request: SetRoleRequest):
    r = await get_redis()
    user_key = f"user:{request.user_id}"
    await r.hset(user_key, "role", request.role)
    return SetRoleResponse(ok=True)


@app.post("/api/events.upsert", response_model=UpsertEventResponse)
async def upsert_event(request: UpsertEventRequest):
    r = await get_redis()
    event_key = f"event:{request.event_id}"

    event_data = {
        "judges": json.dumps(request.judges),
        "rules": json.dumps(request.rules),
        "goals": json.dumps(request.goals),
        "sponsor_tools": json.dumps(request.sponsor_tools)
    }

    await r.hset(event_key, mapping=event_data)
    return UpsertEventResponse(ok=True)


@app.get("/api/leaderboard.generate", response_model=LeaderboardResponse)
async def generate_leaderboard(event_id: str = Query(...)):
    return LeaderboardResponse(leaderboard=[])


# MCP endpoints
@app.get("/mcp/health")
async def mcp_health():
    return {
        "status": "healthy",
        "available_tools": len(list_available_tools())
    }


@app.get("/mcp/tools")
async def mcp_tools():
    return {
        "tools": list_available_tools(),
        "total": len(list_available_tools())
    }


@app.post("/mcp/execute")
async def mcp_execute(request: MCPExecuteRequest):
    try:
        result = await execute_mcp_tool(request.tool, request.arguments)
        if isinstance(result, dict) and "error" in result:
            return {"error": result["error"]}
        return result
    except Exception as e:
        return {"error": str(e)}


# Serve static files (including our test HTML)
@app.get("/test")
async def serve_test_page():
    from fastapi.responses import FileResponse
    return FileResponse("test_recording.html")

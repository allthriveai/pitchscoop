from typing import Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis.asyncio as redis
import os
from dotenv import load_dotenv

# Import shared models
from api.domains.shared.models import HealthResponse

# Import domain routers
from api.domains.events.router import router as events_router
from api.domains.pitches.router import router as pitches_router
from api.domains.scoring.router import router as scoring_router
from api.domains.leaderboards.router import router as leaderboards_router
from api.domains.users.router import router as users_router
from api.domains.websockets.router import router as websockets_router

# Import MCP tools for centralized MCP endpoint
try:
    from api.domains.pitches.mcp.pitch_tools import handle_pitch_mcp_call, pitch_tools
    from api.domains.events.mcp.events_mcp_tools import EVENTS_MCP_TOOLS
    from api.domains.events.mcp.events_mcp_handler import events_mcp_handler
    from api.domains.users.mcp.users_mcp_tools import USERS_TOOLS, handle_users_tool_call
    from api.domains.scoring.mcp.scoring_mcp_tools import SCORING_MCP_TOOLS, execute_scoring_mcp_tool
    from api.domains.leaderboards.mcp.leaderboard_mcp_tools import LEADERBOARD_MCP_TOOLS, execute_leaderboard_mcp_tool
    
    async def execute_mcp_tool(tool, args):
        """Central MCP tool executor for all domains"""
        # Try pitches domain (new clean implementation)
        if tool.startswith('pitch_') or tool in ['pitch_health_check', 'create_pitch_session', 'analyze_pitch_video', 'get_coaching_insights', 'get_session_status', 'list_active_sessions']:
            return await handle_pitch_mcp_call(tool, args)
        # Try events domain 
        elif tool.startswith('events.'):
            if tool in EVENTS_MCP_TOOLS:
                handler_name = EVENTS_MCP_TOOLS[tool]["handler"]
                handler = getattr(events_mcp_handler, handler_name)
                return await handler(**args)
            return {"error": f"Unknown events tool: {tool}"}
        # Try users domain
        elif tool.startswith('users.'):
            return await handle_users_tool_call(tool, args)
        # Try scoring domain
        elif tool.startswith('analysis.'):
            return await execute_scoring_mcp_tool(tool, args)
        # Try leaderboard domain
        elif tool.startswith('leaderboard.'):
            return await execute_leaderboard_mcp_tool(tool, args)
        else:
            return {"error": f"Unknown tool: {tool}"}
    
    def list_available_tools():
        """List all available MCP tools from all domains"""
        tools = []
        # Add pitch tools
        tools.extend([tool["name"] for tool in pitch_tools.get_tool_definitions()])
        tools.extend(list(EVENTS_MCP_TOOLS.keys()))
        tools.extend([tool["name"] for tool in USERS_TOOLS])
        tools.extend(list(SCORING_MCP_TOOLS.keys()))
        tools.extend([tool["name"] for tool in LEADERBOARD_MCP_TOOLS])
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

app = FastAPI(
    title="PitchScoop Backend",
    version="0.2.0",
    description="MCP-first pitch competition platform with Redis Stack"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = None


async def get_redis() -> redis.Redis:
    """Get Redis connection singleton"""
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client


# ============= MCP Models =============

class MCPExecuteRequest(BaseModel):
    """Request to execute an MCP tool"""
    tool: str
    arguments: Dict[str, Any]


class MCPExecuteResponse(BaseModel):
    """Response from MCP tool execution"""
    result: Dict[str, Any] = None
    error: str = None


# ============= App Event Handlers =============

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    await get_redis()
    print("✅ Redis connected")
    print(f"✅ {len(list_available_tools())} MCP tools loaded")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    global redis_client
    if redis_client:
        await redis_client.close()
        print("✅ Redis connection closed")


# ============= Register Domain Routers =============

app.include_router(events_router)
app.include_router(pitches_router)
app.include_router(scoring_router)
app.include_router(leaderboards_router)
app.include_router(users_router)
app.include_router(websockets_router)


# ============= Core Endpoints =============

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "PitchScoop API",
        "version": "0.2.0",
        "description": "MCP-first pitch competition platform",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/healthz",
        "mcp_tools": f"/mcp/tools ({len(list_available_tools())} available)"
    }


@app.get("/api/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    r = await get_redis()
    
    services = {"redis": "healthy"}
    
    try:
        await r.ping()
    except Exception:
        services["redis"] = "unhealthy"
    
    return HealthResponse(
        ok=all(s == "healthy" for s in services.values()),
        services=services
    )



# ============= MCP Endpoints =============
# These remain centralized for AI assistants to have a single entry point

@app.get("/mcp/health")
async def mcp_health():
    """MCP health check"""
    return {
        "status": "healthy",
        "available_tools": len(list_available_tools()),
        "domains": [
            "events",
            "pitches",
            "scoring",
            "leaderboards",
            "users"
        ]
    }


@app.get("/mcp/tools")
async def mcp_tools():
    """List all available MCP tools"""
    tools = list_available_tools()
    
    # Organize by domain
    organized = {
        "pitches": [t for t in tools if t.startswith("pitch_") or "pitch" in t],
        "events": [t for t in tools if t.startswith("events.")],
        "analysis": [t for t in tools if t.startswith("analysis.")],
        "leaderboard": [t for t in tools if t.startswith("leaderboard.")],
        "users": [t for t in tools if t.startswith("users.")]
    }
    
    return {
        "tools": tools,
        "total": len(tools),
        "by_domain": organized
    }


@app.post("/mcp/execute", response_model=MCPExecuteResponse)
async def mcp_execute(request: MCPExecuteRequest):
    """Execute an MCP tool"""
    try:
        result = await execute_mcp_tool(request.tool, request.arguments)
        if isinstance(result, dict) and "error" in result:
            return MCPExecuteResponse(error=result["error"])
        return MCPExecuteResponse(result=result)
    except Exception as e:
        return MCPExecuteResponse(error=str(e))


# ============= Demo & Utility Endpoints =============

@app.get("/test")
async def serve_test_page():
    """Serve test recording page"""
    from fastapi.responses import FileResponse
    return FileResponse("test_recording.html")


@app.get("/interface")
async def serve_interface_page():
    """Serve main interface page"""
    from fastapi.responses import FileResponse
    return FileResponse("test_interface.html")


@app.get("/scoring")
async def serve_scoring_page():
    """Serve scoring interface page"""
    from fastapi.responses import FileResponse
    return FileResponse("scoring_interface.html")


@app.get("/leaderboard")
async def serve_leaderboard_page():
    """Serve leaderboard interface page"""
    from fastapi.responses import FileResponse
    return FileResponse("leaderboard_interface.html")


@app.get("/export")
async def serve_data_export_page():
    """Serve data export page"""
    from fastapi.responses import FileResponse
    return FileResponse("data_export.html")


@app.post("/api/populate-demo-data")
async def populate_mcp_hackathon_demo():
    """Populate Redis with MCP hackathon demo scoring data"""
    try:
        # Import and execute the demo population function
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/..")))
        
        from populate_mcp_hackathon_demo import populate_demo_data
        await populate_demo_data()
        
        return {
            "success": True,
            "message": "MCP hackathon demo data populated successfully",
            "event_id": "mcp-hackathon",
            "teams_created": 12,
            "instructions": "Visit http://localhost:8000/leaderboard and enter 'mcp-hackathon' as the Event ID"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to populate demo data"
        }

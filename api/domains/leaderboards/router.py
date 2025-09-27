"""
Leaderboards domain REST API router
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

# Import MCP handlers
from .mcp.leaderboard_mcp_tools import LEADERBOARD_MCP_TOOLS, execute_leaderboard_mcp_tool

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


# ============= Models =============

class LeaderboardEntry(BaseModel):
    """Individual leaderboard entry"""
    rank: int
    team_name: str
    session_id: str
    total_score: float
    pitch_title: Optional[str]
    category_scores: Optional[Dict[str, float]]
    movement: Optional[str]  # "up", "down", "steady", "new"
    previous_rank: Optional[int]


class LeaderboardResponse(BaseModel):
    """Leaderboard response"""
    event_id: str
    event_name: Optional[str]
    leaderboard: List[LeaderboardEntry]
    total_teams: int
    last_updated: datetime
    filters_applied: Dict[str, Any] = {}


class TeamRankResponse(BaseModel):
    """Individual team rank response"""
    event_id: str
    session_id: str
    team_name: str
    rank: int
    total_score: float
    percentile: float
    teams_ahead: int
    teams_behind: int
    distance_to_leader: float
    distance_to_next: Optional[float]


class LeaderboardStatsResponse(BaseModel):
    """Leaderboard statistics response"""
    event_id: str
    total_teams: int
    average_score: float
    median_score: float
    highest_score: float
    lowest_score: float
    score_distribution: Dict[str, int]
    top_categories: List[Dict[str, Any]]
    competitive_index: float  # How close scores are


class LiveUpdateRequest(BaseModel):
    """Request to subscribe to live leaderboard updates"""
    event_id: str = Field(..., description="Event ID to monitor")
    update_interval: int = Field(5, description="Update interval in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "hackathon-2024",
                "update_interval": 5
            }
        }


class CompareTeamsRequest(BaseModel):
    """Request to compare multiple teams"""
    event_id: str = Field(..., description="Event ID")
    session_ids: List[str] = Field(..., description="Session IDs to compare")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "hackathon-2024",
                "session_ids": ["session_001", "session_002", "session_003"]
            }
        }


# ============= Helper functions =============

async def execute_leaderboard_tool(tool_name: str, args: Dict[str, Any]):
    """Execute leaderboard MCP tool."""
    try:
        return await execute_leaderboard_mcp_tool(tool_name, args)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ============= Endpoints =============

@router.get("/{event_id}", response_model=LeaderboardResponse)
async def get_event_leaderboard(
    event_id: str,
    limit: int = Query(10, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    include_details: bool = Query(True, description="Include detailed scores"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get leaderboard rankings for an event"""
    try:
        result = await execute_leaderboard_tool("leaderboard.get_rankings", {
            "event_id": event_id,
            "limit": limit,
            "offset": offset,
            "include_details": include_details,
            "category": category
        })
        
        # Transform result to match response model
        return LeaderboardResponse(
            event_id=event_id,
            event_name=result.get("event_name"),
            leaderboard=[LeaderboardEntry(**entry) for entry in result.get("leaderboard", [])],
            total_teams=result.get("total_teams", 0),
            last_updated=datetime.utcnow(),
            filters_applied={"category": category} if category else {}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Leaderboard not found: {str(e)}")


@router.get("/{event_id}/team/{session_id}", response_model=TeamRankResponse)
async def get_team_rank(event_id: str, session_id: str):
    """Get individual team's rank and position details"""
    try:
        result = await execute_leaderboard_tool("leaderboard.get_team_rank", {
            "event_id": event_id,
            "session_id": session_id
        })
        return TeamRankResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Team not found: {str(e)}")


@router.get("/{event_id}/stats", response_model=LeaderboardStatsResponse)
async def get_leaderboard_stats(event_id: str):
    """Get statistical analysis of the leaderboard"""
    try:
        result = await execute_leaderboard_tool("leaderboard.get_stats", {
            "event_id": event_id
        })
        return LeaderboardStatsResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{event_id}/top", response_model=LeaderboardResponse)
async def get_top_teams(
    event_id: str,
    top_n: int = Query(3, le=10, description="Number of top teams to return")
):
    """Get only the top N teams (podium view)"""
    try:
        result = await execute_leaderboard_tool("leaderboard.get_rankings", {
            "event_id": event_id,
            "limit": top_n,
            "include_details": True
        })
        
        return LeaderboardResponse(
            event_id=event_id,
            event_name=result.get("event_name"),
            leaderboard=[LeaderboardEntry(**entry) for entry in result.get("leaderboard", [])],
            total_teams=result.get("total_teams", 0),
            last_updated=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{event_id}/compare")
async def compare_teams(event_id: str, request: CompareTeamsRequest):
    """Compare multiple teams side by side"""
    try:
        result = await execute_leaderboard_tool("leaderboard.compare_teams", {
            "event_id": event_id,
            "session_ids": request.session_ids
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{event_id}/changes")
async def get_ranking_changes(
    event_id: str,
    since_minutes: int = Query(5, description="Get changes in the last N minutes")
):
    """Get recent ranking changes and movements"""
    try:
        result = await execute_leaderboard_tool("leaderboard.get_recent_changes", {
            "event_id": event_id,
            "since_minutes": since_minutes
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{event_id}/category/{category}")
async def get_category_leaders(
    event_id: str,
    category: str,
    limit: int = Query(10, description="Number of entries to return")
):
    """Get leaders for a specific scoring category"""
    try:
        result = await execute_leaderboard_tool("leaderboard.get_category_leaders", {
            "event_id": event_id,
            "category": category,
            "limit": limit
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{event_id}/refresh")
async def refresh_leaderboard(event_id: str):
    """Force refresh/recalculation of the leaderboard"""
    try:
        result = await execute_leaderboard_tool("leaderboard.refresh", {
            "event_id": event_id
        })
        return {"message": "Leaderboard refreshed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{event_id}/export")
async def export_leaderboard(
    event_id: str,
    format: str = Query("json", description="Export format: json, csv")
):
    """Export leaderboard data"""
    try:
        result = await execute_leaderboard_tool("leaderboard.export", {
            "event_id": event_id,
            "format": format
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Legacy endpoint for backward compatibility
@router.get("/generate")
async def generate_leaderboard(event_id: str = Query(...)):
    """Legacy endpoint - generates/gets leaderboard for an event"""
    return await get_event_leaderboard(event_id, limit=100)
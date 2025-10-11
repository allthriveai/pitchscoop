#!/usr/bin/env python3
"""
PitchScoop MCP Server (FastMCP 2.0)

Exposes all PitchScoop domain tools via MCP for AI agent integration.
"""

from fastmcp import FastMCP
import logging
from typing import Dict, Any

# Import domain MCP tool executors
from domains.events.mcp.events_mcp_tools import execute_events_mcp_tool
from domains.pitches.mcp.pitch_tools import handle_pitch_mcp_call
from domains.scoring.mcp.scoring_mcp_tools import execute_scoring_mcp_tool
from domains.chat.mcp.chat_mcp_tools import execute_chat_mcp_tool
from domains.market.mcp.market_mcp_tools import execute_market_mcp_tool
from domains.system.mcp.system_mcp_tools import execute_system_mcp_tool
from domains.onboarding.mcp.onboarding_mcp_tools import execute_onboarding_mcp_tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pitchscoop.mcp")

mcp = FastMCP("PitchScoop")

# System Tools
@mcp.tool()
async def system_check_environment() -> Dict[str, Any]:
    """Check if PitchScoop environment is properly configured"""
    return await execute_system_mcp_tool("system.check_environment", {})

@mcp.tool()
async def system_verify_setup() -> Dict[str, Any]:
    """Verify complete PitchScoop setup"""
    return await execute_system_mcp_tool("system.verify_setup", {})

@mcp.tool()
async def system_get_help(topic: str) -> Dict[str, Any]:
    """Get help: 'quickstart', 'setup', 'troubleshooting', 'domains'"""
    return await execute_system_mcp_tool("system.get_help", {"topic": topic})

# Onboarding Tools
@mcp.tool()
async def onboarding_start(user_id: str, role: str, event_id: str = None) -> Dict[str, Any]:
    """Start onboarding as 'organizer' or 'participant'"""
    return await execute_onboarding_mcp_tool("onboarding.start", {
        "user_id": user_id, "role": role, "event_id": event_id
    })

@mcp.tool()
async def onboarding_submit_step(session_id: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
    """Submit data for current onboarding step"""
    return await execute_onboarding_mcp_tool("onboarding.submit_step", {
        "session_id": session_id, "step_data": step_data
    })

@mcp.tool()
async def onboarding_get_current_step(session_id: str) -> Dict[str, Any]:
    """Get details about current onboarding step"""
    return await execute_onboarding_mcp_tool("onboarding.get_current_step", {
        "session_id": session_id
    })

@mcp.tool()
async def onboarding_get_help(topic: str) -> Dict[str, Any]:
    """Get help: 'event_types', 'judging_weights', 'custom_categories', 'project_description'"""
    return await execute_onboarding_mcp_tool("onboarding.get_help", {"topic": topic})

# Events Tools
@mcp.tool()
async def events_create(name: str, event_type: str, description: str = None,
                        start_date: str = None, end_date: str = None,
                        judging_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create pitch competition: 'hackathon', 'vc_pitch', 'practice_session'"""
    return await execute_events_mcp_tool("events.create", {
        "name": name, "event_type": event_type, "description": description,
        "start_date": start_date, "end_date": end_date, "judging_criteria": judging_criteria
    })

@mcp.tool()
async def events_list(status: str = None, event_type: str = None) -> Dict[str, Any]:
    """List events. Status: 'upcoming', 'active', 'completed'"""
    return await execute_events_mcp_tool("events.list", {"status": status, "event_type": event_type})

@mcp.tool()
async def events_get_details(event_id: str) -> Dict[str, Any]:
    """Get event details"""
    return await execute_events_mcp_tool("events.get_details", {"event_id": event_id})

# Scoring Tools
@mcp.tool()
async def scoring_analyze_pitch(pitch_id: str, event_id: str = None) -> Dict[str, Any]:
    """Analyze pitch with AI scoring"""
    return await execute_scoring_mcp_tool("scoring.analyze_pitch", {
        "pitch_id": pitch_id, "event_id": event_id
    })

@mcp.tool()
async def scoring_get_scores(pitch_id: str) -> Dict[str, Any]:
    """Get all scores for pitch"""
    return await execute_scoring_mcp_tool("scoring.get_scores", {"pitch_id": pitch_id})

# Chat Tools
@mcp.tool()
async def chat_query(question: str, event_id: str = None, context: str = None) -> Dict[str, Any]:
    """Query competition data with RAG"""
    return await execute_chat_mcp_tool("chat.query", {
        "question": question, "event_id": event_id, "context": context
    })

# Market Tools  
@mcp.tool()
async def market_research(query: str, focus_areas: list = None) -> Dict[str, Any]:
    """Conduct market research"""
    return await execute_market_mcp_tool("market.research", {
        "query": query, "focus_areas": focus_areas
    })

@mcp.tool()
async def market_analyze_competitors(company_name: str, industry: str = None) -> Dict[str, Any]:
    """Analyze competitors"""
    return await execute_market_mcp_tool("market.analyze_competitors", {
        "company_name": company_name, "industry": industry
    })

# Pitch Tools
@mcp.tool()
async def pitches_upload(event_id: str, team_name: str,
                         video_url: str = None, video_file: str = None) -> Dict[str, Any]:
    """Upload pitch video"""
    return await handle_pitch_mcp_call("pitches.upload", {
        "event_id": event_id, "team_name": team_name,
        "video_url": video_url, "video_file": video_file
    })

@mcp.tool()
async def pitches_analyze(pitch_id: str, analyze_emotions: bool = True) -> Dict[str, Any]:
    """Analyze pitch with Hume AI emotions"""
    return await handle_pitch_mcp_call("pitches.analyze", {
        "pitch_id": pitch_id, "analyze_emotions": analyze_emotions
    })

@mcp.tool()
async def pitches_get_feedback(pitch_id: str) -> Dict[str, Any]:
    """Get coaching feedback"""
    return await handle_pitch_mcp_call("pitches.get_feedback", {"pitch_id": pitch_id})

if __name__ == "__main__":
    logger.info("Starting PitchScoop MCP Server (FastMCP 2.0)")
    mcp.run()

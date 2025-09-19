"""
Leaderboard MCP Tools - Expose leaderboard functionality via MCP interface.

This module provides MCP tools for generating leaderboards, getting team ranks,
and retrieving competition statistics based on existing scoring data.
"""

import traceback
from typing import Dict, Any, List
from .leaderboard_mcp_handler import LeaderboardMCPHandler
from ...shared.infrastructure.logging import get_logger, log_with_context


# Global handler instance
leaderboard_mcp_handler = LeaderboardMCPHandler()


async def execute_leaderboard_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute leaderboard MCP tools with structured error handling and logging.
    
    Args:
        tool_name: Name of the MCP tool to execute
        arguments: Tool arguments
        
    Returns:
        Tool execution result
    """
    logger = get_logger("leaderboards.mcp_execution")
    
    log_with_context(
        logger, "INFO", f"Executing leaderboard MCP tool: {tool_name}",
        tool_name=tool_name,
        event_id=arguments.get("event_id"),
        session_id=arguments.get("session_id")
    )
    
    try:
        # Route to appropriate handler method
        if tool_name == "leaderboard.get_rankings":
            return await _handle_get_rankings(arguments)
        elif tool_name == "leaderboard.get_team_rank":
            return await _handle_get_team_rank(arguments)
        elif tool_name == "leaderboard.get_stats":
            return await _handle_get_stats(arguments)
        else:
            return {
                "error": f"Unknown leaderboard MCP tool: {tool_name}",
                "tool_name": tool_name,
                "available_tools": [
                    "leaderboard.get_rankings",
                    "leaderboard.get_team_rank", 
                    "leaderboard.get_stats"
                ]
            }
    
    except Exception as e:
        log_with_context(
            logger, "ERROR", f"MCP tool execution failed: {str(e)}",
            tool_name=tool_name,
            event_id=arguments.get("event_id"),
            error_type=type(e).__name__,
            traceback=traceback.format_exc()
        )
        return {
            "error": f"MCP tool execution failed: {str(e)}",
            "tool_name": tool_name,
            "error_type": type(e).__name__
        }


async def _handle_get_rankings(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle leaderboard.get_rankings MCP tool.
    
    Get top 10 (or specified limit) team rankings for an event.
    
    Args:
        arguments: {
            "event_id": str,           # Required - Event identifier
            "limit": int,              # Optional - Number of teams to return (default 10)
            "include_details": bool    # Optional - Include pitch titles/details (default true)
        }
    """
    logger = get_logger("leaderboards.get_rankings")
    
    # Validate required parameters
    event_id = arguments.get("event_id")
    if not event_id:
        return {
            "error": "Missing required parameter: event_id",
            "required_params": ["event_id"],
            "optional_params": ["limit", "include_details"]
        }
    
    # Extract optional parameters with defaults
    limit = arguments.get("limit", 10)
    include_details = arguments.get("include_details", True)
    
    # Validate limit parameter
    if not isinstance(limit, int) or limit < 1 or limit > 100:
        return {
            "error": "Invalid limit parameter. Must be integer between 1 and 100",
            "provided_limit": limit
        }
    
    log_with_context(
        logger, "INFO", "Generating event leaderboard",
        event_id=event_id,
        limit=limit,
        include_details=include_details
    )
    
    # Execute leaderboard generation
    result = await leaderboard_mcp_handler.generate_leaderboard(
        event_id=event_id,
        limit=limit,
        include_team_details=include_details
    )
    
    # Add tool execution metadata
    if result.get("success"):
        result["tool_name"] = "leaderboard.get_rankings"
        result["executed_at"] = result.get("generated_at")
        
        log_with_context(
            logger, "INFO", "Leaderboard generated successfully",
            event_id=event_id,
            total_teams=result.get("total_teams", 0),
            returned_count=result.get("returned_count", 0)
        )
    else:
        log_with_context(
            logger, "ERROR", "Leaderboard generation failed",
            event_id=event_id,
            error=result.get("error")
        )
    
    return result


async def _handle_get_team_rank(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle leaderboard.get_team_rank MCP tool.
    
    Get individual team's rank and position in the event leaderboard.
    
    Args:
        arguments: {
            "event_id": str,     # Required - Event identifier
            "session_id": str    # Required - Team's session identifier
        }
    """
    logger = get_logger("leaderboards.get_team_rank")
    
    # Validate required parameters
    event_id = arguments.get("event_id")
    session_id = arguments.get("session_id")
    
    if not event_id or not session_id:
        return {
            "error": "Missing required parameters",
            "required_params": ["event_id", "session_id"],
            "provided_params": {
                "event_id": event_id,
                "session_id": session_id
            }
        }
    
    log_with_context(
        logger, "INFO", "Getting team rank",
        event_id=event_id,
        session_id=session_id
    )
    
    # Execute team rank retrieval
    result = await leaderboard_mcp_handler.get_team_rank(
        event_id=event_id,
        session_id=session_id
    )
    
    # Add tool execution metadata
    if result.get("success"):
        result["tool_name"] = "leaderboard.get_team_rank"
        
        log_with_context(
            logger, "INFO", "Team rank retrieved successfully",
            event_id=event_id,
            session_id=session_id,
            team_name=result.get("team_name"),
            rank=result.get("rank"),
            total_score=result.get("total_score")
        )
    else:
        log_with_context(
            logger, "ERROR", "Team rank retrieval failed",
            event_id=event_id,
            session_id=session_id,
            error=result.get("error")
        )
    
    return result


async def _handle_get_stats(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle leaderboard.get_stats MCP tool.
    
    Get statistical summary of the event leaderboard.
    
    Args:
        arguments: {
            "event_id": str    # Required - Event identifier
        }
    """
    logger = get_logger("leaderboards.get_stats")
    
    # Validate required parameters
    event_id = arguments.get("event_id")
    if not event_id:
        return {
            "error": "Missing required parameter: event_id",
            "required_params": ["event_id"]
        }
    
    log_with_context(
        logger, "INFO", "Getting leaderboard statistics",
        event_id=event_id
    )
    
    # Execute statistics generation
    result = await leaderboard_mcp_handler.get_leaderboard_stats(
        event_id=event_id
    )
    
    # Add tool execution metadata
    if result.get("success"):
        result["tool_name"] = "leaderboard.get_stats"
        
        stats = result.get("stats", {})
        log_with_context(
            logger, "INFO", "Statistics generated successfully",
            event_id=event_id,
            total_teams=stats.get("total_teams", 0),
            avg_score=round(stats.get("average_score", 0), 2) if stats.get("average_score") else 0
        )
    else:
        log_with_context(
            logger, "ERROR", "Statistics generation failed",
            event_id=event_id,
            error=result.get("error")
        )
    
    return result


# MCP Tool Definitions for external registration
LEADERBOARD_MCP_TOOLS = [
    {
        "name": "leaderboard.get_rankings",
        "description": "Get top 10 team rankings for an event based on AI scoring results",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier for multi-tenant isolation"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of top teams to return (1-100, default 10)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10
                },
                "include_details": {
                    "type": "boolean", 
                    "description": "Include pitch titles and scoring details (default true)",
                    "default": True
                }
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "leaderboard.get_team_rank",
        "description": "Get individual team's rank and position in the event leaderboard",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                },
                "session_id": {
                    "type": "string", 
                    "description": "Team's session identifier from their pitch recording"
                }
            },
            "required": ["event_id", "session_id"]
        }
    },
    {
        "name": "leaderboard.get_stats",
        "description": "Get statistical summary of the event leaderboard (score distribution, averages, etc.)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                }
            },
            "required": ["event_id"]
        }
    }
]


if __name__ == "__main__":
    # Test the MCP tools directly
    import asyncio
    
    async def test_leaderboard_tools():
        """Test leaderboard MCP tools with sample data."""
        
        # Test 1: Get rankings for an event
        print("Testing leaderboard.get_rankings...")
        result = await execute_leaderboard_mcp_tool(
            "leaderboard.get_rankings",
            {"event_id": "test-event-123", "limit": 5}
        )
        print(f"Result: {result}\n")
        
        # Test 2: Get team rank
        print("Testing leaderboard.get_team_rank...")
        result = await execute_leaderboard_mcp_tool(
            "leaderboard.get_team_rank",
            {"event_id": "test-event-123", "session_id": "session-123"}
        )
        print(f"Result: {result}\n")
        
        # Test 3: Get statistics
        print("Testing leaderboard.get_stats...")
        result = await execute_leaderboard_mcp_tool(
            "leaderboard.get_stats",
            {"event_id": "test-event-123"}
        )
        print(f"Result: {result}")
    
    # Run test
    asyncio.run(test_leaderboard_tools())
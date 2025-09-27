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
        elif tool_name == "leaderboard.update_score":
            return await update_team_score(arguments)
        elif tool_name == "leaderboard.get_stats":
            return await _handle_get_stats(arguments)
        elif tool_name == "leaderboard.compare_teams":
            return await _handle_compare_teams(arguments)
        elif tool_name == "leaderboard.get_recent_changes":
            return await _handle_get_recent_changes(arguments)
        elif tool_name == "leaderboard.get_category_leaders":
            return await _handle_get_category_leaders(arguments)
        elif tool_name == "leaderboard.refresh":
            return await _handle_refresh_leaderboard(arguments)
        elif tool_name == "leaderboard.export":
            return await _handle_export_leaderboard(arguments)
        else:
            return {
                "error": f"Unknown leaderboard MCP tool: {tool_name}",
                "tool_name": tool_name,
                "available_tools": [
                    "leaderboard.get_rankings",
                    "leaderboard.get_team_rank",
                    "leaderboard.update_score",
                    "leaderboard.get_stats",
                    "leaderboard.compare_teams",
                    "leaderboard.get_recent_changes",
                    "leaderboard.get_category_leaders",
                    "leaderboard.refresh",
                    "leaderboard.export"
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


async def update_team_score(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a team's score in the Redis Sorted Set leaderboard.
    This is called automatically when teams get scored, but can also be used manually.
    """
    logger = get_logger("leaderboards.update_score")
    
    # Validate required parameters
    event_id = arguments.get("event_id")
    session_id = arguments.get("session_id")
    team_name = arguments.get("team_name")
    total_score = arguments.get("total_score")
    
    if not all([event_id, session_id, total_score]):
        return {
            "error": "Missing required parameters",
            "required_params": ["event_id", "session_id", "total_score"],
            "provided_params": list(arguments.keys())
        }
    
    log_with_context(
        logger, "INFO", "Updating team score in leaderboard",
        event_id=event_id,
        session_id=session_id,
        team_name=team_name,
        score=total_score
    )
    
    # Execute score update
    result = await leaderboard_mcp_handler.update_team_score_in_leaderboard(
        event_id=event_id,
        session_id=session_id,
        team_name=team_name or f"Team-{session_id}",
        total_score=float(total_score)
    )
    
    if result.get("success"):
        result["tool_name"] = "leaderboard.update_score"
        log_with_context(
            logger, "INFO", "Team score updated successfully",
            event_id=event_id,
            session_id=session_id,
            new_rank=result.get("rank")
        )
    else:
        log_with_context(
            logger, "ERROR", "Failed to update team score",
            event_id=event_id,
            session_id=session_id,
            error=result.get("error")
        )
    
    return result


async def _handle_compare_teams(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle leaderboard.compare_teams MCP tool."""
    logger = get_logger("leaderboards.compare_teams")
    
    event_id = arguments.get("event_id")
    session_ids = arguments.get("session_ids", [])
    
    if not event_id or not session_ids:
        return {
            "error": "Missing required parameters",
            "required_params": ["event_id", "session_ids"]
        }
    
    try:
        teams_comparison = []
        for session_id in session_ids:
            team_result = await leaderboard_mcp_handler.get_team_rank(
                event_id=event_id,
                session_id=session_id
            )
            if team_result.get("success"):
                teams_comparison.append(team_result)
        
        return {
            "event_id": event_id,
            "teams_comparison": teams_comparison,
            "total_compared": len(teams_comparison),
            "success": True
        }
    except Exception as e:
        return {"error": f"Failed to compare teams: {str(e)}", "success": False}


async def _handle_get_recent_changes(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle leaderboard.get_recent_changes MCP tool."""
    logger = get_logger("leaderboards.recent_changes")
    
    event_id = arguments.get("event_id")
    since_minutes = arguments.get("since_minutes", 5)
    
    if not event_id:
        return {"error": "Missing required parameter: event_id"}
    
    # For now, return current leaderboard since we don't store historical changes
    # In a full implementation, you'd compare current vs previous snapshots
    result = await leaderboard_mcp_handler.generate_leaderboard(
        event_id=event_id,
        limit=20,
        include_team_details=True
    )
    
    if result.get("success"):
        result["message"] = f"Current rankings (changes tracking in last {since_minutes} minutes would require historical snapshots)"
        result["changes_tracked"] = False
    
    return result


async def _handle_get_category_leaders(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle leaderboard.get_category_leaders MCP tool."""
    logger = get_logger("leaderboards.category_leaders")
    
    event_id = arguments.get("event_id")
    category = arguments.get("category")
    limit = arguments.get("limit", 10)
    
    if not event_id or not category:
        return {
            "error": "Missing required parameters",
            "required_params": ["event_id", "category"]
        }
    
    try:
        # Get full leaderboard with details
        result = await leaderboard_mcp_handler.generate_leaderboard(
            event_id=event_id,
            limit=100,  # Get all teams to sort by category
            include_team_details=True
        )
        
        if not result.get("success"):
            return result
        
        # Sort by specific category score
        leaderboard = result.get("leaderboard", [])
        category_map = {
            "idea": "idea_score",
            "technical": "technical_score", 
            "tools": "tool_use_score",
            "presentation": "presentation_score"
        }
        
        category_key = category_map.get(category)
        if not category_key:
            return {
                "error": f"Invalid category: {category}",
                "valid_categories": list(category_map.keys())
            }
        
        # Sort by category score
        category_leaders = []
        for entry in leaderboard:
            category_scores = entry.get("category_scores", {})
            if category_key in category_scores:
                entry["category_score"] = category_scores[category_key]
                category_leaders.append(entry)
        
        # Sort by category score descending
        category_leaders.sort(key=lambda x: x.get("category_score", 0), reverse=True)
        
        return {
            "event_id": event_id,
            "category": category,
            "leaders": category_leaders[:limit],
            "total_teams": len(category_leaders),
            "success": True
        }
        
    except Exception as e:
        return {"error": f"Failed to get category leaders: {str(e)}", "success": False}


async def _handle_refresh_leaderboard(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle leaderboard.refresh MCP tool."""
    logger = get_logger("leaderboards.refresh")
    
    event_id = arguments.get("event_id")
    if not event_id:
        return {"error": "Missing required parameter: event_id"}
    
    # Simply regenerate the leaderboard (it's already real-time with Redis Sorted Sets)
    result = await leaderboard_mcp_handler.generate_leaderboard(
        event_id=event_id,
        limit=100,
        include_team_details=True
    )
    
    if result.get("success"):
        result["message"] = "Leaderboard refreshed from Redis Sorted Sets"
        result["refreshed_at"] = result.get("generated_at")
    
    return result


async def _handle_export_leaderboard(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle leaderboard.export MCP tool."""
    logger = get_logger("leaderboards.export")
    
    event_id = arguments.get("event_id")
    format_type = arguments.get("format", "json")
    
    if not event_id:
        return {"error": "Missing required parameter: event_id"}
    
    # Get full leaderboard
    result = await leaderboard_mcp_handler.generate_leaderboard(
        event_id=event_id,
        limit=1000,
        include_team_details=True
    )
    
    if not result.get("success"):
        return result
    
    if format_type == "json":
        return {
            "event_id": event_id,
            "format": "json",
            "data": result,
            "exported_at": result.get("generated_at"),
            "success": True
        }
    elif format_type == "csv":
        # Simple CSV conversion
        leaderboard = result.get("leaderboard", [])
        csv_rows = ["rank,team_name,session_id,total_score,idea_score,technical_score,tool_use_score,presentation_score"]
        
        for entry in leaderboard:
            category_scores = entry.get("category_scores", {})
            csv_row = f"{entry.get('rank')},{entry.get('team_name')},{entry.get('session_id')},{entry.get('total_score')},{category_scores.get('idea_score', 0)},{category_scores.get('technical_score', 0)},{category_scores.get('tool_use_score', 0)},{category_scores.get('presentation_score', 0)}"
            csv_rows.append(csv_row)
        
        return {
            "event_id": event_id,
            "format": "csv",
            "data": "\n".join(csv_rows),
            "exported_at": result.get("generated_at"),
            "success": True
        }
    else:
        return {
            "error": f"Unsupported format: {format_type}",
            "supported_formats": ["json", "csv"]
        }


# MCP Tool Definitions for external registration
LEADERBOARD_MCP_TOOLS = {
    "leaderboard.get_rankings": {
        "description": "Get top 10 team rankings for an event based on AI scoring results using Redis Sorted Sets",
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
    "leaderboard.get_team_rank": {
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
    "leaderboard.update_score": {
        "description": "Update a team's score in the Redis Sorted Set leaderboard (automatically called when scoring)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                },
                "session_id": {
                    "type": "string",
                    "description": "Team's session identifier"
                },
                "team_name": {
                    "type": "string",
                    "description": "Team name (optional, will use session_id if not provided)"
                },
                "total_score": {
                    "type": "number",
                    "description": "Team's total score (0-100)",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": ["event_id", "session_id", "total_score"]
        }
    },
    "leaderboard.get_stats": {
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
    },
    "leaderboard.compare_teams": {
        "description": "Compare multiple teams side by side with their ranks and scores",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                },
                "session_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of session IDs to compare"
                }
            },
            "required": ["event_id", "session_ids"]
        }
    },
    "leaderboard.get_recent_changes": {
        "description": "Get recent ranking changes and movements (note: requires historical snapshots for full functionality)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                },
                "since_minutes": {
                    "type": "integer",
                    "description": "Get changes in the last N minutes",
                    "default": 5
                }
            },
            "required": ["event_id"]
        }
    },
    "leaderboard.get_category_leaders": {
        "description": "Get leaders for a specific scoring category (idea, technical, tools, presentation)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                },
                "category": {
                    "type": "string",
                    "enum": ["idea", "technical", "tools", "presentation"],
                    "description": "Scoring category to rank by"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of leaders to return",
                    "default": 10
                }
            },
            "required": ["event_id", "category"]
        }
    },
    "leaderboard.refresh": {
        "description": "Force refresh/recalculation of the leaderboard from Redis Sorted Sets",
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
    },
    "leaderboard.export": {
        "description": "Export leaderboard data in JSON or CSV format",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "csv"],
                    "description": "Export format",
                    "default": "json"
                }
            },
            "required": ["event_id"]
        }
    }
}


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
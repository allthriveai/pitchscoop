"""
Events MCP Tools - Event Management for CanaryQA

This module provides MCP (Model Context Protocol) tools for AI assistants
to manage events (hackathons, VC pitches, individual practice sessions).

Available tools:
- events.create_event: Create a new event (hackathon, vc_pitch, or practice)  
- events.list_events: Browse events with filtering
- events.get_event: Get event details and participant information
- events.join_event: Add participant/team to an event
- events.start_event: Begin an event (opens for recording)
- events.end_event: Conclude an event and generate results
- events.delete_event: Remove an event and all associated data

Event Types:
- hackathon: Team competition with judges and leaderboards
- vc_pitch: Pitching to investors with feedback
- individual_practice: Solo practice sessions
"""
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

from .events_mcp_handler import events_mcp_handler


# MCP Tool Registry for Events
EVENTS_MCP_TOOLS = {
    "events.create_event": {
        "name": "events.create_event",
        "description": """
        Create a new event for pitch recordings.
        
        Creates an event that can host multiple recording sessions. Events can be
        hackathons (team competitions), VC pitches (investor presentations), or 
        individual practice sessions. Each event type has different configurations
        and behaviors.
        
        Use this tool to set up a new competition, pitch day, or practice environment.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "enum": ["hackathon", "vc_pitch", "individual_practice"],
                    "description": "Type of event - determines features and behavior"
                },
                "event_name": {
                    "type": "string",
                    "description": "Display name for the event"
                },
                "description": {
                    "type": "string",
                    "description": "Event description and details"
                },
                "max_participants": {
                    "type": "integer",
                    "description": "Maximum number of teams/individuals (default: 50)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 1000
                },
                "duration_minutes": {
                    "type": "integer", 
                    "description": "Pitch duration limit in minutes (default: 5)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 60
                },
                "start_time": {
                    "type": "string",
                    "description": "Optional start time (ISO format). If not provided, event starts immediately"
                },
                "end_time": {
                    "type": "string", 
                    "description": "Optional end time (ISO format). If not provided, runs indefinitely"
                },
                "event_config": {
                    "type": "object",
                    "description": "Event-type specific configuration",
                    "properties": {
                        "judging_enabled": {"type": "boolean", "default": True},
                        "public_leaderboard": {"type": "boolean", "default": True}, 
                        "allow_multiple_attempts": {"type": "boolean", "default": False},
                        "scoring_criteria": {"type": "array", "items": {"type": "string"}},
                        "prize_info": {"type": "string"}
                    },
                    "required": []
                }
            },
            "required": ["event_type", "event_name", "description"]
        },
        "handler": "create_event"
    },

    "events.list_events": {
        "name": "events.list_events",
        "description": """
        List all events with optional filtering.
        
        Browse events by type, status, or date range. Useful for finding
        active competitions, upcoming pitch days, or practice sessions.
        
        Returns event summaries with participant counts and status information.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "enum": ["hackathon", "vc_pitch", "individual_practice"],
                    "description": "Filter by event type"
                },
                "status": {
                    "type": "string",
                    "enum": ["upcoming", "active", "completed", "cancelled"],
                    "description": "Filter by event status"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 20)",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": []
        },
        "handler": "list_events"
    },

    "events.get_event": {
        "name": "events.get_event",
        "description": """
        Get complete event details including participants and recordings.
        
        Retrieves full event information, participant list, recording sessions,
        and leaderboard data. Use this to get current status and results.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                }
            },
            "required": ["event_id"]
        },
        "handler": "get_event_details"
    },

    "events.join_event": {
        "name": "events.join_event",
        "description": """
        Add a participant or team to an event.
        
        Registers a team/individual for the event. For hackathons, can register
        entire teams. For VC pitches and practice, registers individuals.
        
        Returns participant information and event access details.
        """,
        "inputSchema": {
            "type": "object", 
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier to join"
                },
                "participant_name": {
                    "type": "string",
                    "description": "Team name (hackathons) or individual name"
                },
                "contact_info": {
                    "type": "object",
                    "description": "Contact information",
                    "properties": {
                        "email": {"type": "string"},
                        "organization": {"type": "string"}
                    },
                    "required": ["email"]
                },
                "team_members": {
                    "type": "array",
                    "description": "Team member names (for hackathons)",
                    "items": {"type": "string"}
                }
            },
            "required": ["event_id", "participant_name", "contact_info"]
        },
        "handler": "join_event"
    },

    "events.start_event": {
        "name": "events.start_event",
        "description": """
        Start an event and open it for recordings.
        
        Transitions event from 'upcoming' to 'active' status and enables
        pitch recordings. Participants can now start recording sessions.
        
        Use this when the competition/pitch day officially begins.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string", 
                    "description": "Event identifier to start"
                }
            },
            "required": ["event_id"]
        },
        "handler": "start_event"
    },

    "events.end_event": {
        "name": "events.end_event",
        "description": """
        End an event and finalize results.
        
        Stops accepting new recordings, finalizes scoring, and generates
        final leaderboards and results. Event status becomes 'completed'.
        
        Use this when the competition deadline is reached.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier to end"
                }
            },
            "required": ["event_id"]
        },
        "handler": "end_event"
    },

    "events.delete_event": {
        "name": "events.delete_event",
        "description": """
        Delete an event and all associated recordings.
        
        Permanently removes the event, all participant data, recording sessions,
        and audio files. This action cannot be undone.
        
        Use with caution - typically only for test events or cancelled competitions.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier to delete"
                },
                "confirm_deletion": {
                    "type": "boolean", 
                    "description": "Must be true to confirm permanent deletion"
                }
            },
            "required": ["event_id", "confirm_deletion"]
        },
        "handler": "delete_event"
    }
}


async def execute_events_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an Events MCP tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments as a dictionary
        
    Returns:
        Tool execution result
    """
    if tool_name not in EVENTS_MCP_TOOLS:
        return {
            "error": f"Unknown events tool: {tool_name}",
            "available_tools": list(EVENTS_MCP_TOOLS.keys())
        }
    
    tool_config = EVENTS_MCP_TOOLS[tool_name]
    handler_method_name = tool_config["handler"]
    
    try:
        # Get the handler method
        handler_method = getattr(events_mcp_handler, handler_method_name)
        
        # Execute the handler method
        result = await handler_method(**arguments)
        
        # Add tool execution metadata
        if isinstance(result, dict) and "error" not in result:
            result["_mcp_metadata"] = {
                "tool": tool_name,
                "executed_at": datetime.utcnow().isoformat(),
                "success": True
            }
        
        return result
        
    except TypeError as e:
        return {
            "error": f"Invalid arguments for {tool_name}: {str(e)}",
            "tool": tool_name,
            "expected_schema": tool_config["inputSchema"]
        }
    except Exception as e:
        return {
            "error": f"Events tool execution failed: {str(e)}",
            "tool": tool_name,
            "success": False
        }


def get_events_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get the schema definition for a specific events tool."""
    return EVENTS_MCP_TOOLS.get(tool_name)


def list_events_tools() -> List[str]:
    """Get list of all available events tool names."""
    return list(EVENTS_MCP_TOOLS.keys())


def get_events_tools_summary() -> Dict[str, Any]:
    """Get a summary of all available events tools with descriptions."""
    return {
        name: {
            "description": config["description"].strip(),
            "required_params": config["inputSchema"]["required"],
            "optional_params": [
                param for param in config["inputSchema"]["properties"].keys()
                if param not in config["inputSchema"]["required"]
            ]
        }
        for name, config in EVENTS_MCP_TOOLS.items()
    }


# Example usage
async def example_event_workflow():
    """Example workflow for creating and managing events."""
    print("=== Example Event Management Workflow ===\n")
    
    # 1. Create a hackathon event
    print("1. Creating hackathon event...")
    create_result = await execute_events_mcp_tool("events.create_event", {
        "event_type": "hackathon",
        "event_name": "AI Innovation Hackathon 2024",
        "description": "48-hour AI/ML hackathon with $50K in prizes",
        "max_participants": 100,
        "duration_minutes": 5,
        "event_config": {
            "judging_enabled": True,
            "public_leaderboard": True,
            "scoring_criteria": ["Innovation", "Technical Excellence", "Market Potential"]
        }
    })
    print(f"Create result: {create_result}\n")
    
    if "error" in create_result:
        return
    
    event_id = create_result["event_id"]
    
    # 2. Add participants
    print("2. Adding team to event...")
    join_result = await execute_events_mcp_tool("events.join_event", {
        "event_id": event_id,
        "participant_name": "Team Innovators",
        "contact_info": {"email": "team@innovators.com", "organization": "Stanford CS"},
        "team_members": ["Alice Chen", "Bob Smith", "Carol Zhang"]
    })
    print(f"Join result: {join_result}\n")
    
    # 3. Start the event
    print("3. Starting the event...")
    start_result = await execute_events_mcp_tool("events.start_event", {
        "event_id": event_id
    })
    print(f"Start result: {start_result}\n")
    
    # 4. Get event details
    print("4. Getting event details...")
    details_result = await execute_events_mcp_tool("events.get_event", {
        "event_id": event_id
    })
    print(f"Event details: {details_result}\n")
    
    print("=== Event Workflow Complete ===")


if __name__ == "__main__":
    import asyncio
    
    print("Events MCP Tools Summary")
    print("=" * 50)
    
    summary = get_events_tools_summary()
    for tool_name, info in summary.items():
        print(f"\n{tool_name}:")
        print(f"  Description: {info['description'][:80]}...")
        print(f"  Required: {info['required_params']}")
        print(f"  Optional: {info['optional_params'][:3]}...")  # Show first 3
    
    print(f"\nTotal events tools available: {len(EVENTS_MCP_TOOLS)}")
    
    # Run example workflow
    print("\n" + "=" * 50)
    asyncio.run(example_event_workflow())
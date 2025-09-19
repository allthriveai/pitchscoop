"""
MCP Tools for Gladia STT - Pitch Recording and Playback

This module defines the MCP (Model Context Protocol) tools that AI assistants
can use to manage pitch recording sessions with Gladia STT integration.

Available tools:
- pitches.start_recording: Initialize a new pitch recording session
- pitches.stop_recording: Finalize recording and store audio/transcript
- pitches.get_session: Retrieve session details and current status
- pitches.get_playback_url: Generate fresh audio playback URLs
- pitches.list_sessions: Browse all recordings with filtering
- pitches.delete_session: Remove session and audio files

Integration: Uses MinIO for audio storage and Redis for session caching.
"""
from typing import Any, Dict, Optional, List

from .gladia_mcp_handler import gladia_mcp_handler


# MCP Tool Registry - Maps tool names to handler methods
MCP_TOOLS = {
    "pitches.start_recording": {
        "name": "pitches.start_recording",
        "description": """
        Start a new pitch recording session with Gladia STT integration.
        
        Creates a session ID associated with an event, initializes Gladia WebSocket 
        connection, and prepares Redis caching for transcript segments. Returns 
        WebSocket URL and session details for the recording client.
        
        Use this tool to begin recording a pitch for a specific event (hackathon,
        VC pitch, or practice session). The recording will be scoped to the event.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Optional event identifier - recording will be associated with this event (defaults to 'default' if not provided)"
                },
                "team_name": {
                    "type": "string",
                    "description": "Name of the team or participant recording the pitch"
                },
                "pitch_title": {
                    "type": "string", 
                    "description": "Title or topic of the pitch presentation"
                },
                "audio_config": {
                    "type": "object",
                    "description": "Optional audio configuration override",
                    "properties": {
                        "sample_rate": {"type": "integer", "default": 16000},
                        "language": {"type": "string", "default": "en"},
                        "encoding": {"type": "string", "default": "linear16"}
                    },
                    "required": []
                }
            },
            "required": ["team_name", "pitch_title"]
        },
        "handler": "start_pitch_recording"
    },
    
    "pitches.stop_recording": {
        "name": "pitches.stop_recording",
        "description": """
        Stop pitch recording and finalize the session.
        
        Stops the Gladia STT session, uploads audio file to MinIO storage,
        finalizes transcript caching in Redis, and generates initial playback URLs.
        
        Use this when the pitch demo is complete and you want to save the
        recording for playback and analysis.
        """,
        "inputSchema": {
            "type": "object", 
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier returned from start_recording"
                },
                "audio_data_base64": {
                    "type": "string",
                    "description": "Optional base64-encoded complete audio file to store in MinIO"
                }
            },
            "required": ["session_id"]
        },
        "handler": "stop_pitch_recording"
    },
    
    "pitches.get_session": {
        "name": "pitches.get_session",
        "description": """
        Get complete session details including transcript and audio info.
        
        Retrieves session data from Redis cache, including current status,
        transcript segments, team information, and audio file details.
        Generates fresh playback URLs if audio is available.
        
        Use this to check session status or get details for display.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier to retrieve"
                }
            },
            "required": ["session_id"]
        },
        "handler": "get_session_details"
    },
    
    "pitches.get_playback_url": {
        "name": "pitches.get_playback_url", 
        "description": """
        Generate a fresh playback URL for session audio.
        
        Creates a new presigned URL from MinIO storage that can be used
        to stream or download the audio file. URLs have configurable expiry.
        
        Use this to get URLs for audio playback on the website or for
        sharing recorded pitches.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier"
                },
                "expires_hours": {
                    "type": "integer",
                    "description": "URL expiry time in hours (default: 1)",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 168  # 1 week max
                }
            },
            "required": ["session_id"]
        },
        "handler": "get_playback_url"
    },
    
    "pitches.list_sessions": {
        "name": "pitches.list_sessions",
        "description": """
        List all pitch recording sessions with optional filtering.
        
        Retrieves session summaries from Redis cache, optionally filtered
        by team name or session status. Results are sorted by creation time
        (newest first).
        
        Use this to browse recordings, create leaderboards, or find
        sessions for a specific team.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Optional filter by event ID - show only sessions for this event"
                },
                "team_name": {
                    "type": "string",
                    "description": "Optional filter by team name"
                },
                "status": {
                    "type": "string", 
                    "description": "Optional filter by status (initializing, ready_to_record, recording, processing, completed, error)",
                    "enum": ["initializing", "ready_to_record", "recording", "processing", "completed", "error"]
                }
            },
            "required": []
        },
        "handler": "list_sessions"
    },
    
    "pitches.delete_session": {
        "name": "pitches.delete_session",
        "description": """
        Delete a pitch recording session and its audio file.
        
        Removes session data from Redis cache and deletes the associated
        audio file from MinIO storage. This action cannot be undone.
        
        Use this to clean up test recordings or remove unwanted sessions.
        Be careful - this permanently deletes the audio file.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier to delete"
                }
            },
            "required": ["session_id"]
        },
        "handler": "delete_session"
    }
}


async def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an MCP tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments as a dictionary
        
    Returns:
        Tool execution result
    """
    if tool_name not in MCP_TOOLS:
        return {
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(MCP_TOOLS.keys())
        }
    
    tool_config = MCP_TOOLS[tool_name]
    handler_method_name = tool_config["handler"]
    
    try:
        # Get the handler method
        handler_method = getattr(gladia_mcp_handler, handler_method_name)
        
        # Handle special case for audio data decoding
        if tool_name == "pitches.stop_recording" and "audio_data_base64" in arguments:
            import base64
            audio_data_b64 = arguments.pop("audio_data_base64")
            if audio_data_b64:
                try:
                    audio_data = base64.b64decode(audio_data_b64)
                    arguments["audio_data"] = audio_data
                except Exception as e:
                    return {
                        "error": f"Invalid base64 audio data: {str(e)}",
                        "tool": tool_name
                    }
        
        # Execute the handler method
        result = await handler_method(**arguments)
        
        # Add tool execution metadata
        if isinstance(result, dict) and "error" not in result:
            result["_mcp_metadata"] = {
                "tool": tool_name,
                "executed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
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
            "error": f"Tool execution failed: {str(e)}",
            "tool": tool_name,
            "success": False
        }


def get_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    Get the schema definition for a specific tool.
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Tool schema or None if not found
    """
    return MCP_TOOLS.get(tool_name)


def list_available_tools() -> List[str]:
    """
    Get list of all available tool names.
    
    Returns:
        List of tool names
    """
    return list(MCP_TOOLS.keys())


def get_tools_summary() -> Dict[str, Any]:
    """
    Get a summary of all available tools with descriptions.
    
    Returns:
        Dictionary mapping tool names to descriptions
    """
    return {
        name: {
            "description": config["description"].strip(),
            "required_params": config["inputSchema"]["required"],
            "optional_params": [
                param for param in config["inputSchema"]["properties"].keys()
                if param not in config["inputSchema"]["required"]
            ]
        }
        for name, config in MCP_TOOLS.items()
    }


# Example usage and testing functions
async def example_pitch_workflow():
    """
    Example workflow showing how to use the MCP tools for a complete
    pitch recording session.
    """
    print("=== Example Pitch Recording Workflow ===\n")
    
    # 1. Start recording session
    print("1. Starting recording session...")
    start_result = await execute_mcp_tool("pitches.start_recording", {
        "team_name": "AI Innovators",
        "pitch_title": "Revolutionary ML Platform Demo"
    })
    print(f"Start result: {start_result}\n")
    
    if "error" in start_result:
        print("Failed to start session")
        return
    
    session_id = start_result["session_id"]
    
    # 2. Simulate recording (in real use, audio would be sent via WebSocket)
    print("2. Simulating recording...")
    print("   [In real use: Send audio chunks to WebSocket URL]")
    print("   [In real use: Transcript segments received in real-time]\n")
    
    # 3. Stop recording
    print("3. Stopping recording session...")
    stop_result = await execute_mcp_tool("pitches.stop_recording", {
        "session_id": session_id
    })
    print(f"Stop result: {stop_result}\n")
    
    # 4. Get session details
    print("4. Getting session details...")
    details_result = await execute_mcp_tool("pitches.get_session", {
        "session_id": session_id
    })
    print(f"Session details: {details_result}\n")
    
    # 5. List all sessions
    print("5. Listing all sessions...")
    list_result = await execute_mcp_tool("pitches.list_sessions", {})
    print(f"All sessions: {list_result}\n")
    
    # 6. Get playback URL (if audio was stored)
    if details_result.get("has_audio", False):
        print("6. Getting playback URL...")
        url_result = await execute_mcp_tool("pitches.get_playback_url", {
            "session_id": session_id,
            "expires_hours": 2
        })
        print(f"Playback URL: {url_result}\n")
    
    print("=== Workflow Complete ===")


if __name__ == "__main__":
    # Print tools summary when run directly
    import asyncio
    import json
    
    print("Gladia MCP Tools Summary")
    print("=" * 50)
    
    summary = get_tools_summary()
    for tool_name, info in summary.items():
        print(f"\n{tool_name}:")
        print(f"  Description: {info['description'][:100]}...")
        print(f"  Required: {info['required_params']}")
        print(f"  Optional: {info['optional_params']}")
    
    print(f"\nTotal tools available: {len(MCP_TOOLS)}")
    
    # Run example workflow
    print("\n" + "=" * 50)
    asyncio.run(example_pitch_workflow())
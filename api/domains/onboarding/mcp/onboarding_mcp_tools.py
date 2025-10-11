"""
Onboarding MCP Tools

Exposes onboarding functionality to Claude Desktop via MCP.
These tools wrap the OnboardingService for conversational onboarding.
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from domains.shared.infrastructure.database import AsyncSessionLocal
from ..services.onboarding_service import OnboardingService


# MCP Tool Definitions
ONBOARDING_MCP_TOOLS = {
    "onboarding.start": {
        "description": "Start onboarding flow. User chooses to be an event organizer or participant.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier (required)"
                },
                "role": {
                    "type": "string",
                    "enum": ["organizer", "participant"],
                    "description": "User role: 'organizer' to create events, 'participant' to join events"
                },
                "event_id": {
                    "type": "string",
                    "description": "Optional: Event ID if participant is joining specific event"
                }
            },
            "required": ["user_id", "role"]
        }
    },
    
    "onboarding.submit_step": {
        "description": "Submit data for current onboarding step and move to next step",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Onboarding session ID from onboarding.start"
                },
                "step_data": {
                    "type": "object",
                    "description": "Field values for current step (e.g., event_name, event_date, user_name, etc.)"
                }
            },
            "required": ["session_id", "step_data"]
        }
    },
    
    "onboarding.get_current_step": {
        "description": "Get details about the current onboarding step",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Onboarding session ID"
                }
            },
            "required": ["session_id"]
        }
    },
    
    "onboarding.get_help": {
        "description": "Get help text for onboarding topics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": ["event_types", "judging_weights", "custom_categories", "project_description"],
                    "description": "Help topic to get information about"
                }
            },
            "required": ["topic"]
        }
    }
}


async def execute_onboarding_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an onboarding MCP tool.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        
    Returns:
        Tool execution result
    """
    try:
        if tool_name == "onboarding.start":
            return await _start_onboarding(arguments)
        
        elif tool_name == "onboarding.submit_step":
            return await _submit_step(arguments)
        
        elif tool_name == "onboarding.get_current_step":
            return await _get_current_step(arguments)
        
        elif tool_name == "onboarding.get_help":
            return await _get_help(arguments)
        
        else:
            return {
                "success": False,
                "error": f"Unknown onboarding tool: {tool_name}",
                "available_tools": list(ONBOARDING_MCP_TOOLS.keys())
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}",
            "tool": tool_name
        }


async def _start_onboarding(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Start onboarding flow"""
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        result = await service.start_onboarding(
            user_id=arguments["user_id"],
            role=arguments["role"],
            event_id=arguments.get("event_id")
        )
        
        # Format for conversational response
        return {
            "success": True,
            "session_id": result["session_id"],
            "resuming": result.get("resuming", False),
            "role": result.get("role"),
            "message": result.get("welcome_message") or result.get("message"),
            "help_text": result.get("help_text"),
            "current_step": {
                "title": result["current_step"]["title"],
                "description": result["current_step"]["description"],
                "fields": result["current_step"].get("fields", []),
                "options": result["current_step"].get("options", [])
            },
            "conversation_guidance": _format_step_guidance(result["current_step"])
        }


async def _submit_step(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Submit data for current step"""
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        result = await service.process_step(
            session_id=arguments["session_id"],
            step_data=arguments["step_data"]
        )
        
        if not result["success"]:
            # Validation errors
            return {
                "success": False,
                "errors": result["errors"],
                "message": "Some fields need correction: " + ", ".join(result["errors"]),
                "current_step": result.get("current_step")
            }
        
        if result["completed"]:
            # Onboarding finished!
            return {
                "success": True,
                "completed": True,
                "message": result["message"],
                "summary": result["summary"],
                "next_actions": result["next_actions"],
                "event_id": result.get("event_id")
            }
        
        # Move to next step
        return {
            "success": True,
            "completed": False,
            "message": result["message"],
            "progress": result.get("progress"),
            "next_step": {
                "title": result["next_step"]["title"],
                "description": result["next_step"]["description"],
                "fields": result["next_step"].get("fields", []),
                "options": result["next_step"].get("options", [])
            },
            "conversation_guidance": _format_step_guidance(result["next_step"])
        }


async def _get_current_step(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get current step details"""
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        repo = service.repo
        
        session = await repo.get_session(arguments["session_id"])
        if not session:
            return {"success": False, "error": "Session not found"}
        
        step_details = await service._get_step_details(session)
        
        return {
            "success": True,
            "session_id": session.id,
            "current_step": step_details,
            "progress": {
                "completed": len(session.completed_steps),
                "total": session.total_steps,
                "percentage": int((len(session.completed_steps) / session.total_steps) * 100) if session.total_steps else 0
            }
        }


async def _get_help(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Get help text"""
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        result = await service.get_help(arguments["topic"])
        
        return {
            "success": True,
            "topic": result["topic"],
            "help_text": result["help_text"]
        }


def _format_step_guidance(step_details: Dict[str, Any]) -> str:
    """
    Format step details into conversational guidance for Claude.
    Helps Claude understand what to ask the user.
    """
    title = step_details.get("title", "")
    description = step_details.get("description", "")
    
    fields = step_details.get("fields", [])
    options = step_details.get("options", [])
    
    if fields:
        # Form fields - guide Claude to ask for each field
        required_fields = [f for f in fields if f.get("required")]
        optional_fields = [f for f in fields if not f.get("required")]
        
        guidance = f"{description}\n\nRequired fields:\n"
        for field in required_fields:
            guidance += f"- {field['label']}"
            if field.get("help_text"):
                guidance += f" ({field['help_text']})"
            guidance += "\n"
        
        if optional_fields:
            guidance += "\nOptional fields:\n"
            for field in optional_fields:
                guidance += f"- {field['label']}\n"
        
        return guidance
    
    elif options:
        # Multiple choice - guide Claude to present options
        guidance = f"{description}\n\nAvailable options:\n"
        for option in options:
            guidance += f"- {option['label']}\n"
        return guidance
    
    return description

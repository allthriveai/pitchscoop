"""
Users MCP Tools - API endpoint definitions for user management

Defines the MCP tools/endpoints for user operations including:
- Create, read, update, delete users
- User authentication and profile management  
- User-event and user-recording relationship management
"""

from .users_mcp_handler import UsersMCPHandler

# Initialize handler
users_handler = UsersMCPHandler()


USERS_TOOLS = [
    {
        "name": "users.create_user",
        "description": "Create a new user account",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "User's full name"
                },
                "email": {
                    "type": "string",
                    "description": "User's email address (must be unique)"
                },
                "role": {
                    "type": "string", 
                    "enum": ["participant", "organizer", "judge", "mentor", "spectator", "admin"],
                    "description": "User role in the system",
                    "default": "participant"
                },
                "profile": {
                    "type": "object",
                    "description": "Optional profile information",
                    "properties": {
                        "bio": {"type": "string"},
                        "company": {"type": "string"},
                        "position": {"type": "string"},
                        "website": {"type": "string"},
                        "linkedin": {"type": "string"},
                        "twitter": {"type": "string"},
                        "github": {"type": "string"},
                        "location": {"type": "string"},
                        "skills": {"type": "array", "items": {"type": "string"}},
                        "interests": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "org_id": {
                    "type": "string",
                    "description": "Organization ID for multi-tenant isolation"
                }
            },
            "required": ["name", "email"]
        }
    },
    {
        "name": "users.get_user",
        "description": "Get user information by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                },
                "org_id": {
                    "type": "string", 
                    "description": "Organization ID for multi-tenant isolation"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "users.get_user_by_email",
        "description": "Get user information by email address",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "User's email address"
                },
                "org_id": {
                    "type": "string",
                    "description": "Organization ID for multi-tenant isolation"
                }
            },
            "required": ["email"]
        }
    },
    {
        "name": "users.update_user",
        "description": "Update user information",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                },
                "updates": {
                    "type": "object",
                    "description": "Fields to update",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "role": {
                            "type": "string",
                            "enum": ["participant", "organizer", "judge", "mentor", "spectator", "admin"]
                        },
                        "status": {
                            "type": "string",
                            "enum": ["active", "inactive", "pending", "suspended", "deleted"]
                        },
                        "profile": {
                            "type": "object",
                            "properties": {
                                "bio": {"type": "string"},
                                "company": {"type": "string"},
                                "position": {"type": "string"},
                                "website": {"type": "string"},
                                "linkedin": {"type": "string"},
                                "twitter": {"type": "string"},
                                "github": {"type": "string"},
                                "location": {"type": "string"},
                                "skills": {"type": "array", "items": {"type": "string"}},
                                "interests": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    }
                },
                "org_id": {
                    "type": "string",
                    "description": "Organization ID for multi-tenant isolation"
                }
            },
            "required": ["user_id", "updates"]
        }
    },
    {
        "name": "users.list_users",
        "description": "List users with optional filtering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "enum": ["participant", "organizer", "judge", "mentor", "spectator", "admin"],
                    "description": "Filter by user role"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "inactive", "pending", "suspended", "deleted"],
                    "description": "Filter by user status"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                },
                "org_id": {
                    "type": "string",
                    "description": "Organization ID for multi-tenant isolation"
                }
            }
        }
    },
    {
        "name": "users.delete_user",
        "description": "Delete or deactivate a user",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                },
                "hard_delete": {
                    "type": "boolean",
                    "description": "If true, permanently delete; if false, just deactivate",
                    "default": False
                },
                "org_id": {
                    "type": "string",
                    "description": "Organization ID for multi-tenant isolation"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "users.add_user_recording",
        "description": "Add a recording to user's collection (used internally by recording system)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                },
                "recording_id": {
                    "type": "string", 
                    "description": "Recording identifier"
                },
                "org_id": {
                    "type": "string",
                    "description": "Organization ID for multi-tenant isolation"
                }
            },
            "required": ["user_id", "recording_id"]
        }
    },
    {
        "name": "users.add_user_event",
        "description": "Add an event to user's collection (used internally by event system)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"  
                },
                "org_id": {
                    "type": "string",
                    "description": "Organization ID for multi-tenant isolation"
                }
            },
            "required": ["user_id", "event_id"]
        }
    }
]


async def handle_users_tool_call(tool_name: str, arguments: dict):
    """Handle users tool calls."""
    
    if tool_name == "users.create_user":
        return await users_handler.create_user(
            name=arguments["name"],
            email=arguments["email"],
            role=arguments.get("role", "participant"),
            profile_data=arguments.get("profile"),
            org_id=arguments.get("org_id")
        )
    
    elif tool_name == "users.get_user":
        return await users_handler.get_user_by_id(
            user_id=arguments["user_id"],
            org_id=arguments.get("org_id")
        )
    
    elif tool_name == "users.get_user_by_email":
        return await users_handler.get_user_by_email(
            email=arguments["email"],
            org_id=arguments.get("org_id")
        )
    
    elif tool_name == "users.update_user":
        return await users_handler.update_user(
            user_id=arguments["user_id"],
            updates=arguments["updates"],
            org_id=arguments.get("org_id")
        )
    
    elif tool_name == "users.list_users":
        return await users_handler.list_users(
            role=arguments.get("role"),
            status=arguments.get("status"),
            limit=arguments.get("limit", 20),
            org_id=arguments.get("org_id")
        )
    
    elif tool_name == "users.delete_user":
        return await users_handler.delete_user(
            user_id=arguments["user_id"],
            org_id=arguments.get("org_id"),
            hard_delete=arguments.get("hard_delete", False)
        )
    
    elif tool_name == "users.add_user_recording":
        return await users_handler.add_user_recording(
            user_id=arguments["user_id"],
            recording_id=arguments["recording_id"],
            org_id=arguments.get("org_id")
        )
    
    elif tool_name == "users.add_user_event":
        return await users_handler.add_user_event(
            user_id=arguments["user_id"],
            event_id=arguments["event_id"],
            org_id=arguments.get("org_id")
        )
    
    else:
        return {"error": f"Unknown tool: {tool_name}"}
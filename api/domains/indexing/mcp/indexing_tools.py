"""
MCP Tools for Indexing - Redis Vector Integration

Provides MCP tools for indexing various document types into the RAG system
for context-aware scoring and search functionality using Redis Vector Search.
"""
from typing import Dict, Any, List
from ..services.redis_vector_service import redis_vector_service
from ..services.document_processor import document_processor


# MCP Tool Registry for Indexing
INDEXING_MCP_TOOLS = {
    "index.add_rubric": {
        "name": "index.add_rubric",
        "description": """
        Index an event rubric for context-aware scoring.
        
        Converts rubric data into searchable documents that can be used
        by the scoring engine to provide context-aware evaluation of pitches.
        
        Use this when setting up an event to ensure scoring is based on
        the specific rubric criteria and examples for that event.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                },
                "rubric_data": {
                    "type": "object",
                    "description": "Complete rubric data including criteria, weights, examples",
                    "properties": {
                        "event_name": {"type": "string"},
                        "criteria": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "weights": {
                            "type": "object",
                            "description": "Weight for each criterion"
                        },
                        "guidelines": {"type": "string"},
                        "examples": {"type": "object"},
                        "scale": {
                            "type": "object",
                            "properties": {
                                "min": {"type": "number"},
                                "max": {"type": "number"}
                            }
                        }
                    },
                    "required": ["criteria"]
                }
            },
            "required": ["event_id", "rubric_data"]
        },
        "handler": "add_rubric"
    },
    
    "index.add_transcript": {
        "name": "index.add_transcript",
        "description": """
        Index a pitch transcript for search and context-aware analysis.
        
        Processes and indexes the complete transcript with metadata
        for semantic search and contextual scoring analysis.
        
        This is typically called automatically after a recording session
        is completed and transcription is available.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                },
                "session_id": {
                    "type": "string", 
                    "description": "Recording session identifier"
                },
                "transcript_data": {
                    "type": "object",
                    "description": "Complete transcript data with metadata",
                    "properties": {
                        "team_name": {"type": "string"},
                        "pitch_title": {"type": "string"},
                        "transcript_text": {"type": "string"},
                        "duration_seconds": {"type": "number"},
                        "word_count": {"type": "integer"},
                        "words_per_minute": {"type": "number"},
                        "segments": {"type": "array"}
                    },
                    "required": ["team_name", "pitch_title", "transcript_text"]
                }
            },
            "required": ["event_id", "session_id", "transcript_data"]
        },
        "handler": "add_transcript"
    },
    
    "index.add_team_profile": {
        "name": "index.add_team_profile",
        "description": """
        Index team profile information for personalized feedback.
        
        Processes team bios, skills, and experience to provide context
        for more personalized and relevant feedback generation.
        
        Use this when teams register or update their profiles to ensure
        feedback takes their background and experience into account.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier"
                },
                "team_data": {
                    "type": "object",
                    "description": "Complete team profile data",
                    "properties": {
                        "team_name": {"type": "string"},
                        "members": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "bio": {"type": "string"},
                        "focus_areas": {
                            "type": "array", 
                            "items": {"type": "string"}
                        },
                        "experience": {"type": "string"},
                        "skills": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["team_name"]
                }
            },
            "required": ["event_id", "team_data"]
        },
        "handler": "add_team_profile"
    },
    
    "index.health_check": {
        "name": "index.health_check",
        "description": """
        Check the health status of the indexing system.
        
        Verifies that LlamaIndex, Redis Vector Search, and Azure OpenAI connections
        are working properly for indexing and search operations.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "handler": "health_check"
    },
    
    "index.list_collections": {
        "name": "index.list_collections", 
        "description": """
        List all available Redis vector indices for an event.
        
        Shows which document types have been indexed for the event
        and basic statistics about each index.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event identifier to list collections for"
                }
            },
            "required": ["event_id"]
        },
        "handler": "list_collections"
    }
}


# MCP Tool Handler Functions
async def add_rubric(event_id: str, rubric_data: Dict[str, Any]) -> Dict[str, Any]:
    """Index event rubric for context-aware scoring."""
    try:
        # Create rubric document
        doc = document_processor.create_rubric_document(event_id, rubric_data)
        
        # Index the document
        result = await redis_vector_service.index_documents(
            event_id=event_id,
            document_type="rubrics",
            documents=[doc]
        )
        
        if result["success"]:
            return {
                "success": True,
                "event_id": event_id,
                "indexed_documents": result["indexed_count"],
                "message": "Rubric indexed successfully for context-aware scoring",
                "criteria_count": len(rubric_data.get('criteria', [])),
                "document_metadata": doc.metadata
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown indexing error"),
                "event_id": event_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to index rubric: {str(e)}",
            "event_id": event_id
        }


async def add_transcript(event_id: str, session_id: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
    """Index pitch transcript for search and analysis."""
    try:
        # Create transcript document
        doc = document_processor.create_transcript_document(event_id, session_id, transcript_data)
        
        # Index the document
        result = await redis_vector_service.index_documents(
            event_id=event_id,
            document_type="transcripts", 
            documents=[doc]
        )
        
        if result["success"]:
            return {
                "success": True,
                "event_id": event_id,
                "session_id": session_id,
                "indexed_documents": result["indexed_count"],
                "message": "Transcript indexed successfully for search and analysis",
                "word_count": transcript_data.get('word_count', 0),
                "team_name": transcript_data.get('team_name'),
                "document_metadata": doc.metadata
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown indexing error"),
                "event_id": event_id,
                "session_id": session_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to index transcript: {str(e)}",
            "event_id": event_id,
            "session_id": session_id
        }


async def add_team_profile(event_id: str, team_data: Dict[str, Any]) -> Dict[str, Any]:
    """Index team profile for personalized feedback."""
    try:
        # Create team document
        doc = document_processor.create_team_document(event_id, team_data)
        
        # Index the document
        result = await redis_vector_service.index_documents(
            event_id=event_id,
            document_type="teams",
            documents=[doc]
        )
        
        if result["success"]:
            return {
                "success": True,
                "event_id": event_id,
                "team_name": team_data.get('team_name'),
                "indexed_documents": result["indexed_count"],
                "message": "Team profile indexed successfully for personalized feedback",
                "member_count": len(team_data.get('members', [])),
                "document_metadata": doc.metadata
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown indexing error"),
                "event_id": event_id,
                "team_name": team_data.get('team_name')
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to index team profile: {str(e)}",
            "event_id": event_id,
            "team_name": team_data.get('team_name')
        }


async def health_check() -> Dict[str, Any]:
    """Check health of indexing system."""
    try:
        health_status = await redis_vector_service.health_check()
        
        return {
            "service": "indexing",
            "healthy": health_status["healthy"],
            "components": {
                "llamaindex": True,
                "redis_vector": health_status["redis_connected"],
                "vector_search": health_status["vector_search_available"],
                "azure_openai": health_status.get("llm_model") != "unknown"
            },
            "details": health_status,
            "message": "Indexing system operational" if health_status["healthy"] else "Indexing system has issues"
        }
        
    except Exception as e:
        return {
            "service": "indexing",
            "healthy": False,
            "error": str(e),
            "message": "Indexing system health check failed"
        }


async def list_collections(event_id: str) -> Dict[str, Any]:
    """List all Redis vector indices for an event."""
    try:
        # Use the Redis Vector service to list indices
        result = await redis_vector_service.list_event_indices(event_id)
        
        if result["success"]:
            return {
                "success": True,
                "event_id": event_id,
                "collections": result["indices"],
                "total_collections": len(result["indices"]),
                "message": f"Found {len(result['indices'])} indexed document types for event"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Failed to list indices"),
                "event_id": event_id,
                "collections": []
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "event_id": event_id,
            "collections": []
        }


# Tool execution dispatcher
async def execute_indexing_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute an indexing MCP tool."""
    if tool_name not in INDEXING_MCP_TOOLS:
        return {
            "error": f"Unknown indexing tool: {tool_name}",
            "available_tools": list(INDEXING_MCP_TOOLS.keys())
        }
    
    handler_name = INDEXING_MCP_TOOLS[tool_name]["handler"]
    
    try:
        if handler_name == "add_rubric":
            return await add_rubric(**arguments)
        elif handler_name == "add_transcript":
            return await add_transcript(**arguments) 
        elif handler_name == "add_team_profile":
            return await add_team_profile(**arguments)
        elif handler_name == "health_check":
            return await health_check(**arguments)
        elif handler_name == "list_collections":
            return await list_collections(**arguments)
        else:
            return {"error": f"Handler not implemented: {handler_name}"}
            
    except TypeError as e:
        return {
            "error": f"Invalid arguments for {tool_name}: {str(e)}",
            "expected_schema": INDEXING_MCP_TOOLS[tool_name]["inputSchema"]
        }
    except Exception as e:
        return {
            "error": f"Tool execution failed: {str(e)}",
            "tool": tool_name
        }
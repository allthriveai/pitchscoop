"""
Chat MCP Tools Registry - RAG-Powered Conversational AI

This module defines MCP tools for RAG-powered chat functionality in PitchScoop.
Uses LlamaIndex to provide context-aware conversations about pitches, rubrics,
and scoring with proper source attribution.

Available tools:
- chat.start_conversation: Initialize a new conversation with context
- chat.send_message: Send message and get AI response with RAG context
- chat.search_documents: Search indexed documents for specific information
- chat.ask_about_pitch: Ask specific questions about a pitch session
- chat.compare_sessions: Have conversational comparison of multiple sessions
- chat.get_conversation_history: Retrieve conversation messages
- chat.health_check: Check RAG chat system health
"""
from typing import Any, Dict, Optional, List

from .chat_mcp_handler import chat_mcp_handler


# MCP Tool Registry for Chat Domain
CHAT_MCP_TOOLS = {
    "chat.start_conversation": {
        "name": "chat.start_conversation",
        "description": """
        Start a new RAG-powered conversation with contextual awareness.
        
        Creates a new conversation that can reference pitch transcripts, rubrics,
        scoring data, and other indexed documents. The conversation maintains
        context across multiple exchanges and provides source attribution.
        
        Conversation types:
        - general_chat: Open-ended conversation about the event
        - pitch_analysis: Focused analysis of specific pitch sessions
        - scoring_review: Discussion about scoring and evaluation
        - rubric_discussion: Conversation about evaluation criteria
        - comparative_analysis: Comparison between multiple pitches
        
        Supports multi-tenant isolation using event_id for secure access.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "conversation_type": {
                    "type": "string",
                    "enum": ["general_chat", "pitch_analysis", "scoring_review", "rubric_discussion", "comparative_analysis"],
                    "default": "general_chat",
                    "description": "Type of conversation to create"
                },
                "title": {
                    "type": "string",
                    "description": "Optional title for the conversation"
                },
                "session_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional pitch session IDs to include in context"
                },
                "rubric_ids": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "Optional rubric IDs to include in context"
                },
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["idea", "technical", "tools", "presentation", "overall"]},
                    "description": "Optional focus areas for the conversation"
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional user ID for conversation attribution"
                }
            },
            "required": ["event_id"]
        },
        "handler": "start_conversation"
    },
    
    "chat.send_message": {
        "name": "chat.send_message",
        "description": """
        Send a message and get an AI-powered response with RAG context.
        
        Processes user messages using LlamaIndex to provide contextually aware
        responses based on indexed documents including:
        - Pitch transcripts and session data
        - Scoring rubrics and evaluation criteria  
        - Previous scoring results and analysis
        - Comparative data across sessions
        
        The AI response includes proper source attribution showing which
        documents were referenced to generate the answer. Maintains
        conversation context for follow-up questions.
        
        Supports natural language queries about scoring, analysis, and
        pitch evaluation with multi-tenant security.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation ID to send message to"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "message": {
                    "type": "string",
                    "description": "User message to process"
                },
                "include_sources": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include source attribution in response"
                },
                "max_sources": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum number of source references to include"
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional user ID for message attribution"
                }
            },
            "required": ["conversation_id", "event_id", "message"]
        },
        "handler": "send_message"
    },
    
    "chat.search_documents": {
        "name": "chat.search_documents",
        "description": """
        Search indexed documents for specific information using RAG.
        
        Performs semantic search across all indexed documents for an event:
        - Pitch transcripts and recordings metadata
        - Scoring rubrics and evaluation guidelines
        - Previous analysis results and scoring data
        - Judge feedback and comparative evaluations
        
        Returns ranked results with relevance scores and content snippets.
        Useful for finding specific information without starting a full
        conversation. Supports filtering by document type and session.
        
        Results can be used to inform scoring decisions, answer specific
        questions, or provide context for conversations.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "query": {
                    "type": "string",
                    "description": "Search query or question"
                },
                "document_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional filter by document types (e.g., 'transcript', 'rubric', 'scoring')"
                },
                "session_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional filter by specific session IDs"
                },
                "max_results": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of results to return"
                },
                "min_relevance_score": {
                    "type": "number",
                    "default": 0.1,
                    "description": "Minimum relevance score for results (0.0-1.0)"
                }
            },
            "required": ["event_id", "query"]
        },
        "handler": "search_documents"
    },
    
    "chat.ask_about_pitch": {
        "name": "chat.ask_about_pitch",
        "description": """
        Ask specific questions about a pitch session with RAG context.
        
        Provides focused Q&A about specific pitch sessions using all available
        context including:
        - Complete transcript analysis
        - Technical implementation details mentioned
        - Sponsor tool usage and integration
        - Presentation flow and structure
        - Comparative context with other pitches
        
        Automatically includes relevant rubric criteria and scoring guidelines
        to provide comprehensive answers. Ideal for quick specific inquiries
        about individual pitches during evaluation.
        
        Can answer questions about scoring rationale, technical details,
        presentation quality, and competitive positioning.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Pitch session ID to ask about"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "question": {
                    "type": "string",
                    "description": "Specific question about the pitch"
                },
                "include_comparative_context": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to include context from other pitches for comparison"
                },
                "focus_criteria": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["idea", "technical", "tools", "presentation", "overall"]},
                    "description": "Optional focus on specific scoring criteria"
                },
                "user_id": {
                    "type": "string",
                    "description": "Optional user ID for query attribution"
                }
            },
            "required": ["session_id", "event_id", "question"]
        },
        "handler": "ask_about_pitch"
    },
    
    "chat.compare_sessions": {
        "name": "chat.compare_sessions",
        "description": """
        Have conversational comparison of multiple pitch sessions.
        
        Provides interactive comparison analysis between pitch sessions using
        RAG to reference all relevant data:
        - Side-by-side transcript analysis
        - Scoring breakdowns and differentiators  
        - Technical implementation comparisons
        - Tool usage pattern analysis
        - Presentation style differences
        
        Creates a comparative conversation that can handle follow-up questions
        about specific aspects, ranking rationale, and detailed analysis.
        Useful for creating leaderboards and understanding competitive dynamics.
        
        Supports natural language queries like "Why did team A score higher in
        technical implementation?" or "What made team B's tool integration unique?"
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of session IDs to compare (2-10 sessions)",
                    "minItems": 2,
                    "maxItems": 10
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "comparison_focus": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["idea", "technical", "tools", "presentation", "overall"]},
                    "description": "Optional focus areas for comparison"
                },
                "conversation_title": {
                    "type": "string",
                    "description": "Optional title for the comparison conversation"
                },
                "judge_id": {
                    "type": "string",
                    "description": "Optional judge ID conducting the comparison"
                }
            },
            "required": ["session_ids", "event_id"]
        },
        "handler": "compare_sessions"
    },
    
    "chat.get_conversation_history": {
        "name": "chat.get_conversation_history",
        "description": """
        Retrieve conversation history with messages and context.
        
        Gets the complete conversation history including:
        - All user messages and AI responses
        - Source attributions for each AI response
        - Conversation metadata and context
        - Processing timestamps and durations
        - Error states and recovery information
        
        Supports pagination for long conversations and filtering by
        message type. Useful for reviewing conversation flow,
        understanding context development, and debugging interactions.
        
        Can include or exclude detailed source information based on
        the use case (summary view vs detailed analysis).
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "conversation_id": {
                    "type": "string",
                    "description": "Conversation ID to retrieve"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "include_sources": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include detailed source information"
                },
                "message_limit": {
                    "type": "integer",
                    "default": 50,
                    "description": "Maximum number of messages to return"
                },
                "message_offset": {
                    "type": "integer", 
                    "default": 0,
                    "description": "Offset for pagination"
                },
                "message_types": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["user_query", "ai_response", "system_message"]},
                    "description": "Optional filter by message types"
                }
            },
            "required": ["conversation_id", "event_id"]
        },
        "handler": "get_conversation_history"
    },
    
    "chat.health_check": {
        "name": "chat.health_check",
        "description": """
        """Check health and readiness of the RAG chat system.
        
        Verifies that all components of the RAG chat system are working:
        - LlamaIndex service connectivity and configuration
        - RedisVL vector store availability and indices
        - Azure OpenAI integration for chat and embeddings
        - Document indexing status and health
        - Redis conversation storage connectivity
        
        Provides detailed diagnostics for troubleshooting and system
        monitoring. Can perform light functional tests to verify
        end-to-end RAG pipeline functionality.
        
        Essential for ensuring chat system readiness before competitions.
        """
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Optional event ID for context-specific health check"
                },
                "detailed_check": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to perform detailed component testing"
                },
                "test_query": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to test with a sample RAG query"
                }
            },
            "required": []
        },
        "handler": "health_check"
    }
}


async def execute_chat_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a chat MCP tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments as a dictionary
        
    Returns:
        Tool execution result with chat response or data
    """
    from ...shared.infrastructure.logging import get_logger, log_with_context
    import time
    import traceback
    
    logger = get_logger("chat.mcp")
    start_time = time.time()
    
    # Extract context for logging
    event_id = arguments.get("event_id")
    conversation_id = arguments.get("conversation_id")
    user_id = arguments.get("user_id")
    
    log_with_context(
        logger, "INFO", f"Executing chat MCP tool: {tool_name}",
        event_id=event_id,
        conversation_id=conversation_id,
        user_id=user_id,
        tool_name=tool_name,
        operation="execute_chat_mcp_tool",
        argument_keys=list(arguments.keys())
    )
    
    # Validate tool exists
    if tool_name not in CHAT_MCP_TOOLS:
        log_with_context(
            logger, "ERROR", f"Unknown chat tool requested: {tool_name}",
            tool_name=tool_name,
            operation="tool_validation",
            available_tools=list(CHAT_MCP_TOOLS.keys())
        )
        return {
            "error": f"Unknown chat tool: {tool_name}",
            "available_tools": list(CHAT_MCP_TOOLS.keys()),
            "error_type": "unknown_tool"
        }
    
    tool_config = CHAT_MCP_TOOLS[tool_name]
    handler_method_name = tool_config["handler"]
    
    log_with_context(
        logger, "DEBUG", f"Tool validation passed, preparing to execute handler",
        tool_name=tool_name,
        handler_method=handler_method_name,
        operation="handler_preparation"
    )
    
    try:
        # Validate required arguments
        required_params = tool_config["inputSchema"].get("required", [])
        missing_params = [param for param in required_params if param not in arguments]
        
        if missing_params:
            log_with_context(
                logger, "ERROR", f"Missing required parameters for {tool_name}",
                tool_name=tool_name,
                missing_params=missing_params,
                provided_params=list(arguments.keys()),
                operation="parameter_validation"
            )
            return {
                "error": f"Missing required parameters: {missing_params}",
                "tool": tool_name,
                "missing_params": missing_params,
                "expected_schema": tool_config["inputSchema"],
                "error_type": "missing_parameters"
            }
        
        # Get the handler method
        if hasattr(chat_mcp_handler, handler_method_name):
            handler_method = getattr(chat_mcp_handler, handler_method_name)
            log_with_context(
                logger, "DEBUG", f"Handler method found: {handler_method_name}",
                tool_name=tool_name,
                handler_method=handler_method_name,
                operation="handler_resolution"
            )
        else:
            log_with_context(
                logger, "ERROR", f"Handler method not found: {handler_method_name}",
                tool_name=tool_name,
                handler_method=handler_method_name,
                operation="handler_resolution"
            )
            return {
                "error": f"Handler method '{handler_method_name}' not found",
                "tool": tool_name,
                "error_type": "handler_not_found"
            }
        
        # Execute the handler method with timing
        log_with_context(
            logger, "DEBUG", f"Invoking handler method for {tool_name}",
            tool_name=tool_name,
            handler_method=handler_method_name,
            operation="handler_execution"
        )
        
        try:
            result = await handler_method(**arguments)
        except TypeError as type_error:
            duration_ms = (time.time() - start_time) * 1000
            log_with_context(
                logger, "ERROR", f"Invalid arguments for {tool_name}: {str(type_error)}",
                tool_name=tool_name,
                handler_method=handler_method_name,
                operation="handler_execution",
                duration_ms=duration_ms,
                provided_arguments=list(arguments.keys()),
                error_type="invalid_arguments"
            )
            return {
                "error": f"Invalid arguments for {tool_name}: {str(type_error)}",
                "tool": tool_name,
                "expected_schema": tool_config["inputSchema"],
                "error_type": "invalid_arguments"
            }
        except Exception as handler_error:
            duration_ms = (time.time() - start_time) * 1000
            log_with_context(
                logger, "ERROR", f"Handler execution failed for {tool_name}: {str(handler_error)}",
                tool_name=tool_name,
                handler_method=handler_method_name,
                operation="handler_execution", 
                duration_ms=duration_ms,
                error_type=type(handler_error).__name__
            )
            return {
                "error": f"Handler execution failed: {str(handler_error)}",
                "tool": tool_name,
                "success": False,
                "error_type": "handler_execution_error"
            }
        
        # Log successful execution
        duration_ms = (time.time() - start_time) * 1000
        success = isinstance(result, dict) and result.get("success", True) and "error" not in result
        
        log_with_context(
            logger, "INFO" if success else "WARNING",
            f"Tool {tool_name} execution completed",
            event_id=event_id,
            conversation_id=conversation_id, 
            user_id=user_id,
            tool_name=tool_name,
            operation="execute_chat_mcp_tool",
            duration_ms=duration_ms,
            success=success,
            has_error=bool(result.get("error") if isinstance(result, dict) else False)
        )
        
        # Add tool execution metadata
        if isinstance(result, dict) and "error" not in result:
            result["_mcp_metadata"] = {
                "tool": tool_name,
                "executed_at": __import__("datetime").datetime.utcnow().isoformat(),
                "success": True,
                "analysis_type": "rag_powered_chat",
                "duration_ms": duration_ms
            }
        
        return result
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_with_context(
            logger, "ERROR", f"Unexpected error executing chat tool {tool_name}: {str(e)}",
            tool_name=tool_name,
            operation="execute_chat_mcp_tool",
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            traceback_info=traceback.format_exc()
        )
        return {
            "error": f"Chat tool execution failed: {str(e)}",
            "tool": tool_name,
            "success": False,
            "error_type": "unexpected_error"
        }


def get_chat_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get the schema definition for a specific chat tool."""
    return CHAT_MCP_TOOLS.get(tool_name)


def list_chat_tools() -> List[str]:
    """Get list of all available chat tool names."""
    return list(CHAT_MCP_TOOLS.keys())


def get_chat_tools_summary() -> Dict[str, Any]:
    """Get a summary of all available chat tools with descriptions."""
    return {
        name: {
            "description": config["description"].strip(),
            "required_params": config["inputSchema"]["required"],
            "optional_params": [
                param for param in config["inputSchema"]["properties"].keys()
                if param not in config["inputSchema"]["required"]
            ]
        }
        for name, config in CHAT_MCP_TOOLS.items()
    }
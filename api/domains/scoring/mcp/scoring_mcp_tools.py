"""
Scoring MCP Tools Registry - AI-Powered Analysis Tools

This module defines the MCP tools for AI-powered pitch scoring and analysis.
These tools integrate with the existing pitch recording workflow and use
Azure OpenAI + LangChain for structured analysis.

Available tools:
- analysis.score_pitch: Complete pitch scoring using official criteria
- analysis.analyze_tools: Analyze sponsor tool usage and integration  
- analysis.compare_pitches: Compare multiple pitch sessions
- analysis.get_scores: Retrieve existing scoring results
- analysis.health_check: Check AI analysis system health
"""
from typing import Any, Dict, Optional, List

from .scoring_mcp_handler import scoring_mcp_handler


# MCP Tool Registry for Scoring Domain
SCORING_MCP_TOOLS = {
    "analysis.score_pitch": {
        "name": "analysis.score_pitch",
        "description": """
        Score a complete pitch presentation using AI analysis based on official criteria.
        
        Analyzes the pitch transcript using Azure OpenAI and LangChain to provide
        structured scoring across all four criteria areas:
        - Idea (25%): Unique value proposition and vertical-specific agent design
        - Technical Implementation (25%): Novel tool use and technical sophistication  
        - Tool Use (25%): Integration of 3+ sponsor tools for agentic behavior
        - Presentation (25%): Clear 3-minute demo with impact demonstration
        
        Requires the pitch recording to be completed with transcript available.
        Supports multi-tenant isolation using event_id for competition management.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier from the pitch recording"
                },
                "event_id": {
                    "type": "string", 
                    "description": "Event ID for multi-tenant isolation"
                },
                "judge_id": {
                    "type": "string",
                    "description": "Optional judge identifier for tracking scoring attribution"
                },
                "scoring_context": {
                    "type": "object",
                    "description": "Optional context about specific scoring requirements or focus areas",
                    "properties": {
                        "event_type": {"type": "string", "description": "Type of competition event"},
                        "sponsor_tools": {"type": "array", "items": {"type": "string"}, "description": "Expected sponsor tools"},
                        "focus_areas": {"type": "array", "items": {"type": "string"}, "description": "Specific areas to emphasize"}
                    }
                }
            },
            "required": ["session_id", "event_id"]
        },
        "handler": "score_complete_pitch"
    },
    
    "analysis.analyze_tools": {
        "name": "analysis.analyze_tools", 
        "description": """
        Analyze sponsor tool usage and integration in a pitch presentation.
        
        Focuses specifically on the tool usage criteria (25% of total score):
        - Identifies which sponsor tools were mentioned/demonstrated
        - Evaluates whether the 3+ tool requirement is met
        - Analyzes how tools enable sophisticated agentic behavior
        - Assesses innovation and synergy in tool integration
        
        Provides detailed feedback on tool usage patterns and suggestions
        for improvement. Useful for targeted analysis of this specific criterion.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier from the pitch recording"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation" 
                },
                "sponsor_tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of expected sponsor tools to check against"
                }
            },
            "required": ["session_id", "event_id"]
        },
        "handler": "analyze_tool_usage"
    },
    
    "analysis.compare_pitches": {
        "name": "analysis.compare_pitches",
        "description": """
        Compare multiple pitch sessions using AI analysis for competitive evaluation.
        
        Performs comparative analysis across multiple pitches to help judges
        understand relative strengths and create rankings. Analyzes:
        - Comparative scoring across all criteria
        - Identification of strongest team in each category
        - Key differentiators between top-performing pitches
        - Overall competition level assessment
        
        Useful for creating leaderboards, identifying standout performances,
        and providing context for individual pitch evaluations.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of session IDs to compare (minimum 2, maximum 10)",
                    "minItems": 2,
                    "maxItems": 10
                },
                "event_id": {
                    "type": "string",
                    "description": "Organization ID for multi-tenant isolation"
                },
                "comparison_criteria": {
                    "type": "array", 
                    "items": {"type": "string"},
                    "description": "Optional specific criteria to focus comparison on",
                    "default": ["idea", "technical", "tools", "presentation"]
                }
            },
            "required": ["session_ids", "event_id"]
        },
        "handler": "compare_pitches"
    },
    
    "analysis.get_scores": {
        "name": "analysis.get_scores",
        "description": """
        Retrieve existing scoring results for a pitch session.
        
        Gets previously computed AI analysis results including:
        - Complete scoring breakdown across all criteria
        - Tool usage analysis if available  
        - Scoring timestamps and judge attribution
        - Summary scores for quick reference
        
        Supports both detailed analysis retrieval and summary view.
        Useful for displaying results, creating reports, or checking
        if a pitch has already been scored.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier to get scores for"
                },
                "event_id": {
                    "type": "string",
                    "description": "Organization ID for multi-tenant isolation"
                },
                "include_details": {
                    "type": "boolean", 
                    "description": "Whether to include full analysis details or just summary scores",
                    "default": True
                }
            },
            "required": ["session_id", "event_id"]
        },
        "handler": "get_scoring_results"
    },
    
    "analysis.analyze_presentation_delivery": {
        "name": "analysis.analyze_presentation_delivery",
        "description": """
        Analyze presentation delivery using both transcript content and Gladia Audio Intelligence.
        
        Provides comprehensive delivery analysis specifically for the "Presentation Delivery" criterion:
        - Speaking pace and rhythm (Words Per Minute analysis)
        - Professional delivery quality (filler word frequency)
        - Confidence and energy levels (voice quality analysis)
        - Pause effectiveness and timing patterns
        - Content clarity from transcript analysis
        - 3-minute time management assessment
        
        Combines traditional content analysis with objective audio metrics from Gladia's
        Audio Intelligence API to provide data-driven presentation delivery scoring.
        
        Ideal for coaches and judges who want detailed, actionable feedback on
        presentation skills with specific metrics and improvement suggestions.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier from the pitch recording"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "include_audio_metrics": {
                    "type": "boolean",
                    "description": "Whether to include Gladia Audio Intelligence metrics (default: true)",
                    "default": True
                },
                "benchmark_wpm": {
                    "type": "integer",
                    "description": "Target words per minute for comparison (default: 150 for pitch presentations)",
                    "default": 150,
                    "minimum": 100,
                    "maximum": 200
                }
            },
            "required": ["session_id", "event_id"]
        },
        "handler": "analyze_presentation_delivery"
    },
    
    "analysis.score_with_market_intelligence": {
        "name": "analysis.score_with_market_intelligence",
        "description": """
        Score pitch with AI analysis PLUS real-time market intelligence from BrightData.
        
        This tool provides instant scoring by leveraging background market intelligence
        gathering that starts during the pitch presentation. Key features:
        
        - Instant AI scoring (2.75 seconds) with background market data integration
        - Market size validation against real industry data
        - Competitive landscape analysis with funding information
        - Industry trend alignment assessment
        - Enhanced scoring accuracy with data-driven insights
        
        If background market intelligence is ready (cached during pitch), scoring
        is nearly instant. If not ready, falls back to AI-only scoring with
        optional market intelligence gathering.
        
        Perfect for real-time competition flow where judges score one pitch after another.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session identifier from the pitch recording"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "judge_id": {
                    "type": "string",
                    "description": "Optional judge identifier for tracking scoring attribution"
                },
                "wait_for_market_intelligence": {
                    "type": "boolean",
                    "description": "Whether to wait for market intelligence or return AI-only score immediately",
                    "default": False
                },
                "market_intelligence_timeout": {
                    "type": "integer",
                    "description": "Maximum seconds to wait for market intelligence (default: 10)",
                    "default": 10,
                    "minimum": 5,
                    "maximum": 30
                }
            },
            "required": ["session_id", "event_id"]
        },
        "handler": "score_with_background_market_intelligence"
    },
    
    "analysis.health_check": {
        "name": "analysis.health_check",
        "description": """
        Check the health and availability of the AI analysis system.
        
        Verifies that Azure OpenAI integration is working properly:
        - Tests Azure OpenAI API connectivity
        - Validates environment configuration
        - Checks LangChain integration status
        - Reports on system readiness for scoring operations
        
        Useful for troubleshooting, system monitoring, and ensuring
        the analysis tools are ready before important competitions.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Organization ID for context (optional)"
                },
                "detailed_check": {
                    "type": "boolean",
                    "description": "Whether to perform detailed component testing",
                    "default": False
                }
            },
            "required": []
        },
        "handler": "health_check"
    }
}


async def execute_scoring_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a scoring MCP tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments as a dictionary
        
    Returns:
        Tool execution result with analysis data
    """
    from ...shared.infrastructure.logging import get_logger, log_with_context
    import time
    import traceback
    
    logger = get_logger("scoring.mcp")
    start_time = time.time()
    
    # Extract context for logging
    event_id = arguments.get("event_id")
    session_id = arguments.get("session_id")
    judge_id = arguments.get("judge_id")
    
    log_with_context(
        logger, "INFO", f"Executing scoring MCP tool: {tool_name}",
        event_id=event_id,
        session_id=session_id,
        judge_id=judge_id,
        tool_name=tool_name,
        operation="execute_mcp_tool",
        argument_keys=list(arguments.keys())
    )
    
    # Validate tool exists
    if tool_name not in SCORING_MCP_TOOLS:
        log_with_context(
            logger, "ERROR", f"Unknown scoring tool requested: {tool_name}",
            tool_name=tool_name,
            operation="tool_validation",
            available_tools=list(SCORING_MCP_TOOLS.keys())
        )
        return {
            "error": f"Unknown scoring tool: {tool_name}",
            "available_tools": list(SCORING_MCP_TOOLS.keys()),
            "error_type": "unknown_tool"
        }
    
    tool_config = SCORING_MCP_TOOLS[tool_name]
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
        if hasattr(scoring_mcp_handler, handler_method_name):
            handler_method = getattr(scoring_mcp_handler, handler_method_name)
            log_with_context(
                logger, "DEBUG", f"Handler method found: {handler_method_name}",
                tool_name=tool_name,
                handler_method=handler_method_name,
                operation="handler_resolution"
            )
        else:
            # Handle special case for health_check
            if handler_method_name == "health_check":
                log_with_context(
                    logger, "DEBUG", "Executing health check handler",
                    tool_name=tool_name,
                    operation="health_check_handler"
                )
                return await _handle_health_check(arguments)
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
            session_id=session_id,
            judge_id=judge_id,
            tool_name=tool_name,
            operation="execute_mcp_tool",
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
                "analysis_type": "ai_powered_scoring",
                "duration_ms": duration_ms
            }
        
        return result
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_with_context(
            logger, "ERROR", f"Unexpected error executing scoring tool {tool_name}: {str(e)}",
            tool_name=tool_name,
            operation="execute_mcp_tool",
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            traceback_info=traceback.format_exc()
        )
        return {
            "error": f"Scoring tool execution failed: {str(e)}",
            "tool": tool_name,
            "success": False,
            "error_type": "unexpected_error"
        }


async def _handle_health_check(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle health check for the AI analysis system."""
    from ...shared.infrastructure.logging import get_logger, log_with_context
    import time
    
    logger = get_logger("scoring.health")
    start_time = time.time()
    
    event_id = arguments.get("event_id")
    detailed = arguments.get("detailed_check", False)
    
    log_with_context(
        logger, "INFO", "Starting scoring system health check",
        event_id=event_id,
        operation="health_check",
        detailed_check=detailed
    )
    
    try:
        from ...shared.infrastructure.azure_openai_client import get_azure_openai_client
        from ...shared.infrastructure.langchain_config import get_pitch_analysis_chains
        
        health_status = {
            "status": "healthy",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "event_id": event_id,
            "components": {},
            "detailed_check": detailed
        }
        
        # Test Azure OpenAI client
        log_with_context(
            logger, "DEBUG", "Testing Azure OpenAI connectivity",
            event_id=event_id,
            operation="azure_openai_health_check"
        )
        
        try:
            client = await get_azure_openai_client()
            azure_health = await client.health_check()
            health_status["components"]["azure_openai"] = azure_health
            
            log_with_context(
                logger, "INFO", f"Azure OpenAI health check: {azure_health.get('status', 'unknown')}",
                event_id=event_id,
                operation="azure_openai_health_check",
                azure_status=azure_health.get("status")
            )
            
            if azure_health["status"] != "healthy":
                health_status["status"] = "degraded"
                log_with_context(
                    logger, "WARNING", "Azure OpenAI reported degraded status",
                    event_id=event_id,
                    operation="azure_openai_health_check",
                    azure_status=azure_health["status"]
                )
                
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Azure OpenAI health check failed: {str(e)}",
                event_id=event_id,
                operation="azure_openai_health_check",
                error_type=type(e).__name__
            )
            health_status["components"]["azure_openai"] = {
                "status": "error",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
        
        # Test LangChain integration if detailed check requested
        if detailed:
            log_with_context(
                logger, "DEBUG", "Starting detailed LangChain integration test",
                event_id=event_id,
                operation="langchain_health_check"
            )
            
            try:
                chains = get_pitch_analysis_chains()
                
                # Test with a simple sample
                test_transcript = "Test pitch for health check - integrating OpenAI, Qdrant, and MinIO for document analysis."
                test_result = await chains.score_pitch(test_transcript, event_id=event_id)
                
                health_status["components"]["langchain"] = {
                    "status": "healthy" if test_result["success"] else "error",
                    "test_result": test_result.get("success", False),
                    "test_duration_ms": test_result.get("duration_ms"),
                    "analysis_type": test_result.get("analysis_type")
                }
                
                log_with_context(
                    logger, "INFO", f"LangChain integration test: {'passed' if test_result['success'] else 'failed'}",
                    event_id=event_id,
                    operation="langchain_health_check",
                    test_success=test_result.get("success"),
                    test_duration_ms=test_result.get("duration_ms")
                )
                
                if not test_result["success"]:
                    health_status["status"] = "degraded"
                    log_with_context(
                        logger, "WARNING", f"LangChain test failed: {test_result.get('error')}",
                        event_id=event_id,
                        operation="langchain_health_check",
                        langchain_error=test_result.get("error")
                    )
                    
            except Exception as e:
                log_with_context(
                    logger, "ERROR", f"LangChain integration test failed: {str(e)}",
                    event_id=event_id,
                    operation="langchain_health_check",
                    error_type=type(e).__name__
                )
                health_status["components"]["langchain"] = {
                    "status": "error",
                    "error": str(e)
                }
                health_status["status"] = "unhealthy"
        
        # Calculate total health check duration
        duration_ms = (time.time() - start_time) * 1000
        health_status["check_duration_ms"] = duration_ms
        
        log_with_context(
            logger, "INFO", f"Health check completed with status: {health_status['status']}",
            event_id=event_id,
            operation="health_check",
            overall_status=health_status["status"],
            duration_ms=duration_ms,
            components_checked=list(health_status["components"].keys())
        )
        
        return health_status
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_with_context(
            logger, "ERROR", f"Health check system error: {str(e)}",
            event_id=event_id,
            operation="health_check",
            duration_ms=duration_ms,
            error_type=type(e).__name__
        )
        return {
            "status": "unhealthy",
            "error": f"Health check failed: {str(e)}",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "event_id": event_id,
            "check_duration_ms": duration_ms,
            "error_type": "health_check_system_error"
        }


def get_scoring_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get the schema definition for a specific scoring tool."""
    return SCORING_MCP_TOOLS.get(tool_name)


def list_scoring_tools() -> List[str]:
    """Get list of all available scoring tool names."""
    return list(SCORING_MCP_TOOLS.keys())


def get_scoring_tools_summary() -> Dict[str, Any]:
    """Get a summary of all available scoring tools with descriptions."""
    return {
        name: {
            "description": config["description"].strip(),
            "required_params": config["inputSchema"]["required"],
            "optional_params": [
                param for param in config["inputSchema"]["properties"].keys()
                if param not in config["inputSchema"]["required"]
            ]
        }
        for name, config in SCORING_MCP_TOOLS.items()
    }
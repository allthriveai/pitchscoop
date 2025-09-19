"""
Audio-Integrated Scoring MCP Tools

This module provides MCP tools that integrate audio intelligence with presentation analysis.
Works without the problematic llamaindex_service dependency.
"""
from typing import Any, Dict, Optional, List

from .scoring_mcp_handler_audio_integrated import audio_integrated_scoring_mcp_handler


# Audio-integrated MCP Tool Registry for Scoring Domain
AUDIO_INTEGRATED_SCORING_MCP_TOOLS = {
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
    
    "analysis.health_check_audio": {
        "name": "analysis.health_check_audio",
        "description": """
        Check the health and availability of the audio-integrated analysis system.
        
        Verifies that both scoring and audio intelligence systems are working:
        - Tests Redis connectivity for session data
        - Validates Gladia MCP handler integration
        - Checks audio intelligence API availability
        - Reports on system readiness for audio-enhanced scoring
        
        Useful for troubleshooting, system monitoring, and ensuring
        the audio-integrated tools are ready for competitions.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event ID for context (optional)"
                },
                "test_session_id": {
                    "type": "string",
                    "description": "Optional session ID to test with real data"
                }
            },
            "required": []
        },
        "handler": "health_check_audio"
    }
}


async def execute_audio_integrated_scoring_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute an audio-integrated scoring MCP tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments as a dictionary
        
    Returns:
        Tool execution result with analysis data
    """
    import time
    import traceback
    from datetime import datetime
    
    start_time = time.time()
    
    print(f"🔧 Executing audio-integrated scoring tool: {tool_name}")
    print(f"   Arguments: {list(arguments.keys())}")
    
    # Validate tool exists
    if tool_name not in AUDIO_INTEGRATED_SCORING_MCP_TOOLS:
        return {
            "error": f"Unknown audio-integrated scoring tool: {tool_name}",
            "available_tools": list(AUDIO_INTEGRATED_SCORING_MCP_TOOLS.keys()),
            "error_type": "unknown_tool"
        }
    
    tool_config = AUDIO_INTEGRATED_SCORING_MCP_TOOLS[tool_name]
    handler_method_name = tool_config["handler"]
    
    try:
        # Validate required arguments
        required_params = tool_config["inputSchema"].get("required", [])
        missing_params = [param for param in required_params if param not in arguments]
        
        if missing_params:
            return {
                "error": f"Missing required parameters: {missing_params}",
                "tool": tool_name,
                "missing_params": missing_params,
                "expected_schema": tool_config["inputSchema"],
                "error_type": "missing_parameters"
            }
        
        # Get the handler method
        if hasattr(audio_integrated_scoring_mcp_handler, handler_method_name):
            handler_method = getattr(audio_integrated_scoring_mcp_handler, handler_method_name)
            
            # Execute the handler method
            result = await handler_method(**arguments)
            
            # Add tool execution metadata
            execution_duration = time.time() - start_time
            if isinstance(result, dict) and "error" not in result:
                if "_analysis_metadata" not in result:
                    result["_analysis_metadata"] = {}
                
                result["_analysis_metadata"].update({
                    "tool_name": tool_name,
                    "handler_method": handler_method_name,
                    "execution_duration_seconds": round(execution_duration, 3),
                    "success": True,
                    "audio_integration_enabled": True
                })
            
            print(f"✅ Tool executed successfully in {execution_duration:.2f}s")
            return result
            
        else:
            return {
                "error": f"Handler method '{handler_method_name}' not found in audio integrated handler",
                "tool": tool_name,
                "available_methods": [method for method in dir(audio_integrated_scoring_mcp_handler) if not method.startswith('_')],
                "error_type": "handler_not_found"
            }
        
    except TypeError as e:
        return {
            "error": f"Invalid arguments for {tool_name}: {str(e)}",
            "tool": tool_name,
            "expected_schema": tool_config["inputSchema"],
            "error_type": "invalid_arguments"
        }
    except Exception as e:
        error_msg = f"Tool execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "error": error_msg,
            "tool": tool_name,
            "success": False,
            "error_type": "execution_failure",
            "traceback": traceback.format_exc()
        }


async def health_check_audio(event_id: Optional[str] = None, test_session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Health check for audio-integrated scoring system.
    
    Args:
        event_id: Optional event ID for context
        test_session_id: Optional session ID to test with
        
    Returns:
        System health status
    """
    from datetime import datetime
    
    health_status = {
        "system": "audio_integrated_scoring",
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "healthy",
        "components": {}
    }
    
    try:
        # Test Redis connectivity
        print("🔍 Testing Redis connectivity...")
        redis_client = await audio_integrated_scoring_mcp_handler.get_redis()
        await redis_client.ping()
        health_status["components"]["redis"] = {"status": "healthy", "message": "Connection successful"}
        print("✅ Redis connection healthy")
        
    except Exception as e:
        health_status["components"]["redis"] = {"status": "unhealthy", "message": f"Connection failed: {str(e)}"}
        health_status["overall_status"] = "degraded"
        print(f"❌ Redis connection failed: {e}")
    
    try:
        # Test Gladia MCP handler integration
        print("🔍 Testing Gladia MCP handler...")
        from ...recordings.mcp.gladia_mcp_handler import gladia_mcp_handler
        
        # Test method exists
        if hasattr(gladia_mcp_handler, 'get_audio_intelligence'):
            health_status["components"]["gladia_mcp"] = {"status": "healthy", "message": "Handler available"}
            print("✅ Gladia MCP handler available")
            
            # If test session provided, try actual call
            if test_session_id:
                print(f"🧪 Testing with session: {test_session_id}")
                test_result = await gladia_mcp_handler.get_audio_intelligence(test_session_id)
                if "error" in test_result:
                    health_status["components"]["gladia_audio_intelligence"] = {
                        "status": "degraded", 
                        "message": f"Test call returned error: {test_result.get('error_type', 'unknown')}"
                    }
                else:
                    health_status["components"]["gladia_audio_intelligence"] = {
                        "status": "healthy", 
                        "message": "Test call successful"
                    }
            
        else:
            health_status["components"]["gladia_mcp"] = {"status": "unhealthy", "message": "Handler method not found"}
            health_status["overall_status"] = "unhealthy"
            
    except Exception as e:
        health_status["components"]["gladia_mcp"] = {"status": "unhealthy", "message": f"Import/test failed: {str(e)}"}
        health_status["overall_status"] = "unhealthy"
        print(f"❌ Gladia MCP handler test failed: {e}")
    
    # Test audio intelligence value objects
    try:
        print("🔍 Testing audio intelligence value objects...")
        from ...recordings.value_objects.audio_intelligence import AudioIntelligence, SpeechMetrics
        health_status["components"]["audio_intelligence_objects"] = {"status": "healthy", "message": "Value objects available"}
        print("✅ Audio intelligence value objects available")
        
    except Exception as e:
        health_status["components"]["audio_intelligence_objects"] = {"status": "unhealthy", "message": f"Import failed: {str(e)}"}
        health_status["overall_status"] = "degraded"
        print(f"❌ Audio intelligence value objects failed: {e}")
    
    return health_status


# Add the health check method to the handler
audio_integrated_scoring_mcp_handler.health_check_audio = health_check_audio


def get_audio_integrated_tools_summary() -> Dict[str, Any]:
    """
    Get a summary of all available audio-integrated tools with descriptions.
    
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
            ],
            "audio_intelligence_enabled": True
        }
        for name, config in AUDIO_INTEGRATED_SCORING_MCP_TOOLS.items()
    }


if __name__ == "__main__":
    # Print tools summary when run directly
    import asyncio
    import json
    
    print("Audio-Integrated Scoring MCP Tools Summary")
    print("=" * 60)
    
    summary = get_audio_integrated_tools_summary()
    for tool_name, info in summary.items():
        print(f"\n{tool_name}:")
        print(f"  Description: {info['description'][:100]}...")
        print(f"  Required: {info['required_params']}")
        print(f"  Optional: {info['optional_params']}")
        print(f"  Audio Intelligence: {info['audio_intelligence_enabled']}")
    
    print(f"\nTotal audio-integrated tools available: {len(AUDIO_INTEGRATED_SCORING_MCP_TOOLS)}")
    
    # Run health check
    print("\n" + "=" * 60)
    async def test_health():
        health = await health_check_audio()
        print(json.dumps(health, indent=2))
    
    asyncio.run(test_health())
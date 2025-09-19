"""
Market MCP Tools - Bright Data Integration

MCP tools for market validation, competitive analysis, and industry trend analysis
using Bright Data web scraping capabilities.

Available tools:
- market.validate_claims: Validate market size claims against real data
- market.analyze_competitors: Find and analyze competitive landscape
- market.industry_trends: Get current industry trends and news
- market.health_check: Test Bright Data service connectivity
"""
from typing import Any, Dict, Optional, List

from ..services.bright_data_service import bright_data_service
from ..entities.market_analysis import MarketAnalysis, MarketValidation, CompetitorProfile


# MCP Tool Registry for Market Domain
MARKET_MCP_TOOLS = {
    "market.validate_claims": {
        "name": "market.validate_claims",
        "description": """
        Validate market size and growth claims using real-time web scraping.
        
        Uses Bright Data to scrape industry reports, market research, and recent
        data to validate the market claims made in pitch presentations.
        
        Provides confidence scoring and sourced validation of:
        - Market size claims (TAM, SAM, SOM)
        - Growth rate projections
        - Market trend assertions
        - Industry opportunity size
        
        Returns validation results with confidence scoring and sources.
        Essential for judges to understand if market claims are realistic.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "market_claims": {
                    "type": "string",
                    "description": "Market claims to validate (e.g., '$50B market opportunity')"
                },
                "industry": {
                    "type": "string",
                    "description": "Industry or sector (e.g., 'fintech', 'healthcare', 'AI')"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "team_name": {
                    "type": "string",
                    "description": "Optional team name for context"
                },
                "session_id": {
                    "type": "string",
                    "description": "Optional session ID to link with pitch"
                }
            },
            "required": ["market_claims", "industry", "event_id"]
        },
        "handler": "validate_market_claims"
    },
    
    "market.analyze_competitors": {
        "name": "market.analyze_competitors",
        "description": """
        Analyze competitive landscape using web scraping and company data.
        
        Uses Bright Data to find and analyze competitors based on company
        description and industry. Provides comprehensive competitive intelligence:
        - Direct competitor identification
        - Funding and valuation data
        - Employee counts and company size
        - Recent news and developments
        - Competitive density assessment
        
        Essential for judges to understand how crowded the market is and
        whether the team has identified their true competitive landscape.
        """,
        "inputSchema": {
            "type": "object", 
            "properties": {
                "company_description": {
                    "type": "string",
                    "description": "Description of the company/product to find competitors for"
                },
                "industry": {
                    "type": "string",
                    "description": "Industry or sector to search within"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "team_name": {
                    "type": "string",
                    "description": "Optional team name for context"
                },
                "max_competitors": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of competitors to return"
                },
                "include_funding_data": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include funding and valuation information"
                }
            },
            "required": ["company_description", "industry", "event_id"]
        },
        "handler": "analyze_competitors"
    },
    
    "market.industry_trends": {
        "name": "market.industry_trends", 
        "description": """
        Get current industry trends and recent developments.
        
        Uses Bright Data to scrape recent industry news, trend reports, and
        market developments to provide context on industry dynamics:
        - Trending keywords and topics
        - Recent funding activity
        - Regulatory changes
        - Technology developments
        - Market sentiment
        
        Helps judges understand if the team is building in a growing,
        stable, or declining market segment.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "industry": {
                    "type": "string", 
                    "description": "Industry to analyze trends for"
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional specific keywords to track"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID for multi-tenant isolation"
                },
                "timeframe": {
                    "type": "string",
                    "enum": ["1month", "3months", "6months"],
                    "default": "3months",
                    "description": "Timeframe for trend analysis"
                },
                "include_news": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include recent news articles"
                }
            },
            "required": ["industry", "event_id"]
        },
        "handler": "get_industry_trends"
    },
    
    "market.health_check": {
        "name": "market.health_check",
        "description": """
        Check health and connectivity of Bright Data market intelligence system.
        
        Verifies that:
        - Bright Data API is accessible
        - API key is valid and working
        - Rate limiting is functioning
        - Mock mode status (if no API key)
        
        Essential for troubleshooting market intelligence features before
        important competitions or demonstrations.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Optional event ID for context"
                },
                "test_real_api": {
                    "type": "boolean", 
                    "default": False,
                    "description": "Whether to test with real API call (costs money)"
                }
            },
            "required": []
        },
        "handler": "health_check"
    }
}


async def execute_market_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a market MCP tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments as a dictionary
        
    Returns:
        Tool execution result with market intelligence data
    """
    from ...shared.infrastructure.logging import get_logger, log_with_context
    import time
    import traceback
    
    logger = get_logger("market.mcp")
    start_time = time.time()
    
    # Extract context for logging
    event_id = arguments.get("event_id")
    team_name = arguments.get("team_name")
    
    log_with_context(
        logger, "INFO", f"Executing market MCP tool: {tool_name}",
        event_id=event_id,
        team_name=team_name,
        tool_name=tool_name,
        operation="execute_market_mcp_tool",
        argument_keys=list(arguments.keys())
    )
    
    # Validate tool exists
    if tool_name not in MARKET_MCP_TOOLS:
        log_with_context(
            logger, "ERROR", f"Unknown market tool requested: {tool_name}",
            tool_name=tool_name,
            operation="tool_validation",
            available_tools=list(MARKET_MCP_TOOLS.keys())
        )
        return {
            "error": f"Unknown market tool: {tool_name}",
            "available_tools": list(MARKET_MCP_TOOLS.keys()),
            "error_type": "unknown_tool"
        }
    
    tool_config = MARKET_MCP_TOOLS[tool_name]
    handler_method_name = tool_config["handler"]
    
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
        
        # Execute the handler
        if handler_method_name == "validate_market_claims":
            result = await validate_market_claims(**arguments)
        elif handler_method_name == "analyze_competitors":
            result = await analyze_competitors(**arguments)
        elif handler_method_name == "get_industry_trends":
            result = await get_industry_trends(**arguments)
        elif handler_method_name == "health_check":
            result = await health_check(**arguments)
        else:
            return {
                "error": f"Handler method '{handler_method_name}' not implemented",
                "tool": tool_name,
                "error_type": "handler_not_implemented"
            }
        
        # Log successful execution
        duration_ms = (time.time() - start_time) * 1000
        success = isinstance(result, dict) and result.get("success", True) and "error" not in result
        
        log_with_context(
            logger, "INFO" if success else "WARNING",
            f"Tool {tool_name} execution completed",
            event_id=event_id,
            team_name=team_name,
            tool_name=tool_name,
            operation="execute_market_mcp_tool",
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
                "analysis_type": "bright_data_market_intelligence", 
                "duration_ms": duration_ms
            }
        
        return result
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_with_context(
            logger, "ERROR", f"Unexpected error executing market tool {tool_name}: {str(e)}",
            tool_name=tool_name,
            operation="execute_market_mcp_tool", 
            duration_ms=duration_ms,
            error_type=type(e).__name__,
            traceback_info=traceback.format_exc()
        )
        return {
            "error": f"Market tool execution failed: {str(e)}",
            "tool": tool_name,
            "success": False,
            "error_type": "unexpected_error"
        }


# MCP Tool Handler Functions

async def validate_market_claims(
    market_claims: str, 
    industry: str, 
    event_id: str, 
    team_name: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """Validate market size claims using Bright Data."""
    try:
        result = await bright_data_service.validate_market_size(market_claims, industry, event_id)
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "event_id": event_id,
                "team_name": team_name
            }
        
        return {
            "success": True,
            "event_id": event_id,
            "team_name": team_name,
            "session_id": session_id,
            "market_validation": {
                "claimed_market_size": market_claims,
                "validated_market_size": result.get("market_size"),
                "market_size_confidence": result.get("confidence"),
                "growth_rate": result.get("growth_rate"),
                "market_trends": result.get("trends", []),
                "sources": result.get("sources", [])
            },
            "industry": industry
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Market validation failed: {str(e)}",
            "event_id": event_id,
            "team_name": team_name
        }


async def analyze_competitors(
    company_description: str,
    industry: str, 
    event_id: str,
    team_name: Optional[str] = None,
    max_competitors: int = 10,
    include_funding_data: bool = True
) -> Dict[str, Any]:
    """Analyze competitive landscape using Bright Data."""
    try:
        result = await bright_data_service.analyze_competitors(company_description, industry, event_id)
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "event_id": event_id,
                "team_name": team_name
            }
        
        # Convert to our data structure
        competitors = []
        for comp_data in result.get("competitors", [])[:max_competitors]:
            competitor = CompetitorProfile(
                name=comp_data.get("name", ""),
                description=comp_data.get("description", ""),
                website=comp_data.get("website"),
                funding_amount=comp_data.get("funding_amount"),
                funding_stage=comp_data.get("funding_stage"),
                employees=comp_data.get("employees"),
                founded_year=comp_data.get("founded_year"),
                similarity_score=comp_data.get("similarity_score")
            )
            competitors.append(competitor.__dict__)
        
        return {
            "success": True,
            "event_id": event_id,
            "team_name": team_name,
            "competitive_analysis": {
                "competitors": competitors,
                "total_competitors_found": result.get("total_found", len(competitors)),
                "competitive_density": result.get("competitive_density", "MEDIUM"),
                "company_description": company_description,
                "industry": industry
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Competitive analysis failed: {str(e)}",
            "event_id": event_id,
            "team_name": team_name
        }


async def get_industry_trends(
    industry: str,
    event_id: str,
    keywords: Optional[List[str]] = None,
    timeframe: str = "3months",
    include_news: bool = True
) -> Dict[str, Any]:
    """Get industry trends using Bright Data."""
    if keywords is None:
        keywords = []
        
    try:
        result = await bright_data_service.get_industry_trends(industry, keywords, event_id)
        
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "event_id": event_id,
                "industry": industry
            }
        
        return {
            "success": True,
            "event_id": event_id,
            "industry_trends": {
                "industry": industry,
                "timeframe": timeframe,
                "trending_keywords": result.get("trending_keywords", []),
                "recent_news": result.get("recent_news", []) if include_news else [],
                "market_sentiment": result.get("market_sentiment", "NEUTRAL")
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Industry trends analysis failed: {str(e)}",
            "event_id": event_id,
            "industry": industry
        }


async def health_check(event_id: Optional[str] = None, test_real_api: bool = False) -> Dict[str, Any]:
    """Check health of Bright Data service."""
    try:
        import os
        
        health_status = {
            "status": "healthy",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "event_id": event_id,
            "components": {}
        }
        
        # Check API key configuration
        api_key_configured = bool(os.getenv("BRIGHT_DATA_API_KEY"))
        health_status["components"]["api_key"] = {
            "status": "configured" if api_key_configured else "missing",
            "mock_mode": not api_key_configured
        }
        
        # Test service connectivity
        if test_real_api and api_key_configured:
            # Make a small test request
            test_result = await bright_data_service.get_industry_trends("technology", ["AI"], event_id or "health_check")
            health_status["components"]["api_connectivity"] = {
                "status": "healthy" if "error" not in test_result else "error",
                "test_performed": True,
                "error": test_result.get("error") if "error" in test_result else None
            }
        else:
            # Just test mock mode
            test_result = await bright_data_service._mock_response("industry-trends", {})
            health_status["components"]["mock_service"] = {
                "status": "healthy" if "error" not in test_result else "error", 
                "mock_mode": True
            }
        
        # Determine overall health
        component_statuses = [comp["status"] for comp in health_status["components"].values()]
        if "error" in component_statuses:
            health_status["status"] = "unhealthy"
        elif "missing" in component_statuses:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": f"Health check failed: {str(e)}",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "event_id": event_id
        }


def get_market_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """Get the schema definition for a specific market tool."""
    return MARKET_MCP_TOOLS.get(tool_name)


def list_market_tools() -> List[str]:
    """Get list of all available market tool names."""
    return list(MARKET_MCP_TOOLS.keys())


def get_market_tools_summary() -> Dict[str, Any]:
    """Get a summary of all available market tools with descriptions."""
    return {
        name: {
            "description": config["description"].strip(),
            "required_params": config["inputSchema"]["required"],
            "optional_params": [
                param for param in config["inputSchema"]["properties"].keys()
                if param not in config["inputSchema"]["required"]
            ]
        }
        for name, config in MARKET_MCP_TOOLS.items()
    }
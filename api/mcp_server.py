#!/usr/bin/env python3
"""
PitchScoop MCP Server

This server exposes all PitchScoop domain tools via the Model Context Protocol (MCP),
allowing AI assistants like Claude Desktop to interact with the pitch competition platform.

Available domains:
- Events: Create and manage competitions (hackathons, VC pitches, practice sessions)
- Recordings: Record and manage pitch audio with Gladia STT integration
- Scoring: AI-powered pitch analysis and scoring
- Chat: RAG-powered conversational AI over competition data
- Leaderboards: Competition rankings and standings
- Feedback: Individual team feedback and improvement suggestions

Usage:
    python mcp_server.py

The server runs on stdio transport for Claude Desktop integration.
"""
import asyncio
import sys
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import traceback

# MCP server imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult,
)
import mcp.server.stdio
import mcp.types as types

# Import all domain MCP tool executors
from domains.events.mcp.events_mcp_tools import execute_events_mcp_tool, EVENTS_MCP_TOOLS
from domains.recordings.mcp.mcp_tools import execute_mcp_tool as execute_recordings_tool, MCP_TOOLS as RECORDINGS_MCP_TOOLS
from domains.scoring.mcp.scoring_mcp_tools import execute_scoring_mcp_tool, SCORING_MCP_TOOLS
from domains.chat.mcp.chat_mcp_tools import execute_chat_mcp_tool, CHAT_MCP_TOOLS
from domains.market.mcp.market_mcp_tools import execute_market_mcp_tool, MARKET_MCP_TOOLS


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pitchscoop.mcp.server")


class PitchScoopMCPServer:
    """
    MCP server for PitchScoop pitch competition platform.
    
    Provides AI assistants with access to:
    - Event management tools
    - Pitch recording and playback
    - AI-powered scoring and analysis  
    - RAG-powered chat over competition data
    - Leaderboards and rankings (when implemented)
    - Individual feedback generation (when implemented)
    """
    
    def __init__(self):
        """Initialize the PitchScoop MCP server."""
        self.server = Server("pitchscoop")
        self._setup_handlers()
        
        # Tool registry - maps tool names to their domains and executors
        self.tool_registry = {
            # Events domain tools
            **{name: {"domain": "events", "executor": execute_events_mcp_tool, "config": config} 
               for name, config in EVENTS_MCP_TOOLS.items()},
            
            # Recordings domain tools  
            **{name: {"domain": "recordings", "executor": execute_recordings_tool, "config": config}
               for name, config in RECORDINGS_MCP_TOOLS.items()},
            
            # Scoring domain tools
            **{name: {"domain": "scoring", "executor": execute_scoring_mcp_tool, "config": config}
               for name, config in SCORING_MCP_TOOLS.items()},
            
            # Chat domain tools
            **{name: {"domain": "chat", "executor": execute_chat_mcp_tool, "config": config}
               for name, config in CHAT_MCP_TOOLS.items()},
            
            # Market domain tools
            **{name: {"domain": "market", "executor": execute_market_mcp_tool, "config": config}
               for name, config in MARKET_MCP_TOOLS.items()},
        }
        
        logger.info(f"PitchScoop MCP server initialized with {len(self.tool_registry)} tools")
        logger.info(f"Available tools: {list(self.tool_registry.keys())}")
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools(request: ListToolsRequest) -> ListToolsResult:
            """List all available tools."""
            logger.info("Received list_tools request")
            
            tools = []
            for tool_name, tool_info in self.tool_registry.items():
                config = tool_info["config"]
                
                # Convert our tool schema to MCP Tool format
                tool = Tool(
                    name=tool_name,
                    description=config["description"],
                    inputSchema=config["inputSchema"]
                )
                tools.append(tool)
            
            logger.info(f"Returning {len(tools)} tools")
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def handle_call_tool(request: CallToolRequest) -> CallToolResult:
            """Execute a tool call."""
            tool_name = request.name
            arguments = request.arguments or {}
            
            logger.info(f"Received tool call: {tool_name}")
            logger.debug(f"Arguments: {arguments}")
            
            try:
                # Check if tool exists
                if tool_name not in self.tool_registry:
                    error_msg = f"Unknown tool: {tool_name}. Available tools: {list(self.tool_registry.keys())}"
                    logger.error(error_msg)
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps({
                            "error": error_msg,
                            "available_tools": list(self.tool_registry.keys())
                        }, indent=2))]
                    )
                
                # Get tool info
                tool_info = self.tool_registry[tool_name]
                executor = tool_info["executor"]
                domain = tool_info["domain"]
                
                logger.info(f"Executing {domain} domain tool: {tool_name}")
                
                # Execute the tool
                start_time = datetime.utcnow()
                result = await executor(tool_name, arguments)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                # Add execution metadata
                if isinstance(result, dict):
                    result["_mcp_execution"] = {
                        "domain": domain,
                        "tool": tool_name,
                        "duration_seconds": duration,
                        "executed_at": start_time.isoformat(),
                        "server": "pitchscoop-mcp"
                    }
                
                # Format result for MCP response
                result_text = json.dumps(result, indent=2, default=str)
                
                logger.info(f"Tool {tool_name} executed successfully in {duration:.2f}s")
                logger.debug(f"Result preview: {result_text[:200]}...")
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)]
                )
                
            except Exception as e:
                error_msg = f"Error executing tool {tool_name}: {str(e)}"
                logger.error(error_msg)
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                error_result = {
                    "error": error_msg,
                    "tool": tool_name,
                    "domain": tool_info.get("domain", "unknown") if tool_name in self.tool_registry else "unknown",
                    "traceback": traceback.format_exc(),
                    "success": False
                }
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(error_result, indent=2))]
                )
    
    async def run(self):
        """Run the MCP server on stdio transport."""
        logger.info("Starting PitchScoop MCP server...")
        logger.info("Server ready for AI assistant connections")
        
        # Additional startup info
        domains = {}
        for tool_name, tool_info in self.tool_registry.items():
            domain = tool_info["domain"]
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(tool_name)
        
        logger.info("Available domains and tools:")
        for domain, tools in domains.items():
            logger.info(f"  {domain}: {len(tools)} tools")
            for tool in tools:
                logger.debug(f"    - {tool}")
        
        # Run server on stdio
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="pitchscoop",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point for the MCP server."""
    try:
        # Create and run the server
        server = PitchScoopMCPServer()
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # Run the server
    asyncio.run(main())
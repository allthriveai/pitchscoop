#!/usr/bin/env python3
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

PitchScoop MCP Server (Test Version)

Minimal MCP server for testing with just Events and Recordings domains.
This avoids any LlamaIndex/scoring dependencies while proving the MCP concept works.

Available domains:
- Events: Create and manage competitions  
- Recordings: Record and manage pitch audio with Gladia STT

Usage:
    python mcp_server_test.py
"""
import asyncio
import sys
import json
import logging
from typing import Any, Dict
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

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))

# Import only the working domains
from domains.events.mcp.events_mcp_tools import execute_events_mcp_tool, EVENTS_MCP_TOOLS
from domains.recordings.mcp.mcp_tools import execute_mcp_tool as execute_recordings_tool, MCP_TOOLS as RECORDINGS_MCP_TOOLS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pitchscoop.mcp.test")


class PitchScoopMCPTest:
    """Test MCP server with just Events and Recordings domains."""
    
    def __init__(self):
        """Initialize the test MCP server."""
        self.server = Server("pitchscoop")
        self._setup_handlers()
        
        # Tool registry - only working domains
        self.tool_registry = {
            # Events domain tools
            **{name: {"domain": "events", "executor": execute_events_mcp_tool, "config": config} 
               for name, config in EVENTS_MCP_TOOLS.items()},
            
            # Recordings domain tools  
            **{name: {"domain": "recordings", "executor": execute_recordings_tool, "config": config}
               for name, config in RECORDINGS_MCP_TOOLS.items()},
        }
        
        logger.info(f"Test MCP server initialized with {len(self.tool_registry)} tools")
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools(request: ListToolsRequest) -> ListToolsResult:
            """List all available tools."""
            tools = []
            for tool_name, tool_info in self.tool_registry.items():
                config = tool_info["config"]
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
            
            logger.info(f"Executing tool: {tool_name}")
            
            try:
                if tool_name not in self.tool_registry:
                    error_result = {
                        "error": f"Unknown tool: {tool_name}",
                        "available_tools": list(self.tool_registry.keys())
                    }
                    return CallToolResult(
                        content=[TextContent(type="text", text=json.dumps(error_result, indent=2))]
                    )
                
                # Get tool info and execute
                tool_info = self.tool_registry[tool_name]
                executor = tool_info["executor"]
                
                start_time = datetime.utcnow()
                result = await executor(tool_name, arguments)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                # Add execution metadata
                if isinstance(result, dict):
                    result["_mcp_test"] = {
                        "tool": tool_name,
                        "duration_seconds": duration,
                        "executed_at": start_time.isoformat()
                    }
                
                result_text = json.dumps(result, indent=2, default=str)
                logger.info(f"Tool {tool_name} completed in {duration:.2f}s")
                
                return CallToolResult(
                    content=[TextContent(type="text", text=result_text)]
                )
                
            except Exception as e:
                error_result = {
                    "error": f"Tool execution failed: {str(e)}",
                    "tool": tool_name,
                    "traceback": traceback.format_exc()
                }
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(error_result, indent=2))]
                )
    
    async def run(self):
        """Run the test MCP server."""
        logger.info("Starting Test MCP server...")
        logger.info(f"Available tools: {list(self.tool_registry.keys())}")
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="pitchscoop-test",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point."""
    try:
        server = PitchScoopMCPTest()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
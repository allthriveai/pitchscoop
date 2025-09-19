#!/usr/bin/env python3
"""
Simple Web Server for Testing CanaryQA MCP Tools

This creates a basic FastAPI server that exposes the MCP tools via HTTP
so they can be tested in the browser interface.

Run with: python web_test_server.py
Then open: http://localhost:8000/test
"""
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import our MCP tools
from domains.recordings.mcp.mcp_tools import execute_mcp_tool, list_available_tools, get_tools_summary

app = FastAPI(
    title="CanaryQA MCP Test Server",
    description="Web interface for testing CanaryQA MCP tools",
    version="1.0.0"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MCPRequest(BaseModel):
    """Request model for MCP tool execution."""
    tool: str
    arguments: Dict[str, Any]


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "message": "CanaryQA MCP Test Server",
        "test_interface": "/test",
        "available_tools": len(list_available_tools()),
        "documentation": "/docs"
    }


@app.get("/test")
async def test_interface():
    """Serve the test interface HTML file."""
    return FileResponse("test_interface.html")


@app.post("/mcp/execute")
async def execute_mcp(request: MCPRequest):
    """
    Execute an MCP tool with the provided arguments.
    
    This endpoint allows the browser interface to call MCP tools.
    """
    try:
        # Execute the MCP tool
        result = await execute_mcp_tool(request.tool, request.arguments)
        
        # Return the result (success or error)
        return result
        
    except Exception as e:
        # Handle unexpected errors
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Server error: {str(e)}",
                "tool": request.tool,
                "success": False
            }
        )


@app.get("/mcp/tools")
async def get_available_tools():
    """Get list of available MCP tools."""
    try:
        return {
            "tools": list_available_tools(),
            "summary": get_tools_summary()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get tools: {str(e)}"}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test basic functionality
        tools = list_available_tools()
        
        return {
            "status": "healthy",
            "available_tools": len(tools),
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
            }
        )


@app.get("/mcp/test")
async def quick_test():
    """Quick test endpoint to verify MCP functionality."""
    try:
        # Test listing sessions (should work even if empty)
        result = await execute_mcp_tool("pitches.list_sessions", {})
        
        return {
            "test": "success",
            "message": "MCP tools are working",
            "sample_result": result
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "test": "failed",
                "error": str(e)
            }
        )


if __name__ == "__main__":
    print("🚀 Starting CanaryQA MCP Test Server...")
    print("📋 Available endpoints:")
    print("   • http://localhost:8000/test - Browser test interface")
    print("   • http://localhost:8000/docs - API documentation")
    print("   • http://localhost:8000/health - Health check")
    print("   • http://localhost:8000/mcp/test - Quick MCP test")
    print()
    print("🎙️  Use the browser interface to test recording workflows!")
    print()
    
    uvicorn.run(
        "web_test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
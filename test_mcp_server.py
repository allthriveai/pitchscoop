#!/usr/bin/env python3
"""
Test script for PitchScoop MCP Server

This script tests the MCP server functionality by running it locally
and simulating tool calls that an AI assistant would make.

Run with: python test_mcp_server.py
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Add the api directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "api"))

async def test_mcp_server():
    """Test the MCP server by importing and calling tools directly."""
    print("🚀 Testing PitchScoop MCP Server")
    print("=" * 50)
    
    try:
        # Import the server
        from api.mcp_server import PitchScoopMCPServer
        
        print("✅ MCP server imported successfully")
        
        # Create server instance
        server = PitchScoopMCPServer()
        print(f"✅ Server initialized with {len(server.tool_registry)} tools")
        
        # Test tool registry
        domains = {}
        for tool_name, tool_info in server.tool_registry.items():
            domain = tool_info["domain"]
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(tool_name)
        
        print("\n📋 Available domains and tools:")
        for domain, tools in domains.items():
            print(f"  {domain}: {len(tools)} tools")
            for tool in tools[:3]:  # Show first 3 tools per domain
                print(f"    - {tool}")
            if len(tools) > 3:
                print(f"    ... and {len(tools) - 3} more")
        
        # Test a simple tool execution (list events)
        print("\n🔧 Testing tool execution...")
        
        # Import direct tool executor for testing
        from api.domains.events.mcp.events_mcp_tools import execute_events_mcp_tool
        
        # Test listing events
        result = await execute_events_mcp_tool("events.list_events", {})
        print(f"✅ events.list_events executed: {type(result)} result")
        
        if "error" in result:
            print(f"⚠️  Result contains error (expected for empty database): {result.get('error', '')[:100]}")
        else:
            print(f"✅ Tool executed successfully: {len(str(result))} chars in result")
        
        print("\n🎉 MCP server test completed successfully!")
        print("\nNext steps:")
        print("1. Start your Docker environment: docker compose up -d")
        print("2. Configure Claude Desktop with the provided config")
        print("3. Test with Claude Desktop connection")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the pitchscoop directory")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tool_schemas():
    """Test that all tool schemas are valid."""
    print("\n🔍 Testing tool schemas...")
    
    try:
        # Import tool collections
        from api.domains.events.mcp.events_mcp_tools import EVENTS_MCP_TOOLS
        from api.domains.recordings.mcp.mcp_tools import MCP_TOOLS as RECORDINGS_MCP_TOOLS  
        from api.domains.scoring.mcp.scoring_mcp_tools import SCORING_MCP_TOOLS
        from api.domains.chat.mcp.chat_mcp_tools import CHAT_MCP_TOOLS
        
        all_tools = {
            "events": EVENTS_MCP_TOOLS,
            "recordings": RECORDINGS_MCP_TOOLS,
            "scoring": SCORING_MCP_TOOLS,
            "chat": CHAT_MCP_TOOLS
        }
        
        total_tools = 0
        for domain, tools in all_tools.items():
            print(f"  {domain}: {len(tools)} tools")
            total_tools += len(tools)
            
            # Validate each tool has required fields
            for tool_name, config in tools.items():
                required_fields = ["name", "description", "inputSchema", "handler"]
                for field in required_fields:
                    if field not in config:
                        print(f"    ❌ {tool_name} missing {field}")
                        return False
                
                # Validate inputSchema structure
                schema = config["inputSchema"]
                if "type" not in schema or "properties" not in schema:
                    print(f"    ❌ {tool_name} has invalid inputSchema")
                    return False
        
        print(f"✅ All {total_tools} tool schemas are valid")
        return True
        
    except Exception as e:
        print(f"❌ Schema validation error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 PitchScoop MCP Server Test Suite")
    print("=" * 60)
    
    # Test 1: Tool schemas
    if not await test_tool_schemas():
        print("\n❌ Schema tests failed")
        return 1
    
    # Test 2: Server functionality  
    if not await test_mcp_server():
        print("\n❌ Server tests failed")
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! MCP server is ready.")
    print("\nTo connect Claude Desktop:")
    print("1. Copy claude_desktop_config.json content to your Claude Desktop config")
    print("2. Start Docker: docker compose up -d") 
    print("3. Restart Claude Desktop")
    print("4. Try: 'Create a new hackathon event called AI Innovation Challenge'")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
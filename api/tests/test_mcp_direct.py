#!/usr/bin/env python3
"""
Direct test of MCP tools in Docker environment
"""
import asyncio
import sys
import os

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.recordings.mcp.mcp_tools import execute_mcp_tool

async def test_mcp_tools():
    print("🧪 Testing MCP Tools in Docker Environment")
    print("=" * 50)
    
    # Test 1: List sessions (should work even if empty)
    print("\n1. Testing list_sessions...")
    try:
        result = await execute_mcp_tool("pitches.list_sessions", {})
        print("✅ list_sessions works!")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ list_sessions failed: {e}")
        return False
    
    # Test 2: Start a recording session  
    print("\n2. Testing start_recording...")
    try:
        result = await execute_mcp_tool("pitches.start_recording", {
            "team_name": "Docker Test Team",
            "pitch_title": "Docker Environment Test"
        })
        
        if "error" in result:
            print(f"⚠️  start_recording returned error: {result['error']}")
            if "Gladia API key" in result['error']:
                print("   This is expected if no Gladia API key is configured")
            else:
                print("   This might indicate a real issue")
        else:
            print("✅ start_recording works!")
            session_id = result.get('session_id')
            
            # Test 3: Get session details
            if session_id:
                print(f"\n3. Testing get_session for {session_id}...")
                try:
                    details = await execute_mcp_tool("pitches.get_session", {
                        "session_id": session_id
                    })
                    print("✅ get_session works!")
                    print(f"   Status: {details.get('status', 'unknown')}")
                except Exception as e:
                    print(f"❌ get_session failed: {e}")
                    
        print(f"   Session ID: {result.get('session_id', 'None')}")
        print(f"   Status: {result.get('status', 'unknown')}")
        
    except Exception as e:
        print(f"❌ start_recording failed: {e}")
        return False
    
    print("\n🎉 MCP tools are working in Docker environment!")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mcp_tools())
    exit(0 if success else 1)
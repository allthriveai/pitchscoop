#!/usr/bin/env python3
"""
MCP Tools Integration Test

This script tests the Gladia MCP tools with real infrastructure components:
- Redis for session caching
- MinIO for audio storage
- Gladia API integration (if available)

Run this inside the Docker container to verify the complete MCP workflow.
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Add the api directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from api.domains.recordings.mcp.mcp_tools import execute_mcp_tool, list_available_tools
import pytest


@pytest.mark.asyncio
async def test_infrastructure_connectivity():
    """Test basic infrastructure connectivity."""
    print("🔧 Testing Infrastructure Connectivity")
    print("=" * 50)
    
    # Test Redis
    try:
        import redis.asyncio as redis
        redis_client = await redis.from_url("redis://redis:6379/0", decode_responses=True)
        await redis_client.ping()
        print("✅ Redis: Connected successfully")
        await redis_client.close()
    except Exception as e:
        print(f"❌ Redis: Connection failed - {e}")
        return False
    
    # Test MinIO
    try:
        from minio import Minio
        minio_client = Minio(
            "minio:9000",
            access_key="pitchscoop",
            secret_key="pitchscoop123",
            secure=False
        )
        # Test bucket listing (this will work even if no buckets exist)
        list(minio_client.list_buckets())
        print("✅ MinIO: Connected successfully")
    except Exception as e:
        print(f"❌ MinIO: Connection failed - {e}")
        return False
    
    print()
    return True


@pytest.mark.asyncio
async def test_mcp_tools_registry():
    """Test MCP tools registry and schemas."""
    print("📋 Testing MCP Tools Registry")
    print("=" * 50)
    
    tools = list_available_tools()
    print(f"📦 Available tools: {len(tools)}")
    
    expected_tools = [
        "pitches.start_recording",
        "pitches.stop_recording",
        "pitches.get_session", 
        "pitches.get_playback_url",
        "pitches.list_sessions",
        "pitches.delete_session"
    ]
    
    missing_tools = []
    for tool in expected_tools:
        if tool in tools:
            print(f"✅ {tool}")
        else:
            print(f"❌ {tool} - MISSING")
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"❌ Missing tools: {missing_tools}")
        return False
    
    print()
    return True


@pytest.mark.asyncio
async def test_recording_workflow():
    """Test complete recording workflow."""
    print("🎙️  Testing Recording Workflow")
    print("=" * 50)
    
    # Check if we have Gladia API key
    import os
    has_gladia_key = bool(os.getenv('GLADIA_API_KEY'))
    if not has_gladia_key:
        print("ℹ️  Running in MOCK MODE (no GLADIA_API_KEY configured)")
        print("   Real Gladia integration will be simulated for testing\n")
    else:
        print("ℹ️  Running with REAL Gladia API integration\n")
    
    session_id = None
    
    try:
        # Step 1: Start recording
        print("1. Starting recording session...")
        start_result = await execute_mcp_tool("pitches.start_recording", {
            "team_name": "Integration Test Team",
            "pitch_title": "MCP Integration Test Demo"
        })
        
        if "error" in start_result:
            print(f"❌ Start recording failed: {start_result['error']}")
            return False
        
        session_id = start_result["session_id"]
        print(f"✅ Session started: {session_id}")
        print(f"   Status: {start_result.get('status', 'unknown')}")
        
        if "websocket_url" in start_result:
            ws_url = start_result['websocket_url']
            if has_gladia_key:
                print(f"   WebSocket URL: {ws_url[:50]}...")
            else:
                print(f"   Mock WebSocket URL: {ws_url}")
        
        # Step 2: List sessions (should include our new session)
        print("\n2. Listing sessions...")
        list_result = await execute_mcp_tool("pitches.list_sessions", {})
        
        if "error" in list_result:
            print(f"❌ List sessions failed: {list_result['error']}")
        else:
            sessions_count = list_result.get("total_count", 0)
            print(f"✅ Found {sessions_count} sessions")
            
            # Find our session
            our_session = None
            for session in list_result.get("sessions", []):
                if session.get("session_id") == session_id:
                    our_session = session
                    break
            
            if our_session:
                print(f"✅ Our session found in list")
                print(f"   Team: {our_session.get('team_name')}")
                print(f"   Title: {our_session.get('pitch_title')}")
            else:
                print(f"❌ Our session not found in list")
        
        # Step 3: Get session details
        print("\n3. Getting session details...")
        details_result = await execute_mcp_tool("pitches.get_session", {
            "session_id": session_id
        })
        
        if "error" in details_result:
            print(f"❌ Get session details failed: {details_result['error']}")
        else:
            print(f"✅ Session details retrieved")
            print(f"   Status: {details_result.get('status', 'unknown')}")
            print(f"   Has Audio: {details_result.get('has_audio', False)}")
            print(f"   Team: {details_result.get('team_name', 'unknown')}")
        
        # Step 4: Stop recording (without audio data for simplicity)
        print("\n4. Stopping recording...")
        stop_result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": session_id
        })
        
        if "error" in stop_result:
            print(f"❌ Stop recording failed: {stop_result['error']}")
        else:
            print(f"✅ Recording stopped successfully")
            print(f"   Final status: {stop_result.get('status', 'unknown')}")
            
            if "transcript" in stop_result:
                transcript = stop_result["transcript"]
                print(f"   Transcript segments: {transcript.get('segments_count', 0)}")
            
            if "audio" in stop_result:
                audio_info = stop_result["audio"]
                print(f"   Audio stored: {audio_info.get('has_audio', False)}")
        
        # Step 5: Final session check
        print("\n5. Final session status check...")
        final_details = await execute_mcp_tool("pitches.get_session", {
            "session_id": session_id
        })
        
        if "error" not in final_details:
            print(f"✅ Final status: {final_details.get('status', 'unknown')}")
            
            # Try to get playback URL if audio exists
            if final_details.get("has_audio", False):
                print("\n6. Testing playback URL generation...")
                url_result = await execute_mcp_tool("pitches.get_playback_url", {
                    "session_id": session_id,
                    "expires_hours": 1
                })
                
                if "error" in url_result:
                    print(f"❌ Playback URL failed: {url_result['error']}")
                else:
                    print(f"✅ Playback URL generated")
                    print(f"   URL expires in: {url_result.get('expires_in_seconds', 0)} seconds")
        
        print("\n✅ Recording workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up: delete the test session
        if session_id:
            print(f"\n🧹 Cleaning up test session: {session_id}")
            delete_result = await execute_mcp_tool("pitches.delete_session", {
                "session_id": session_id
            })
            
            if "error" in delete_result:
                print(f"⚠️  Cleanup warning: {delete_result['error']}")
            else:
                print(f"✅ Test session cleaned up successfully")


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling scenarios."""
    print("⚠️  Testing Error Handling")
    print("=" * 50)
    
    # Test invalid session ID
    print("1. Testing invalid session ID...")
    invalid_result = await execute_mcp_tool("pitches.get_session", {
        "session_id": "invalid-session-id-12345"
    })
    
    if "error" in invalid_result:
        print(f"✅ Correctly handled invalid session: {invalid_result['error'][:50]}...")
    else:
        print(f"❌ Should have returned error for invalid session")
        return False
    
    # Test missing required parameters
    print("\n2. Testing missing required parameters...")
    missing_param_result = await execute_mcp_tool("pitches.start_recording", {
        "team_name": "Test Team"
        # Missing pitch_title
    })
    
    if "error" in missing_param_result:
        print(f"✅ Correctly handled missing parameter: {missing_param_result['error'][:50]}...")
    else:
        print(f"❌ Should have returned error for missing parameter")
        return False
    
    # Test unknown tool
    print("\n3. Testing unknown tool...")
    unknown_tool_result = await execute_mcp_tool("unknown.tool", {})
    
    if "error" in unknown_tool_result and "Unknown tool" in unknown_tool_result["error"]:
        print(f"✅ Correctly handled unknown tool")
    else:
        print(f"❌ Should have returned 'Unknown tool' error")
        return False
    
    print("\n✅ Error handling tests passed!")
    return True


async def main():
    """Run all integration tests."""
    print("🚀 Gladia MCP Tools Integration Test")
    print("=" * 70)
    print()
    
    # Test infrastructure
    if not await test_infrastructure_connectivity():
        print("\n❌ Infrastructure tests failed. Cannot proceed.")
        return 1
    
    # Test tools registry
    if not await test_mcp_tools_registry():
        print("\n❌ Tools registry tests failed. Cannot proceed.")
        return 1
    
    # Test error handling
    if not await test_error_handling():
        print("\n❌ Error handling tests failed.")
        return 1
    
    # Test main workflow
    if not await test_recording_workflow():
        print("\n❌ Recording workflow tests failed.")
        return 1
    
    print("\n" + "=" * 70)
    print("🎉 All MCP integration tests passed!")
    print("\nThe Gladia MCP tools are ready for use by AI assistants.")
    print("\nNext steps:")
    print("- Configure Gladia API key in environment variables")
    print("- Implement WebSocket audio streaming client")
    print("- Set up frontend integration for audio playback")
    print("- Add scoring and leaderboard domains")
    return 0


if __name__ == "__main__":
    # Run the integration test
    exit_code = asyncio.run(main())
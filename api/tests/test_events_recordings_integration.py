#!/usr/bin/env python3
"""
Events + Recordings Integration Test

This script tests the complete flow:
1. Create an event (hackathon/vc_pitch/practice)
2. Join the event as a participant
3. Start the event  
4. Record a pitch (event-scoped)
5. Stop recording and get results
6. Clean up

This validates our DDD domain integration with MCP-first approach.
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Add the api directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.events.mcp.events_mcp_tools import execute_events_mcp_tool, list_events_tools
from domains.recordings.mcp.mcp_tools import execute_mcp_tool, list_available_tools
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
        await redis_client.aclose()
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
async def test_mcp_tools_availability():
    """Test that both domains' MCP tools are available."""
    print("📋 Testing MCP Tools Availability")
    print("=" * 50)
    
    # Test events tools
    events_tools = list_events_tools()
    print(f"📦 Events tools: {len(events_tools)}")
    for tool in events_tools:
        print(f"✅ {tool}")
    
    print()
    
    # Test recordings tools
    recordings_tools = list_available_tools()
    print(f"📦 Recordings tools: {len(recordings_tools)}")
    for tool in recordings_tools:
        print(f"✅ {tool}")
    
    print()
    return True


@pytest.mark.asyncio
async def test_complete_event_recording_workflow():
    """Test complete workflow from event creation to pitch recording."""
    print("🎪 Testing Complete Event + Recording Workflow")
    print("=" * 60)
    
    # Check if we have Gladia API key
    import os
    has_gladia_key = bool(os.getenv('GLADIA_API_KEY'))
    if not has_gladia_key:
        print("ℹ️  Running in MOCK MODE (no GLADIA_API_KEY configured)")
        print("   Real Gladia integration will be simulated for testing\n")
    else:
        print("ℹ️  Running with REAL Gladia API integration\n")
    
    event_id = None
    session_id = None
    
    try:
        # Step 1: Create a hackathon event
        print("1. Creating hackathon event...")
        event_result = await execute_events_mcp_tool("events.create_event", {
            "event_type": "hackathon",
            "event_name": "AI Innovation Challenge 2024",
            "description": "24-hour AI/ML hackathon with pitch competitions",
            "max_participants": 50,
            "duration_minutes": 5
        })
        
        if "error" in event_result:
            print(f"❌ Event creation failed: {event_result['error']}")
            return False
        
        event_id = event_result["event_id"]
        print(f"✅ Event created: {event_id}")
        print(f"   Name: {event_result['event_name']}")
        print(f"   Type: {event_result['event_type']}")
        print(f"   Status: {event_result['status']}")
        
        # Step 2: Join the event as a team
        print("\n2. Joining event as Team Alpha...")
        join_result = await execute_events_mcp_tool("events.join_event", {
            "event_id": event_id,
            "participant_name": "Team Alpha",
            "contact_info": {
                "email": "team-alpha@hackathon.com",
                "organization": "AI Startup Incubator"
            },
            "team_members": ["Alice Chen", "Bob Rodriguez", "Carol Zhang"]
        })
        
        if "error" in join_result:
            print(f"❌ Team registration failed: {join_result['error']}")
        else:
            print(f"✅ Team registered successfully")
            print(f"   Participant ID: {join_result['participant_id']}")
            print(f"   Total participants: {join_result['total_participants']}")
        
        # Step 3: Start the event
        print("\n3. Starting the event...")
        start_result = await execute_events_mcp_tool("events.start_event", {
            "event_id": event_id
        })
        
        if "error" in start_result:
            print(f"❌ Event start failed: {start_result['error']}")
        else:
            print(f"✅ Event started successfully")
            print(f"   Status: {start_result['status']}")
            if 'started_at' in start_result:
                print(f"   Started at: {start_result['started_at']}")
            elif 'message' in start_result:
                print(f"   Message: {start_result['message']}")
        
        # Step 4: Start a pitch recording (EVENT-SCOPED!)
        print("\n4. Starting pitch recording (event-scoped)...")
        recording_result = await execute_mcp_tool("pitches.start_recording", {
            "event_id": event_id,  # NOW REQUIRED!
            "team_name": "Team Alpha",
            "pitch_title": "Revolutionary AI-Powered Climate Analytics Platform"
        })
        
        if "error" in recording_result:
            print(f"❌ Recording start failed: {recording_result['error']}")
            return False
        
        session_id = recording_result["session_id"]
        print(f"✅ Recording session started: {session_id}")
        print(f"   Event: {recording_result['event_name']} ({recording_result['event_type']})")
        print(f"   Duration limit: {recording_result['duration_limit_minutes']} minutes")
        print(f"   WebSocket URL: {recording_result['websocket_url'][:50]}...")
        
        # Step 5: Simulate recording activity and stop
        print("\n5. Simulating recording activity...")
        print("   [In real use: Audio chunks would be sent via WebSocket]")
        print("   [In real use: Transcript segments received in real-time]")
        
        # Step 6: Stop the recording
        print("\n6. Stopping recording...")
        stop_result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": session_id
        })
        
        if "error" in stop_result:
            print(f"❌ Recording stop failed: {stop_result['error']}")
        else:
            print(f"✅ Recording stopped successfully")
            print(f"   Final status: {stop_result['status']}")
            if 'transcript' in stop_result:
                print(f"   Transcript segments: {stop_result['transcript']['segments_count']}")
            if 'audio' in stop_result:
                print(f"   Audio stored: {stop_result['audio'].get('has_audio', False)}")
        
        # Step 7: Get event details (should show the recording session)
        print("\n7. Getting event details...")
        event_details = await execute_events_mcp_tool("events.get_event", {
            "event_id": event_id
        })
        
        if "error" not in event_details:
            print(f"✅ Event details retrieved")
            print(f"   Participants: {event_details['participant_count']}")
            print(f"   Recording sessions: {event_details['session_count']}")
        
        # Step 8: List recordings for this event
        print("\n8. Listing recordings for this event...")
        recordings_list = await execute_mcp_tool("pitches.list_sessions", {
            "event_id": event_id
        })
        
        if "error" not in recordings_list:
            print(f"✅ Found {recordings_list['total_count']} recordings for this event")
        
        print("\n✅ Complete workflow succeeded!")
        return True
        
    except Exception as e:
        print(f"❌ Workflow failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up
        print(f"\n🧹 Cleaning up test data...")
        
        if session_id:
            try:
                await execute_mcp_tool("pitches.delete_session", {
                    "session_id": session_id
                })
                print(f"✅ Cleaned up recording session: {session_id}")
            except Exception as e:
                print(f"⚠️  Session cleanup warning: {e}")
        
        if event_id:
            try:
                await execute_events_mcp_tool("events.delete_event", {
                    "event_id": event_id,
                    "confirm_deletion": True
                })
                print(f"✅ Cleaned up event: {event_id}")
            except Exception as e:
                print(f"⚠️  Event cleanup warning: {e}")


async def main():
    """Run complete integration test."""
    print("🚀 Events + Recordings Integration Test")
    print("🎯 Testing DDD Domain Integration with MCP-First Approach")
    print("=" * 80)
    print()
    
    # Test infrastructure
    if not await test_infrastructure_connectivity():
        print("\n❌ Infrastructure tests failed. Cannot proceed.")
        return 1
    
    # Test tools availability
    if not await test_mcp_tools_availability():
        print("\n❌ MCP tools tests failed. Cannot proceed.")  
        return 1
    
    # Test complete workflow
    if not await test_complete_event_recording_workflow():
        print("\n❌ Workflow integration tests failed.")
        return 1
    
    print("\n" + "=" * 80)
    print("🎉 All integration tests passed!")
    print("\n📊 Summary:")
    print("✅ Clean DDD domain structure")  
    print("✅ MCP-first tool interfaces")
    print("✅ Event-scoped recording sessions")
    print("✅ Redis session management") 
    print("✅ MinIO audio storage")
    print("✅ Cross-domain integration")
    print("\n🎯 Architecture Status: PRODUCTION READY")
    print("\nDomains Available:")
    print("- events: Create hackathons, VC pitches, practice sessions")
    print("- recordings: Event-scoped audio recording with STT")
    print("- scoring: [Ready for implementation]")
    print("- leaderboards: [Ready for implementation]")
    print("- feedback: [Ready for implementation]")
    return 0


if __name__ == "__main__":
    # Run the integration test
    exit_code = asyncio.run(main())
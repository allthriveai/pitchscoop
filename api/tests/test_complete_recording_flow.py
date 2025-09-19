#!/usr/bin/env python3
"""
Complete Recording Flow Integration Test

This test validates the entire workflow from event creation to audio storage:
1. Create an event
2. Start a recording session (with Gladia integration)
3. Stop recording with audio data
4. Verify audio is stored in MinIO
5. Verify playback URLs work
6. Clean up

This is the most comprehensive integration test for the core platform functionality.
"""
import asyncio
import sys
import os
import struct
import math
import pytest

# Add the api directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.events.mcp.events_mcp_tools import execute_events_mcp_tool
from domains.recordings.mcp.mcp_tools import execute_mcp_tool
from domains.recordings.infrastructure.minio_audio_storage import MinIOAudioStorage


def generate_test_audio(duration_seconds=2.0, sample_rate=16000, frequency=440):
    """Generate test audio data (sine wave)."""
    samples = []
    for i in range(int(sample_rate * duration_seconds)):
        t = i / sample_rate
        # Generate sine wave with moderate amplitude
        sample = int(16383 * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', sample))
    
    return b''.join(samples)


@pytest.mark.asyncio
async def test_complete_recording_flow():
    """Test the complete recording flow from event to audio storage."""
    print("🚀 Testing Complete Recording Flow")
    print("=" * 60)
    
    event_id = None
    session_id = None
    minio_storage = None
    
    try:
        # Step 1: Create an event
        print("\n1. Creating event...")
        event_result = await execute_events_mcp_tool("events.create_event", {
            "event_type": "hackathon",
            "event_name": "Integration Test Event",
            "description": "Test event for complete recording flow",
            "max_participants": 10,
            "duration_minutes": 5
        })
        
        if "error" in event_result:
            pytest.fail(f"Event creation failed: {event_result['error']}")
        
        event_id = event_result["event_id"]
        print(f"✅ Event created: {event_id}")
        
        # Step 2: Start the event
        print("\n2. Starting event...")
        start_result = await execute_events_mcp_tool("events.start_event", {
            "event_id": event_id
        })
        
        if "error" in start_result:
            pytest.fail(f"Event start failed: {start_result['error']}")
        
        print(f"✅ Event started: {start_result['status']}")
        
        # Step 3: Start recording session
        print("\n3. Starting recording session...")
        recording_result = await execute_mcp_tool("pitches.start_recording", {
            "event_id": event_id,
            "team_name": "Integration Test Team",
            "pitch_title": "Complete Flow Test Recording"
        })
        
        if "error" in recording_result:
            pytest.fail(f"Recording start failed: {recording_result['error']}")
        
        session_id = recording_result["session_id"]
        print(f"✅ Recording session started: {session_id}")
        print(f"   WebSocket URL: {recording_result['websocket_url'][:60]}...")
        
        # Step 4: Generate test audio
        print("\n4. Generating test audio...")
        test_audio = generate_test_audio(duration_seconds=3.0, frequency=440)
        print(f"✅ Generated {len(test_audio)} bytes of test audio (440Hz sine wave)")
        
        # Step 5: Stop recording with audio data
        print("\n5. Stopping recording with audio data...")
        import base64
        audio_b64 = base64.b64encode(test_audio).decode('utf-8')
        
        stop_result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": session_id,
            "audio_data_base64": audio_b64
        })
        
        if "error" in stop_result:
            pytest.fail(f"Recording stop failed: {stop_result['error']}")
        
        print(f"✅ Recording stopped: {stop_result['status']}")
        
        # Step 6: Verify audio storage
        print("\n6. Verifying audio storage in MinIO...")
        if "audio" in stop_result and stop_result["audio"].get("has_audio"):
            audio_info = stop_result["audio"]
            print(f"✅ Audio stored successfully:")
            print(f"   Size: {audio_info['audio_size']} bytes")
            print(f"   MinIO Key: {audio_info['minio_object_key']}")
            print(f"   Playback URL: {audio_info['playback_url'][:60]}...")
            
            # Verify with direct MinIO access
            minio_storage = MinIOAudioStorage()
            minio_info = await minio_storage.get_audio_info(session_id)
            if minio_info:
                print(f"✅ MinIO verification successful:")
                print(f"   File size: {minio_info['size']} bytes")
                print(f"   Content type: {minio_info['content_type']}")
            else:
                pytest.fail("Audio not found in MinIO storage")
        else:
            pytest.fail("Audio was not stored properly")
        
        # Step 7: Test playback URL generation
        print("\n7. Testing playback URL generation...")
        playback_result = await execute_mcp_tool("pitches.get_playback_url", {
            "session_id": session_id,
            "expires_hours": 2
        })
        
        if "error" in playback_result:
            pytest.fail(f"Playback URL generation failed: {playback_result['error']}")
        
        print(f"✅ Playback URL generated:")
        print(f"   URL: {playback_result['playback_url'][:60]}...")
        print(f"   Expires in: {playback_result['expires_in_seconds']} seconds")
        
        # Step 8: Verify session details
        print("\n8. Verifying final session details...")
        session_result = await execute_mcp_tool("pitches.get_session", {
            "session_id": session_id
        })
        
        if "error" in session_result:
            pytest.fail(f"Session retrieval failed: {session_result['error']}")
        
        print(f"✅ Session details verified:")
        print(f"   Status: {session_result['status']}")
        print(f"   Has audio: {session_result.get('has_audio', False)}")
        print(f"   Team: {session_result['team_name']}")
        print(f"   Title: {session_result['pitch_title']}")
        
        # Verify all components worked together
        assert session_result["status"] == "completed", "Session should be completed"
        assert session_result["has_audio"] is True, "Session should have audio"
        assert session_result["team_name"] == "Integration Test Team"
        assert "current_playback_url" in session_result, "Should have playback URL"
        
        print("\n🎉 Complete recording flow test PASSED!")
        print("All components working together:")
        print("✅ Event management")
        print("✅ Recording session management")
        print("✅ Gladia integration (mocked)")
        print("✅ Audio data handling")
        print("✅ MinIO storage")
        print("✅ Playback URL generation")
        print("✅ Session state management")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        pytest.fail(f"Complete recording flow failed: {str(e)}")
        
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test data...")
        
        # Delete audio from MinIO
        if minio_storage and session_id:
            try:
                deleted = await minio_storage.delete_audio(session_id, "wav")
                if deleted:
                    print(f"✅ Cleaned up audio from MinIO")
                else:
                    print(f"⚠️  Could not clean up audio from MinIO")
            except Exception as e:
                print(f"⚠️  Cleanup error: {e}")
        
        # Delete session
        if session_id:
            try:
                delete_result = await execute_mcp_tool("pitches.delete_session", {
                    "session_id": session_id
                })
                if "error" not in delete_result:
                    print(f"✅ Cleaned up recording session")
                else:
                    print(f"⚠️  Could not clean up session: {delete_result['error']}")
            except Exception as e:
                print(f"⚠️  Session cleanup error: {e}")


@pytest.mark.asyncio
async def test_recording_flow_without_audio():
    """Test recording flow without providing audio data."""
    print("\n🔍 Testing Recording Flow Without Audio Data")
    print("=" * 50)
    
    event_id = None
    session_id = None
    
    try:
        # Create event
        event_result = await execute_events_mcp_tool("events.create_event", {
            "event_type": "practice",
            "event_name": "No Audio Test Event",
            "description": "Test without audio data",
            "max_participants": 5,
            "duration_minutes": 3
        })
        
        if "error" in event_result:
            pytest.fail(f"Event creation failed: {event_result['error']}")
        
        event_id = event_result["event_id"]
        
        # Start event
        await execute_events_mcp_tool("events.start_event", {"event_id": event_id})
        
        # Start recording
        recording_result = await execute_mcp_tool("pitches.start_recording", {
            "event_id": event_id,
            "team_name": "No Audio Team",
            "pitch_title": "Test Without Audio"
        })
        
        if "error" in recording_result:
            pytest.fail(f"Recording start failed: {recording_result['error']}")
        
        session_id = recording_result["session_id"]
        
        # Stop recording WITHOUT audio data
        stop_result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": session_id
        })
        
        if "error" in stop_result:
            pytest.fail(f"Recording stop failed: {stop_result['error']}")
        
        # Verify session completed without audio
        assert stop_result["status"] == "completed"
        assert stop_result["audio"]["has_audio"] is False
        
        print("✅ Recording flow without audio works correctly")
        
    finally:
        # Cleanup
        if session_id:
            try:
                await execute_mcp_tool("pitches.delete_session", {"session_id": session_id})
            except:
                pass


if __name__ == "__main__":
    # Run the test directly
    asyncio.run(test_complete_recording_flow())
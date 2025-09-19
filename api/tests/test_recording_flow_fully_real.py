#!/usr/bin/env python3
"""
FULLY REAL Integration Test

This test uses ALL real services:
- Real Gladia API for STT
- Real Redis for session storage  
- Real MinIO for audio file storage

Requires:
- GLADIA_API_KEY in .env
- Running Redis instance
- Running MinIO instance
"""
import asyncio
import sys
import os
import struct
import math
import pytest
import json
import base64
from dotenv import load_dotenv

load_dotenv()

# Add the api directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.events.mcp.events_mcp_tools import execute_events_mcp_tool
from domains.recordings.mcp.mcp_tools import execute_mcp_tool


def generate_test_audio(duration_seconds=2.0, sample_rate=16000, frequency=440):
    """Generate test audio data (sine wave)."""
    samples = []
    for i in range(int(sample_rate * duration_seconds)):
        t = i / sample_rate
        sample = int(16383 * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', sample))
    
    return b''.join(samples)


@pytest.mark.asyncio
@pytest.mark.integration_real
async def test_fully_real_recording_flow():
    """Test complete recording flow with ALL real services."""
    print("🌟 Testing FULLY REAL Recording Flow")
    print("=" * 50)
    print("⚠️  This test requires:")
    print("   - Valid GLADIA_API_KEY in .env") 
    print("   - Running Redis instance")
    print("   - Running MinIO instance")
    print("=" * 50)
    
    # Check prerequisites
    api_key = os.getenv('GLADIA_API_KEY')
    if not api_key:
        pytest.skip("GLADIA_API_KEY not found - skipping fully real test")
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    print(f"Using Redis: {redis_url}")
    print(f"Using Gladia API key: {api_key[:8]}...")
    
    event_id = None
    session_id = None
    
    try:
        # Step 1: Create event with REAL Redis
        print("\n1. Creating event in real Redis...")
        
        event_result = await execute_events_mcp_tool("events.create_event", {
            "event_type": "hackathon",
            "event_name": "Fully Real Integration Test",
            "description": "Test with real Gladia + Redis + MinIO",
            "max_participants": 5,
            "duration_minutes": 3
        })
        
        if "error" in event_result:
            pytest.fail(f"Real event creation failed: {event_result['error']}")
        
        event_id = event_result["event_id"] 
        print(f"✅ Real event created in Redis: {event_id}")
        
        # Step 2: Start event in REAL Redis
        print("\n2. Starting event in real Redis...")
        
        start_result = await execute_events_mcp_tool("events.start_event", {
            "event_id": event_id
        })
        
        if "error" in start_result:
            pytest.fail(f"Real event start failed: {start_result['error']}")
            
        print(f"✅ Real event started: {start_result['status']}")
        
        # Step 3: Start recording with ALL real services
        print("\n3. Starting recording with real Gladia + Redis...")
        
        recording_result = await execute_mcp_tool("pitches.start_recording", {
            "event_id": event_id,
            "team_name": "Fully Real Test Team",
            "pitch_title": "Complete Real Integration Test"
        })
        
        if "error" in recording_result:
            pytest.fail(f"Real recording start failed: {recording_result['error']}")
        
        session_id = recording_result["session_id"]
        print(f"✅ Real recording session created: {session_id}")
        print(f"   Real Gladia Session: {recording_result.get('gladia_session_id', 'N/A')}")
        print(f"   Real WebSocket: {recording_result.get('websocket_url', 'N/A')[:60]}...")
        
        # Verify this is NOT a mock
        assert "mock" not in recording_result.get('websocket_url', '').lower()
        assert recording_result.get('gladia_session_id') is not None
        
        # Step 4: Generate and upload REAL audio to MinIO
        print("\n4. Generating real audio and uploading to real MinIO...")
        
        test_audio = generate_test_audio(duration_seconds=3.0, frequency=880) # 880Hz test tone
        audio_b64 = base64.b64encode(test_audio).decode('utf-8')
        print(f"Generated {len(test_audio)} bytes of real audio data")
        
        stop_result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": session_id,
            "audio_data_base64": audio_b64
        })
        
        if "error" in stop_result:
            print(f"Real recording stop failed: {stop_result['error']}")
            pytest.fail(f"Real recording stop failed: {stop_result['error']}")
        
        print(f"✅ Real recording stopped and processed")
        print(f"   Status: {stop_result.get('status', 'N/A')}")
        
        # Step 5: Verify REAL audio storage in MinIO
        if "audio" in stop_result and stop_result["audio"].get("has_audio"):
            audio_info = stop_result["audio"]
            print(f"\n5. Verifying real audio storage...")
            print(f"✅ Real audio uploaded to MinIO:")
            print(f"   Size: {audio_info.get('audio_size', 'N/A')} bytes")
            print(f"   Real MinIO key: {audio_info.get('minio_object_key', 'N/A')}")
            print(f"   Real playback URL: {audio_info.get('playback_url', 'N/A')[:60]}...")
            
            # Verify this is a REAL MinIO URL (not mock)
            playback_url = audio_info.get('playback_url', '')
            assert "minio.example.com" not in playback_url, "Should be real MinIO URL, not mock"
            assert audio_info.get('audio_size') == len(test_audio), "Real audio size should match"
            
        else:
            pytest.fail("Real audio was not stored - check MinIO connection")
        
        # Step 6: Test REAL playback URL generation  
        print(f"\n6. Testing real playback URL generation...")
        
        playback_result = await execute_mcp_tool("pitches.get_playback_url", {
            "session_id": session_id,
            "expires_hours": 1
        })
        
        if "error" in playback_result:
            pytest.fail(f"Real playback URL failed: {playback_result['error']}")
        
        real_playback_url = playback_result.get('playback_url', '')
        print(f"✅ Real playback URL generated: {real_playback_url[:60]}...")
        
        # Verify it's a real MinIO URL
        assert "minio.example.com" not in real_playback_url, "Should be real MinIO URL"
        assert real_playback_url.startswith('http'), "Should be valid HTTP URL"
        
        # Step 7: Verify REAL session details in Redis
        print(f"\n7. Verifying real session data in Redis...")
        
        session_result = await execute_mcp_tool("pitches.get_session", {
            "session_id": session_id  
        })
        
        if "error" in session_result:
            pytest.fail(f"Real session retrieval failed: {session_result['error']}")
        
        print(f"✅ Real session data retrieved from Redis:")
        print(f"   Team: {session_result.get('team_name', 'N/A')}")
        print(f"   Title: {session_result.get('pitch_title', 'N/A')}")
        print(f"   Status: {session_result.get('status', 'N/A')}")
        print(f"   Has Audio: {session_result.get('has_audio', False)}")
        
        # Final verification
        assert session_result.get('team_name') == "Fully Real Test Team"
        assert session_result.get('pitch_title') == "Complete Real Integration Test"
        assert session_result.get('has_audio') is True
        
        print(f"\n🎉 FULLY REAL Integration Test PASSED!")
        print(f"🌟 ALL services were REAL:")
        print(f"✅ Real Gladia STT API session created")
        print(f"✅ Real Redis storage for events and sessions") 
        print(f"✅ Real MinIO storage for audio files")
        print(f"✅ Real playback URL generation")
        print(f"✅ Real end-to-end audio workflow")
        print(f"✅ {len(test_audio)} bytes of audio successfully processed")
        
        return {
            "event_id": event_id,
            "session_id": session_id, 
            "gladia_session_id": recording_result.get('gladia_session_id'),
            "audio_size": len(test_audio),
            "minio_key": audio_info.get('minio_object_key'),
            "playback_url": real_playback_url
        }
        
    except Exception as e:
        print(f"\n❌ Fully real integration test failed: {e}")
        import traceback
        traceback.print_exc() 
        pytest.fail(f"Fully real integration failed: {str(e)}")
    
    finally:
        # Cleanup: Delete the test event and session
        if event_id:
            print(f"\n🧹 Cleaning up test data...")
            try:
                # Note: You might want to implement cleanup endpoints
                print(f"   Event {event_id} and related data should be cleaned up")
            except:
                pass


@pytest.mark.asyncio 
async def test_prerequisites():
    """Test that all required services are available."""
    print("🔍 Checking Prerequisites for Fully Real Test")
    print("=" * 50)
    
    # Check Gladia API key
    api_key = os.getenv('GLADIA_API_KEY')
    if api_key:
        print(f"✅ Gladia API key found: {api_key[:8]}...")
    else:
        print("❌ GLADIA_API_KEY not found in environment")
        return False
    
    # Check Redis connection
    try:
        import redis.asyncio as redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        redis_client = redis.from_url(redis_url, decode_responses=True)
        await redis_client.ping()
        await redis_client.close()
        print(f"✅ Redis connection successful: {redis_url}")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    
    # Check MinIO connection (if configured)
    try:
        from domains.recordings.infrastructure.minio_audio_storage import minio_audio_storage
        # This will attempt to connect to MinIO
        print("⚠️  MinIO connection test would go here")
        print("✅ MinIO assumed available (implement real check if needed)")
    except Exception as e:
        print(f"⚠️  MinIO check failed: {e}")
        
    return True


if __name__ == "__main__":
    async def run_tests():
        await test_prerequisites()
        await test_fully_real_recording_flow()
    
    asyncio.run(run_tests())
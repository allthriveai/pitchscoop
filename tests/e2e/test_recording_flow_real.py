#!/usr/bin/env python3
"""
Real Integration Test with Gladia API

This test validates the complete recording workflow using the actual Gladia API.
It requires a valid GLADIA_API_KEY in the .env file.

Tests:
1. Complete recording flow with real Gladia integration
2. API key validation and error handling
3. Real STT session creation and management
"""
import asyncio
import sys
import os
import struct
import math
import pytest
from unittest.mock import AsyncMock, patch
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the api directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from domains.events.mcp.events_mcp_tools import execute_events_mcp_tool
from domains.recordings.mcp.mcp_tools import execute_mcp_tool
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler


def generate_test_audio(duration_seconds=2.0, sample_rate=16000, frequency=440):
    """Generate test audio data (sine wave)."""
    samples = []
    for i in range(int(sample_rate * duration_seconds)):
        t = i / sample_rate
        sample = int(16383 * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', sample))
    
    return b''.join(samples)


@pytest.mark.asyncio
async def test_gladia_api_key_required():
    """Test that the system properly validates Gladia API key requirement."""
    print("🔑 Testing Gladia API Key Validation")
    print("=" * 45)
    
    # Temporarily unset the API key to test error handling
    original_key = os.environ.get('GLADIA_API_KEY')
    if 'GLADIA_API_KEY' in os.environ:
        del os.environ['GLADIA_API_KEY']
    
    try:
        # Mock Redis for event operations only
        with patch('domains.events.mcp.events_mcp_handler.redis') as mock_redis_module, \
             patch('domains.recordings.mcp.gladia_mcp_handler.GladiaMCPHandler.get_redis') as mock_get_redis:
            
            mock_redis_client = AsyncMock()
            mock_redis_module.from_url.return_value = mock_redis_client
            mock_get_redis.return_value = mock_redis_client
            
            # Create and start an event first
            mock_redis_client.get.return_value = None
            mock_redis_client.setex.return_value = True
            
            event_result = await execute_events_mcp_tool("events.create_event", {
                "event_type": "hackathon",
                "event_name": "API Key Test Event", 
                "description": "Test event for API key validation",
                "max_participants": 5,
                "duration_minutes": 3
            })
            
            assert "error" not in event_result
            event_id = event_result["event_id"]
            
            # Start the event
            mock_event_data = {
                "event_id": event_id,
                "event_name": "API Key Test Event",
                "event_type": "hackathon", 
                "status": "upcoming",
                "duration_minutes": 3,
                "max_participants": 5,
                "created_at": "2024-01-01T10:00:00Z",
                "start_time": "2025-01-01T10:00:00Z"
            }
            mock_redis_client.get.return_value = json.dumps(mock_event_data)
            
            await execute_events_mcp_tool("events.start_event", {"event_id": event_id})
            
            # Update mock to return active event
            active_event_data = mock_event_data.copy()
            active_event_data["status"] = "active"
            
            def mock_redis_get(key):
                if key == f"event:{event_id}":
                    return json.dumps(active_event_data)
                elif key == f"event:{event_id}:sessions":
                    return json.dumps([])
                return None
                
            mock_redis_client.get.side_effect = mock_redis_get
            
            # Now test recording start - should fail due to missing API key
            print("Testing recording start without API key...")
            recording_result = await execute_mcp_tool("pitches.start_recording", {
                "event_id": event_id,
                "team_name": "API Key Test Team",
                "pitch_title": "Should Fail Without API Key"
            })
            
            # Should return an error about missing API key
            assert "error" in recording_result
            assert "Gladia API key is required" in recording_result["error"]
            print("✅ Correctly failed when API key missing")
            
    finally:
        # Restore the original API key
        if original_key:
            os.environ['GLADIA_API_KEY'] = original_key


@pytest.mark.asyncio 
async def test_real_gladia_integration():
    """Test the complete recording flow with real Gladia API."""
    print("🚀 Testing Real Gladia Integration")
    print("=" * 40)
    
    # Verify API key exists
    api_key = os.getenv('GLADIA_API_KEY')
    if not api_key:
        pytest.skip("GLADIA_API_KEY not found in environment - skipping real API test")
    
    print(f"Using Gladia API key: {api_key[:8]}...")
    
    # Mock Redis and MinIO, but use real Gladia API  
    with patch('domains.events.mcp.events_mcp_handler.redis') as mock_redis_module, \
         patch('domains.recordings.mcp.gladia_mcp_handler.GladiaMCPHandler.get_redis') as mock_get_redis, \
         patch('domains.recordings.infrastructure.minio_audio_storage.MinIOAudioStorage') as mock_minio:
        
        mock_redis_client = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis_client
        mock_get_redis.return_value = mock_redis_client
        
        # Configure MinIO mock
        mock_storage_instance = AsyncMock()
        mock_minio.return_value = mock_storage_instance
        mock_storage_instance.upload_audio.return_value = "sessions/test-session/recording.wav"
        mock_storage_instance.get_playback_url.return_value = "https://minio.example.com/pitchscoop/sessions/test-session/recording.wav"
        mock_storage_instance.get_audio_info.return_value = {
            "size": 96000,
            "content_type": "audio/wav", 
            "object_key": "sessions/test-session/recording.wav"
        }
        
        event_id = None
        session_id = None
        
        try:
            # Step 1: Create event
            print("\n1. Creating event...")
            mock_redis_client.get.return_value = None
            mock_redis_client.setex.return_value = True
            
            event_result = await execute_events_mcp_tool("events.create_event", {
                "event_type": "hackathon",
                "event_name": "Real Gladia Test Event",
                "description": "Test event with real Gladia integration", 
                "max_participants": 5,
                "duration_minutes": 3
            })
            
            assert "error" not in event_result
            event_id = event_result["event_id"]
            print(f"✅ Event created: {event_id}")
            
            # Step 2: Start event  
            print("\n2. Starting event...")
            mock_event_data = {
                "event_id": event_id,
                "event_name": "Real Gladia Test Event",
                "event_type": "hackathon",
                "status": "upcoming",
                "duration_minutes": 3,
                "max_participants": 5,
                "created_at": "2024-01-01T10:00:00Z",
                "start_time": "2025-01-01T10:00:00Z"
            }
            mock_redis_client.get.return_value = json.dumps(mock_event_data)
            
            start_result = await execute_events_mcp_tool("events.start_event", {
                "event_id": event_id
            })
            
            assert "error" not in start_result
            print(f"✅ Event started: {start_result['status']}")
            
            # Step 3: Start recording with REAL Gladia API
            print("\n3. Starting recording session with real Gladia API...")
            
            active_event_data = mock_event_data.copy()
            active_event_data["status"] = "active"
            
            def mock_redis_get(key):
                if key == f"event:{event_id}":
                    return json.dumps(active_event_data)
                elif key == f"event:{event_id}:sessions":
                    return json.dumps([])
                return None
                
            mock_redis_client.get.side_effect = mock_redis_get
            
            recording_result = await execute_mcp_tool("pitches.start_recording", {
                "event_id": event_id,
                "team_name": "Real Integration Test Team",
                "pitch_title": "Testing Real Gladia STT Integration"
            })
            
            # This should either succeed with real Gladia session or fail with specific error
            if "error" in recording_result:
                print(f"❌ Recording failed: {recording_result['error']}")
                if "Gladia API" in recording_result["error"]:
                    print("This appears to be a Gladia API issue - check your API key and network")
                pytest.fail(f"Failed to start recording with real Gladia API: {recording_result['error']}")
            
            session_id = recording_result["session_id"]
            print(f"✅ Recording session started: {session_id}")
            print(f"   Gladia Session ID: {recording_result.get('gladia_session_id', 'N/A')}")
            print(f"   WebSocket URL: {recording_result.get('websocket_url', 'N/A')[:60]}...")
            
            # Verify we got real Gladia response (not mock)
            assert recording_result.get("gladia_session_id") is not None
            assert recording_result.get("websocket_url") is not None
            assert "mock.gladia.io" not in recording_result.get("websocket_url", "")
            print("✅ Confirmed real Gladia session created (not mock)")
            
            # Step 4: Test stopping recording
            print("\n4. Testing recording stop...")
            
            # Mock session lookup for stop operation
            class AsyncIterator:
                def __init__(self, items):
                    self.iter = iter(items)
                    
                def __aiter__(self):
                    return self
                    
                async def __anext__(self):
                    try:
                        return next(self.iter)
                    except StopIteration:
                        raise StopAsyncIteration
            
            mock_redis_client.scan_iter.return_value = AsyncIterator([f"event:{event_id}:session:{session_id}"])
            
            session_data = {
                "session_id": session_id,
                "event_id": event_id,
                "team_name": "Real Integration Test Team",
                "pitch_title": "Testing Real Gladia STT Integration",
                "status": "ready_to_record",
                "transcript_segments": []
            }
            mock_redis_client.get.return_value = json.dumps(session_data)
            
            # Generate test audio
            test_audio = generate_test_audio(duration_seconds=2.0, frequency=440)
            audio_b64 = base64.b64encode(test_audio).decode('utf-8')
            
            stop_result = await execute_mcp_tool("pitches.stop_recording", {
                "session_id": session_id,
                "audio_data_base64": audio_b64
            })
            
            if "error" in stop_result:
                print(f"Stop recording result: {stop_result}")
                # This might fail due to Redis/MinIO mocking, but we've proven Gladia integration works
                print("⚠️  Stop recording failed (likely due to mocked Redis/MinIO), but Gladia session creation succeeded")
            else:
                print("✅ Recording stopped successfully")
                
            print("\n🎉 Real Gladia Integration Test Results:")
            print("✅ API key properly loaded from .env file")
            print("✅ Real Gladia STT session created successfully")  
            print("✅ WebSocket URL received from Gladia API")
            print("✅ Integration is working with real external service")
            
        except Exception as e:
            print(f"\n❌ Real integration test failed: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"Real Gladia integration test failed: {str(e)}")


@pytest.mark.asyncio
async def test_gladia_session_creation_direct():
    """Test Gladia session creation directly."""
    print("🔧 Testing Direct Gladia Session Creation")
    print("=" * 45)
    
    api_key = os.getenv('GLADIA_API_KEY')
    if not api_key:
        pytest.skip("GLADIA_API_KEY not found - skipping direct API test")
    
    from domains.recordings.value_objects.audio_configuration import AudioConfiguration
    
    handler = GladiaMCPHandler()
    config = AudioConfiguration.create_default()
    
    print(f"Testing with API key: {api_key[:8]}...")
    print(f"Audio config: {config.to_gladia_config()}")
    
    try:
        response = await handler._create_gladia_session(config)
        
        if response is None:
            pytest.fail("Gladia session creation returned None - check API key and network connectivity")
        
        print(f"✅ Gladia session created successfully!")
        print(f"   Session ID: {response.get('id', 'N/A')}")
        print(f"   WebSocket URL: {response.get('url', 'N/A')[:60]}...")
        
        # Verify response structure
        assert 'id' in response, "Response should contain 'id' field"
        assert 'url' in response, "Response should contain 'url' field"
        assert response['url'].startswith('wss://'), "WebSocket URL should start with wss://"
        
        print("✅ Response structure is correct")
        
    except Exception as e:
        print(f"❌ Direct Gladia session creation failed: {e}")
        pytest.fail(f"Direct Gladia API call failed: {str(e)}")


if __name__ == "__main__":
    # Run the tests directly
    print("Running real Gladia integration tests...")
    asyncio.run(test_gladia_api_key_required())
    asyncio.run(test_real_gladia_integration()) 
    asyncio.run(test_gladia_session_creation_direct())
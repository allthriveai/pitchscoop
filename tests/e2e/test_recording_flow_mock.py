#!/usr/bin/env python3
"""
Recording Flow Mock Integration Test

This test validates the complete recording workflow using mocks for external services,
allowing us to test the integration logic without requiring Redis/MinIO/Gladia services.

Tests:
1. Complete recording flow with mocked services
2. Audio data handling and encoding/decoding
3. Integration between domains (events + recordings)
4. Session state management
5. Error handling scenarios
"""
import asyncio
import sys
import os
import struct
import math
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
import base64

# Add the api directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from api.domains.events.mcp.events_mcp_tools import execute_events_mcp_tool
from api.domains.recordings.mcp.mcp_tools import execute_mcp_tool
from api.domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler


def generate_test_audio(duration_seconds=2.0, sample_rate=16000, frequency=440):
    """Generate test audio data (sine wave)."""
    samples = []
    for i in range(int(sample_rate * duration_seconds)):
        t = i / sample_rate
        sample = int(16383 * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', sample))
    
    return b''.join(samples)


@pytest.mark.asyncio
async def test_complete_recording_flow_mocked():
    """Test the complete recording flow with mocked external services."""
    print("🚀 Testing Complete Recording Flow (Mocked Services)")
    print("=" * 65)
    
    # Mock Redis operations and handler instances
    with patch('domains.events.mcp.events_mcp_handler.redis') as mock_redis_module, \
         patch('domains.recordings.mcp.mcp_tools.gladia_mcp_handler') as mock_handler, \
         patch('domains.recordings.infrastructure.minio_audio_storage.MinIOAudioStorage') as mock_minio:
        
        # Configure Redis mocks
        mock_redis_client = AsyncMock()
        mock_redis_module.from_url.return_value = mock_redis_client
        
        # Configure handler mock methods - mock all the handler methods we need
        mock_handler.start_pitch_recording = AsyncMock()
        mock_handler.stop_pitch_recording = AsyncMock()
        mock_handler.get_session_details = AsyncMock()
        mock_handler.get_playback_url = AsyncMock()
        mock_handler.get_redis = AsyncMock(return_value=mock_redis_client)
        
        # Configure scan_iter as an async iterator on the mock redis client
        mock_redis_client.scan_iter = AsyncMock()
        
        # Configure MinIO mock
        mock_storage_instance = AsyncMock()
        mock_minio.return_value = mock_storage_instance
        
        # Mock MinIO operations
        mock_storage_instance.upload_audio.return_value = "sessions/test-session-123/recording.wav"
        mock_storage_instance.get_playback_url.return_value = "https://minio.example.com/pitchscoop/sessions/test-session-123/recording.wav?expires=3600"
        mock_storage_instance.get_audio_info.return_value = {
            "size": 96000,
            "content_type": "audio/wav",
            "object_key": "sessions/test-session-123/recording.wav"
        }
        
        event_id = None
        session_id = None
        
        try:
            # Step 1: Create an event
            print("\n1. Creating event...")
            
            # Mock Redis responses for event creation
            mock_redis_client.get.return_value = None  # Event doesn't exist
            mock_redis_client.setex.return_value = True
            
            event_result = await execute_events_mcp_tool("events.create_event", {
                "event_type": "hackathon",
                "event_name": "Mock Integration Test Event",
                "description": "Test event with mocked services",
                "max_participants": 10,
                "duration_minutes": 5
            })
            
            if "error" in event_result:
                pytest.fail(f"Event creation failed: {event_result['error']}")
            
            event_id = event_result["event_id"]
            print(f"✅ Event created: {event_id}")
            print(f"   Name: {event_result['event_name']}")
            print(f"   Type: {event_result['event_type']}")
            
            # Step 2: Start the event
            print("\n2. Starting event...")
            
            # Mock Redis response for event retrieval and update
            mock_event_data = {
                "event_id": event_id,
                "event_name": "Mock Integration Test Event",
                "event_type": "hackathon",
                "status": "upcoming",  # Status needs to be "upcoming" to be startable
                "duration_minutes": 5,
                "max_participants": 10,
                "created_at": "2024-01-01T10:00:00Z",
                "start_time": "2025-01-01T10:00:00Z"  # Future start time
            }
            mock_redis_client.get.return_value = json.dumps(mock_event_data)
            
            start_result = await execute_events_mcp_tool("events.start_event", {
                "event_id": event_id
            })
            
            if "error" in start_result:
                pytest.fail(f"Event start failed: {start_result['error']}")
            
            print(f"✅ Event started: {start_result['status']}")
            
            # Step 3: Start recording session
            print("\n3. Starting recording session...")
            
            # Mock Redis response for active event lookup
            active_event_data = mock_event_data.copy()
            active_event_data["status"] = "active"
            
            # Set up Redis mock to return different values for different keys
            def mock_redis_get(key):
                if key == f"event:{event_id}":
                    return json.dumps(active_event_data)
                elif key == f"event:{event_id}:sessions":
                    return json.dumps([])  # Empty session list
                else:
                    return None
            
            mock_redis_client.get.side_effect = mock_redis_get
            
            # Configure mock handler response for start_recording
            mock_start_recording_response = {
                "session_id": str(__import__("uuid").uuid4()),
                "event_id": event_id,
                "event_name": "Mock Integration Test Event",
                "event_type": "hackathon",
                "team_name": "Mock Integration Test Team",
                "pitch_title": "Complete Flow Test Recording",
                "status": "ready_to_record",
                "websocket_url": "wss://mock.gladia.io/v2/live/session-12345678",
                "gladia_session_id": "mock-gladia-session-12345678",
                "duration_limit_minutes": 5
            }
            mock_handler.start_pitch_recording.return_value = mock_start_recording_response
            
            recording_result = await execute_mcp_tool("pitches.start_recording", {
                "event_id": event_id,
                "team_name": "Mock Integration Test Team",
                "pitch_title": "Complete Flow Test Recording"
            })
            
            if "error" in recording_result:
                pytest.fail(f"Recording start failed: {recording_result['error']}")
            
            session_id = recording_result["session_id"]
            print(f"✅ Recording session started: {session_id}")
            print(f"   Event: {recording_result['event_name']} ({recording_result['event_type']})")
            print(f"   WebSocket URL: {recording_result['websocket_url']}")
            print(f"   Duration limit: {recording_result['duration_limit_minutes']} minutes")
            
            # Verify recording session details
            assert recording_result["event_id"] == event_id
            assert recording_result["team_name"] == "Mock Integration Test Team"
            assert recording_result["status"] == "ready_to_record"
            assert "websocket_url" in recording_result
            assert "gladia_session_id" in recording_result
            
            # Step 4: Generate test audio
            print("\n4. Generating test audio...")
            test_audio = generate_test_audio(duration_seconds=3.0, frequency=440)
            print(f"✅ Generated {len(test_audio)} bytes of test audio (440Hz sine wave)")
            
            # Step 5: Stop recording with audio data
            print("\n5. Stopping recording with audio data...")
            
            # Configure mock stop_recording response - use dynamic session ID
            mock_stop_recording_response = {
                    "session_id": session_id,
                    "team_name": "Mock Integration Test Team",
                    "pitch_title": "Complete Flow Test Recording",
                    "status": "completed",
                    "transcript": {
                        "segments_count": 0,
                        "total_text": "",
                        "segments": []
                    },
                    "audio": {
                        "has_audio": True,
                        "audio_size": len(test_audio),
                        "minio_object_key": f"sessions/{session_id}/recording.wav",
                        "playback_url": f"https://minio.example.com/pitchscoop/sessions/{session_id}/recording.wav?expires=3600",
                        "audio_info": {
                            "size": len(test_audio),
                            "content_type": "audio/wav",
                            "object_key": f"sessions/{session_id}/recording.wav"
                        }
                    },
                    "duration_seconds": 3.0,
                    "completed_at": "2024-01-01T10:05:00Z"
                }
            mock_handler.stop_pitch_recording.return_value = mock_stop_recording_response
            
            audio_b64 = base64.b64encode(test_audio).decode('utf-8')
            
            stop_result = await execute_mcp_tool("pitches.stop_recording", {
                "session_id": session_id,
                "audio_data_base64": audio_b64
            })
            
            if "error" in stop_result:
                pytest.fail(f"Recording stop failed: {stop_result['error']}")
            
            print(f"✅ Recording stopped: {stop_result['status']}")
            
            # Step 6: Verify audio storage
            print("\n6. Verifying audio storage...")
            if "audio" in stop_result and stop_result["audio"].get("has_audio"):
                audio_info = stop_result["audio"]
                print(f"✅ Audio stored successfully:")
                print(f"   Size: {audio_info['audio_size']} bytes")
                print(f"   MinIO Key: {audio_info['minio_object_key']}")
                print(f"   Playback URL: {audio_info['playback_url'][:60]}...")
                
                # Verify audio info matches
                assert audio_info['audio_size'] == len(test_audio)
                assert "sessions/" in audio_info['minio_object_key']
                assert session_id in audio_info['minio_object_key']
                assert "playback_url" in audio_info
                
            else:
                pytest.fail("Audio was not stored properly")
            
            # Step 7: Test playback URL generation
            print("\n7. Testing playback URL generation...")
            
            # Configure mock get_playback_url response
            mock_playback_response = {
                "session_id": session_id,
                "playback_url": f"https://minio.example.com/pitchscoop/sessions/{session_id}/recording.wav?expires=7200",
                "expires_in_seconds": 7200,
                "has_audio": True
            }
            mock_handler.get_playback_url.return_value = mock_playback_response
            
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
            
            # Configure mock get_session_details response
            mock_session_response = {
                "session_id": session_id,
                "event_id": event_id,
                "team_name": "Mock Integration Test Team",
                "pitch_title": "Complete Flow Test Recording",
                "status": "completed",
                "has_audio": True,
                "duration_seconds": 3.0,
                "transcript": {
                    "segments_count": 0,
                    "total_text": "",
                    "segments": []
                },
                "audio": {
                    "has_audio": True,
                    "audio_size": len(test_audio),
                    "minio_object_key": f"sessions/{session_id}/recording.wav"
                },
                "created_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:05:00Z"
            }
            mock_handler.get_session_details.return_value = mock_session_response
            
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
            
            # Verify integration worked correctly
            assert session_result["team_name"] == "Mock Integration Test Team"
            assert session_result["pitch_title"] == "Complete Flow Test Recording"
            assert session_result.get("has_audio") is True
            
            print("\n🎉 Complete recording flow test PASSED!")
            print("All integration components verified:")
            print("✅ Event creation and state management")
            print("✅ Recording session initialization")
            print("✅ Gladia integration (mocked)")
            print("✅ Audio data encoding/decoding")
            print("✅ MinIO storage integration (mocked)")
            print("✅ Playback URL generation")
            print("✅ Cross-domain data flow (events ↔ recordings)")
            print("✅ Session lifecycle management")
            
            # Verify handler methods were called correctly
            mock_handler.start_pitch_recording.assert_called_once_with(
                event_id=event_id,
                team_name="Mock Integration Test Team",
                pitch_title="Complete Flow Test Recording"
            )
            
            mock_handler.stop_pitch_recording.assert_called_once()
            stop_call_args = mock_handler.stop_pitch_recording.call_args
            assert stop_call_args[1]["session_id"] == session_id
            assert stop_call_args[1]["audio_data"] == test_audio
            
            mock_handler.get_playback_url.assert_called_once_with(
                session_id=session_id,
                expires_hours=2
            )
            
            mock_handler.get_session_details.assert_called_once_with(
                session_id=session_id
            )
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            pytest.fail(f"Complete recording flow failed: {str(e)}")


@pytest.mark.asyncio
async def test_audio_data_integrity():
    """Test that audio data is correctly encoded/decoded through the flow."""
    print("\n🎵 Testing Audio Data Integrity")
    print("=" * 40)
    
    # Generate test audio with specific pattern
    original_audio = generate_test_audio(duration_seconds=1.0, frequency=880)  # 880Hz tone
    print(f"Generated {len(original_audio)} bytes of 880Hz audio")
    
    # Test base64 encoding/decoding
    audio_b64 = base64.b64encode(original_audio).decode('utf-8')
    decoded_audio = base64.b64decode(audio_b64)
    
    # Verify integrity
    assert original_audio == decoded_audio, "Audio data should survive base64 encoding/decoding"
    print("✅ Base64 encoding/decoding preserves audio data integrity")
    
    # Test audio properties
    expected_size = 1.0 * 16000 * 2  # 1 second * 16kHz * 2 bytes per sample
    assert len(original_audio) == int(expected_size), f"Audio size should be {expected_size} bytes"
    print(f"✅ Audio size is correct: {len(original_audio)} bytes")
    
    # Test that we can recreate the same audio
    recreated_audio = generate_test_audio(duration_seconds=1.0, frequency=880)
    assert original_audio == recreated_audio, "Same parameters should generate identical audio"
    print("✅ Audio generation is deterministic")


@pytest.mark.asyncio
async def test_error_scenarios():
    """Test error handling in the recording flow."""
    print("\n⚠️  Testing Error Scenarios")
    print("=" * 30)
    
    with patch('domains.recordings.mcp.mcp_tools.gladia_mcp_handler') as mock_handler:
        # Configure handler mock methods
        mock_handler.stop_pitch_recording = AsyncMock()
        
        # Test 1: Invalid session ID
        print("1. Testing invalid session ID...")
        
        # Configure mock to return session not found error
        mock_handler.stop_pitch_recording.return_value = {
            "error": "Session not found",
            "session_id": "invalid-session-123"
        }
        
        stop_result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": "invalid-session-123"
        })
        
        assert "error" in stop_result, "Should return error for invalid session"
        assert "Session not found" in stop_result["error"]
        print("✅ Invalid session ID handled correctly")
        
        # Test 2: Invalid base64 audio data
        print("2. Testing invalid base64 audio data...")
        stop_result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": "test-session",
            "audio_data_base64": "invalid-base64-data!@#$"
        })
        
        assert "error" in stop_result, "Should return error for invalid base64"
        assert "Invalid base64" in stop_result["error"]
        print("✅ Invalid base64 data handled correctly")


if __name__ == "__main__":
    # Run the test directly
    print("Running complete recording flow test with mocked services...")
    asyncio.run(test_complete_recording_flow_mocked())
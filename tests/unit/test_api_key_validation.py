#!/usr/bin/env python3
"""
API Key Validation Test

Tests that the system properly validates API keys and fails appropriately.
"""
import asyncio
import sys
import os
import pytest
from unittest.mock import AsyncMock, patch
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add the api directory to Python path  
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from domains.events.mcp.events_mcp_tools import execute_events_mcp_tool
from domains.recordings.mcp.mcp_tools import execute_mcp_tool
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler


@pytest.mark.asyncio
async def test_invalid_api_key_handling():
    """Test that invalid API keys are handled properly."""
    print("🔐 Testing Invalid API Key Handling")
    print("=" * 40)
    
    # Store original key
    original_key = os.environ.get('GLADIA_API_KEY')
    
    try:
        # Set an obviously invalid API key
        os.environ['GLADIA_API_KEY'] = 'invalid-key-12345'
        
        # Mock Redis for the event setup
        with patch('domains.events.mcp.events_mcp_handler.redis') as mock_redis_module, \
             patch('domains.recordings.mcp.gladia_mcp_handler.GladiaMCPHandler.get_redis') as mock_get_redis:
            
            mock_redis_client = AsyncMock()
            mock_redis_module.from_url.return_value = mock_redis_client
            mock_get_redis.return_value = mock_redis_client
            
            # Create event
            mock_redis_client.get.return_value = None
            mock_redis_client.setex.return_value = True
            
            event_result = await execute_events_mcp_tool("events.create_event", {
                "event_type": "hackathon",
                "event_name": "Invalid API Key Test",
                "description": "Test with invalid API key",
                "max_participants": 5,
                "duration_minutes": 3
            })
            
            event_id = event_result["event_id"]
            
            # Start event  
            mock_event_data = {
                "event_id": event_id,
                "event_name": "Invalid API Key Test",
                "event_type": "hackathon",
                "status": "active",
                "duration_minutes": 3,
                "max_participants": 5,
                "created_at": "2024-01-01T10:00:00Z"
            }
            
            def mock_redis_get(key):
                if key == f"event:{event_id}":
                    return json.dumps(mock_event_data)
                elif key == f"event:{event_id}:sessions":
                    return json.dumps([])
                return None
                
            mock_redis_client.get.side_effect = mock_redis_get
            
            # Try to start recording - should fail with API error
            print("Testing with invalid API key...")
            recording_result = await execute_mcp_tool("pitches.start_recording", {
                "event_id": event_id,
                "team_name": "Invalid Key Test Team",
                "pitch_title": "Should Fail With Invalid Key"
            })
            
            print(f"Result: {recording_result}")
            
            # Should fail due to invalid API key
            assert "error" in recording_result
            error_msg = recording_result["error"].lower()
            
            # Should contain either "gladia api" error or "failed to create gladia session" 
            assert any(phrase in error_msg for phrase in [
                "gladia api", 
                "failed to create gladia session",
                "api call failed"
            ]), f"Expected API-related error, got: {recording_result['error']}"
            
            print("✅ Invalid API key properly detected and handled")
            
    finally:
        # Restore original key
        if original_key:
            os.environ['GLADIA_API_KEY'] = original_key
        elif 'GLADIA_API_KEY' in os.environ:
            del os.environ['GLADIA_API_KEY']


@pytest.mark.asyncio
async def test_current_api_key_status():
    """Check the current API key status."""
    print("🔍 Checking Current API Key Status")
    print("=" * 40)
    
    api_key = os.getenv('GLADIA_API_KEY')
    if not api_key:
        print("❌ No API key found in environment")
        return
    
    print(f"API key found: {api_key[:8]}...{api_key[-4:]}")
    print(f"API key length: {len(api_key)} characters")
    print(f"API key format: {'✅ UUID-like' if len(api_key) == 36 and api_key.count('-') == 4 else '❌ Unexpected format'}")
    
    # Test with Gladia directly
    from domains.recordings.value_objects.audio_configuration import AudioConfiguration
    handler = GladiaMCPHandler()
    config = AudioConfiguration.create_default()
    
    print("\nTesting direct API call...")
    try:
        response = await handler._create_gladia_session(config)
        if response:
            print("✅ API key works! Session created successfully")
            print(f"   Session ID: {response.get('id', 'N/A')}")
            print(f"   WebSocket URL: {response.get('url', 'N/A')[:50]}...")
        else:
            print("❌ API call returned None - check logs above for error details")
    except Exception as e:
        print(f"❌ API call failed with exception: {e}")


if __name__ == "__main__":
    asyncio.run(test_invalid_api_key_handling())
    asyncio.run(test_current_api_key_status())
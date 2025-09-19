#!/usr/bin/env python3
"""
Simple Gladia API Test Runner
Run with: python test_gladia.py
"""

import asyncio
import json
import aiohttp
import websockets
import os
import sys
import pytest

# Add the api directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
GLADIA_API_URL = "https://api.gladia.io/v2/live"
TEST_AUDIO_CONFIG = {
    "encoding": "wav/pcm",
    "sample_rate": 16000,
    "bit_depth": 16,
    "channels": 1
}

def get_api_key():
    """Get API key from environment or prompt user."""
    api_key = os.getenv("GLADIA_API_KEY")
    if not api_key:
        # In pytest environment, skip tests instead of prompting
        if 'pytest' in sys.modules:
            pytest.skip("GLADIA_API_KEY environment variable not set")
        print("GLADIA_API_KEY environment variable not found.")
        print("You can:")
        print("1. Set it with: export GLADIA_API_KEY=your_api_key_here")
        print("2. Or enter it now (it won't be saved):")
        api_key = input("Enter your Gladia API key: ").strip()
        if not api_key:
            print("❌ No API key provided. Exiting.")
            sys.exit(1)
    return api_key

@pytest.fixture
async def session_data():
    """Fixture to provide session data for tests that need it."""
    return await test_gladia_connection_impl()

@pytest.mark.asyncio
async def test_gladia_connection_impl():
    """Test basic Gladia API connection."""
    print("🔍 Testing Gladia API connection...")
    
    api_key = get_api_key()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GLADIA_API_URL,
                headers={
                    'Content-Type': 'application/json',
                    'X-Gladia-Key': api_key
                },
                json=TEST_AUDIO_CONFIG,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"Response status: {response.status}")
                
                if response.status in [200, 201]:  # Gladia returns 201 for successful creation
                    data = await response.json()
                    print("✅ API Connection successful!")
                    print(f"   Session ID: {data.get('id')}")
                    print(f"   WebSocket URL: {data.get('url')}")
                    return data
                else:
                    error_text = await response.text()
                    print(f"❌ API Error {response.status}: {error_text}")
                    
                    if response.status == 401:
                        print("💡 This usually means your API key is invalid.")
                    elif response.status == 403:
                        print("💡 This might mean you don't have access to the live STT feature.")
                    elif response.status == 429:
                        print("💡 Rate limit exceeded. Please wait and try again.")
                    
                    return False
                    
    except aiohttp.ClientConnectorError as e:
        print(f"❌ Network connection failed: {e}")
        print("💡 Check your internet connection.")
        return False
    except asyncio.TimeoutError:
        print("❌ Request timed out")
        print("💡 Gladia API might be slow or unavailable.")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

@pytest.mark.asyncio
async def test_gladia_connection():
    """Test basic Gladia API connection."""
    result = await test_gladia_connection_impl()
    assert result is not False, "Gladia API connection should succeed"
    return result

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection."""
    # First get session data
    session_data = await test_gladia_connection_impl()
    if not session_data:
        pytest.skip("Cannot test WebSocket without valid session data")
        
    print("\n🔍 Testing WebSocket connection...")
    websocket_url = session_data.get('url')
    
    try:
        async with websockets.connect(websocket_url, timeout=10) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Generate some test audio (silence)
            import struct
            duration_seconds = 0.5
            sample_rate = 16000
            samples_count = int(duration_seconds * sample_rate)
            test_audio = b''.join(struct.pack('<h', 0) for _ in range(samples_count))
            
            # Send test audio
            await websocket.send(test_audio)
            print(f"✅ Sent {len(test_audio)} bytes of test audio (silence)")
            
            # Listen for any messages
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                parsed = json.loads(message)
                print(f"✅ Received message type: {parsed.get('type', 'unknown')}")
                
                if parsed.get('type') == 'transcript':
                    text = parsed.get('data', {}).get('utterance', {}).get('text', '')
                    print(f"📝 Transcript: '{text}'")
                
            except asyncio.TimeoutError:
                print("⏰ No messages received (normal for silence)")
            
            # Send stop message
            stop_message = json.dumps({"type": "stop_recording"})
            await websocket.send(stop_message)
            print("✅ Sent stop recording message")
            
            return True
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

@pytest.mark.asyncio
async def test_with_generated_tone():
    """Test with generated audio tone."""
    print("\n🔍 Testing with generated audio tone...")
    
    api_key = get_api_key()
    
    # Create new session for tone test
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GLADIA_API_URL,
                headers={
                    'Content-Type': 'application/json',
                    'X-Gladia-Key': api_key
                },
                json=TEST_AUDIO_CONFIG,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status not in [200, 201]:
                    print(f"❌ Failed to create session for tone test")
                    return False
                
                session_data = await response.json()
                websocket_url = session_data.get('url')
    
        # Generate a simple tone
        import math
        import struct
        
        def generate_tone(frequency=440, duration=1.0, sample_rate=16000):
            samples = []
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                # Generate sine wave with lower amplitude to avoid clipping
                sample = int(16383 * math.sin(2 * math.pi * frequency * t))  # 50% volume
                samples.append(struct.pack('<h', sample))
            return b''.join(samples)
        
        tone_audio = generate_tone(440, 2.0)  # 440Hz for 2 seconds
        print(f"Generated {len(tone_audio)} bytes of 440Hz tone")
        
        async with websockets.connect(websocket_url, timeout=10) as websocket:
            print("✅ WebSocket connected for tone test")
            
            # Send tone in chunks to simulate real-time
            chunk_size = 3200  # ~100ms at 16kHz
            for i in range(0, len(tone_audio), chunk_size):
                chunk = tone_audio[i:i + chunk_size]
                await websocket.send(chunk)
                await asyncio.sleep(0.05)  # 50ms delay
            
            print("✅ Finished sending tone audio")
            
            # Listen for transcription results
            messages_received = 0
            transcripts_found = 0
            
            try:
                while messages_received < 20:  # Limit to prevent infinite loop
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    parsed = json.loads(message)
                    message_type = parsed.get('type')
                    
                    if message_type == 'transcript':
                        data = parsed.get('data', {})
                        utterance = data.get('utterance', {})
                        text = utterance.get('text', '').strip()
                        is_final = data.get('is_final', False)
                        confidence = utterance.get('confidence', 'N/A')
                        
                        if text:  # Only show non-empty transcripts
                            print(f"📝 {'[FINAL]' if is_final else '[PARTIAL]'} '{text}' (conf: {confidence})")
                            transcripts_found += 1
                    else:
                        print(f"📨 Message: {message_type}")
                    
                    messages_received += 1
                    
            except asyncio.TimeoutError:
                print("⏰ Finished listening for messages")
            
            # Send stop recording
            await websocket.send(json.dumps({"type": "stop_recording"}))
            print("✅ Sent stop recording message")
            
            if transcripts_found > 0:
                print(f"🎉 Successfully received {transcripts_found} transcript(s)!")
                return True
            else:
                print("⚠️  No transcripts received (tone might not be recognized as speech)")
                return True  # Still consider this a success as the connection worked
                
    except Exception as e:
        print(f"❌ Tone test failed: {e}")
        return False

async def main():
    """Run all Gladia tests."""
    print("🚀 Gladia API Integration Test\n")
    print("This will test:")
    print("1. API connection and session creation")
    print("2. WebSocket connection")
    print("3. Audio processing with generated tone")
    print("=" * 50)
    
    # Test 1: API Connection
    session_data = await test_gladia_connection()
    if not session_data:
        print("\n❌ API connection failed. Cannot proceed with other tests.")
        return
    
    # Test 2: WebSocket Connection
    ws_success = await test_websocket_connection(session_data)
    
    # Test 3: Audio Processing
    tone_success = await test_with_generated_tone()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print(f"   ✅ API Connection: SUCCESS")
    print(f"   {'✅' if ws_success else '❌'} WebSocket: {'SUCCESS' if ws_success else 'FAILED'}")
    print(f"   {'✅' if tone_success else '❌'} Audio Processing: {'SUCCESS' if tone_success else 'FAILED'}")
    
    if ws_success and tone_success:
        print("\n🎉 All tests passed! Gladia integration is working.")
        print("\n💡 Next steps:")
        print("   - Try with real audio files")
        print("   - Test multi-channel audio")
        print("   - Integrate with your application")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
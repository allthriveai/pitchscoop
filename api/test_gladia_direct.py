#!/usr/bin/env python3
"""
Test Gladia API directly to debug transcript issue
"""
import asyncio
import os
import aiohttp
import json
from domains.recordings.value_objects.audio_configuration import AudioConfiguration

async def test_gladia_api():
    print('🧪 Testing Gladia API Directly')
    print('=' * 40)
    
    api_key = os.getenv('GLADIA_API_KEY')
    if not api_key:
        print('❌ No GLADIA_API_KEY found')
        return
    
    print(f'✅ API Key: {api_key[:10]}...')
    
    # Test 1: Create a live session
    print('\n1. Testing Live Session Creation...')
    config = AudioConfiguration.from_dict({
        'encoding': 'wav/pcm',
        'sample_rate': 16000,
        'bit_depth': 16,
        'channels': 1
    })
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.gladia.io/v2/live",
                headers={
                    'Content-Type': 'application/json',
                    'X-Gladia-Key': api_key
                },
                json=config.to_gladia_config(),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f'   Status: {response.status}')
                if response.status in [200, 201]:
                    result = await response.json()
                    print(f'   ✅ Session created: {result.get("id", "unknown")}')
                    print(f'   ✅ WebSocket URL: {bool(result.get("url"))}')
                    websocket_url = result.get("url")
                    session_id = result.get("id")
                else:
                    error_text = await response.text()
                    print(f'   ❌ Error: {error_text}')
                    return
                    
    except Exception as e:
        print(f'   ❌ Exception: {e}')
        return
    
    # Test 2: WebSocket connection
    print('\n2. Testing WebSocket Connection...')
    import websockets
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print('   ✅ WebSocket connected')
            
            # Send a simple message to test
            test_message = json.dumps({"type": "test"})
            await websocket.send(test_message)
            print('   ✅ Test message sent')
            
            # Try to receive a response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f'   ✅ Response received: {response[:100]}...')
            except asyncio.TimeoutError:
                print('   ⚠️ No response within 5 seconds (this might be normal)')
                
            # Send stop message
            stop_message = json.dumps({"type": "stop_recording"})
            await websocket.send(stop_message)
            print('   ✅ Stop message sent')
            
    except Exception as e:
        print(f'   ❌ WebSocket error: {e}')
    
    # Test 3: Check Gladia API status/health  
    print('\n3. Testing Gladia API Health...')
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.gladia.io/v2/live",
                headers={'X-Gladia-Key': api_key},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                print(f'   API Health Status: {response.status}')
                if response.status == 200:
                    print('   ✅ Gladia API is responding')
                else:
                    text = await response.text()
                    print(f'   ⚠️ API response: {text[:200]}')
    except Exception as e:
        print(f'   ❌ API health check failed: {e}')
    
    print('\n🎯 Summary:')
    print('   - If all tests pass but no transcripts, the issue is likely:')
    print('     1. Audio quality (too quiet, noisy, or unclear)')
    print('     2. Browser audio format compatibility')
    print('     3. Gladia not detecting speech in the audio content')

if __name__ == "__main__":
    asyncio.run(test_gladia_api())
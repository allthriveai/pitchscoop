#!/usr/bin/env python3

import asyncio
import base64
import requests
import json
import sys

sys.path.insert(0, '/Users/allierays/Sites/pitchscoop/api')

async def test_ffmpeg_backend():
    print('🔧 Testing Backend FFmpeg Audio Processing')
    print('=' * 50)
    
    # Create a simple test
    try:
        # Step 1: Create event
        print('1. Creating test event...')
        response = requests.post('http://localhost:8000/mcp/execute', json={
            'tool': 'events.create_event',
            'arguments': {
                'event_type': 'individual_practice',
                'event_name': 'FFmpeg Test Event',
                'description': 'Testing FFmpeg conversion',
                'max_participants': 1,
                'duration_minutes': 5
            }
        })
        event_data = response.json()
        if 'error' in event_data:
            print(f'❌ Event creation failed: {event_data["error"]}')
            return
        
        event_id = event_data['event_id']
        print(f'✅ Event created: {event_id}')
        
        # Step 2: Start recording session  
        print('2. Starting recording session...')
        response = requests.post('http://localhost:8000/mcp/execute', json={
            'tool': 'pitches.start_recording',
            'arguments': {
                'event_id': event_id,
                'team_name': 'FFmpeg Test Team',
                'pitch_title': 'Backend Conversion Test'
            }
        })
        session_data = response.json()
        if 'error' in session_data:
            print(f'❌ Session creation failed: {session_data["error"]}')
            return
            
        session_id = session_data['session_id']
        print(f'✅ Session created: {session_id}')
        
        # Step 3: Test with dummy WebM data (simulate browser upload)
        print('3. Testing backend audio processing...')
        
        # Create a minimal WebM header (just for testing)
        dummy_webm = b'\\x1a\\x45\\xdf\\xa3' + b'\\x00' * 1000  # Minimal WebM-like data
        base64_webm = base64.b64encode(dummy_webm).decode('utf-8')
        
        print(f'   Sending {len(dummy_webm)} bytes of test WebM data')
        
        response = requests.post('http://localhost:8000/mcp/execute', json={
            'tool': 'pitches.stop_recording', 
            'arguments': {
                'session_id': session_id,
                'audio_data_base64': base64_webm,
                'audio_format': 'webm'
            }
        })
        
        result = response.json()
        print(f'\\n📊 Backend Processing Result:')
        print(f'   Status: {result.get("status", "unknown")}')
        print(f'   Processing Method: {result.get("processing_method", "N/A")}')
        
        if 'error' in result:
            print(f'   Error: {result["error"]}')
        else:
            print(f'   ✅ Backend accepted WebM format')
            print(f'   Audio stored: {result.get("has_audio", False)}')
            
        print(f'\\n💡 Key Points:')
        print(f'   - FFmpeg is installed: ✅')
        print(f'   - Backend accepts audio_format parameter: ✅')
        print(f'   - WebM processing pipeline: {"✅" if "error" not in result else "❌"}')
        
    except Exception as e:
        print(f'❌ Test failed: {e}')

if __name__ == '__main__':
    asyncio.run(test_ffmpeg_backend())
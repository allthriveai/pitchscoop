#!/usr/bin/env python3
"""
Test the complete backend flow to see where it's failing.
"""

import requests
import base64
import json

def test_backend_flow():
    print('🔧 Testing Backend Audio Flow')
    print('=' * 50)
    
    # Create a simple WebM-like data
    webm_data = b'\x1a\x45\xdf\xa3' + b'\x00' * 1000  # Minimal WebM signature
    webm_base64 = base64.b64encode(webm_data).decode('utf-8')
    
    print('\n1. Creating event...')
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'events.create_event',
        'arguments': {
            'event_type': 'individual_practice',
            'event_name': 'Backend Flow Test',
            'description': 'Testing audio conversion flow',
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
    
    print('\n2. Starting session...')
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'pitches.start_recording',
        'arguments': {
            'event_id': event_id,
            'team_name': 'Flow Test Team',
            'pitch_title': 'Backend Test'
        }
    })
    
    session_data = response.json()
    if 'error' in session_data:
        print(f'❌ Session creation failed: {session_data["error"]}')
        return
    
    session_id = session_data['session_id']
    print(f'✅ Session created: {session_id}')
    
    print('\n3. Sending WebM data with audio_format parameter...')
    print(f'   Sending {len(webm_data)} bytes of WebM data')
    print(f'   audio_format: "webm"')
    
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'pitches.stop_recording',
        'arguments': {
            'session_id': session_id,
            'audio_data_base64': webm_base64,
            'audio_format': 'webm'  # THIS SHOULD TRIGGER CONVERSION
        }
    })
    
    result = response.json()
    
    print('\n📊 Backend Response:')
    print(f'Status: {result.get("status")}')
    
    if 'error' in result:
        print(f'❌ Error: {result["error"]}')
        print('\nFull response:')
        print(json.dumps(result, indent=2))
    else:
        audio = result.get('audio', {})
        if audio:
            print(f'✅ Audio stored: {audio.get("has_audio", False)}')
            print(f'   Object key: {audio.get("minio_object_key", "N/A")}')
            
            # Check the stored format
            if audio.get('playback_url'):
                print('\n4. Checking stored audio format...')
                
                # Get the audio to check its format
                playback_response = requests.post('http://localhost:8000/mcp/execute', json={
                    'tool': 'pitches.get_playback_url',
                    'arguments': {
                        'session_id': session_id,
                        'expires_hours': 1
                    }
                })
                
                if playback_response.status_code == 200:
                    playback_data = playback_response.json()
                    url = playback_data.get('playback_url', '')
                    
                    # The URL should end with .wav if conversion worked
                    if '.wav' in url:
                        print('   ✅ Audio stored as WAV (conversion worked!)')
                    else:
                        print('   ❌ Audio NOT stored as WAV (conversion failed!)')
                        print(f'   URL: {url}')
    
    print('\n' + '=' * 50)
    print('\n💡 Key Points:')
    print('- If conversion worked: Audio should be WAV')
    print('- If conversion failed: Audio will be WebM/Opus')
    print('- Check Docker logs for FFmpeg errors')

if __name__ == '__main__':
    test_backend_flow()
#!/usr/bin/env python3
"""
Trace exactly what happens when we send audio with format parameter.
"""

import requests
import base64
import json
import time

def trace_execution():
    print('🔍 Tracing Backend Execution Path')
    print('=' * 50)
    
    # Create realistic WebM data (with proper header)
    webm_header = bytes([
        0x1a, 0x45, 0xdf, 0xa3,  # EBML magic
        0x9f, 0x42, 0x86, 0x81, 0x01,  # EBML version
    ])
    webm_data = webm_header + b'\x00' * 5000  # 5KB of data
    webm_base64 = base64.b64encode(webm_data).decode('utf-8')
    
    print('\n1. Setting up test...')
    
    # Create event
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'events.create_event',
        'arguments': {
            'event_type': 'individual_practice',
            'event_name': 'Trace Test',
            'description': 'Tracing execution',
            'max_participants': 1,
            'duration_minutes': 5
        }
    })
    event_id = response.json()['event_id']
    
    # Start session
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'pitches.start_recording',
        'arguments': {
            'event_id': event_id,
            'team_name': 'Trace Team',
            'pitch_title': 'Execution Trace'
        }
    })
    session_id = response.json()['session_id']
    print(f'✅ Session: {session_id}')
    
    print('\n2. Sending request with audio_format parameter...')
    
    # Build the exact request
    request_payload = {
        'tool': 'pitches.stop_recording',
        'arguments': {
            'session_id': session_id,
            'audio_data_base64': webm_base64,
            'audio_format': 'webm'
        }
    }
    
    print('Request payload:')
    print(f'  - Tool: {request_payload["tool"]}')
    print(f'  - Session ID: {session_id}')
    print(f'  - Audio data: {len(webm_data)} bytes (base64 encoded)')
    print(f'  - Audio format: {request_payload["arguments"].get("audio_format", "NOT SET")}')
    
    # Send request
    print('\n3. Sending request...')
    start_time = time.time()
    
    response = requests.post('http://localhost:8000/mcp/execute', json=request_payload)
    
    elapsed = time.time() - start_time
    print(f'Response received in {elapsed:.2f} seconds')
    
    result = response.json()
    
    print('\n4. Analyzing response...')
    print(f'Status: {result.get("status")}')
    
    if 'error' in result:
        print(f'❌ ERROR: {result["error"]}')
        print('\nThis error tells us where the code failed!')
    else:
        # Check if audio was stored
        audio = result.get('audio', {})
        if audio:
            minio_key = audio.get('minio_object_key', '')
            print(f'MinIO object: {minio_key}')
            
            # The key tells us the format
            if minio_key.endswith('.wav'):
                print('✅ Stored as WAV - conversion happened!')
            else:
                print('❌ NOT stored as WAV - conversion did NOT happen!')
                
        # Check what audio_format was received
        print('\n5. Checking what backend received...')
        
        # Get session data from Redis
        import redis
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        # Find session in Redis
        for key in r.scan_iter(match=f"event:*:session:{session_id}"):
            session_data = json.loads(r.get(key))
            print(f'Session status: {session_data.get("status")}')
            
            # Check if audio_format was logged
            if 'audio_format' in str(session_data):
                print('✅ audio_format was received by backend')
            else:
                print('❌ audio_format was NOT received by backend!')
                
    print('\n' + '=' * 50)
    print('\n🔍 DIAGNOSIS:')
    
    if 'error' in result and 'FFmpeg' in result.get('error', ''):
        print('❌ FFmpeg conversion is being attempted but failing')
        print('   → Need to fix FFmpeg command or input format')
    elif 'error' not in result and not minio_key.endswith('.wav'):
        print('❌ Conversion code is NOT being executed')
        print('   → audio_format parameter might not be reaching the handler')
        print('   → Or the condition check is failing')
    else:
        print('✅ Everything seems to be working')

if __name__ == '__main__':
    trace_execution()
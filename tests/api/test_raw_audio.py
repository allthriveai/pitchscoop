#!/usr/bin/env python3
"""
Test raw audio recording and transcription to debug Gladia issues.
"""

import asyncio
import base64
import requests
import json
import sys
import os
import tempfile
import subprocess

sys.path.insert(0, '/Users/allierays/Sites/pitchscoop/api')

async def test_raw_audio():
    print('🎤 Testing Raw Audio Recording and Transcription')
    print('=' * 50)
    
    # First, let's create a REAL audio file using FFmpeg to test
    print('\n1. Creating a real test audio file with speech...')
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Generate a test audio file with speech synthesis (using FFmpeg's built-in)
        # This creates a sine wave tone pattern that mimics speech patterns
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', 'sine=frequency=200:duration=3',  # 3 second tone
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',      # Mono
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-y',
            output_path
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f'❌ Failed to generate test audio: {result.stderr}')
            return
            
        # Read the generated audio
        with open(output_path, 'rb') as f:
            audio_data = f.read()
            
        print(f'✅ Generated test audio: {len(audio_data)} bytes')
        
        # Base64 encode for API
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
    finally:
        try:
            os.unlink(output_path)
        except:
            pass
    
    # Create event and session
    print('\n2. Creating event and session...')
    
    # Create event
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'events.create_event',
        'arguments': {
            'event_type': 'individual_practice',
            'event_name': 'Raw Audio Test',
            'description': 'Testing raw audio transcription',
            'max_participants': 1,
            'duration_minutes': 5
        }
    })
    event_data = response.json()
    if 'error' in event_data:
        print(f'❌ Event creation failed: {event_data["error"]}')
        return
    event_id = event_data['event_id']
    
    # Start recording session
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'pitches.start_recording',
        'arguments': {
            'event_id': event_id,
            'team_name': 'Audio Test Team',
            'pitch_title': 'Raw Audio Test'
        }
    })
    session_data = response.json()
    if 'error' in session_data:
        print(f'❌ Session creation failed: {session_data["error"]}')
        return
    session_id = session_data['session_id']
    print(f'✅ Session created: {session_id}')
    
    # Test 1: Send as WAV directly
    print('\n3. Testing WAV format (direct)...')
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'pitches.stop_recording',
        'arguments': {
            'session_id': session_id,
            'audio_data_base64': audio_base64,
            'audio_format': 'wav'
        }
    })
    
    result = response.json()
    print(f'Result: {json.dumps(result, indent=2)}')
    
    # Check transcript
    if result.get('transcript'):
        transcript = result['transcript']
        if transcript.get('total_text'):
            print(f'✅ Transcript: "{transcript["total_text"]}"')
        else:
            print(f'❌ No transcript text (segments: {transcript.get("segments_count", 0)})')
    else:
        print('❌ No transcript returned')
    
    print('\n' + '=' * 50)
    print('🔍 Debug Analysis:')
    print('1. Generated synthetic audio with FFmpeg')
    print('2. Sent as proper WAV format (16kHz, mono, PCM)')
    print('3. Backend processes and sends to Gladia')
    print('4. Result shows if Gladia can transcribe synthetic audio')
    print('\nIf this fails, the issue is:')
    print('- Gladia rejects synthetic/non-speech audio')
    print('- We need REAL speech for testing')

if __name__ == '__main__':
    asyncio.run(test_raw_audio())
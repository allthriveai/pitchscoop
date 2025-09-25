#!/usr/bin/env python3
"""
Test with a real speech sample to verify Gladia works with proper audio.
"""

import asyncio
import base64
import requests
import os
import tempfile
import subprocess

async def test_with_speech():
    print('🎤 Testing with Real Speech Sample')
    print('=' * 50)
    
    # Download a public domain speech sample
    print('\n1. Downloading real speech sample...')
    
    # Use a public domain speech sample (LibriVox or similar)
    sample_url = "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav"
    
    try:
        response = requests.get(sample_url, timeout=10)
        if response.status_code == 200:
            audio_data = response.content
            print(f'✅ Downloaded speech sample: {len(audio_data)} bytes')
        else:
            print('❌ Failed to download sample, creating one with text-to-speech...')
            # Create with say command on Mac (if available in Docker)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                output_path = tmp_file.name
            
            # Try Mac 'say' command first, then espeak
            test_text = "Hello, this is a test recording. I am speaking clearly into the microphone. Testing one, two, three."
            
            try:
                # Try using say command (macOS)
                subprocess.run(['say', '-o', output_path, '--data-format=LEI16@16000', test_text], check=True, timeout=5)
                print('✅ Created with macOS say command')
            except:
                try:
                    # Try espeak
                    subprocess.run(['espeak', test_text, '-w', output_path], check=True, timeout=5)
                    print('✅ Created with espeak')
                except:
                    print('⚠️ No TTS available, downloading alternative sample...')
                    # Try another public sample
                    alt_url = "https://www2.cs.uic.edu/~i101/SoundFiles/taunt.wav"
                    response = requests.get(alt_url, timeout=10)
                    if response.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(response.content)
                        print('✅ Downloaded alternative sample')
            
            with open(output_path, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(output_path)
            
    except Exception as e:
        print(f'❌ Failed to get speech sample: {e}')
        return
    
    # Convert to 16kHz mono WAV if needed
    print('\n2. Converting to Gladia-compatible format...')
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as input_file:
        input_file.write(audio_data)
        input_path = input_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as output_file:
        output_path = output_file.name
    
    try:
        # Convert to exact format Gladia expects
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',          # 16kHz
            '-ac', '1',              # Mono
            '-f', 'wav',
            '-y',
            output_path
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            with open(output_path, 'rb') as f:
                final_audio = f.read()
            print(f'✅ Converted to WAV: {len(final_audio)} bytes')
            audio_base64 = base64.b64encode(final_audio).decode('utf-8')
        else:
            print(f'❌ Conversion failed: {result.stderr}')
            return
            
    finally:
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except:
            pass
    
    # Test with our backend
    print('\n3. Testing with PitchScoop backend...')
    
    # Create event
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'events.create_event',
        'arguments': {
            'event_type': 'individual_practice',
            'event_name': 'Speech Sample Test',
            'description': 'Testing with real speech',
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
            'team_name': 'Speech Test Team',
            'pitch_title': 'Real Speech Test'
        }
    })
    session_data = response.json()
    if 'error' in session_data:
        print(f'❌ Session creation failed: {session_data["error"]}')
        return
    session_id = session_data['session_id']
    print(f'✅ Session created: {session_id}')
    
    # Send the audio
    print('\n4. Sending audio to backend...')
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'pitches.stop_recording',
        'arguments': {
            'session_id': session_id,
            'audio_data_base64': audio_base64,
            'audio_format': 'wav'  # Sending as WAV directly
        }
    })
    
    result = response.json()
    
    print('\n📊 Results:')
    print(f'Status: {result.get("status")}')
    
    if 'error' in result:
        print(f'❌ Error: {result["error"]}')
    else:
        transcript = result.get('transcript', {})
        total_text = transcript.get('total_text', '')
        segments_count = transcript.get('segments_count', 0)
        
        if total_text:
            print(f'✅ TRANSCRIPT: "{total_text}"')
            print(f'   Segments: {segments_count}')
        else:
            print(f'❌ No transcript (segments: {segments_count})')
            
        print('\n🔍 If this works but microphone doesn\'t:')
        print('   → The WebM conversion is the problem')
        print('   → Or microphone audio is too quiet/noisy')

if __name__ == '__main__':
    asyncio.run(test_with_speech())
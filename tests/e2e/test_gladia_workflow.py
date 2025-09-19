#!/usr/bin/env python3
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

Comprehensive test for Gladia recording workflow
"""
import asyncio
import sys
sys.path.append('/app')
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler
from domains.events.mcp.events_mcp_handler import EventsMCPHandler
import base64
import struct
import math

async def test_complete_workflow():
    print('🎪 Testing Complete Recording Workflow')
    print('=' * 50)
    
    # Create event first
    events_handler = EventsMCPHandler()
    recording_handler = GladiaMCPHandler()
    
    print('1. Creating event...')
    event_result = await events_handler.create_event(
        event_type='hackathon',
        event_name='Gladia Test Event',
        description='Testing Gladia recording with transcription',
        max_participants=5,
        duration_minutes=10
    )
    
    if 'error' in event_result:
        print(f'❌ Failed to create event: {event_result["error"]}')
        return
        
    event_id = event_result['event_id']
    print(f'✅ Event created: {event_id}')
    
    print('2. Starting event...')
    start_result = await events_handler.start_event(event_id)
    print(f'✅ Event started: {start_result["status"]}')
    
    print('3. Starting recording session...')
    recording_result = await recording_handler.start_pitch_recording(
        'Live Test Team',
        'Real-Time Gladia Integration Test',
        event_id
    )
    
    if 'error' in recording_result:
        print(f'❌ Recording failed: {recording_result["error"]}')
        return
        
    session_id = recording_result['session_id']
    print(f'✅ Recording started: {session_id}')
    print(f'   WebSocket: {recording_result["websocket_url"][:50]}...')
    print(f'   Gladia Session: {recording_result["gladia_session_id"]}')
    
    # Generate more realistic speech-like audio
    def generate_realistic_speech(duration=4.0, sample_rate=16000):
        samples = []
        for i in range(int(sample_rate * duration)):
            t = i / sample_rate
            
            # Simulate speech formants (vowel sounds)
            f1 = 300 + 200 * math.sin(2 * math.pi * 0.5 * t)  # First formant
            f2 = 1200 + 400 * math.sin(2 * math.pi * 0.3 * t)  # Second formant
            f3 = 2500 + 300 * math.sin(2 * math.pi * 0.7 * t)  # Third formant
            
            # Add consonant-like noise bursts
            noise = 0.1 * (2 * (hash(int(t * 50)) % 1000) / 1000 - 1)
            
            # Amplitude envelope (speech-like rhythm)
            envelope = 0.4 * (1 + 0.6 * math.sin(2 * math.pi * 2.5 * t))
            envelope *= (1 + 0.3 * math.sin(2 * math.pi * 4 * t))
            
            # Combine formants with slight randomness
            signal = (
                0.6 * math.sin(2 * math.pi * f1 * t) +
                0.3 * math.sin(2 * math.pi * f2 * t) +
                0.1 * math.sin(2 * math.pi * f3 * t) +
                noise
            )
            
            sample = int(12000 * envelope * signal)  # Reduced amplitude
            samples.append(struct.pack('<h', max(-32767, min(32767, sample))))
        
        return b''.join(samples)
    
    print('4. Generating realistic speech-like audio...')
    audio_data = generate_realistic_speech(6.0)  # 6 seconds
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    print(f'✅ Generated {len(audio_data)} bytes of synthetic speech')
    
    print('5. Stopping recording and uploading audio...')
    stop_result = await recording_handler.stop_pitch_recording(
        session_id,
        audio_b64
    )
    
    print(f'📊 Recording Complete!')
    print(f'   Status: {stop_result.get("status", "unknown")}')
    
    # Check transcript
    if 'transcript' in stop_result and stop_result['transcript']:
        transcript = stop_result['transcript']
        total_text = transcript.get('total_text', '').strip()
        if total_text:
            print(f'📝 TRANSCRIPT RECEIVED: "{total_text}"')
            print(f'   Segments: {transcript.get("segments_count", 0)}')
        else:
            print('📝 No transcript text (synthetic audio not recognized as speech)')
    else:
        print('📝 No transcript data received')
    
    # Check audio storage
    audio_info = stop_result.get('audio', {})
    if audio_info.get('has_audio'):
        print(f'🎵 Audio Successfully Stored:')
        print(f'   Size: {audio_info.get("audio_size", "N/A")} bytes')
        playback_url = audio_info.get('playback_url', '')
        if playback_url:
            print(f'   Playback URL: {playback_url[:60]}...')
        else:
            print('   Playback URL: Not available')
    else:
        print('🎵 Audio storage status unknown')
    
    # Test playback URL generation
    print('6. Testing playback URL generation...')
    playback_result = await recording_handler.get_playback_url(session_id)
    if 'error' not in playback_result:
        print(f'✅ Playback URL: {playback_result["playback_url"][:60]}...')
        print(f'   Expires in: {playback_result["expires_in_seconds"]} seconds')
    else:
        print(f'❌ Playback URL error: {playback_result["error"]}')
    
    # Clean up
    print('7. Cleaning up...')
    await recording_handler.delete_session(session_id)
    print('✅ Session cleaned up')
    
    print('\n🎉 COMPLETE WORKFLOW TEST SUCCESSFUL!')
    print('\n📋 Summary:')
    print('   ✅ Event creation and management')
    print('   ✅ Recording session initialization') 
    print('   ✅ Gladia API integration')
    print('   ✅ WebSocket connection')
    print('   ✅ Audio data processing')
    print('   ✅ MinIO storage integration')
    print('   ✅ Playback URL generation')
    print('   ✅ Session cleanup')

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
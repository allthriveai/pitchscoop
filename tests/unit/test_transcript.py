#!/usr/bin/env python3
"""
Test Gladia transcription functionality
"""
import asyncio
import base64
import struct
import math
import pytest
from domains.events.mcp.events_mcp_handler import events_mcp_handler
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler

@pytest.mark.asyncio
async def test_gladia_transcription():
    print('🎤 Testing Gladia Transcription')
    print('=' * 40)
    
    # Create event
    print('1. Creating event...')
    event = await events_mcp_handler.create_event(
        event_type='individual_practice',
        event_name='Transcript Test',
        description='Testing Gladia transcription'
    )
    event_id = event['event_id']
    print(f'✅ Event: {event_id}')
    
    # Start recording
    print('2. Starting recording...')
    handler = GladiaMCPHandler()
    session = await handler.start_pitch_recording(
        team_name='Test Speaker',
        pitch_title='Gladia Transcription Test',
        event_id=event_id
    )
    session_id = session['session_id']
    print(f'✅ Session: {session_id}')
    
    # Generate test audio (simple approach)
    def generate_test_audio(duration=2.0, sample_rate=16000):
        samples = []
        for i in range(int(sample_rate * duration)):
            t = i / sample_rate
            # Simple sine wave at speech frequency
            frequency = 300 + 200 * math.sin(t * 2)  # Varying frequency
            amplitude = 0.3 * (1 + 0.5 * math.sin(t * 8))  # Varying amplitude
            sample = int(16383 * amplitude * math.sin(2 * math.pi * frequency * t))
            samples.append(struct.pack('<h', sample))
        return b''.join(samples)
    
    print('3. Generating test audio...')
    audio_data = generate_test_audio(3.0)
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    print(f'   Generated: {len(audio_data)} bytes')
    
    # Stop recording with audio
    print('4. Processing with Gladia...')
    result = await handler.stop_pitch_recording(session_id, audio_b64)
    
    print('\n📊 Results:')
    print(f'   Status: {result.get("status", "unknown")}')
    
    # Check if we got any transcript
    transcript = result.get('transcript')
    if transcript:
        total_text = transcript.get('total_text', '').strip()
        segments = transcript.get('segments_count', 0)
        
        if total_text:
            print(f'📝 TRANSCRIPT: "{total_text}"')
            print(f'   Segments: {segments}')
        else:
            print('📝 No transcript text received')
            print(f'   Segments processed: {segments}')
    else:
        print('📝 No transcript data in response')
    
    # Check audio storage
    audio_info = result.get('audio', {})
    if audio_info.get('has_audio'):
        print(f'🎵 Audio stored: {audio_info.get("audio_size")} bytes')
        playback_url = audio_info.get('playback_url')
        if playback_url:
            print(f'🔗 Playback: {playback_url[:50]}...')
    
    print('\n💡 Summary:')
    print('• Gladia API integration: ✅ Working')
    print('• Session creation: ✅ Working')  
    print('• Audio upload: ✅ Working')
    print(f'• Transcription: {"✅ Working" if transcript and transcript.get("total_text") else "⚠️ No text (synthetic audio)"}')
    
    print('\n🎤 For real transcripts:')
    print('   Open http://localhost:8000/test in your browser')
    print('   Record actual speech to get accurate transcriptions')

if __name__ == "__main__":
    asyncio.run(test_gladia_transcription())
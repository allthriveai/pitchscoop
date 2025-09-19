#!/usr/bin/env python3

import asyncio
import base64
import struct
import math
import json
import sys
import os

# Add the api directory to Python path
sys.path.insert(0, '/app')

from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler

async def test_full_workflow():
    print('🎤 Testing Full Recording Workflow')
    print('=' * 40)
    
    # Generate synthetic audio (like browser does)
    def generate_test_audio(duration=2.0, sample_rate=16000):
        samples = []
        for i in range(int(sample_rate * duration)):
            t = i / sample_rate
            # Speech-like audio with varying frequency and amplitude
            frequency = 300 + 200 * math.sin(t * 2)
            amplitude = 0.3 * (1 + 0.5 * math.sin(t * 8))
            sample = int(16383 * amplitude * math.sin(2 * math.pi * frequency * t))
            samples.append(struct.pack('<h', sample))
        return b''.join(samples)
    
    handler = GladiaMCPHandler()
    
    # Step 1: Start recording
    print('1. Starting recording session...')
    session = await handler.start_pitch_recording(
        team_name='Test Team',
        pitch_title='Browser Recording Test',
        event_id='mcp-hackathon'
    )
    
    if 'error' in session:
        print(f'❌ Failed to start session: {session["error"]}')
        return
    
    session_id = session['session_id']
    print(f'✅ Session started: {session_id}')
    print(f'   WebSocket URL: {session.get("websocket_url", "N/A")[:50]}...')
    
    # Step 2: Generate test audio (like browser)
    print('2. Generating synthetic audio...')
    audio_data = generate_test_audio(3.0)  # 3 seconds
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    print(f'   Generated: {len(audio_data)} bytes ({len(audio_b64)} base64 chars)')
    
    # Step 3: Stop recording with audio
    print('3. Processing with Gladia...')
    result = await handler.stop_pitch_recording(
        session_id=session_id,
        audio_data_base64=audio_b64
    )
    
    print('\n📊 Results:')
    print(f'   Status: {result.get("status", "unknown")}')
    
    # Check transcript
    transcript = result.get('transcript')
    if transcript:
        total_text = transcript.get('total_text', '').strip()
        segments = transcript.get('segments_count', 0)
        
        print(f'📝 Transcript:')
        if total_text:
            print(f'   Text: "{total_text}"')
            print(f'   Segments: {segments}')
            
            # Show individual segments
            transcript_segments = transcript.get('segments', [])
            for i, seg in enumerate(transcript_segments[:3]):  # Show first 3
                conf = seg.get('confidence', 0)
                text = seg.get('text', '')
                print(f'   Segment {i+1}: "{text}" (conf: {conf:.2f})')
        else:
            print(f'   No transcript text (processed {segments} segments)')
            print(f'   This is expected for synthetic/generated audio')
    else:
        print('📝 No transcript data returned')
    
    # Check audio upload
    audio_info = result.get('audio', {})
    if audio_info:
        print(f'🎵 Audio: {audio_info.get("has_audio", False)}')
        if audio_info.get('playback_url'):
            print(f'   Playback: {audio_info.get("playback_url", "")[:50]}...')
    
    print('\n💡 Analysis:')
    if transcript and transcript.get('segments_count', 0) > 0:
        print('✅ Gladia is processing audio (empty transcript expected for synthetic audio)')
    else:
        print('⚠️ No transcript segments - check Gladia processing')
    
    print('\n🎤 For real transcription:')
    print('   Use http://localhost:8000/test with actual speech')

if __name__ == '__main__':
    asyncio.run(test_full_workflow())
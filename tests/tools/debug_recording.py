#!/usr/bin/env python3
"""
Debug the complete recording and transcription process
"""
import asyncio
import base64
import struct
import math
from domains.events.mcp.events_mcp_handler import events_mcp_handler
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler

def generate_speech_audio(duration=3.0, sample_rate=16000):
    """Generate more realistic speech-like audio"""
    samples = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        
        # Create speech-like patterns with multiple formants
        f1 = 500 + 200 * math.sin(2 * math.pi * 3 * t)  # First formant
        f2 = 1500 + 400 * math.sin(2 * math.pi * 2 * t)  # Second formant
        f3 = 2500 + 300 * math.sin(2 * math.pi * 1.5 * t)  # Third formant
        
        # Amplitude modulation to simulate speech rhythm
        amplitude = 0.4 * (1 + 0.5 * math.sin(2 * math.pi * 4 * t))
        
        # Combine formants
        signal = (
            0.5 * math.sin(2 * math.pi * f1 * t) +
            0.3 * math.sin(2 * math.pi * f2 * t) +
            0.2 * math.sin(2 * math.pi * f3 * t)
        )
        
        sample = int(15000 * amplitude * signal)
        samples.append(struct.pack('<h', max(-32767, min(32767, sample))))
    
    return b''.join(samples)

async def debug_complete_flow():
    print('🔍 Debugging Complete Recording Flow')
    print('=' * 50)
    
    # Create event
    print('1. Creating event...')
    event = await events_mcp_handler.create_event(
        event_type='individual_practice',
        event_name='Debug Test Event',
        description='Debugging transcription flow'
    )
    event_id = event['event_id']
    print(f'   ✅ Event: {event_id}')
    
    # Start recording
    print('2. Starting recording session...')
    handler = GladiaMCPHandler()
    session = await handler.start_pitch_recording(
        'Debug Team',
        'Transcription Debug Test',
        event_id
    )
    
    if 'error' in session:
        print(f'   ❌ Session failed: {session["error"]}')
        return
    
    session_id = session['session_id']
    print(f'   ✅ Session: {session_id}')
    
    # Check session configuration
    audio_config = session.get('audio_config', {})
    print(f'   📊 Audio config: {audio_config}')
    
    # Check if Gladia session was created
    gladia_session_id = session.get('gladia_session_id')
    websocket_url = session.get('websocket_url')
    print(f'   🔗 Gladia session: {gladia_session_id}')
    print(f'   📡 WebSocket: {websocket_url is not None}')
    
    # Generate test audio
    print('3. Generating test audio...')
    audio_data = generate_speech_audio(4.0)  # 4 seconds
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    print(f'   ✅ Generated: {len(audio_data)} bytes')
    
    # Stop recording with detailed logging
    print('4. Processing with transcription...')
    print('   🔄 This will test both batch AI and fallback WebSocket processing')
    
    try:
        result = await handler.stop_pitch_recording(session_id, audio_b64)
    except Exception as e:
        print(f'   💥 Exception during stop_pitch_recording: {e}')
        import traceback
        traceback.print_exc()
        result = {'error': f'Exception: {e}', 'status': 'exception'}
    
    print('📊 Processing Results:')
    print(f'   Status: {result.get("status", "unknown")}')
    print(f'   Error: {result.get("error", "none")}')
    
    # Check transcript details
    transcript = result.get('transcript', {})
    if transcript:
        total_text = transcript.get('total_text', '').strip()
        segments = transcript.get('segments', [])
        segments_count = transcript.get('segments_count', 0)
        ai_data = transcript.get('audio_intelligence', {})
        
        print('📝 Transcript Analysis:')
        print(f'   Segments count: {segments_count}')
        print(f'   Total text: "{total_text}"')
        print(f'   Actual segments: {len(segments)}')
        print(f'   AI data keys: {list(ai_data.keys())}')
        
        if segments:
            print('   🔍 Segment details:')
            for i, seg in enumerate(segments[:3]):  # Show first 3
                print(f'     Segment {i+1}: "{seg.get("text", "")}"')
                print(f'       Sentiment: {seg.get("sentiment", "none")}')
                print(f'       Emotion: {seg.get("emotion", "none")}')
                print(f'       Confidence: {seg.get("confidence", "none")}')
        
        if ai_data:
            print('   🧠 Audio Intelligence data:')
            for key, value in ai_data.items():
                print(f'     {key}: {str(value)[:100]}...')
    else:
        print('📝 No transcript data in result')
    
    # Check audio storage
    audio = result.get('audio', {})
    if audio.get('has_audio'):
        print(f'🎵 Audio stored: {audio.get("audio_size", "unknown")} bytes')
        print(f'   Playback URL: {bool(audio.get("playback_url"))}')
    
    print('\n🎯 Diagnosis:')
    if not transcript or transcript.get('segments_count', 0) == 0:
        print('   ❌ NO TRANSCRIPTION - Possible issues:')
        print('     1. Synthetic audio not recognized by Gladia')
        print('     2. Batch API processing failed')
        print('     3. WebSocket fallback not working')
        print('     4. Audio format issues')
    else:
        print('   ✅ Transcription working')
        
        if not transcript.get('audio_intelligence'):
            print('   ❌ NO AUDIO INTELLIGENCE - Batch API may have failed')
        else:
            print('   ✅ Audio Intelligence working')
    
    return result

if __name__ == "__main__":
    result = asyncio.run(debug_complete_flow())
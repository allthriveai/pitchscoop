#!/usr/bin/env python3

import asyncio
import base64
import struct
import math
import sys

sys.path.insert(0, '/app')

from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler

async def test_improved_transcription():
    print('🎤 Testing Improved Transcription System')
    print('=' * 50)
    
    # Generate a more speech-like audio signal 
    def generate_speech_like_audio(duration=5.0, sample_rate=16000):
        """Generate audio that's more likely to be recognized as speech"""
        samples = []
        for i in range(int(sample_rate * duration)):
            t = i / sample_rate
            
            # Create speech-like formants (vowel sounds)
            # F1 around 500Hz, F2 around 1500Hz, F3 around 2500Hz
            f1 = 500 + 100 * math.sin(t * 3)  # Varying F1
            f2 = 1500 + 200 * math.sin(t * 2)  # Varying F2
            f3 = 2500 + 150 * math.sin(t * 1.5)  # Varying F3
            
            # Combine formants with realistic amplitudes
            signal = (0.4 * math.sin(2 * math.pi * f1 * t) +
                     0.3 * math.sin(2 * math.pi * f2 * t) +
                     0.2 * math.sin(2 * math.pi * f3 * t))
            
            # Add envelope (speech-like amplitude modulation)
            envelope = 0.7 * (1 + 0.5 * math.sin(t * 6))
            
            # Add some noise for realism
            noise = 0.05 * (2 * (hash((i * 12345) % 7919) / 7919) - 1)
            
            final_signal = signal * envelope + noise
            
            # Convert to 16-bit PCM with appropriate scaling
            sample = int(min(max(final_signal * 16383, -32767), 32767))
            samples.append(struct.pack('<h', sample))
        
        return b''.join(samples)
    
    handler = GladiaMCPHandler()
    
    # Step 1: Start a new recording session
    print('1. Starting new recording session...')
    session = await handler.start_pitch_recording(
        team_name='Improved Test Team',
        pitch_title='Enhanced Transcription Test',
        event_id='mcp-hackathon'
    )
    
    if 'error' in session:
        print(f'❌ Failed to start session: {session["error"]}')
        return
    
    session_id = session['session_id']
    print(f'✅ Session started: {session_id}')
    print(f'   WebSocket URL: {session.get("websocket_url", "N/A")[:60]}...')
    
    # Step 2: Generate more realistic audio
    print('2. Generating speech-like audio...')
    audio_data = generate_speech_like_audio(5.0)  # 5 seconds
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    print(f'   Generated: {len(audio_data)} bytes ({len(audio_data) / 1024:.1f}KB)')
    
    # Step 3: Process with improved transcription
    print('3. Processing with improved Gladia transcription...')
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
        
        print(f'📝 Transcript Results:')
        if total_text:
            print(f'   ✅ Text Found: "{total_text}"')
            print(f'   Segments: {segments}')
            
            # Show segment details
            transcript_segments = transcript.get('segments', [])
            for i, seg in enumerate(transcript_segments[:5]):
                conf = seg.get('confidence', 0)
                text = seg.get('text', '')
                is_final = seg.get('is_final', False)
                print(f'   Segment {i+1}: "{text}" (confidence: {conf:.3f}, final: {is_final})')
        else:
            print(f'   ⚠️ No transcript text (processed {segments} segments)')
            print(f'   This is expected for synthetic audio')
    else:
        print('📝 No transcript data returned')
    
    # Check audio storage
    audio_info = result.get('audio', {})
    if audio_info.get('has_audio'):
        print(f'🎵 Audio stored: {audio_info.get("audio_size", 0)} bytes')
        if audio_info.get('playback_url'):
            print(f'   Playback URL available: {audio_info.get("playback_url", "")[:50]}...')
    
    print('\n💡 Summary:')
    success_indicators = []
    
    if result.get('status') == 'completed':
        success_indicators.append('Session completed successfully')
    
    if audio_info.get('has_audio'):
        success_indicators.append('Audio uploaded to MinIO')
    
    if transcript and transcript.get('segments_count', 0) > 0:
        success_indicators.append(f'Transcript processing worked ({transcript.get("segments_count")} segments)')
    
    if transcript and transcript.get('total_text', '').strip():
        success_indicators.append('Text transcription successful')
    
    for indicator in success_indicators:
        print(f'   ✅ {indicator}')
    
    print('\n🎤 For real speech transcription:')
    print('   Use http://localhost:8000/test and speak clearly into your microphone')
    print('   The improved system should now better handle microphone audio')

if __name__ == '__main__':
    asyncio.run(test_improved_transcription())
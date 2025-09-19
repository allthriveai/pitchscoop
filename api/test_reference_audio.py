#!/usr/bin/env python3
"""
Test Gladia with a high-quality reference audio to isolate format conversion issues
"""
import asyncio
import base64
import struct
import math
import tempfile
import wave
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler
from domains.events.mcp.events_mcp_handler import events_mcp_handler

def generate_clear_speech_wav(text="Hello this is a test", duration=3.0, sample_rate=16000):
    """Generate a clear speech-like WAV file for testing"""
    
    # Create WAV file with clear speech patterns
    samples = []
    total_samples = int(sample_rate * duration)
    
    # Generate speech-like patterns with clear formants and timing
    for i in range(total_samples):
        t = i / sample_rate
        
        # Create realistic speech formants
        f1 = 700 + 200 * math.sin(2 * math.pi * 1.5 * t)  # First formant (vowel)
        f2 = 1200 + 300 * math.sin(2 * math.pi * 2.1 * t)  # Second formant
        f3 = 2400 + 200 * math.sin(2 * math.pi * 0.8 * t)  # Third formant
        
        # Add speech rhythm and pauses
        word_pattern = math.sin(2 * math.pi * 2.5 * t)  # ~2.5 words per second
        amplitude = 0.6 * (0.5 + 0.5 * (word_pattern > -0.3))  # Create pauses
        
        # Combine formants with harmonic content
        signal = (
            0.4 * math.sin(2 * math.pi * f1 * t) +
            0.3 * math.sin(2 * math.pi * f2 * t) +
            0.2 * math.sin(2 * math.pi * f3 * t) +
            0.1 * math.sin(2 * math.pi * (f1 * 2) * t)  # Harmonic
        )
        
        # Add slight noise for realism but keep it minimal
        noise = 0.02 * (2 * (i % 1000) / 1000 - 1)  # Very low noise
        
        sample_value = int(20000 * amplitude * (signal + noise))
        sample_value = max(-32767, min(32767, sample_value))
        samples.append(sample_value)
    
    # Create WAV file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        with wave.open(tmp_file, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Convert samples to bytes
            for sample in samples:
                wav_file.writeframes(struct.pack('<h', sample))
        
        return tmp_file.name

async def test_reference_audio():
    print('🎤 Testing with Reference Quality Audio')
    print('=' * 50)
    
    # Generate high-quality reference audio
    print('1. Generating reference WAV file...')
    wav_file_path = generate_clear_speech_wav("Hello this is a clear test of speech recognition", 4.0)
    print(f'   ✅ Created: {wav_file_path}')
    
    # Read the WAV file
    with open(wav_file_path, 'rb') as f:
        audio_data = f.read()
    
    print(f'   📊 Audio size: {len(audio_data)} bytes')
    
    # Create event
    print('2. Creating test event...')
    event = await events_mcp_handler.create_event(
        event_type='individual_practice',
        event_name='Reference Audio Test',
        description='Testing with high-quality reference audio'
    )
    event_id = event['event_id']
    print(f'   ✅ Event: {event_id}')
    
    # Start recording session
    print('3. Starting recording session...')
    handler = GladiaMCPHandler()
    session = await handler.start_pitch_recording(
        'Reference Test Team',
        'High Quality Audio Test',
        event_id
    )
    
    if 'error' in session:
        print(f'   ❌ Session failed: {session["error"]}')
        return
    
    session_id = session['session_id']
    print(f'   ✅ Session: {session_id}')
    print(f'   🔧 Audio Intelligence: {bool(session.get("audio_config", {}).get("sentiment_analysis"))}')
    
    # Convert to base64
    print('4. Processing reference audio...')
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    
    # Process with Gladia
    result = await handler.stop_pitch_recording(session_id, audio_b64)
    
    print('📊 Reference Audio Results:')
    print(f'   Status: {result.get("status", "unknown")}')
    
    if result.get('status') == 'completed':
        transcript = result.get('transcript', {})
        total_text = transcript.get('total_text', '').strip()
        segments = transcript.get('segments', [])
        ai_data = transcript.get('audio_intelligence', {})
        
        print(f'   📝 Transcript: "{total_text}"')
        print(f'   📊 Segments: {len(segments)}')
        print(f'   🧠 Audio Intelligence: {list(ai_data.keys())}')
        
        if segments:
            confidences = [seg.get('confidence', 0) for seg in segments if seg.get('confidence') is not None]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                print(f'   📈 Average Confidence: {avg_confidence:.2f} ({avg_confidence*100:.0f}%)')
                
                if avg_confidence > 0.6:
                    print('   ✅ HIGH CONFIDENCE: Reference audio processed well')
                elif avg_confidence > 0.3:
                    print('   ⚠️ MEDIUM CONFIDENCE: Some processing issues remain')
                else:
                    print('   🔴 LOW CONFIDENCE: Fundamental processing problems')
    else:
        print(f'   ❌ Processing failed: {result.get("error")}')
    
    # Clean up
    import os
    os.unlink(wav_file_path)
    
    print('\n🎯 Analysis:')
    print('   If reference audio ALSO has low confidence/wrong transcripts:')
    print('     → Issue is in Gladia API integration or audio format processing')
    print('   If reference audio works well but browser audio doesn\'t:')
    print('     → Issue is in WebM→WAV conversion in the browser')

if __name__ == "__main__":
    asyncio.run(test_reference_audio())
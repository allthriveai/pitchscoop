#!/usr/bin/env python3
"""
Test script to verify Gladia batch processing 413 error fix.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from api.domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler
from api.domains.recordings.value_objects.audio_configuration import AudioConfiguration

async def test_batch_processing():
    """Test the fixed batch processing implementation."""
    print("Testing Gladia batch processing fix...")
    
    # Create handler
    handler = GladiaMCPHandler()
    
    # Create test audio configuration with Audio Intelligence
    config = AudioConfiguration.create_pitch_analysis()
    print(f"Audio config: sentiment={config.sentiment_analysis}, emotion={config.emotion_analysis}")
    
    # Load a test audio file (using the existing test audio)
    test_audio_path = Path(__file__).parent / "api" / "test_audio.wav"
    if not test_audio_path.exists():
        print(f"Test audio file not found: {test_audio_path}")
        print("Creating a small test audio file...")
        
        # Create a minimal WAV file for testing (2 seconds of silence)
        import wave
        import numpy as np
        
        sample_rate = 16000
        duration = 2.0  # 2 seconds
        samples = int(sample_rate * duration)
        audio_data = np.zeros(samples, dtype=np.int16)
        
        with wave.open(str(test_audio_path), 'wb') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        print(f"Created test audio: {test_audio_path}")
    
    # Read audio file
    with open(test_audio_path, 'rb') as f:
        audio_data = f.read()
    
    print(f"Test audio size: {len(audio_data)} bytes ({len(audio_data)/1024:.1f}KB)")
    
    # Test the new batch processing method
    try:
        result = await handler._process_audio_with_intelligence(audio_data, config)
        
        if result:
            print("✅ Batch processing SUCCESS!")
            print(f"Transcript segments: {len(result.get('transcript_segments', []))}")
            print(f"Intelligence data keys: {list(result.get('intelligence_data', {}).keys())}")
            
            # Print first few segments
            segments = result.get('transcript_segments', [])
            for i, segment in enumerate(segments[:3]):
                print(f"Segment {i+1}: '{segment.get('text', '')}' (confidence: {segment.get('confidence', 0):.3f})")
                
        else:
            print("❌ Batch processing returned None (likely fell back to WebSocket)")
            
    except Exception as e:
        print(f"❌ Batch processing FAILED with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if Gladia API key is available
    if not os.getenv('GLADIA_API_KEY'):
        print("⚠️  GLADIA_API_KEY not set. Please add it to your .env file.")
        print("Skipping test...")
        exit(1)
    
    asyncio.run(test_batch_processing())
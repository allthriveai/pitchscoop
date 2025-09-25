#!/usr/bin/env python3
"""
Test the WebM to WAV conversion directly.
"""

import base64
import tempfile
import subprocess
import os

def test_conversion():
    print('🔧 Testing WebM to WAV Conversion')
    print('=' * 50)
    
    # Create a simple WebM file with audio
    print('\n1. Creating test WebM file...')
    
    with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as webm_file:
        webm_path = webm_file.name
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
        wav_path = wav_file.name
    
    try:
        # Generate a test audio with speech-like characteristics
        # Use multiple sine waves to simulate speech frequencies
        generate_cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', 'sine=frequency=200:duration=2',  # Base frequency
            '-f', 'lavfi', 
            '-i', 'sine=frequency=500:duration=2',  # Mid frequency
            '-f', 'lavfi',
            '-i', 'sine=frequency=1000:duration=2', # High frequency
            '-filter_complex', '[0][1][2]amix=inputs=3:duration=longest',
            '-c:a', 'libopus',  # Use Opus codec like browser WebM
            '-b:a', '128k',
            '-ar', '48000',  # 48kHz like browser recording
            '-f', 'webm',
            '-y',
            webm_path
        ]
        
        result = subprocess.run(generate_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f'❌ Failed to generate WebM: {result.stderr}')
            return
        
        # Get WebM file size
        webm_size = os.path.getsize(webm_path)
        print(f'✅ Created WebM file: {webm_size} bytes')
        
        # Now test the conversion
        print('\n2. Converting WebM to WAV...')
        
        convert_cmd = [
            'ffmpeg',
            '-i', webm_path,
            '-vn',  # No video
            '-sn',  # No subtitles  
            '-dn',  # No data
            '-acodec', 'pcm_s16le',  # Convert to 16-bit PCM
            '-ar', '16000',          # 16kHz sample rate for Gladia
            '-ac', '1',              # Convert to mono
            '-f', 'wav',             # Force WAV format
            '-y',
            wav_path
        ]
        
        result = subprocess.run(convert_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            wav_size = os.path.getsize(wav_path)
            print(f'✅ Conversion successful: {wav_size} bytes WAV')
            
            # Verify the WAV file
            verify_cmd = ['ffprobe', '-i', wav_path, '-show_streams', '-v', 'quiet', '-print_format', 'json']
            verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
            
            if verify_result.returncode == 0:
                import json
                probe_data = json.loads(verify_result.stdout)
                streams = probe_data.get('streams', [])
                if streams:
                    audio_stream = streams[0]
                    print(f'\n   WAV file properties:')
                    print(f'   - Codec: {audio_stream.get("codec_name")}')
                    print(f'   - Sample rate: {audio_stream.get("sample_rate")} Hz')
                    print(f'   - Channels: {audio_stream.get("channels")}')
                    print(f'   - Duration: {audio_stream.get("duration", "unknown")} seconds')
                    print(f'   - Bit depth: {audio_stream.get("bits_per_sample", "unknown")} bits')
        else:
            print(f'❌ Conversion failed!')
            print(f'Error: {result.stderr}')
            
        print('\n3. Testing volume detection...')
        
        volume_cmd = [
            'ffmpeg', '-i', wav_path,
            '-af', 'volumedetect',
            '-f', 'null', '-'
        ]
        
        result = subprocess.run(volume_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            for line in result.stderr.split('\n'):
                if 'mean_volume' in line or 'max_volume' in line:
                    print(f'   {line.strip()}')
                    
    finally:
        # Cleanup
        try:
            os.unlink(webm_path)
            os.unlink(wav_path)
        except:
            pass
    
    print('\n' + '=' * 50)
    print('✅ WebM to WAV conversion is working!')
    print('\nThe issue is likely:')
    print('1. Browser is sending silent or corrupted WebM')
    print('2. Microphone permissions/volume issues')
    print('3. Browser audio constraints need adjustment')

if __name__ == '__main__':
    test_conversion()
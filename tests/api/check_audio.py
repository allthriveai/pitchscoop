#!/usr/bin/env python3
"""
Check what's in the latest audio recording.
"""

import subprocess
import tempfile
import os
import requests
import base64

def check_audio():
    print('🔍 Checking Latest Audio Recording')
    print('=' * 50)
    
    session_id = 'a86c27b4-497f-417a-b0df-83e6ac9e35ef'  # Your latest session
    
    # Get the audio URL
    print(f'\nSession ID: {session_id}')
    
    # Get playback URL
    response = requests.post('http://localhost:8000/mcp/execute', json={
        'tool': 'pitches.get_playback_url',
        'arguments': {
            'session_id': session_id,
            'expires_hours': 1
        }
    })
    
    result = response.json()
    
    if 'error' in result:
        print(f'❌ Error: {result["error"]}')
        return
    
    playback_url = result.get('playback_url')
    if not playback_url:
        print('❌ No playback URL available')
        return
    
    print(f'✅ Got playback URL')
    
    # Download the audio file
    print('\nDownloading audio file...')
    
    # Replace external MinIO URL with internal one
    internal_url = playback_url.replace('http://localhost:9000', 'http://minio:9000')
    
    audio_response = requests.get(internal_url)
    if audio_response.status_code != 200:
        print(f'❌ Failed to download audio: {audio_response.status_code}')
        return
    
    audio_data = audio_response.content
    print(f'✅ Downloaded {len(audio_data)} bytes')
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        tmp_file.write(audio_data)
        audio_path = tmp_file.name
    
    try:
        # Analyze with FFmpeg
        print('\n📊 Audio Analysis:')
        print('-' * 30)
        
        # Get format info
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'stream=codec_name,sample_rate,channels,duration,bit_rate',
            '-of', 'default=noprint_wrappers=1',
            audio_path
        ]
        
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        print('Audio Properties:')
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f'  {line}')
        
        # Get volume statistics
        print('\nVolume Analysis:')
        volume_cmd = [
            'ffmpeg', '-i', audio_path,
            '-af', 'volumedetect',
            '-f', 'null', '-'
        ]
        
        result = subprocess.run(volume_cmd, capture_output=True, text=True, timeout=10)
        
        for line in result.stderr.split('\n'):
            if 'mean_volume' in line or 'max_volume' in line:
                print(f'  {line.strip()}')
        
        # Check if audio is silent
        print('\n🎤 Checking for actual audio content...')
        
        # Extract raw PCM samples to check for silence
        pcm_cmd = [
            'ffmpeg', '-i', audio_path,
            '-f', 's16le',  # 16-bit PCM
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            'pipe:1'
        ]
        
        result = subprocess.run(pcm_cmd, capture_output=True, timeout=10)
        
        if result.returncode == 0:
            pcm_data = result.stdout
            
            # Check first 1000 samples
            import struct
            sample_count = min(1000, len(pcm_data) // 2)
            samples = struct.unpack(f'<{sample_count}h', pcm_data[:sample_count * 2])
            
            max_sample = max(abs(s) for s in samples) if samples else 0
            avg_sample = sum(abs(s) for s in samples) / len(samples) if samples else 0
            
            print(f'\n  Sample Analysis (first {sample_count} samples):')
            print(f'  Max amplitude: {max_sample} / 32768 ({(max_sample/32768)*100:.1f}%)')
            print(f'  Avg amplitude: {avg_sample:.1f} / 32768 ({(avg_sample/32768)*100:.1f}%)')
            
            if max_sample < 100:
                print('\n  ⚠️ AUDIO IS SILENT OR NEARLY SILENT!')
                print('  The microphone is not capturing audio properly.')
            elif max_sample < 1000:
                print('\n  ⚠️ Audio volume is VERY low')
                print('  Try speaking louder or adjusting microphone settings.')
            else:
                print(f'\n  ✅ Audio has content (not silent)')
        
        # Try to convert to a format we know works
        print('\n🔧 Testing conversion to standard WAV...')
        
        with tempfile.NamedTemporaryFile(suffix='_converted.wav', delete=False) as conv_file:
            conv_path = conv_file.name
        
        convert_cmd = [
            'ffmpeg', '-i', audio_path,
            '-vn',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-y',
            conv_path
        ]
        
        result = subprocess.run(convert_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            conv_size = os.path.getsize(conv_path)
            print(f'  ✅ Conversion successful: {conv_size} bytes')
            
            # Upload this converted audio back for testing
            with open(conv_path, 'rb') as f:
                conv_data = f.read()
            conv_base64 = base64.b64encode(conv_data).decode('utf-8')
            
            print('\n  Testing converted audio with Gladia...')
            
            # Create new session
            response = requests.post('http://localhost:8000/mcp/execute', json={
                'tool': 'pitches.start_recording',
                'arguments': {
                    'event_id': 'mcp-hackathon',
                    'team_name': 'Debug Team',
                    'pitch_title': 'Converted Audio Test'
                }
            })
            
            if response.status_code == 200:
                new_session = response.json().get('session_id')
                
                # Send converted audio
                response = requests.post('http://localhost:8000/mcp/execute', json={
                    'tool': 'pitches.stop_recording',
                    'arguments': {
                        'session_id': new_session,
                        'audio_data_base64': conv_base64,
                        'audio_format': 'wav'
                    }
                })
                
                result = response.json()
                transcript = result.get('transcript', {})
                text = transcript.get('total_text', '')
                
                if text:
                    print(f'  ✅ TRANSCRIPT: "{text}"')
                else:
                    print(f'  ❌ Still no transcript - audio may be non-speech')
            
            os.unlink(conv_path)
        else:
            print(f'  ❌ Conversion failed: {result.stderr[:200]}')
        
        print('\n' + '=' * 50)
        print('\n📋 DIAGNOSIS:')
        
        if max_sample < 100:
            print('❌ PROBLEM: Microphone is not recording any audio')
            print('\nSOLUTIONS:')
            print('1. Check browser microphone permissions')
            print('2. Check system microphone settings')
            print('3. Try a different browser')
            print('4. Make sure microphone is not muted')
        elif max_sample < 1000:
            print('⚠️ PROBLEM: Audio is too quiet for Gladia')
            print('\nSOLUTIONS:')
            print('1. Speak louder and closer to the microphone')
            print('2. Increase microphone gain/volume in system settings')
            print('3. Use a better quality microphone')
        else:
            print('🤔 Audio seems OK but Gladia cannot transcribe it')
            print('\nPOSSIBLE ISSUES:')
            print('1. Too much background noise')
            print('2. Audio quality issues from WebM conversion')
            print('3. Gladia requires clearer speech')
            
    finally:
        try:
            os.unlink(audio_path)
        except:
            pass

if __name__ == '__main__':
    check_audio()
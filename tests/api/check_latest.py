#!/usr/bin/env python3
"""
Check the most recent audio recording.
"""

import subprocess
import tempfile
import os
import requests
import base64
import redis
import json

def check_latest():
    print('🔍 Checking Most Recent Audio Recording')
    print('=' * 50)
    
    # Connect to Redis to find latest session
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    
    print('\nSearching for latest recording session...')
    latest_session = None
    latest_time = None
    
    # Scan all session keys
    for key in r.scan_iter(match="event:*:session:*"):
        session_data = r.get(key)
        if session_data:
            try:
                data = json.loads(session_data)
                session_id = data.get('session_id')
                created_at = data.get('recording_started_at', data.get('created_at'))
                
                if created_at and (not latest_time or created_at > latest_time):
                    latest_time = created_at
                    latest_session = session_id
            except:
                pass
    
    if not latest_session:
        print('❌ No sessions found in Redis')
        return
    
    session_id = latest_session
    print(f'✅ Found latest session: {session_id}')
    print(f'   Created at: {latest_time}')
    
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
        print(f'❌ Error getting playback URL: {result["error"]}')
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
        
        has_volume_info = False
        for line in result.stderr.split('\n'):
            if 'mean_volume' in line or 'max_volume' in line:
                print(f'  {line.strip()}')
                has_volume_info = True
        
        if not has_volume_info:
            print('  ⚠️ Could not detect volume levels')
        
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
            
            if len(pcm_data) > 0:
                # Check samples throughout the audio
                import struct
                
                # Check beginning, middle, and end
                positions = [0, len(pcm_data)//4, len(pcm_data)//2, 3*len(pcm_data)//4]
                
                all_samples = []
                for pos in positions:
                    if pos + 2000 < len(pcm_data):
                        chunk = pcm_data[pos:pos+2000]
                        samples = struct.unpack(f'<{len(chunk)//2}h', chunk)
                        all_samples.extend(samples)
                
                if all_samples:
                    max_sample = max(abs(s) for s in all_samples)
                    avg_sample = sum(abs(s) for s in all_samples) / len(all_samples)
                    
                    print(f'\n  Sample Analysis ({len(all_samples)} samples from various positions):')
                    print(f'  Max amplitude: {max_sample} / 32768 ({(max_sample/32768)*100:.1f}%)')
                    print(f'  Avg amplitude: {avg_sample:.1f} / 32768 ({(avg_sample/32768)*100:.1f}%)')
                    
                    if max_sample < 100:
                        print('\n  ❌ AUDIO IS COMPLETELY SILENT!')
                        print('  The microphone is not capturing any audio.')
                    elif max_sample < 500:
                        print('\n  ⚠️ Audio is EXTREMELY quiet')
                        print('  This is too quiet for speech recognition.')
                    elif max_sample < 2000:
                        print('\n  ⚠️ Audio volume is very low')
                        print('  Gladia may struggle with this volume level.')
                    else:
                        print(f'\n  ✅ Audio has reasonable volume')
                else:
                    print('  ❌ Could not extract audio samples')
            else:
                print('  ❌ No audio data extracted')
        else:
            print(f'  ❌ Failed to extract PCM data: {result.stderr[:200]}')
        
        print('\n' + '=' * 50)
        print('\n📋 DIAGNOSIS SUMMARY:')
        
        if 'max_sample' in locals():
            if max_sample < 100:
                print('\n❌ CRITICAL ISSUE: No audio is being recorded!')
                print('\nIMPORTANT: Your microphone is not sending any audio to the browser.')
                print('\nTROUBLESHOOTING STEPS:')
                print('1. Check browser permissions:')
                print('   - Click the lock icon in the address bar')
                print('   - Ensure microphone is set to "Allow"')
                print('2. Check macOS System Preferences:')
                print('   - Go to System Preferences > Security & Privacy > Microphone')
                print('   - Make sure your browser is checked')
                print('3. Test microphone:')
                print('   - Open System Preferences > Sound > Input')
                print('   - Speak and check if input level moves')
                print('4. Try a different browser (Chrome/Firefox/Safari)')
            elif max_sample < 1000:
                print('\n⚠️ ISSUE: Audio is too quiet')
                print('\nSOLUTIONS:')
                print('1. Increase microphone volume in System Preferences > Sound > Input')
                print('2. Speak louder and closer to the microphone')
                print('3. Check if microphone is muted')
            else:
                print('\n🤔 Audio volume seems OK')
                print('The issue might be:')
                print('1. Audio quality/codec issues')
                print('2. Too much background noise')
                print('3. WebM conversion problems')
        else:
            print('\n❌ Could not analyze audio levels')
            print('The audio file may be corrupted or in an unexpected format')
            
    finally:
        try:
            os.unlink(audio_path)
        except:
            pass

if __name__ == '__main__':
    check_latest()
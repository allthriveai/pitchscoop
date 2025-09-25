#!/usr/bin/env python3
"""
Debug microphone recording issues - check what audio we're actually getting.
"""

import asyncio
import base64
import requests
import json
import sys
import os
import tempfile
import subprocess
import wave
import struct

sys.path.insert(0, '/Users/allierays/Sites/pitchscoop/api')

async def debug_microphone():
    print('🎤 Microphone Audio Debugging Tool')
    print('=' * 50)
    
    # Get the latest session from Redis
    print('\n1. Finding latest recording session...')
    
    import redis.asyncio as redis
    redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
    
    # Find the most recent session
    session_id = None
    async for key in redis_client.scan_iter(match="event:*:session:*"):
        session_id = key.split(':')[-1]
        print(f'Found session: {session_id}')
        break
    
    if not session_id:
        print('❌ No sessions found. Please record something first at http://localhost:8000/test')
        return
    
    # Get the audio from MinIO using existing infrastructure
    print('\n2. Retrieving audio from MinIO...')
    
    try:
        # Import the existing MinIO storage module
        from api.domains.recordings.infrastructure.minio_audio_storage import minio_audio_storage
        
        # Get the audio info first
        audio_info = await minio_audio_storage.get_audio_info(session_id)
        if not audio_info:
            print(f'❌ No audio found for session {session_id}')
            return
            
        print(f"Found audio: {audio_info.get('size', 0)} bytes")
        
        # Download the audio
        audio_data = await minio_audio_storage.download_audio(session_id)
        if not audio_data:
            print('❌ Failed to download audio')
            return
            
        print(f'✅ Retrieved audio: {len(audio_data)} bytes')
        
        # Save to temp file for analysis
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            tmp_file.write(audio_data)
            audio_path = tmp_file.name
            
    except Exception as e:
        print(f'❌ Failed to retrieve audio: {e}')
        import traceback
        traceback.print_exc()
        return
    
    # Analyze the audio
    print('\n3. Analyzing audio file...')
    
    try:
        # Use FFmpeg to get audio stats
        ffmpeg_cmd = [
            'ffmpeg', '-i', audio_path, 
            '-af', 'volumedetect',
            '-f', 'null', '-'
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=10)
        
        # Parse volume stats
        output = result.stderr
        for line in output.split('\n'):
            if 'mean_volume' in line or 'max_volume' in line:
                print(f'   {line.strip()}')
        
        # Get basic WAV info
        with wave.open(audio_path, 'rb') as wav_file:
            params = wav_file.getparams()
            print(f'\n   WAV Format:')
            print(f'   - Channels: {params.nchannels}')
            print(f'   - Sample Rate: {params.framerate} Hz')
            print(f'   - Sample Width: {params.sampwidth} bytes')
            print(f'   - Duration: {params.nframes / params.framerate:.2f} seconds')
            
            # Read first few samples to check if there's actual audio
            wav_file.rewind()
            frames = wav_file.readframes(min(params.framerate, params.nframes))  # Read 1 second
            
            # Convert to samples
            if params.sampwidth == 2:  # 16-bit
                samples = struct.unpack(f'<{len(frames)//2}h', frames)
                max_sample = max(abs(s) for s in samples)
                avg_sample = sum(abs(s) for s in samples) / len(samples)
                
                print(f'\n   Audio Signal Analysis:')
                print(f'   - Max amplitude: {max_sample} (out of 32768)')
                print(f'   - Avg amplitude: {avg_sample:.1f}')
                print(f'   - Volume level: {(max_sample/32768)*100:.1f}%')
                
                if max_sample < 100:
                    print('   ⚠️ AUDIO IS NEARLY SILENT!')
                elif max_sample < 1000:
                    print('   ⚠️ Audio is very quiet')
                elif max_sample < 5000:
                    print('   ⚠️ Audio volume is low')
                else:
                    print('   ✅ Audio volume looks OK')
        
        # Test with different Gladia settings
        print('\n4. Testing Gladia with different configurations...')
        
        api_key = os.getenv('GLADIA_API_KEY')
        if not api_key:
            print('❌ No GLADIA_API_KEY found')
            return
        
        # Try uploading the audio directly to Gladia
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # Upload the audio
            with open(audio_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('audio', f, filename='test.wav', content_type='audio/wav')
                
                async with session.post(
                    'https://api.gladia.io/v2/upload',
                    headers={'X-Gladia-Key': api_key},
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        upload_result = await response.json()
                        audio_url = upload_result.get('audio_url')
                        print(f'✅ Upload successful')
                    else:
                        print(f'❌ Upload failed: {await response.text()}')
                        return
            
            # Try transcription with audio enhancement
            configs = [
                {'audio_enhancer': True, 'name': 'With audio enhancement'},
                {'audio_enhancer': False, 'name': 'Without enhancement'},
            ]
            
            for config in configs:
                print(f'\n   Testing: {config["name"]}...')
                
                payload = {
                    'audio_url': audio_url,
                    'language': 'en',
                    'audio_enhancer': config.get('audio_enhancer', False)
                }
                
                async with session.post(
                    'https://api.gladia.io/v2/pre-recorded',
                    headers={
                        'X-Gladia-Key': api_key,
                        'Content-Type': 'application/json'
                    },
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        result_url = result.get('result_url')
                        
                        # Poll for results
                        for _ in range(5):
                            await asyncio.sleep(2)
                            
                            async with session.get(
                                result_url,
                                headers={'X-Gladia-Key': api_key}
                            ) as poll_response:
                                if poll_response.status == 200:
                                    poll_result = await poll_response.json()
                                    if poll_result.get('status') in ['done', 'completed']:
                                        utterances = poll_result.get('result', {}).get('transcription', {}).get('utterances', [])
                                        if utterances:
                                            print(f'   ✅ Got transcript: "{utterances[0].get("text", "")[:50]}..."')
                                        else:
                                            print(f'   ❌ No transcript (Gladia found no speech)')
                                        break
                    else:
                        print(f'   ❌ Request failed: {await response.text()}')
        
        print('\n' + '=' * 50)
        print('📊 DIAGNOSIS:')
        
        if max_sample < 100:
            print('❌ PROBLEM: Audio is completely silent or nearly silent')
            print('   SOLUTION: Check microphone permissions and volume settings')
        elif max_sample < 1000:
            print('⚠️ PROBLEM: Audio volume is extremely low')
            print('   SOLUTION: Speak louder or move closer to microphone')
        else:
            print('🤔 Audio volume seems OK, but Gladia is not detecting speech')
            print('   POSSIBLE ISSUES:')
            print('   - Too much background noise')
            print('   - Audio codec incompatibility')
            print('   - Microphone producing non-speech frequencies')
        
    except Exception as e:
        print(f'❌ Error analyzing audio: {e}')
        import traceback
        traceback.print_exc()
    finally:
        try:
            os.unlink(audio_path)
        except:
            pass

if __name__ == '__main__':
    asyncio.run(debug_microphone())
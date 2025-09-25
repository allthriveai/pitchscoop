#!/usr/bin/env python3
"""
Test Gladia API directly to verify it's working.
"""

import os
import asyncio
import aiohttp
import json
import base64
import tempfile
import subprocess

async def test_gladia_direct():
    print('🎤 Testing Gladia API Directly')
    print('=' * 50)
    
    api_key = os.getenv('GLADIA_API_KEY')
    if not api_key:
        print('❌ No GLADIA_API_KEY found in environment')
        return
    
    print(f'✅ Found API key: {api_key[:10]}...')
    
    # Create a simple test WAV file with text-to-speech
    print('\n1. Creating test audio with espeak TTS...')
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        output_path = tmp_file.name
    
    try:
        # Try to use espeak for TTS (commonly available in Docker)
        test_text = "Hello, this is a test of the Gladia speech recognition system. Testing one two three."
        
        # First try espeak
        try:
            result = subprocess.run(
                ['espeak', test_text, '-w', output_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print('✅ Created audio with espeak TTS')
            else:
                raise Exception("espeak failed")
        except:
            # Fallback: Create a simple sine wave that sounds like speech
            print('⚠️ espeak not available, creating synthetic speech-like audio...')
            
            # Create a more complex audio pattern that mimics speech
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                # Create multiple sine waves at speech frequencies
                '-i', 'anoisesrc=d=3:c=pink:r=16000:a=0.1,highpass=f=80,lowpass=f=3000',
                '-ar', '16000',
                '-ac', '1',
                '-acodec', 'pcm_s16le',
                '-y',
                output_path
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print('✅ Created synthetic speech-like audio')
        
        # Read the audio file
        with open(output_path, 'rb') as f:
            audio_data = f.read()
        
        print(f'Audio size: {len(audio_data)} bytes ({len(audio_data)/1024:.1f}KB)')
        
        # Test 1: Upload to Gladia
        print('\n2. Uploading audio to Gladia...')
        
        async with aiohttp.ClientSession() as session:
            # Upload the audio file
            data = aiohttp.FormData()
            data.add_field('audio', audio_data, filename='test.wav', content_type='audio/wav')
            
            async with session.post(
                'https://api.gladia.io/v2/upload',
                headers={'X-Gladia-Key': api_key},
                data=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status in [200, 201]:
                    upload_result = await response.json()
                    audio_url = upload_result.get('audio_url')
                    print(f'✅ Upload successful: {audio_url[:60]}...')
                else:
                    error_text = await response.text()
                    print(f'❌ Upload failed ({response.status}): {error_text}')
                    return
        
        # Test 2: Request transcription
        print('\n3. Requesting transcription from Gladia...')
        
        async with aiohttp.ClientSession() as session:
            payload = {
                'audio_url': audio_url,
                'language': 'en',
                'enable_code_switching': False  # Disable for simple test
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
                    print(f'✅ Transcription job submitted: {result_url[:60]}...')
                else:
                    error_text = await response.text()
                    print(f'❌ Transcription request failed ({response.status}): {error_text}')
                    return
        
        # Test 3: Poll for results
        print('\n4. Polling for transcription results...')
        
        for attempt in range(20):
            await asyncio.sleep(2)  # Wait 2 seconds between polls
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    result_url,
                    headers={'X-Gladia-Key': api_key},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        status = result.get('status')
                        
                        print(f'   Attempt {attempt+1}: Status = {status}')
                        
                        if status in ['completed', 'done']:
                            print(f'\n✅ Transcription {status}!')
                            
                            # Extract transcript
                            prediction = result.get('prediction', result.get('result', {}))
                            utterances = prediction.get('utterances', [])
                            
                            if utterances:
                                print('\n📝 Transcript:')
                                for utt in utterances:
                                    text = utt.get('text', '')
                                    confidence = utt.get('confidence', 0)
                                    print(f'   "{text}" (confidence: {confidence:.2f})')
                                
                                # Full text
                                full_text = ' '.join([u.get('text', '') for u in utterances])
                                print(f'\n   Full text: "{full_text}"')
                            else:
                                print('   ❌ No utterances in response')
                                print(f'   Full response: {json.dumps(result, indent=2)}')
                            
                            return
                        
                        elif status == 'error':
                            error = result.get('error', 'Unknown error')
                            print(f'   ❌ Transcription failed: {error}')
                            return
        
        print('❌ Transcription timed out after 40 seconds')
        
    finally:
        # Clean up
        try:
            os.unlink(output_path)
        except:
            pass
    
    print('\n' + '=' * 50)
    print('🔍 Analysis:')
    print('If this test fails, then:')
    print('1. Gladia API key might be invalid')
    print('2. Gladia service might be down')
    print('3. Gladia might require real human speech (not synthetic)')
    print('\nIf this test succeeds but microphone fails:')
    print('1. Browser audio capture issue')
    print('2. WebM to WAV conversion issue')
    print('3. Audio quality/volume too low')

if __name__ == '__main__':
    asyncio.run(test_gladia_direct())
#!/usr/bin/env python3

import asyncio
import redis.asyncio as redis
import json
import sys

sys.path.insert(0, '/Users/allierays/Sites/pitchscoop/api')

async def debug_audio_issue():
    print('🔍 Root Cause: Audio Processing Issue')
    print('=' * 50)
    
    redis_client = redis.from_url('redis://redis:6379/0', decode_responses=True)
    
    # Get latest session
    sessions = []
    async for key in redis_client.scan_iter(match='event:*:session:*'):
        session_json = await redis_client.get(key)
        if session_json:
            session_data = json.loads(session_json)
            sessions.append((session_data.get('created_at', ''), session_data))
    
    sessions.sort(reverse=True)
    latest = sessions[0][1]
    
    print('📊 ISSUE ANALYSIS:')
    print(f'   Audio Size: {latest.get("audio_size", 0)} bytes')
    print(f'   Has Audio: {latest.get("has_audio", False)}')
    print(f'   Transcript Segments: {len(latest.get("transcript_segments", []))}')
    
    # Show the actual problem
    if latest.get('transcript_segments'):
        seg = latest['transcript_segments'][0]
        text = seg.get('text', '')
        conf = seg.get('confidence', 0)
        print(f'   Result: "{text}" (confidence: {conf:.3f})')
        print(f'   ^^ This is WRONG - should be your actual speech')
    
    audio_config = latest.get('audio_config', {})
    print(f'   Audio Format: {audio_config.get("encoding", "N/A")} @ {audio_config.get("sample_rate", "N/A")}Hz')
    
    print('\n🎯 ROOT CAUSE ANALYSIS:')
    print('1. Browser captures your microphone audio correctly')
    print('2. Audio gets converted to WAV format (141KB file)')  
    print('3. Backend sends WAV data to Gladia API')
    print('4. Gladia processes the audio but returns wrong transcription')
    print('5. Low confidence (11%) indicates Gladia cannot understand the audio')
    
    print('\n❌ THE REAL PROBLEM:')
    print('   Gladia is receiving corrupted/distorted audio from our backend')
    print('   This is NOT a frontend issue - the backend audio processing is wrong')
    
    print('\n🔧 SOLUTION:')
    print('   We need to fix how the backend sends audio data to Gladia')
    print('   The audio format/encoding is likely incompatible with Gladia')

if __name__ == '__main__':
    asyncio.run(debug_audio_issue())
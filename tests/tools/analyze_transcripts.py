#!/usr/bin/env python3
"""
Analyze transcript segments in detail to understand accuracy issues
"""
import asyncio
import json
from api.domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler

async def analyze_transcript_quality():
    print('🔍 Analyzing Transcript Quality Issues')
    print('=' * 50)
    
    handler = GladiaMCPHandler()
    result = await handler.list_sessions()
    sessions = result.get('sessions', [])
    
    transcript_sessions = [s for s in sessions if s['transcript_segments'] > 0]
    
    if not transcript_sessions:
        print('❌ No sessions with transcripts found')
        return
    
    print(f'📊 Found {len(transcript_sessions)} sessions with transcripts')
    print()
    
    for i, session in enumerate(transcript_sessions[:3]):
        session_id = session['session_id']
        print(f'🎤 Session {i+1}: {session_id}')
        print(f'   Created: {session["created_at"]}')
        print(f'   Segments: {session["transcript_segments"]}')
        
        # Get detailed session info
        session_details = await handler.get_session_details(session_id)
        
        # Audio info
        audio_size = session_details.get('audio_size', 0)
        duration_seconds = session_details.get('duration_seconds', 0) 
        print(f'   Audio Size: {audio_size} bytes ({audio_size/1024:.1f} KB)')
        if duration_seconds:
            print(f'   Duration: {duration_seconds:.1f} seconds')
        
        # Transcript analysis
        final_transcript = session_details.get('final_transcript', {})
        total_text = final_transcript.get('total_text', '')
        segments = final_transcript.get('segments', [])
        
        print(f'   📝 Final Text: "{total_text}"')
        print(f'   📊 Individual Segments:')
        
        for j, segment in enumerate(segments[:5]):  # Show first 5 segments
            text = segment.get('text', '')
            confidence = segment.get('confidence', 0)
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 0)
            is_final = segment.get('is_final', False)
            
            print(f'     Segment {j+1}: "{text}"')
            print(f'       Confidence: {confidence:.2f}')
            print(f'       Time: {start_time:.1f}s - {end_time:.1f}s')
            print(f'       Final: {is_final}')
            
            # Check for Audio Intelligence data
            sentiment = segment.get('sentiment', None)
            emotion = segment.get('emotion', None)
            if sentiment or emotion:
                print(f'       AI: sentiment={sentiment}, emotion={emotion}')
            print()
        
        # Audio Intelligence summary
        audio_intelligence = session_details.get('audio_intelligence', {})
        if audio_intelligence:
            print(f'   🧠 Audio Intelligence: {list(audio_intelligence.keys())}')
        
        # Check audio config that was used
        audio_config = session_details.get('audio_config', {})
        print(f'   🔧 Audio Config: {audio_config}')
        
        print('-' * 50)
    
    print('\n🎯 Transcript Quality Analysis:')
    print('   Common issues with inaccurate transcripts:')
    print('   1. Low confidence scores (< 0.5) indicate poor audio quality')
    print('   2. Short segments might be picking up noise or artifacts')  
    print('   3. Audio format conversion issues (WebM -> WAV)')
    print('   4. Microphone pickup issues (background noise, echo)')
    print('   5. Speaking too fast or unclear pronunciation')
    print()
    print('   Recommendations:')
    print('   - Check confidence scores in segments above')
    print('   - Test with very clear, slow speech')
    print('   - Ensure good microphone placement')
    print('   - Test in a quiet environment')

if __name__ == "__main__":
    asyncio.run(analyze_transcript_quality())
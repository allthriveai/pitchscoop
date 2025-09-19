#!/usr/bin/env python3
"""
Examine session details to debug transcript issue
"""
import asyncio
import json
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler

async def examine_latest_session():
    print('🔍 Examining Latest Session')
    print('=' * 50)
    
    handler = GladiaMCPHandler()
    
    # Get latest sessions
    result = await handler.list_sessions()
    sessions = result.get('sessions', [])
    
    if not sessions:
        print('❌ No sessions found')
        return
    
    # Get most recent session
    latest_session = sessions[0]
    session_id = latest_session['session_id']
    
    print(f'📋 Latest Session: {session_id}')
    print(f'   Status: {latest_session["status"]}')
    print(f'   Has Audio: {latest_session["has_audio"]}')
    print(f'   Transcript Segments: {latest_session["transcript_segments"]}')
    print()
    
    # Get full session details
    session_details = await handler.get_session_details(session_id)
    
    print('🔧 Full Session Analysis:')
    print(f'   Audio Size: {session_details.get("audio_size", "unknown")} bytes')
    print(f'   Gladia Session ID: {session_details.get("gladia_session_id", "none")}')
    print(f'   WebSocket URL: {bool(session_details.get("websocket_url"))}')
    
    # Audio Intelligence configuration
    audio_config = session_details.get('audio_config', {})
    print(f'   Audio Config: {audio_config}')
    
    # Check what transcript processing was attempted
    transcript_segments = session_details.get('transcript_segments', [])
    print(f'   Raw Transcript Segments: {len(transcript_segments)}')
    
    if transcript_segments:
        print('   Sample segments:')
        for i, seg in enumerate(transcript_segments[:2]):
            print(f'     Segment {i+1}: {seg}')
    
    # Check final transcript
    final_transcript = session_details.get('final_transcript', {})
    print(f'   Final Transcript:')
    print(f'     Total Text: "{final_transcript.get("total_text", "")}"')
    print(f'     Segments Count: {final_transcript.get("segments_count", 0)}')
    print(f'     Segments: {len(final_transcript.get("segments", []))}')
    
    # Audio Intelligence data
    audio_intelligence = session_details.get('audio_intelligence', {})
    print(f'   Audio Intelligence: {list(audio_intelligence.keys())}')
    
    # Check playback URL
    playback_url = session_details.get('playback_url')
    if playback_url:
        print(f'   ✅ Audio stored successfully - playback available')
    else:
        print(f'   ❌ No playback URL found')
    
    return session_details

if __name__ == "__main__":
    asyncio.run(examine_latest_session())
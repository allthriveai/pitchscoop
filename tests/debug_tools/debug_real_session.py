#!/usr/bin/env python3

import asyncio
import sys
import json

sys.path.insert(0, '/Users/allierays/Sites/pitchscoop/api')

from api.domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler

async def debug_real_session():
    print('🔍 Debugging Real Session: c28e0d3a-49fc-44f6-a382-4ba15ba28a9d')
    print('=' * 60)
    
    handler = GladiaMCPHandler()
    session_id = 'c28e0d3a-49fc-44f6-a382-4ba15ba28a9d'
    
    # Get session details
    session_details = await handler.get_session_details(session_id)
    
    print('📊 Session Details:')
    print(f'   Status: {session_details.get("status", "unknown")}')
    print(f'   Team: {session_details.get("team_name", "N/A")}')
    print(f'   Title: {session_details.get("pitch_title", "N/A")}')
    print(f'   Has Audio: {session_details.get("has_audio", False)}')
    
    # Check audio config
    audio_config = session_details.get("audio_config", {})
    print(f'   Audio Format: {audio_config.get("encoding", "N/A")}')
    print(f'   Sample Rate: {audio_config.get("sample_rate", "N/A")}')
    print(f'   Channels: {audio_config.get("channels", "N/A")}')
    print(f'   AI Features: sentiment={audio_config.get("sentiment_analysis", False)}, emotion={audio_config.get("emotion_analysis", False)}')
    
    print(f'   Transcript Segments: {len(session_details.get("transcript_segments", []))}')
    
    # Check if we have stored transcript segments
    segments = session_details.get('transcript_segments', [])
    if segments:
        print('\n📝 Found Transcript Segments:')
        for i, seg in enumerate(segments[:5]):  # Show first 5
            text = seg.get('text', '')
            conf = seg.get('confidence', 0)
            is_final = seg.get('is_final', False)
            print(f'   Segment {i+1}: "{text}" (confidence: {conf:.3f}, final: {is_final})')
    else:
        print('\n❌ No transcript segments found in session data')
    
    # Check Gladia session info
    gladia_session_id = session_details.get('gladia_session_id')
    websocket_url = session_details.get('websocket_url')
    
    print('\n🔗 Gladia Integration:')
    if gladia_session_id:
        print(f'   Session ID: {gladia_session_id[:8]}...{gladia_session_id[-4:]}')
        print(f'   WebSocket URL: {websocket_url[:60] if websocket_url else "N/A"}...')
    else:
        print('   ❌ No Gladia session ID found')
    
    # Check for any error messages
    if 'error' in session_details:
        print(f'\n🚨 Error: {session_details["error"]}')
    
    # Check enhanced audio intelligence
    enhanced_ai = session_details.get('enhanced_audio_intelligence', {})
    gladia_ai = session_details.get('gladia_audio_intelligence', {})
    
    if enhanced_ai or gladia_ai:
        print('\n🧠 AI Analysis:')
        if enhanced_ai:
            print(f'   Enhanced AI: {enhanced_ai.get("success", False)}')
        if gladia_ai:
            print(f'   Gladia AI: {len(gladia_ai)} features')
    
    print('\n💡 Potential Issues:')
    issues = []
    
    if not session_details.get('has_audio'):
        issues.append('No audio file stored')
    
    if not segments:
        issues.append('No transcript segments generated')
    
    if not gladia_session_id:
        issues.append('No Gladia session created')
    
    if not audio_config:
        issues.append('Missing audio configuration')
    
    if issues:
        for issue in issues:
            print(f'   ⚠️ {issue}')
    else:
        print('   ✅ All components present')

if __name__ == '__main__':
    asyncio.run(debug_real_session())
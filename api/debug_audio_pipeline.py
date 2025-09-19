#!/usr/bin/env python3
"""
Debug the audio processing pipeline to find why transcripts are wrong
"""
import asyncio
import base64
import tempfile
import os
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler

async def debug_audio_pipeline():
    print('🔍 Debugging Audio Processing Pipeline')
    print('=' * 50)
    
    handler = GladiaMCPHandler()
    
    # Get the most recent session with audio
    result = await handler.list_sessions()
    sessions = result.get('sessions', [])
    
    audio_sessions = [s for s in sessions if s['has_audio']]
    if not audio_sessions:
        print('❌ No sessions with audio found')
        return
    
    latest_session = audio_sessions[0]
    session_id = latest_session['session_id']
    
    print(f'🎤 Analyzing Session: {session_id}')
    print(f'   Status: {latest_session["status"]}')
    print(f'   Audio Size: {latest_session.get("audio_size", "unknown")} bytes')
    
    # Get session details
    session_details = await handler.get_session_details(session_id)
    
    print('\n📊 Session Analysis:')
    print(f'   Gladia Session ID: {session_details.get("gladia_session_id")}')
    print(f'   WebSocket URL exists: {bool(session_details.get("websocket_url"))}')
    
    # Check how the audio was processed
    audio_config = session_details.get('audio_config', {})
    print(f'   Audio Config: {audio_config}')
    
    # Check if we have a playback URL to test the stored audio
    playback_url = session_details.get('playback_url')
    if playback_url:
        print(f'   ✅ Stored Audio URL: {playback_url}')
        print('   💡 You can test this URL in browser to verify stored audio quality')
    
    # Check what processing method was used
    transcript_segments = session_details.get('transcript_segments', [])
    final_transcript = session_details.get('final_transcript', {})
    audio_intelligence = session_details.get('audio_intelligence', {})
    
    print(f'\n🧠 Processing Analysis:')
    print(f'   Raw transcript segments: {len(transcript_segments)}')
    print(f'   Final transcript segments: {len(final_transcript.get("segments", []))}')
    print(f'   Audio Intelligence enabled: {len(audio_intelligence) > 0}')
    
    # Analyze the processing path taken
    print(f'\n🛤️ Processing Path Analysis:')
    
    # Check if Audio Intelligence was attempted (batch processing)
    if len(audio_intelligence) > 0:
        print('   ✅ Used Gladia Batch API (Audio Intelligence)')
        print('   📝 This should provide higher accuracy than WebSocket')
    else:
        print('   📡 Used Gladia WebSocket API (Live processing)')
        print('   ⚠️ WebSocket processing may have lower accuracy')
    
    # Check confidence scores
    if final_transcript.get('segments'):
        confidences = []
        for seg in final_transcript['segments']:
            if seg.get('confidence') is not None:
                confidences.append(seg['confidence'])
        
        if confidences:
            avg_conf = sum(confidences) / len(confidences)
            min_conf = min(confidences)
            max_conf = max(confidences)
            
            print(f'\n📈 Confidence Analysis:')
            print(f'   Average Confidence: {avg_conf:.2f} ({avg_conf*100:.0f}%)')
            print(f'   Min Confidence: {min_conf:.2f} ({min_conf*100:.0f}%)')
            print(f'   Max Confidence: {max_conf:.2f} ({max_conf*100:.0f}%)')
            
            if avg_conf < 0.3:
                print('   🔴 ISSUE: Very low confidence suggests audio format/quality issues')
            elif avg_conf < 0.6:
                print('   🟡 ISSUE: Low confidence suggests processing issues')
            else:
                print('   🟢 Confidence levels are acceptable')
    
    print(f'\n🎯 Diagnostic Summary:')
    print('   Possible causes of transcript inaccuracy:')
    print('   1. Browser audio format (WebM) to WAV conversion issues')
    print('   2. Sample rate or bit depth conversion problems')
    print('   3. Gladia API processing differences between live/batch')
    print('   4. Audio encoding artifacts during conversion')
    print('   5. Timing issues in audio streaming to WebSocket')
    
    print(f'\n💡 Next Steps:')
    print('   1. Test the stored audio URL to verify quality')
    print('   2. Check if batch vs WebSocket processing makes a difference')
    print('   3. Test with a different audio format/sample rate')
    print('   4. Compare browser recording with direct file upload')

if __name__ == "__main__":
    asyncio.run(debug_audio_pipeline())
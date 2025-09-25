#!/usr/bin/env python3
"""
Test directly if audio_format parameter is being passed.
"""

import sys
import asyncio

# Add the API path
sys.path.insert(0, '/app/api')

from api.domains.recordings.mcp.mcp_tools import execute_mcp_tool
import base64

async def test_direct():
    print('Testing audio_format parameter passing...')
    print('=' * 50)
    
    # First create a session
    result = await execute_mcp_tool("pitches.start_recording", {
        "team_name": "Direct Test",
        "pitch_title": "Parameter Test",
        "event_id": "mcp-hackathon"
    })
    
    if 'error' in result:
        print(f'Error starting: {result["error"]}')
        return
        
    session_id = result['session_id']
    print(f'Session: {session_id}')
    
    # Create dummy WebM data
    webm_data = b'\x1a\x45\xdf\xa3' + b'\x00' * 1000
    webm_base64 = base64.b64encode(webm_data).decode('utf-8')
    
    print('\nCalling stop_recording with:')
    print(f'  - session_id: {session_id}')
    print(f'  - audio_data_base64: {len(webm_base64)} chars')
    print(f'  - audio_format: "webm"')
    
    # Call stop_recording with audio_format
    result = await execute_mcp_tool("pitches.stop_recording", {
        "session_id": session_id,
        "audio_data_base64": webm_base64,
        "audio_format": "webm"  # THIS IS THE KEY PARAMETER
    })
    
    print('\nResult:')
    if 'error' in result:
        print(f'❌ Error: {result["error"]}')
        if 'debug_info' in result:
            print(f'Debug info: {result["debug_info"]}')
    else:
        print(f'✅ Status: {result.get("status")}')
        audio = result.get('audio', {})
        if audio:
            key = audio.get('minio_object_key', '')
            if '.wav' in key:
                print('✅ Stored as WAV - conversion worked!')
            else:
                print('❌ Not stored as WAV')

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
    asyncio.run(test_direct())
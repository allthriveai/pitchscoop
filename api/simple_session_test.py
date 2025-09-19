#!/usr/bin/env python3
"""
Simple test to check session state management
"""
import asyncio
import json
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler
from domains.events.mcp.events_mcp_handler import events_mcp_handler

async def test_session_state():
    print('🧪 Testing Session State Management')
    print('=' * 40)
    
    handler = GladiaMCPHandler()
    
    print(f'Initial active_sessions: {list(handler.active_sessions.keys())}')
    
    # Create an event first
    print('0. Creating event...')
    event = await events_mcp_handler.create_event(
        event_type='individual_practice',
        event_name='Session State Test',
        description='Testing session state management'
    )
    event_id = event['event_id']
    print(f'✅ Created event: {event_id}')
    
    # Start a session
    print('1. Starting session...')
    session = await handler.start_pitch_recording(
        'Test Team',
        'State Test',
        event_id
    )
    
    if 'error' in session:
        print(f'❌ Failed to start: {session["error"]}')
        return
    
    session_id = session['session_id']
    print(f'✅ Started session: {session_id}')
    print(f'Active sessions after start: {list(handler.active_sessions.keys())}')
    
    # Check if session is in active_sessions
    if session_id in handler.active_sessions:
        print(f'✅ Session found in active_sessions')
        print(f'   Session data keys: {list(handler.active_sessions[session_id].keys())}')
    else:
        print(f'❌ Session NOT found in active_sessions')
        print(f'   Available sessions: {list(handler.active_sessions.keys())}')
    
    # Now try to stop without audio data (should not fail on session cleanup)
    print('2. Stopping session without audio...')
    try:
        result = await handler.stop_pitch_recording(session_id)
        print(f'✅ Stop result: {result.get("status", "unknown")}')
        
        if 'error' in result:
            print(f'❌ Stop error: {result["error"]}')
    except Exception as e:
        print(f'💥 Exception during stop: {e}')
        import traceback
        traceback.print_exc()
    
    print(f'Final active_sessions: {list(handler.active_sessions.keys())}')

if __name__ == "__main__":
    asyncio.run(test_session_state())
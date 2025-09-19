#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add project root and api directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))

import redis.asyncio as redis
import json

async def list_existing_recordings():
    try:
        redis_client = redis.from_url('redis://redis:6379/0', decode_responses=True)
        
        print('🔍 Scanning for existing recordings...')
        session_keys = []
        async for key in redis_client.scan_iter(match='event:*:session:*'):
            session_keys.append(key)
        
        if not session_keys:
            print('❌ No existing recording sessions found')
            return None, None
        
        print(f'📊 Found {len(session_keys)} recording sessions:')
        print('=' * 50)
        
        sessions = []
        for key in session_keys:
            try:
                session_json = await redis_client.get(key)
                if session_json:
                    session_data = json.loads(session_json)
                    sessions.append((key, session_data))
            except Exception as e:
                print(f'⚠️  Error reading {key}: {e}')
        
        # Sort by creation time (newest first)
        sessions.sort(key=lambda x: x[1].get('created_at', ''), reverse=True)
        
        for i, (key, session) in enumerate(sessions[:5], 1):  # Show top 5
            print(f'{i}. Session: {session.get("session_id", "unknown")}')
            print(f'   Event: {session.get("event_id", "unknown")} ({session.get("event_name", "N/A")})')
            print(f'   Team: {session.get("team_name", "unknown")}')
            print(f'   Pitch: {session.get("pitch_title", "unknown")}')
            print(f'   Status: {session.get("status", "unknown")}')
            print(f'   Created: {session.get("created_at", "unknown")}')
            print(f'   Has Audio: {session.get("has_audio", False)}')
            
            transcript = session.get("final_transcript", {})
            transcript_text = transcript.get("total_text", "")
            print(f'   Transcript Available: {bool(transcript_text)}')
            if transcript_text:
                print(f'   Transcript Preview: {transcript_text[:100]}...')
            
            print(f'   Redis Key: {key}')
            print()
        
        if sessions:
            latest_session = sessions[0][1]
            print(f'🎯 Latest session details:')
            print(f'   Session ID: {latest_session.get("session_id")}')
            print(f'   Event ID: {latest_session.get("event_id")}')
            
            await redis_client.close()
            return latest_session.get('session_id'), latest_session.get('event_id')
        
        await redis_client.close()
        return None, None
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return None, None

if __name__ == "__main__":
    result = asyncio.run(list_existing_recordings())
    if result[0]:
        print(f'TARGET_SESSION_ID={result[0]}')
        print(f'TARGET_EVENT_ID={result[1]}')
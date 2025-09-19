#!/usr/bin/env python3
"""
List all sessions available in Gladia handler
"""
import asyncio
import json
import sys
import os
sys.path.append('/app')

async def list_gladia_sessions():
    print("📋 Listing all sessions in Gladia handler...")
    print("=" * 60)
    
    try:
        from domains.recordings.mcp.gladia_mcp_handler import gladia_mcp_handler
        
        # Get all sessions
        sessions = await gladia_mcp_handler.list_sessions()
        print(f"Found {sessions.get('total_count', 0)} sessions total")
        print()
        
        for i, session in enumerate(sessions.get('sessions', []), 1):
            print(f"{i}. Session: {session['session_id']}")
            print(f"   Team: {session.get('team_name', 'N/A')}")
            print(f"   Pitch: {session.get('pitch_title', 'N/A')}")
            print(f"   Status: {session.get('status', 'N/A')}")
            print(f"   Has Audio: {session.get('has_audio', False)}")
            print(f"   Transcript Segments: {session.get('transcript_segments', 0)}")
            print(f"   Created: {session.get('created_at', 'N/A')}")
            if 'completed_at' in session:
                print(f"   Completed: {session['completed_at']}")
            print()
        
        # Find the best session for testing (completed with audio)
        completed_sessions = [s for s in sessions.get('sessions', []) 
                            if s.get('status') == 'completed' and s.get('has_audio', False)]
        
        if completed_sessions:
            best_session = completed_sessions[0]  # Get the first completed session
            print("🎯 Best session for testing:")
            print(f"   SESSION_ID={best_session['session_id']}")
            return best_session['session_id']
        else:
            print("❌ No completed sessions with audio found")
            return None
        
    except Exception as e:
        print(f"❌ Error listing sessions: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(list_gladia_sessions())
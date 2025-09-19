#!/usr/bin/env python3
"""
Simple test for just the Gladia audio intelligence handler
"""
import asyncio
import json
import sys
import os
sys.path.append('/app')

async def test_gladia_handler():
    # Test session and event IDs from the listing
    session_id = "944a9aa4-ee61-4a44-bbb9-4a9ced07ac2b"  # Completed session with audio
    
    print(f"🔍 Testing Gladia audio intelligence handler")
    print(f"   Session: {session_id}")
    print("=" * 60)
    
    try:
        # Test Gladia MCP handler directly
        from domains.recordings.mcp.gladia_mcp_handler import gladia_mcp_handler
        
        # First, let's check if the session exists
        print("📋 Checking session status...")
        sessions = await gladia_mcp_handler.list_sessions()
        print(f"Found {sessions.get('total_count', 0)} sessions total")
        
        target_session = None
        for session in sessions.get('sessions', []):
            if session['session_id'] == session_id:
                target_session = session
                break
        
        if target_session:
            print("✅ Target session found:")
            print(json.dumps(target_session, indent=2))
        else:
            print("❌ Target session not found in listing")
            return
        
        print("\n" + "=" * 40)
        
        # Now test audio intelligence
        print("🎵 Testing get_audio_intelligence...")
        audio_intelligence_result = await gladia_mcp_handler.get_audio_intelligence(
            session_id=session_id
        )
        
        print("✅ Audio intelligence result:")
        print(json.dumps(audio_intelligence_result, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error testing Gladia handler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gladia_handler())
#!/usr/bin/env python3
"""
Direct test of audio intelligence handlers without full MCP server startup
"""
import asyncio
import json
import sys
import os
sys.path.append('/app')

async def test_direct_handlers():
    # Test session and event IDs from the listing
    session_id = "fe51a45f-5a80-48f7-a985-c1ca355b9434"
    event_id = "2d62de3f-6f3d-4896-8994-d9d5b26cd50a"
    
    print(f"🧪 Testing audio intelligence handlers directly")
    print(f"   Session: {session_id}")
    print(f"   Event: {event_id}")
    print("=" * 60)
    
    try:
        # Test Gladia MCP handler directly
        print("🔍 Testing Gladia MCP handler...")
        from domains.recordings.mcp.gladia_mcp_handler import gladia_mcp_handler
        
        audio_intelligence_result = await gladia_mcp_handler.get_audio_intelligence(
            session_id=session_id
        )
        
        print("✅ Gladia audio intelligence result:")
        print(json.dumps(audio_intelligence_result, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error testing Gladia handler: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    
    try:
        # Test Scoring MCP handler directly  
        print("🎯 Testing Scoring MCP handler...")
        from domains.scoring.mcp.scoring_mcp_handler import scoring_mcp_handler
        
        delivery_analysis = await scoring_mcp_handler.analyze_presentation_delivery(
            session_id=session_id,
            event_id=event_id
        )
        
        print("✅ Scoring presentation delivery analysis:")
        print(json.dumps(delivery_analysis, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error testing Scoring handler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_handlers())
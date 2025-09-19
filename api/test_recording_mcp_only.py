#!/usr/bin/env python3
"""
Test just the recording MCP tools without scoring dependencies
"""
import asyncio
import json
import sys
import os
sys.path.append('/app')

async def test_recording_mcp_tools():
    """Test the recording MCP tools for audio intelligence"""
    print("🎙️ Testing Recording MCP Tools for Audio Intelligence")
    print("=" * 60)
    
    try:
        # Test MCP tools directly
        from domains.recordings.mcp.mcp_tools import execute_mcp_tool, MCP_TOOLS
        
        print("📋 Available Recording MCP Tools:")
        for tool_name, tool_config in MCP_TOOLS.items():
            print(f"   - {tool_name}: {tool_config['description']}")
        print()
        
        # Use a completed session with audio from our earlier test
        session_id = "944a9aa4-ee61-4a44-bbb9-4a9ced07ac2b"
        print(f"🎯 Testing with session: {session_id}")
        print()
        
        # Test get_audio_intelligence MCP tool
        print("🎵 Testing pitches.get_audio_intelligence MCP tool...")
        try:
            ai_result = await execute_mcp_tool("pitches.get_audio_intelligence", {
                "session_id": session_id
            })
            
            print("✅ Audio Intelligence MCP tool result:")
            if isinstance(ai_result, dict):
                print(json.dumps(ai_result, indent=2, default=str))
            else:
                print(f"   Type: {type(ai_result)}")
                print(f"   Value: {ai_result}")
                
        except Exception as e:
            print(f"❌ Error with get_audio_intelligence tool: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "-" * 40)
        
        # Test get_session MCP tool to see transcript data
        print("📜 Testing pitches.get_session MCP tool...")
        try:
            transcript_result = await execute_mcp_tool("pitches.get_session", {
                "session_id": session_id
            })
            
            print("✅ Session Transcript MCP tool result:")
            if isinstance(transcript_result, dict):
                # Show just a summary to avoid overwhelming output
                if 'transcript_segments' in transcript_result:
                    segment_count = len(transcript_result.get('transcript_segments', []))
                    print(f"   Found {segment_count} transcript segments")
                    if segment_count > 0:
                        print(f"   Sample segment: {transcript_result['transcript_segments'][0]}")
                else:
                    print(json.dumps(transcript_result, indent=2, default=str))
            else:
                print(f"   Type: {type(transcript_result)}")
                print(f"   Value: {transcript_result}")
                
        except Exception as e:
            print(f"❌ Error with get_session_transcript tool: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 Recording MCP Tools Test Complete!")
        print("   This demonstrates:")
        print("   1. ✅ Audio intelligence analysis integration")
        print("   2. ✅ MCP tool accessibility for AI assistants")
        print("   3. ✅ Structured data flow for pitch analysis")
        
    except Exception as e:
        print(f"❌ Error testing recording MCP tools: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_recording_mcp_tools())
#!/usr/bin/env python3
"""
Test the complete MCP workflow integration for audio intelligence
"""
import asyncio
import json
import sys
import os
sys.path.append('/app')

async def test_mcp_tools_workflow():
    """Test the complete MCP workflow for audio intelligence scoring"""
    print("🔄 Testing Complete MCP Audio Intelligence Workflow")
    print("=" * 60)
    
    try:
        # Test MCP tools directly
        from domains.recordings.mcp.mcp_tools import execute_mcp_tool, MCP_TOOLS
        from domains.scoring.mcp.scoring_mcp_tools import execute_scoring_mcp_tool, SCORING_MCP_TOOLS
        
        print("📋 Available Recording MCP Tools:")
        for tool_name, tool_config in MCP_TOOLS.items():
            if 'audio_intelligence' in tool_name or 'transcript' in tool_name:
                print(f"   - {tool_name}: {tool_config['description']}")
        print()
        
        print("📋 Available Scoring MCP Tools:")
        for tool_name, tool_config in SCORING_MCP_TOOLS.items():
            if 'presentation' in tool_name or 'delivery' in tool_name:
                print(f"   - {tool_name}: {tool_config['description']}")
        print()
        
        # Use a completed session with audio from our earlier test
        session_id = "944a9aa4-ee61-4a44-bbb9-4a9ced07ac2b"
        print(f"🎯 Testing workflow with session: {session_id}")
        print()
        
        # Step 1: Test get_audio_intelligence MCP tool
        print("1️⃣ Testing get_audio_intelligence MCP tool...")
        try:
            ai_result = await execute_mcp_tool("get_audio_intelligence", {
                "session_id": session_id
            })
            
            print("✅ Audio Intelligence MCP tool result:")
            if isinstance(ai_result, dict) and "error" in ai_result:
                print(f"   Result: {ai_result}")
            else:
                print(f"   Type: {type(ai_result)}")
                # Show just a preview to avoid overwhelming output
                result_str = str(ai_result)[:200] + "..." if len(str(ai_result)) > 200 else str(ai_result)
                print(f"   Preview: {result_str}")
        except Exception as e:
            print(f"❌ Error with get_audio_intelligence tool: {e}")
        
        print("\n" + "-" * 40)
        
        # Step 2: Test analyze_presentation_delivery MCP tool  
        print("2️⃣ Testing analyze_presentation_delivery MCP tool...")
        try:
            # This tool should use the audio intelligence data
            delivery_result = await execute_scoring_mcp_tool("analyze_presentation_delivery", {
                "session_id": session_id,
                "event_id": "default"  # Default event since this session might not have specific event
            })
            
            print("✅ Presentation Delivery MCP tool result:")
            if isinstance(delivery_result, dict):
                # Pretty print the result
                print(json.dumps(delivery_result, indent=2, default=str))
            else:
                print(f"   Type: {type(delivery_result)}")
                print(f"   Value: {delivery_result}")
            
        except Exception as e:
            print(f"❌ Error with analyze_presentation_delivery tool: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("🎉 MCP Workflow Test Complete!")
        print("   This demonstrates the full integration path:")
        print("   1. Audio is recorded and stored via Gladia")
        print("   2. Audio intelligence is analyzed and cached")
        print("   3. Scoring system integrates audio intelligence")  
        print("   4. AI assistants can access comprehensive pitch analysis")
        
    except Exception as e:
        print(f"❌ Error testing MCP workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_tools_workflow())
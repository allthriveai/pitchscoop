#!/usr/bin/env python3
"""
Test script for audio intelligence MCP integration
"""
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_audio_intelligence():
    # Test session and event IDs from the listing
    session_id = "fe51a45f-5a80-48f7-a985-c1ca355b9434"
    event_id = "2d62de3f-6f3d-4896-8994-d9d5b26cd50a"
    
    print(f"🧪 Testing audio intelligence for session: {session_id}")
    print(f"   Event: {event_id}")
    print("=" * 60)
    
    try:
        # Connect to main PitchScoop MCP server
        server_params = StdioServerParameters(
            command="/usr/local/bin/python",
            args=["/app/mcp_server.py"],
            env={}
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # List available tools
                print("📋 Available tools:")
                tools = await session.list_tools()
                recording_tools = []
                scoring_tools = []
                for tool in tools.tools:
                    if 'audio_intelligence' in tool.name or 'transcript' in tool.name or tool.name.startswith('get_'):
                        recording_tools.append(tool)
                    elif 'presentation' in tool.name or 'delivery' in tool.name or tool.name.startswith('analyze_'):
                        scoring_tools.append(tool)
                
                print("   Recording & Audio Tools:")
                for tool in recording_tools:
                    print(f"     - {tool.name}: {tool.description}")
                
                print("   Scoring & Analysis Tools:")
                for tool in scoring_tools:
                    print(f"     - {tool.name}: {tool.description}")
                print()
                
                # Test get_audio_intelligence
                print("🔍 Testing get_audio_intelligence...")
                try:
                    result = await session.call_tool(
                        "get_audio_intelligence",
                        arguments={
                            "session_id": session_id,
                            "event_id": event_id
                        }
                    )
                    
                    print("✅ Audio intelligence result:")
                    for content in result.content:
                        if hasattr(content, 'text'):
                            # Pretty print JSON if possible
                            try:
                                data = json.loads(content.text)
                                print(json.dumps(data, indent=2))
                            except:
                                print(content.text)
                        else:
                            print(content)
                    
                except Exception as e:
                    print(f"❌ Error calling get_audio_intelligence: {e}")
                
                print("\n" + "=" * 60)
                
                # Test analyze_presentation_delivery
                print("🎤 Testing analyze_presentation_delivery...")
                try:
                    delivery_result = await session.call_tool(
                        "analyze_presentation_delivery",
                        arguments={
                            "session_id": session_id,
                            "event_id": event_id
                        }
                    )
                    
                    print("✅ Presentation delivery analysis:")
                    for content in delivery_result.content:
                        if hasattr(content, 'text'):
                            try:
                                data = json.loads(content.text)
                                print(json.dumps(data, indent=2))
                            except:
                                print(content.text)
                        else:
                            print(content)
                    
                except Exception as e:
                    print(f"❌ Error calling analyze_presentation_delivery: {e}")
                    
    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_audio_intelligence())
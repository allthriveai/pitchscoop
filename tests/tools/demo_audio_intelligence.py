#!/usr/bin/env python3
"""
Demo: Gladia Audio Intelligence Integration with Scoring

This script demonstrates how to use the new MCP tool for presentation delivery analysis
that combines transcript content analysis with Gladia Audio Intelligence metrics.
"""
import asyncio
import json

async def demo_presentation_delivery_analysis():
    """Demo the new presentation delivery analysis MCP tool."""
    
    print("🎪 Demo: Presentation Delivery Analysis with Audio Intelligence")
    print("=" * 70)
    
    # This would be provided by your MCP client
    demo_session_data = {
        "session_id": "demo-session-12345",
        "event_id": "hackathon-demo-2024",
        "team_name": "AI Innovators",
        "pitch_title": "SmartAgent: Revolutionary Customer Service AI"
    }
    
    print(f"📊 Analyzing presentation for: {demo_session_data['team_name']}")
    print(f"🎯 Pitch: {demo_session_data['pitch_title']}")
    print(f"🎪 Event: {demo_session_data['event_id']}")
    print()
    
    # Import the MCP tool execution function
    from api.domains.scoring.mcp.scoring_mcp_tools import execute_scoring_mcp_tool
    
    # Call the new MCP tool
    print("🔍 Calling analysis.analyze_presentation_delivery...")
    result = await execute_scoring_mcp_tool(
        "analysis.analyze_presentation_delivery",
        {
            "session_id": demo_session_data["session_id"],
            "event_id": demo_session_data["event_id"],
            "include_audio_metrics": True,
            "benchmark_wpm": 150
        }
    )
    
    print("\n📋 Analysis Results:")
    print("-" * 30)
    
    if result.get("success"):
        # Display content analysis
        content = result.get("content_analysis", {})
        print(f"📄 Content Analysis:")
        print(f"   Demo Clarity: {content.get('demo_clarity', 'N/A')}")
        print(f"   Impact Demo: {content.get('impact_demonstration', 'N/A')}")
        print(f"   Time Management: {content.get('time_management', 'N/A')}")
        print(f"   Content Score: {content.get('content_score', 0)}/10")
        
        # Display audio intelligence if available
        audio = result.get("audio_intelligence", {})
        if audio.get("available"):
            print(f"\n🎤 Audio Intelligence:")
            pace = audio.get("speech_pace", {})
            print(f"   Speaking Pace: {pace.get('words_per_minute', 0)} WPM ({pace.get('speaking_rate_assessment', 'unknown')})")
            
            quality = audio.get("delivery_quality", {})
            print(f"   Filler Words: {quality.get('filler_percentage', 0):.1f}% ({quality.get('professionalism_grade', 'unknown')})")
            
            confidence = audio.get("confidence_energy", {})
            print(f"   Confidence: {confidence.get('confidence_assessment', 'unknown')} ({confidence.get('confidence_score', 0):.2f})")
            print(f"   Energy Level: {confidence.get('energy_level', 'unknown')}")
        else:
            print(f"\n🎤 Audio Intelligence: Not available")
            print(f"   Reason: {audio.get('reason', 'Unknown')}")
        
        # Display final score
        score = result.get("presentation_delivery_score", {})
        final_score = score.get("final_score", 0)
        max_score = score.get("max_score", 25)
        print(f"\n🏆 Final Presentation Delivery Score: {final_score}/{max_score}")
        
        # Display insights
        insights = result.get("insights", {})
        strengths = insights.get("strengths", [])
        improvements = insights.get("areas_of_improvement", [])
        coaching = insights.get("coaching_recommendations", [])
        
        if strengths:
            print(f"\n✅ Strengths:")
            for strength in strengths[:3]:  # Show top 3
                print(f"   • {strength}")
        
        if improvements:
            print(f"\n📈 Areas of Improvement:")
            for improvement in improvements[:3]:  # Show top 3
                print(f"   • {improvement}")
        
        if coaching:
            print(f"\n🎯 Coaching Recommendations:")
            for rec in coaching[:3]:  # Show top 3
                print(f"   • {rec}")
    
    else:
        print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 70)
    print("✨ Demo complete! This shows how Audio Intelligence enhances presentation scoring.")


async def demo_tool_discovery():
    """Demo discovering the new MCP tool."""
    
    print("\n🔍 MCP Tool Discovery:")
    print("-" * 30)
    
    from api.domains.scoring.mcp.scoring_mcp_tools import SCORING_MCP_TOOLS
    
    # Show the new tool
    tool_name = "analysis.analyze_presentation_delivery"
    if tool_name in SCORING_MCP_TOOLS:
        tool_info = SCORING_MCP_TOOLS[tool_name]
        print(f"📋 Tool: {tool_info['name']}")
        print(f"📄 Description: {tool_info['description'][:100]}...")
        
        required_params = tool_info['inputSchema']['required']
        print(f"🔧 Required Parameters: {', '.join(required_params)}")
        
        optional_params = [
            param for param in tool_info['inputSchema']['properties'].keys()
            if param not in required_params
        ]
        if optional_params:
            print(f"⚙️  Optional Parameters: {', '.join(optional_params)}")
    
    print(f"\n📊 Total Scoring MCP Tools Available: {len(SCORING_MCP_TOOLS)}")
    for tool_name in SCORING_MCP_TOOLS.keys():
        print(f"   • {tool_name}")


if __name__ == "__main__":
    print("🚀 Starting Audio Intelligence MCP Demo...")
    
    asyncio.run(demo_tool_discovery())
    
    print("\n" + "🎵" * 20 + " AUDIO INTELLIGENCE DEMO " + "🎵" * 20)
    
    # Note: This demo would need actual session data to work fully
    print("📝 Note: This demo shows the MCP tool interface.")
    print("📝 For full functionality, you need:")
    print("   • A completed pitch recording session")
    print("   • Gladia STT transcription") 
    print("   • Audio Intelligence processing")
    print("   • Redis session storage")
    
    print("\n🎯 Key Benefits of Audio Intelligence Integration:")
    print("   ✅ Objective presentation delivery metrics")
    print("   ✅ Data-driven coaching recommendations") 
    print("   ✅ Fair, consistent scoring across participants")
    print("   ✅ Actionable feedback with specific WPM and filler data")
    print("   ✅ Enhanced judge decision-making with audio evidence")
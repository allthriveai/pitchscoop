#!/usr/bin/env python3
"""
Test script for Leaderboard MCP Tools.

This script tests the new leaderboard functionality with real data
from your existing scoring system.
"""

import asyncio
import pytest

from api.domains.leaderboards.mcp.leaderboard_mcp_tools import execute_leaderboard_mcp_tool


@pytest.mark.asyncio
async def test_leaderboard_with_real_data():
    """Test leaderboard MCP tools with existing event data."""
    
    print("🏆 Testing Leaderboard MCP Tools")
    print("=" * 50)
    
    # Use a test event ID - replace with actual event ID if you have one
    test_event_id = "ai-hackathon-2024"
    
    print(f"\n1. Testing leaderboard.get_rankings for event: {test_event_id}")
    print("-" * 60)
    
    # Test 1: Get top 10 rankings
    rankings_result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_rankings",
        {
            "event_id": test_event_id,
            "limit": 10,
            "include_details": True
        }
    )
    
    if rankings_result.get("success"):
        leaderboard = rankings_result.get("leaderboard", [])
        total_teams = rankings_result.get("total_teams", 0)
        
        print(f"✅ Success! Found {total_teams} teams total")
        print(f"📊 Showing top {len(leaderboard)} teams:")
        
        for entry in leaderboard:
            rank = entry.get("rank", "?")
            team_name = entry.get("team_name", "Unknown Team")
            total_score = entry.get("total_score", 0)
            pitch_title = entry.get("pitch_title", "No title")
            
            print(f"  #{rank}: {team_name} - {total_score:.1f} pts")
            print(f"        Pitch: {pitch_title}")
            
            # Show category breakdown
            category_scores = entry.get("category_scores", {})
            print(f"        Categories: Idea={category_scores.get('idea_score', 0):.1f}, "
                  f"Technical={category_scores.get('technical_score', 0):.1f}, "
                  f"Tools={category_scores.get('tool_use_score', 0):.1f}, "
                  f"Presentation={category_scores.get('presentation_score', 0):.1f}")
            print()
    else:
        print(f"❌ Error getting rankings: {rankings_result.get('error')}")
        if "No scored pitches found" in str(rankings_result.get('error', '')):
            print("💡 This is expected if no teams have been scored yet.")
    
    print(f"\n2. Testing leaderboard.get_stats for event: {test_event_id}")
    print("-" * 60)
    
    # Test 2: Get event statistics
    stats_result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_stats",
        {"event_id": test_event_id}
    )
    
    if stats_result.get("success"):
        stats = stats_result.get("stats", {})
        print(f"✅ Statistics generated successfully:")
        print(f"  📈 Total Teams: {stats.get('total_teams', 0)}")
        print(f"  🏅 Highest Score: {stats.get('highest_score', 0):.1f}")
        print(f"  📊 Average Score: {stats.get('average_score', 0):.1f}")
        print(f"  📉 Lowest Score: {stats.get('lowest_score', 0):.1f}")
        
        distribution = stats.get("score_distribution", {})
        print(f"  🎯 Score Distribution:")
        print(f"    90-100: {distribution.get('90_100', 0)} teams")
        print(f"    80-89:  {distribution.get('80_89', 0)} teams")
        print(f"    70-79:  {distribution.get('70_79', 0)} teams")
        print(f"    60-69:  {distribution.get('60_69', 0)} teams")
        print(f"    <60:    {distribution.get('below_60', 0)} teams")
    else:
        print(f"❌ Error getting stats: {stats_result.get('error')}")
        if stats_result.get('message'):
            print(f"💡 {stats_result.get('message')}")
    
    # Test 3: Test individual team rank (only if we found teams)
    if rankings_result.get("success") and rankings_result.get("leaderboard"):
        first_team = rankings_result["leaderboard"][0]
        test_session_id = first_team.get("session_id")
        
        if test_session_id:
            print(f"\n3. Testing leaderboard.get_team_rank for session: {test_session_id}")
            print("-" * 60)
            
            team_rank_result = await execute_leaderboard_mcp_tool(
                "leaderboard.get_team_rank",
                {
                    "event_id": test_event_id,
                    "session_id": test_session_id
                }
            )
            
            if team_rank_result.get("success"):
                print(f"✅ Team rank retrieved successfully:")
                print(f"  🏆 Rank: #{team_rank_result.get('rank')}")
                print(f"  👥 Team: {team_rank_result.get('team_name')}")
                print(f"  📊 Score: {team_rank_result.get('total_score'):.1f}")
                print(f"  🎯 Out of {team_rank_result.get('total_teams')} teams")
                
                category_scores = team_rank_result.get("category_scores", {})
                print(f"  📈 Category Breakdown:")
                print(f"    Idea: {category_scores.get('idea_score', 0):.1f}")
                print(f"    Technical: {category_scores.get('technical_score', 0):.1f}")
                print(f"    Tool Use: {category_scores.get('tool_use_score', 0):.1f}")
                print(f"    Presentation: {category_scores.get('presentation_score', 0):.1f}")
            else:
                print(f"❌ Error getting team rank: {team_rank_result.get('error')}")
    
    print(f"\n🎉 Leaderboard MCP Testing Complete!")
    print("=" * 50)


@pytest.mark.asyncio
async def test_with_different_events():
    """Test with multiple event IDs to show multi-tenant isolation."""
    
    print(f"\n🔄 Testing Multi-Tenant Event Isolation")
    print("-" * 50)
    
    test_events = [
        "hackathon-demo-2024",
        "vc-pitch-contest",  
        "practice-session-001"
    ]
    
    for event_id in test_events:
        print(f"\nTesting event: {event_id}")
        
        result = await execute_leaderboard_mcp_tool(
            "leaderboard.get_rankings",
            {"event_id": event_id, "limit": 3}
        )
        
        if result.get("success"):
            total = result.get("total_teams", 0)
            print(f"  ✅ Found {total} teams in event {event_id}")
        else:
            print(f"  ℹ️  No data for event {event_id}")


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling with invalid parameters."""
    
    print(f"\n🔧 Testing Error Handling")
    print("-" * 50)
    
    # Test missing event_id
    print("Testing missing event_id...")
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_rankings",
        {"limit": 5}
    )
    print(f"  Expected error: {result.get('error', 'No error?')}")
    
    # Test invalid limit
    print("\nTesting invalid limit...")
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_rankings",
        {"event_id": "test", "limit": -5}
    )
    print(f"  Expected error: {result.get('error', 'No error?')}")
    
    # Test unknown tool
    print("\nTesting unknown tool...")
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.invalid_tool",
        {"event_id": "test"}
    )
    print(f"  Expected error: {result.get('error', 'No error?')}")


if __name__ == "__main__":
    async def run_all_tests():
        await test_leaderboard_with_real_data()
        await test_with_different_events()
        await test_error_handling()
    
    # Run the test
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
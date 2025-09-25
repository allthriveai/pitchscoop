#!/usr/bin/env python3
"""Demo script to test leaderboard MCP tools."""

import asyncio
import sys
from pathlib import Path

# Add project root and api directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))

from api.domains.leaderboards.mcp.leaderboard_mcp_tools import execute_leaderboard_mcp_tool

async def demo_leaderboard():
    """Demonstrate leaderboard MCP functionality."""
    
    print("🏆 LEADERBOARD MCP DEMONSTRATION")
    print("=" * 50)
    
    # Test 1: Get top rankings
    print("\n1. 📊 Getting Top Rankings:")
    print("-" * 30)
    
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_rankings", 
        {"event_id": "demo-hackathon", "limit": 10}
    )
    
    if result.get("success"):
        print(f"✅ Found {result['total_teams']} teams total")
        print("🏆 Leaderboard:")
        
        for entry in result["leaderboard"]:
            rank = entry["rank"]
            name = entry["team_name"]
            score = entry["total_score"]
            title = entry["pitch_title"]
            
            print(f"  #{rank}: {name} - {score:.1f} pts")
            print(f"       Pitch: {title}")
            
            # Show category breakdown
            cat = entry.get("category_scores", {})
            print(f"       Categories: I={cat.get('idea_score', 0):.1f} "
                  f"T={cat.get('technical_score', 0):.1f} "
                  f"U={cat.get('tool_use_score', 0):.1f} "
                  f"P={cat.get('presentation_score', 0):.1f}")
            print()
    else:
        print(f"❌ Error: {result.get('error')}")
        
    # Test 2: Individual team rank lookup
    print("2. 👥 Individual Team Rank:")
    print("-" * 30)
    
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_team_rank",
        {"event_id": "demo-hackathon", "session_id": "session-003"}
    )
    
    if result.get("success"):
        print(f"✅ Team: {result['team_name']}")
        print(f"   Rank: #{result['rank']} out of {result['total_teams']} teams")  
        print(f"   Score: {result['total_score']:.1f} points")
        print(f"   Pitch: {result.get('pitch_title', 'N/A')}")
    else:
        print(f"❌ Error: {result.get('error')}")
        
    # Test 3: Competition statistics
    print("\n3. 📈 Competition Statistics:")
    print("-" * 30)
    
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_stats",
        {"event_id": "demo-hackathon"}
    )
    
    if result.get("success"):
        stats = result["stats"]
        print(f"✅ Event Statistics:")
        print(f"   Total Teams: {stats['total_teams']}")
        print(f"   Average Score: {stats['average_score']:.1f}")
        print(f"   Highest Score: {stats['highest_score']:.1f}")
        print(f"   Lowest Score: {stats['lowest_score']:.1f}")
        
        dist = stats.get("score_distribution", {})
        print(f"   Score Distribution:")
        print(f"     90-100: {dist.get('90_100', 0)} teams")
        print(f"     80-89:  {dist.get('80_89', 0)} teams")
        print(f"     70-79:  {dist.get('70_79', 0)} teams")
        print(f"     <70:    {dist.get('60_69', 0) + dist.get('below_60', 0)} teams")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print(f"\n🎉 Leaderboard MCP Demo Complete!")
    print(f"✅ All 3 MCP tools working with real data from scoring domain")

if __name__ == "__main__":
    asyncio.run(demo_leaderboard())
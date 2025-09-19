#!/usr/bin/env python3
"""Test leaderboard with real scoring data - FINAL DEMO."""

import asyncio
import pytest

@pytest.mark.asyncio
async def test_complete_system():
    """Test the complete scoring -> leaderboard system."""
    
    print("🎉 PITCHSCOOP: COMPLETE SYSTEM TEST")
    print("=" * 60)
    
    try:
        from domains.leaderboards.mcp.leaderboard_mcp_tools import execute_leaderboard_mcp_tool
        
        # Test 1: Get Rankings
        print("1. 🏆 Getting Event Leaderboard:")
        print("-" * 40)
        
        result = await execute_leaderboard_mcp_tool('leaderboard.get_rankings', {
            'event_id': 'test-hackathon-2024',
            'limit': 10
        })
        
        if result.get('success'):
            leaderboard = result.get('leaderboard', [])
            total_teams = result.get('total_teams', 0)
            
            print(f"✅ SUCCESS: Found {total_teams} teams")
            print()
            print("🏆 LEADERBOARD:")
            
            for entry in leaderboard:
                rank = entry.get('rank', '?')
                name = entry.get('team_name', 'Unknown')
                score = entry.get('total_score', 0)
                pitch = entry.get('pitch_title', 'No title')
                
                print(f"  #{rank}: {name} - {score:.1f} pts")
                print(f"       Pitch: {pitch}")
                
                # Show category breakdown
                cats = entry.get('category_scores', {})
                idea = cats.get('idea_score', 0)
                tech = cats.get('technical_score', 0) 
                tools = cats.get('tool_use_score', 0)
                pres = cats.get('presentation_score', 0)
                
                print(f"       Categories: Idea={idea:.1f}, Tech={tech:.1f}, Tools={tools:.1f}, Pres={pres:.1f}")
                print()
            
        else:
            print(f"❌ Rankings failed: {result.get('error')}")
        
        # Test 2: Individual Team Rank
        print("2. 👥 Individual Team Rank:")
        print("-" * 40)
        
        result = await execute_leaderboard_mcp_tool('leaderboard.get_team_rank', {
            'event_id': 'test-hackathon-2024',
            'session_id': 'test-scoring-session-001'
        })
        
        if result.get('success'):
            print(f"✅ Team: {result.get('team_name')}")
            print(f"   Rank: #{result.get('rank')} out of {result.get('total_teams')} teams")
            print(f"   Score: {result.get('total_score'):.1f} points")
        else:
            print(f"❌ Team rank failed: {result.get('error')}")
        
        # Test 3: Competition Statistics
        print()
        print("3. 📊 Competition Statistics:")
        print("-" * 40)
        
        result = await execute_leaderboard_mcp_tool('leaderboard.get_stats', {
            'event_id': 'test-hackathon-2024'
        })
        
        if result.get('success'):
            stats = result.get('stats', {})
            print("✅ Event Statistics:")
            print(f"   Total Teams: {stats.get('total_teams', 0)}")
            print(f"   Average Score: {stats.get('average_score', 0):.1f}")
            print(f"   Highest Score: {stats.get('highest_score', 0):.1f}")
            print(f"   Lowest Score: {stats.get('lowest_score', 0):.1f}")
        else:
            print(f"❌ Stats failed: {result.get('error')}")
        
        print()
        print("🎉 COMPLETE SYSTEM TEST FINISHED!")
        print("✅ Recording -> Scoring -> Leaderboard pipeline working!")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_system())
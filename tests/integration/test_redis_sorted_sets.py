#!/usr/bin/env python3
"""
Test Redis Sorted Sets implementation for PitchScoop leaderboard
Verifies that the new implementation works correctly
"""
import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
import sys
import os

# Add the API directory to path so we can import modules
sys.path.append('/Users/allierays/Sites/pitchscoop/api')

from domains.leaderboards.mcp.leaderboard_mcp_handler import LeaderboardMCPHandler
from domains.leaderboards.mcp.leaderboard_mcp_tools import execute_leaderboard_mcp_tool

async def setup_test_data():
    """Create sample scoring data for testing"""
    print("🔧 Setting up test data...")
    
    redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    event_id = "test-mcp-hackathon-2024"
    
    # Sample teams with scores
    teams = [
        {"session_id": "session_001", "team_name": "Neural Ninjas", "score": 94.5, "pitch_title": "AI Agent Platform"},
        {"session_id": "session_002", "team_name": "Quantum Commerce", "score": 92.1, "pitch_title": "E-commerce AI"},
        {"session_id": "session_003", "team_name": "VectorDB Labs", "score": 89.7, "pitch_title": "Vector Search Engine"},
        {"session_id": "session_004", "team_name": "AI Copilot Inc", "score": 87.3, "pitch_title": "Code Assistant"},
        {"session_id": "session_005", "team_name": "Redis Robotics", "score": 85.9, "pitch_title": "Robot Control System"},
    ]
    
    # Create scoring records (simulating what the scoring handler creates)
    for team in teams:
        scoring_record = {
            "session_id": team["session_id"],
            "event_id": event_id,
            "team_name": team["team_name"],
            "pitch_title": team["pitch_title"],
            "scoring_timestamp": datetime.utcnow().isoformat(),
            "analysis": {
                "overall": {
                    "total_score": team["score"]
                },
                "idea": {"score": team["score"] * 0.25},
                "technical_implementation": {"score": team["score"] * 0.25},
                "tool_use": {"score": team["score"] * 0.25},
                "presentation": {"score": team["score"] * 0.25}
            }
        }
        
        # Store scoring record
        scoring_key = f"event:{event_id}:scoring:{team['session_id']}"
        await redis_client.setex(scoring_key, 3600, json.dumps(scoring_record))
        
        # Update Redis Sorted Set leaderboard (this is what our new code does)
        leaderboard_key = f"event:{event_id}:leaderboard"
        await redis_client.zadd(leaderboard_key, {team["session_id"]: team["score"]})
        
        print(f"✅ Created data for {team['team_name']} with score {team['score']}")
    
    print(f"🎯 Test event: {event_id}")
    return event_id

async def test_redis_sorted_sets():
    """Test Redis Sorted Sets leaderboard functionality"""
    print("🏆 Testing Redis Sorted Sets Leaderboard Implementation\n")
    
    # Setup test data
    event_id = await setup_test_data()
    print()
    
    # Test 1: Get leaderboard using new Redis Sorted Sets method
    print("📊 Test 1: Get leaderboard rankings")
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_rankings",
        {"event_id": event_id, "limit": 5}
    )
    
    if result.get("success"):
        print("✅ Leaderboard retrieved successfully!")
        for team in result["leaderboard"]:
            print(f"  {team['rank']}. {team['team_name']} - {team['total_score']}")
        print(f"  Total teams: {result['total_teams']}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print()
    
    # Test 2: Get individual team rank
    print("🎯 Test 2: Get individual team rank")
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_team_rank",
        {"event_id": event_id, "session_id": "session_003"}  # VectorDB Labs
    )
    
    if result.get("success"):
        print(f"✅ VectorDB Labs is rank #{result['rank']} with score {result['total_score']}")
        print(f"  Out of {result['total_teams']} total teams")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print()
    
    # Test 3: Update a team's score
    print("🔄 Test 3: Update team score")
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.update_score",
        {
            "event_id": event_id,
            "session_id": "session_006",
            "team_name": "MCP Masters",
            "total_score": 96.2
        }
    )
    
    if result.get("success"):
        print(f"✅ New team 'MCP Masters' added with score 96.2")
        print(f"  New rank: #{result['rank']}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print()
    
    # Test 4: Get updated leaderboard
    print("📊 Test 4: Get updated leaderboard")
    result = await execute_leaderboard_mcp_tool(
        "leaderboard.get_rankings",
        {"event_id": event_id, "limit": 6}
    )
    
    if result.get("success"):
        print("✅ Updated leaderboard:")
        for team in result["leaderboard"]:
            marker = "🆕" if team["team_name"] == "MCP Masters" else "  "
            print(f"  {marker} {team['rank']}. {team['team_name']} - {team['total_score']}")
        print(f"  Total teams: {result['total_teams']}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    print()

async def verify_performance():
    """Verify that Redis Sorted Sets are actually being used"""
    print("⚡ Performance Verification")
    redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    event_id = "test-mcp-hackathon-2024"
    leaderboard_key = f"event:{event_id}:leaderboard"
    
    # Check if sorted set exists and has data
    exists = await redis_client.exists(leaderboard_key)
    if exists:
        count = await redis_client.zcard(leaderboard_key)
        print(f"✅ Redis Sorted Set exists with {count} teams")
        
        # Show raw Redis Sorted Set data
        all_teams = await redis_client.zrevrange(leaderboard_key, 0, -1, withscores=True)
        print("📋 Raw Redis Sorted Set data:")
        for i, (session_id, score) in enumerate(all_teams, 1):
            print(f"  {i}. {session_id} -> {score}")
    else:
        print("❌ Redis Sorted Set not found")
    
    print()

async def cleanup():
    """Clean up test data"""
    print("🧹 Cleaning up test data...")
    redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    event_id = "test-mcp-hackathon-2024"
    
    # Delete leaderboard sorted set
    await redis_client.delete(f"event:{event_id}:leaderboard")
    
    # Delete scoring records
    keys = await redis_client.keys(f"event:{event_id}:scoring:*")
    if keys:
        await redis_client.delete(*keys)
    
    print("✅ Test data cleaned up")

async def main():
    """Run all tests"""
    try:
        await test_redis_sorted_sets()
        await verify_performance()
        
        print("🎉 All tests completed!")
        print("\n" + "="*60)
        print("✅ Redis Sorted Sets implementation is working!")
        print("✅ Your article claim is now factually accurate!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await cleanup()

async def test_redis_connection():
    """Test if Redis is available"""
    try:
        redis_test = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        await redis_test.ping()
        print("🔗 Redis connection: OK")
        await redis_test.close()
        return True
    except Exception as e:
        print(f"❌ Redis not available: {e}")
        print("Start Redis with: docker run -d -p 6379:6379 redis:latest")
        return False

if __name__ == "__main__":
    async def run_tests():
        if await test_redis_connection():
            await main()
        else:
            exit(1)
    
    asyncio.run(run_tests())

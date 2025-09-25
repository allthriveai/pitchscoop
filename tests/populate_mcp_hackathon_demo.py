#!/usr/bin/env python3
"""
Populate MCP Hackathon Demo Data

This script creates hardcoded demo scoring data for the "mcp-hackathon" event
to showcase the leaderboard functionality at http://localhost:8000/leaderboard
"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Demo teams with realistic hackathon project scores (out of 100)
DEMO_TEAMS = [
    {
        "session_id": "session-mcp-001",
        "team_name": "CodeCrafters",
        "pitch_title": "AI-Powered Code Review Assistant",
        "total_score": 92.3,
        "scores": {
            "idea_score": 23.1,  # 25% weight
            "technical_score": 22.0,  # 25% weight
            "tool_use_score": 23.8,  # 25% weight
            "presentation_score": 23.4   # 25% weight
        }
    },
    {
        "session_id": "session-mcp-002", 
        "team_name": "DataWizards",
        "pitch_title": "Real-time Analytics Dashboard with MCP Integration",
        "total_score": 90.1,
        "scores": {
            "idea_score": 21.8,
            "technical_score": 23.6,
            "tool_use_score": 22.5,
            "presentation_score": 22.2
        }
    },
    {
        "session_id": "session-mcp-003",
        "team_name": "InnovateNow",
        "pitch_title": "Smart Home Automation Hub",
        "total_score": 86.5,
        "scores": {
            "idea_score": 21.4,
            "technical_score": 20.5,
            "tool_use_score": 21.9,
            "presentation_score": 22.7
        }
    },
    {
        "session_id": "session-mcp-004",
        "team_name": "TechTitans",
        "pitch_title": "Blockchain-Based Supply Chain Tracker",
        "total_score": 87.1,
        "scores": {
            "idea_score": 22.5,
            "technical_score": 21.6,
            "tool_use_score": 22.0,
            "presentation_score": 21.0
        }
    },
    {
        "session_id": "session-mcp-005",
        "team_name": "CloudPioneers",
        "pitch_title": "Serverless ML Model Deployment Platform",
        "total_score": 88.4,
        "scores": {
            "idea_score": 22.4,
            "technical_score": 22.8,
            "tool_use_score": 21.4,
            "presentation_score": 21.8
        }
    },
    {
        "session_id": "session-mcp-006",
        "team_name": "DevDreamers",
        "pitch_title": "Voice-Controlled Development Environment",
        "total_score": 86.1,
        "scores": {
            "idea_score": 20.8,
            "technical_score": 22.3,
            "tool_use_score": 23.0,
            "presentation_score": 20.0
        }
    },
    {
        "session_id": "session-mcp-007",
        "team_name": "ByteBuilders", 
        "pitch_title": "Collaborative 3D Modeling Tool",
        "total_score": 87.0,
        "scores": {
            "idea_score": 21.5,
            "technical_score": 21.1,
            "tool_use_score": 22.4,
            "presentation_score": 22.0
        }
    },
    {
        "session_id": "session-mcp-008",
        "team_name": "AlgoAces",
        "pitch_title": "Quantum Computing Algorithm Simulator",
        "total_score": 87.8,
        "scores": {
            "idea_score": 23.5,
            "technical_score": 21.8,
            "tool_use_score": 20.9,
            "presentation_score": 21.6
        }
    },
    {
        "session_id": "session-mcp-009",
        "team_name": "WebWeavers",
        "pitch_title": "Progressive Web App Framework",
        "total_score": 87.5,
        "scores": {
            "idea_score": 20.4,
            "technical_score": 22.6,
            "tool_use_score": 21.5,
            "presentation_score": 23.0
        }
    },
    {
        "session_id": "session-mcp-010",
        "team_name": "APIArchitects",
        "pitch_title": "GraphQL Schema Generator with AI",
        "total_score": 87.0,
        "scores": {
            "idea_score": 22.0,
            "technical_score": 21.4,
            "tool_use_score": 22.9,
            "presentation_score": 20.7
        }
    },
    {
        "session_id": "session-mcp-011",
        "team_name": "MobileMinds",
        "pitch_title": "Cross-Platform AR Shopping Experience",
        "total_score": 87.9,
        "scores": {
            "idea_score": 23.0,
            "technical_score": 20.8,
            "tool_use_score": 21.8,
            "presentation_score": 22.3
        }
    },
    {
        "session_id": "session-mcp-012",
        "team_name": "SecuritySquad", 
        "pitch_title": "Zero-Trust Network Security Scanner",
        "total_score": 87.3,
        "scores": {
            "idea_score": 21.9,
            "technical_score": 23.1,
            "tool_use_score": 21.0,
            "presentation_score": 21.3
        }
    }
]

EVENT_ID = "mcp-hackathon"


async def get_redis_client():
    """Get Redis client connection."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        # Try Docker first
        client = redis.from_url("redis://redis:6379/0", decode_responses=True)
        await client.ping()
        return client
    except Exception:
        # Fallback to localhost
        return redis.from_url("redis://localhost:6379/0", decode_responses=True)


async def create_scoring_data(team_data):
    """Create realistic scoring data structure for a team."""
    scores = team_data.get("scores", {})
    total_score = team_data["total_score"]  # Use the pre-calculated total score out of 100
    
    # Create timestamp (random time in the last 3 days)
    base_time = datetime.utcnow() - timedelta(days=3)
    scoring_timestamp = base_time + timedelta(
        hours=hash(team_data["session_id"]) % 72  # Deterministic but varied
    )
    
    scoring_data = {
        "session_id": team_data["session_id"],
        "team_name": team_data["team_name"],
        "pitch_title": team_data["pitch_title"],
        "event_id": EVENT_ID,
        "scoring_timestamp": scoring_timestamp.isoformat(),
        "scoring_method": "ai_analysis",
        "analysis": {
            "idea": {
                "score": scores.get("idea_score", total_score * 0.25),
                "reasoning": f"Strong concept with good market potential. The {team_data['pitch_title']} addresses a real problem.",
                "strengths": ["Innovation", "Market fit", "Scalability"],
                "improvements": ["User research", "Competitive analysis"]
            },
            "technical_implementation": {
                "score": scores.get("technical_score", total_score * 0.25), 
                "reasoning": "Solid technical approach with good architecture decisions.",
                "strengths": ["Clean code", "Good patterns", "Performance"],
                "improvements": ["Error handling", "Testing coverage"]
            },
            "tool_use": {
                "score": scores.get("tool_use_score", total_score * 0.25),
                "reasoning": "Excellent integration of sponsor tools and APIs.",
                "strengths": ["API integration", "Tool selection", "Documentation"],
                "improvements": ["Performance optimization", "Error handling"]
            },
            "presentation": {
                "score": scores.get("presentation_score", total_score * 0.25),
                "reasoning": "Well-structured presentation with clear communication.",
                "strengths": ["Clear messaging", "Good visuals", "Time management"],
                "improvements": ["More demos", "Q&A handling"]
            },
            "overall": {
                "total_score": total_score,
                "summary": f"Impressive project by {team_data['team_name']}. Great work on {team_data['pitch_title']}!",
                "recommendation": "Strong contender with solid execution across all categories."
            }
        },
        "total_score": total_score  # Store the 100-point scale total
    }
    
    return scoring_data


async def populate_demo_data():
    """Populate Redis with MCP hackathon demo data."""
    print("🏆 MCP HACKATHON DEMO DATA POPULATION")
    print("=" * 50)
    
    try:
        # Connect to Redis
        redis_client = await get_redis_client()
        print(f"✅ Connected to Redis")
        
        # Clear any existing demo data
        pattern = f"event:{EVENT_ID}:scoring:*"
        existing_keys = await redis_client.keys(pattern)
        if existing_keys:
            await redis_client.delete(*existing_keys)
            print(f"🧹 Cleaned up {len(existing_keys)} existing demo records")
        
        # Create and store scoring data for each team
        print(f"\n📊 Creating scoring data for {len(DEMO_TEAMS)} teams...")
        
        for i, team_data in enumerate(DEMO_TEAMS, 1):
            scoring_data = await create_scoring_data(team_data)
            scoring_key = f"event:{EVENT_ID}:scoring:{team_data['session_id']}"
            
            # Store in Redis as JSON
            await redis_client.set(
                scoring_key, 
                json.dumps(scoring_data, indent=2),
                ex=86400 * 7  # Expire in 7 days
            )
            
            print(f"  {i:2d}. {team_data['team_name']:15s} - {scoring_data['total_score']:6.1f} pts - {team_data['pitch_title']}")
        
        # Also create event metadata
        event_key = f"event:{EVENT_ID}"
        event_data = {
            "event_id": EVENT_ID,
            "event_name": "MCP Hackathon 2024", 
            "event_type": "hackathon",
            "status": "completed",
            "judges": json.dumps(["AI Judge", "Technical Judge", "Industry Judge"]),
            "rules": json.dumps({
                "time_limit": "5 minutes",
                "categories": ["idea", "technical", "tools", "presentation"],
                "max_score_per_category": 100
            }),
            "goals": json.dumps([
                "Build innovative solutions using MCP protocol",
                "Demonstrate technical excellence", 
                "Showcase sponsor tool integration",
                "Present clearly and effectively"
            ]),
            "sponsor_tools": json.dumps([
                "OpenAI API", "Anthropic Claude", "Redis", "MinIO",
                "FastAPI", "Docker", "Python", "TypeScript"
            ]),
            "created_at": (datetime.utcnow() - timedelta(days=5)).isoformat(),
            "started_at": (datetime.utcnow() - timedelta(days=3)).isoformat(),
            "ended_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
        }
        
        await redis_client.hset(event_key, mapping=event_data)
        print(f"✅ Created event metadata for {EVENT_ID}")
        
        await redis_client.close()
        
        print(f"\n🎉 SUCCESS: Demo data populated!")
        print(f"📍 Event ID: {EVENT_ID}")
        print(f"👥 Teams: {len(DEMO_TEAMS)}")
        print(f"🏆 Ready for leaderboard at: http://localhost:8000/leaderboard")
        print(f"💡 In the web interface, enter '{EVENT_ID}' as the Event ID")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(populate_demo_data())
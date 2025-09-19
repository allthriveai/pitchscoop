#!/usr/bin/env python3
"""Test scoring system on real session data."""

import asyncio
import pytest

@pytest.mark.asyncio
async def test_scoring():
    """Test scoring on a real session."""
    
    print("🧪 TESTING SCORING SYSTEM")
    print("=" * 40)
    
    try:
        from domains.scoring.mcp.scoring_mcp_handler import ScoringMCPHandler
        print("✅ Scoring handler imported successfully")
        
        handler = ScoringMCPHandler()
        
        # Test on the real session we found
        session_id = "f51f80d9-98dd-4ee0-9e11-a2a063886409"
        event_id = "hackathon-2024"
        
        print(f"📋 Testing session: {session_id}")
        print(f"📋 Event: {event_id}")
        
        result = await handler.score_complete_pitch(
            session_id=session_id,
            event_id=event_id
        )
        
        print(f"\n📊 Result:")
        print(f"   Success: {result.get('success')}")
        
        if result.get('success'):
            print("🎉 SCORING WORKED!")
            
            team_name = result.get('team_name', 'Unknown')
            print(f"   Team: {team_name}")
            
            scores = result.get('scores', {})
            print(f"   Scores type: {type(scores)}")
            
            if isinstance(scores, dict):
                print(f"   Score keys: {list(scores.keys())}")
                
                # Try different ways to get total score
                total_score = None
                if 'overall' in scores and isinstance(scores['overall'], dict):
                    total_score = scores['overall'].get('total_score')
                elif 'total_score' in scores:
                    total_score = scores.get('total_score')
                    
                print(f"   Total Score: {total_score}")
                
                # Show category scores
                categories = ['idea', 'technical_implementation', 'tool_use', 'presentation']
                for cat in categories:
                    if cat in scores and isinstance(scores[cat], dict):
                        cat_score = scores[cat].get('score', 'N/A')
                        print(f"   {cat.replace('_', ' ').title()}: {cat_score}")
            
            print(f"   Timestamp: {result.get('scoring_timestamp', 'N/A')}")
            
        else:
            print("❌ SCORING FAILED")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Error Type: {result.get('error_type', 'Unknown type')}")
    
    except Exception as e:
        print(f"❌ Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scoring())
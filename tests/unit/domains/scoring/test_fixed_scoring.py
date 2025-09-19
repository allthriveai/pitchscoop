#!/usr/bin/env python3
"""Test fixed scoring system with JSON serialization."""

import asyncio
import pytest

@pytest.mark.asyncio
async def test_fixed_scoring():
    """Test the fixed scoring system."""
    
    print("🔧 Testing Fixed Scoring System with JSON Serialization")
    print("=" * 60)
    
    try:
        from domains.scoring.mcp.scoring_mcp_handler import ScoringMCPHandler
        
        handler = ScoringMCPHandler()
        result = await handler.score_complete_pitch(
            session_id='test-scoring-session-001',
            event_id='test-hackathon-2024'
        )
        
        print(f"📊 Result:")
        print(f"   Success: {result.get('success')}")
        
        if result.get('success'):
            print("🎉 SCORING AND STORAGE SUCCESS!")
            print(f"   Team: {result.get('team_name')}")
            
            scores = result.get('scores', {})
            if 'overall' in scores:
                total = scores['overall'].get('total_score', 'N/A')
                print(f"   Total Score: {total}")
                
                # Show category breakdown
                categories = ['idea', 'technical_implementation', 'tool_use', 'presentation_delivery']
                for cat in categories:
                    if cat in scores and isinstance(scores[cat], dict):
                        cat_score = scores[cat].get('score', 'N/A')
                        cat_name = cat.replace('_', ' ').title()
                        print(f"   {cat_name}: {cat_score}")
            
            print(f"   Timestamp: {result.get('scoring_timestamp')}")
            
        else:
            print("❌ SCORING FAILED")
            print(f"   Error: {result.get('error')}")
            print(f"   Error Type: {result.get('error_type')}")
    
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_scoring())
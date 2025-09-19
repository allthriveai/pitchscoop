#!/usr/bin/env python3
"""
Batch Scoring Script

This script finds all existing recording sessions with transcripts
and runs AI scoring on them to populate the leaderboard.

Use this when Docker is working to score your existing 8 sessions.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root and api directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))

class BatchScorer:
    """Batch scoring service for existing sessions."""
    
    def __init__(self):
        self.sessions_found = 0
        self.sessions_scored = 0
        self.sessions_failed = 0
        self.results = []

    async def find_sessions_with_transcripts(self) -> List[Dict[str, Any]]:
        """Find all sessions that have transcripts but no scoring."""
        
        import redis.asyncio as redis
        client = redis.from_url('redis://redis:6379/0', decode_responses=True)
        
        print("🔍 Scanning for sessions with transcripts...")
        
        # Find all session keys
        session_keys = []
        async for key in client.scan_iter(match='event:*:session:*'):
            session_keys.append(key)
        
        print(f"Found {len(session_keys)} total session keys")
        
        # Check each session for transcript and missing scoring
        scoreable_sessions = []
        
        for session_key in session_keys:
            try:
                session_json = await client.get(session_key)
                if not session_json:
                    continue
                    
                session_data = json.loads(session_json)
                
                # Extract identifiers
                session_id = session_key.split(':')[-1]
                event_id = session_data.get('event_id')
                team_name = session_data.get('team_name', 'Unknown')
                
                # Check if has transcript
                transcript_text = session_data.get('final_transcript', {}).get('total_text', '')
                has_transcript = bool(transcript_text and len(transcript_text.strip()) > 50)
                
                if not has_transcript:
                    continue
                
                # Check if already has scoring
                scoring_key = f"event:{event_id}:scoring:{session_id}"
                has_scoring = await client.exists(scoring_key)
                
                if has_scoring:
                    print(f"   ✅ {team_name} already scored")
                    continue
                
                # This session needs scoring
                scoreable_sessions.append({
                    'session_id': session_id,
                    'event_id': event_id,
                    'team_name': team_name,
                    'pitch_title': session_data.get('pitch_title', 'Untitled'),
                    'transcript_length': len(transcript_text),
                    'created_at': session_data.get('created_at'),
                })
                
                print(f"   📝 {team_name} needs scoring ({len(transcript_text)} chars)")
                
            except Exception as e:
                print(f"   ❌ Error processing {session_key}: {str(e)}")
                continue
        
        await client.aclose()
        self.sessions_found = len(scoreable_sessions)
        
        print(f"\n📊 Summary:")
        print(f"   Total sessions: {len(session_keys)}")
        print(f"   Sessions needing scoring: {self.sessions_found}")
        
        return scoreable_sessions

    async def score_session(self, session_info: Dict[str, Any]) -> Dict[str, Any]:
        """Score a single session."""
        
        from domains.scoring.mcp.scoring_mcp_handler import scoring_mcp_handler
        
        team_name = session_info['team_name']
        session_id = session_info['session_id']
        event_id = session_info['event_id']
        
        print(f"🧠 Scoring {team_name}...")
        
        try:
            # Call the scoring system
            result = await scoring_mcp_handler.score_complete_pitch(
                session_id=session_id,
                event_id=event_id,
                judge_id=None,
                scoring_context={
                    "triggered_by": "batch_scoring_script",
                    "batch_timestamp": asyncio.get_event_loop().time(),
                    "session_metadata": session_info
                }
            )
            
            if result.get("success"):
                total_score = "N/A"
                scores = result.get("scores", {})
                if isinstance(scores, dict) and "overall" in scores:
                    total_score = scores["overall"].get("total_score", "N/A")
                
                session_info['scoring_result'] = {
                    'success': True,
                    'total_score': total_score,
                    'timestamp': result.get('scoring_timestamp')
                }
                
                print(f"   ✅ {team_name}: {total_score} points")
                self.sessions_scored += 1
                
            else:
                error_msg = result.get("error", "Unknown error")
                session_info['scoring_result'] = {
                    'success': False,
                    'error': error_msg,
                    'error_type': result.get("error_type")
                }
                
                print(f"   ❌ {team_name}: {error_msg}")
                self.sessions_failed += 1
                
            return session_info
            
        except Exception as e:
            session_info['scoring_result'] = {
                'success': False,
                'error': str(e),
                'error_type': 'exception'
            }
            
            print(f"   💥 {team_name}: Exception - {str(e)}")
            self.sessions_failed += 1
            
            return session_info

    async def batch_score_all(self, sessions: List[Dict[str, Any]], 
                            max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """Score multiple sessions with concurrency control."""
        
        print(f"\n🚀 Starting batch scoring of {len(sessions)} sessions...")
        print(f"   Max concurrent: {max_concurrent}")
        
        # Process in batches to avoid overwhelming the system
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def score_with_limit(session_info):
            async with semaphore:
                return await self.score_session(session_info)
        
        # Score all sessions concurrently (but limited)
        results = await asyncio.gather(
            *[score_with_limit(session) for session in sessions],
            return_exceptions=True
        )
        
        # Handle any exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                sessions[i]['scoring_result'] = {
                    'success': False,
                    'error': str(result),
                    'error_type': 'batch_exception'
                }
                final_results.append(sessions[i])
                self.sessions_failed += 1
            else:
                final_results.append(result)
        
        return final_results

    def print_summary(self, results: List[Dict[str, Any]]) -> None:
        """Print batch scoring summary."""
        
        print(f"\n🎯 BATCH SCORING COMPLETE")
        print("=" * 50)
        print(f"Sessions found: {self.sessions_found}")
        print(f"Successfully scored: {self.sessions_scored}")
        print(f"Failed: {self.sessions_failed}")
        
        if self.sessions_scored > 0:
            print(f"\n✅ Successfully Scored Teams:")
            for result in results:
                if result['scoring_result']['success']:
                    name = result['team_name']
                    score = result['scoring_result']['total_score']
                    print(f"   {name}: {score} points")
        
        if self.sessions_failed > 0:
            print(f"\n❌ Failed Sessions:")
            for result in results:
                if not result['scoring_result']['success']:
                    name = result['team_name']
                    error = result['scoring_result']['error']
                    print(f"   {name}: {error}")
        
        print(f"\n🏆 Leaderboards are now populated with {self.sessions_scored} teams!")

async def main():
    """Main batch scoring workflow."""
    
    print("🤖 PitchScoop Batch Scoring Tool")
    print("=" * 60)
    print("This tool will find existing sessions and score them for leaderboards")
    print()
    
    try:
        scorer = BatchScorer()
        
        # Step 1: Find sessions that need scoring
        sessions_to_score = await scorer.find_sessions_with_transcripts()
        
        if not sessions_to_score:
            print("🎉 No sessions need scoring - all are already processed!")
            return
        
        # Step 2: Confirm with user (if running interactively)
        print(f"\n🤔 Ready to score {len(sessions_to_score)} sessions.")
        print("Teams that will be scored:")
        for session in sessions_to_score:
            print(f"   - {session['team_name']} ({session['pitch_title']})")
        
        # For automation, skip confirmation
        # input("\nPress Enter to continue or Ctrl+C to cancel...")
        
        # Step 3: Run batch scoring
        results = await scorer.batch_score_all(sessions_to_score, max_concurrent=2)
        
        # Step 4: Show summary
        scorer.print_summary(results)
        
        if scorer.sessions_scored > 0:
            print(f"\n🔗 Test your leaderboards:")
            events = set(r['event_id'] for r in results if r['scoring_result']['success'])
            for event_id in events:
                print(f"   Event {event_id}: Use leaderboard MCP tools")
        
    except KeyboardInterrupt:
        print("\n🛑 Batch scoring cancelled by user")
    except Exception as e:
        print(f"\n💥 Batch scoring failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
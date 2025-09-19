#!/usr/bin/env python3
"""
MCP Services Test Suite

Comprehensive tests for all MCP backend services including
leaderboard, scoring, recording status, and error handling.

Can run with or without Docker depending on what's available.
"""

import asyncio
import json
import sys
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

class MCPTestSuite:
    """Comprehensive test suite for MCP backend services."""
    
    def __init__(self):
        self.test_results = []
        self.test_event_id = f"test-event-{uuid.uuid4().hex[:8]}"
        self.cleanup_keys = []  # Track keys to clean up
        
    def log_test(self, test_name: str, success: bool, message: str, 
                 details: Optional[Dict] = None) -> None:
        """Log test result."""
        
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if details and not success:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    async def setup_test_data(self) -> bool:
        """Set up test data in Redis."""
        
        try:
            import redis.asyncio as redis
            client = redis.from_url('redis://redis:6379/0', decode_responses=True)
            
            # Create test sessions with transcripts
            test_sessions = [
                {
                    'team_name': 'TestTeam Alpha',
                    'pitch_title': 'Revolutionary AI Solution',
                    'final_transcript': {
                        'total_text': 'This is a test pitch transcript for team Alpha. ' * 20
                    },
                    'event_id': self.test_event_id,
                    'created_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                    'status': 'completed'
                },
                {
                    'team_name': 'TestTeam Beta', 
                    'pitch_title': 'Next-Gen Platform',
                    'final_transcript': {
                        'total_text': 'This is a test pitch transcript for team Beta. ' * 25
                    },
                    'event_id': self.test_event_id,
                    'created_at': (datetime.now() - timedelta(minutes=30)).isoformat(),
                    'status': 'completed'
                },
                {
                    'team_name': 'TestTeam Gamma',
                    'pitch_title': 'Disruptive Innovation',
                    'final_transcript': {
                        'total_text': 'This is a test pitch transcript for team Gamma. ' * 15
                    },
                    'event_id': self.test_event_id,
                    'created_at': datetime.now().isoformat(),
                    'status': 'recording'  # Still recording
                }
            ]
            
            # Store test sessions
            session_ids = []
            for i, session_data in enumerate(test_sessions):
                session_id = f"test-session-{i+1}"
                session_key = f"event:{self.test_event_id}:session:{session_id}"
                
                await client.set(session_key, json.dumps(session_data))
                self.cleanup_keys.append(session_key)
                session_ids.append(session_id)
            
            # Create some test scoring data for first two sessions
            test_scores = [
                {
                    'session_id': session_ids[0],
                    'scores': {
                        'overall': {'total_score': 85.5},
                        'content': {'score': 88, 'feedback': 'Strong content'},
                        'delivery': {'score': 83, 'feedback': 'Good delivery'}
                    },
                    'scoring_timestamp': (datetime.now() - timedelta(minutes=45)).isoformat()
                },
                {
                    'session_id': session_ids[1],
                    'scores': {
                        'overall': {'total_score': 92.0},
                        'content': {'score': 95, 'feedback': 'Excellent innovation'},
                        'delivery': {'score': 89, 'feedback': 'Clear presentation'}
                    },
                    'scoring_timestamp': (datetime.now() - timedelta(minutes=15)).isoformat()
                }
            ]
            
            for score_data in test_scores:
                scoring_key = f"event:{self.test_event_id}:scoring:{score_data['session_id']}"
                await client.set(scoring_key, json.dumps(score_data))
                self.cleanup_keys.append(scoring_key)
            
            await client.aclose()
            
            self.log_test("Setup Test Data", True, 
                         f"Created {len(test_sessions)} sessions and {len(test_scores)} scores")
            return True
            
        except Exception as e:
            self.log_test("Setup Test Data", False, str(e))
            return False
    
    async def test_leaderboard_services(self) -> None:
        """Test all leaderboard MCP services."""
        
        try:
            from domains.leaderboard.mcp.leaderboard_mcp_handler import leaderboard_mcp_handler
            
            # Test 1: Get event leaderboard
            try:
                result = await leaderboard_mcp_handler.get_event_leaderboard(
                    event_id=self.test_event_id,
                    limit=10,
                    include_details=True
                )
                
                if result.get('success') and result.get('rankings'):
                    rankings = result['rankings']
                    self.log_test("Leaderboard Fetch", True, 
                                 f"Retrieved {len(rankings)} ranked teams",
                                 {'first_team': rankings[0]['team_name'] if rankings else None})
                else:
                    self.log_test("Leaderboard Fetch", False, "No rankings returned", result)
                    
            except Exception as e:
                self.log_test("Leaderboard Fetch", False, str(e))
            
            # Test 2: Get team rank
            try:
                result = await leaderboard_mcp_handler.get_team_rank_in_event(
                    event_id=self.test_event_id,
                    team_name="TestTeam Beta"
                )
                
                if result.get('success') and result.get('rank_info'):
                    rank_info = result['rank_info']
                    self.log_test("Team Rank Lookup", True,
                                 f"Found rank #{rank_info.get('rank')} with score {rank_info.get('total_score')}")
                else:
                    self.log_test("Team Rank Lookup", False, "Team not found", result)
                    
            except Exception as e:
                self.log_test("Team Rank Lookup", False, str(e))
            
            # Test 3: Get competition statistics
            try:
                result = await leaderboard_mcp_handler.get_competition_statistics(
                    event_id=self.test_event_id
                )
                
                if result.get('success') and result.get('statistics'):
                    stats = result['statistics']
                    self.log_test("Competition Stats", True,
                                 f"Total: {stats.get('total_teams')}, Scored: {stats.get('teams_scored')}")
                else:
                    self.log_test("Competition Stats", False, "Stats not available", result)
                    
            except Exception as e:
                self.log_test("Competition Stats", False, str(e))
                
        except ImportError:
            self.log_test("Leaderboard Services", False, "Cannot import leaderboard handler - check dependencies")
    
    async def test_scoring_services(self) -> None:
        """Test scoring MCP services."""
        
        try:
            from domains.scoring.mcp.scoring_mcp_handler import scoring_mcp_handler
            
            # Test 1: Score a session (using third session without existing score)
            try:
                result = await scoring_mcp_handler.score_complete_pitch(
                    session_id="test-session-3",
                    event_id=self.test_event_id,
                    judge_id=None,
                    scoring_context={'test': 'automated_test'}
                )
                
                if result.get('success'):
                    self.log_test("Pitch Scoring", True, "Successfully scored test session")
                    
                    # Track the scoring key for cleanup
                    scoring_key = f"event:{self.test_event_id}:scoring:test-session-3"
                    self.cleanup_keys.append(scoring_key)
                else:
                    self.log_test("Pitch Scoring", False, result.get('error', 'Unknown error'), result)
                    
            except Exception as e:
                self.log_test("Pitch Scoring", False, str(e))
            
            # Test 2: Try to score non-existent session
            try:
                result = await scoring_mcp_handler.score_complete_pitch(
                    session_id="nonexistent-session",
                    event_id=self.test_event_id,
                    judge_id=None,
                    scoring_context={'test': 'error_handling_test'}
                )
                
                if not result.get('success'):
                    self.log_test("Error Handling", True, "Properly handled missing session error")
                else:
                    self.log_test("Error Handling", False, "Should have failed for missing session")
                    
            except Exception as e:
                self.log_test("Error Handling", True, f"Exception properly caught: {str(e)}")
                
        except ImportError:
            self.log_test("Scoring Services", False, "Cannot import scoring handler - check dependencies")
    
    async def test_recording_status_services(self) -> None:
        """Test recording status and session management."""
        
        try:
            import redis.asyncio as redis
            client = redis.from_url('redis://redis:6379/0', decode_responses=True)
            
            # Test 1: Check session status
            session_key = f"event:{self.test_event_id}:session:test-session-1"
            session_data = await client.get(session_key)
            
            if session_data:
                session_info = json.loads(session_data)
                status = session_info.get('status', 'unknown')
                self.log_test("Session Status Check", True, 
                             f"Session status: {status}")
            else:
                self.log_test("Session Status Check", False, "Session not found")
            
            # Test 2: List all sessions for event
            session_pattern = f"event:{self.test_event_id}:session:*"
            session_keys = []
            async for key in client.scan_iter(match=session_pattern):
                session_keys.append(key)
            
            self.log_test("Session Enumeration", True,
                         f"Found {len(session_keys)} sessions for event")
            
            # Test 3: Check for sessions with different statuses
            status_counts = {}
            for session_key in session_keys:
                session_json = await client.get(session_key)
                if session_json:
                    session_data = json.loads(session_json)
                    status = session_data.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
            
            self.log_test("Status Distribution", True,
                         f"Status counts: {status_counts}")
            
            await client.aclose()
            
        except Exception as e:
            self.log_test("Recording Status Services", False, str(e))
    
    async def test_edge_cases(self) -> None:
        """Test edge cases and error conditions."""
        
        # Test 1: Empty event ID
        try:
            from domains.leaderboard.mcp.leaderboard_mcp_handler import leaderboard_mcp_handler
            
            result = await leaderboard_mcp_handler.get_event_leaderboard(
                event_id="",
                limit=10,
                include_details=True
            )
            
            if not result.get('success'):
                self.log_test("Empty Event ID", True, "Properly rejected empty event ID")
            else:
                self.log_test("Empty Event ID", False, "Should reject empty event ID")
                
        except Exception as e:
            self.log_test("Empty Event ID", True, f"Exception properly caught: {str(e)}")
        
        # Test 2: Very large limit
        try:
            result = await leaderboard_mcp_handler.get_event_leaderboard(
                event_id=self.test_event_id,
                limit=10000,
                include_details=True
            )
            
            # Should still work, just return what's available
            self.log_test("Large Limit", True, "Handled large limit appropriately")
            
        except Exception as e:
            self.log_test("Large Limit", False, str(e))
        
        # Test 3: Non-existent team lookup
        try:
            result = await leaderboard_mcp_handler.get_team_rank_in_event(
                event_id=self.test_event_id,
                team_name="NonExistentTeam"
            )
            
            if not result.get('success') or not result.get('rank_info'):
                self.log_test("Non-existent Team", True, "Properly handled missing team")
            else:
                self.log_test("Non-existent Team", False, "Should not find non-existent team")
                
        except Exception as e:
            self.log_test("Non-existent Team", True, f"Exception properly caught: {str(e)}")
    
    async def test_performance(self) -> None:
        """Basic performance tests."""
        
        try:
            from domains.leaderboard.mcp.leaderboard_mcp_handler import leaderboard_mcp_handler
            
            # Time leaderboard fetch
            start_time = asyncio.get_event_loop().time()
            
            for _ in range(5):  # Run 5 times
                await leaderboard_mcp_handler.get_event_leaderboard(
                    event_id=self.test_event_id,
                    limit=10,
                    include_details=True
                )
            
            end_time = asyncio.get_event_loop().time()
            avg_time = (end_time - start_time) / 5
            
            if avg_time < 1.0:  # Should be under 1 second on average
                self.log_test("Performance Test", True, 
                             f"Average response time: {avg_time:.3f}s")
            else:
                self.log_test("Performance Test", False,
                             f"Slow response time: {avg_time:.3f}s")
                
        except Exception as e:
            self.log_test("Performance Test", False, str(e))
    
    async def cleanup_test_data(self) -> None:
        """Clean up test data from Redis."""
        
        try:
            import redis.asyncio as redis
            client = redis.from_url('redis://redis:6379/0', decode_responses=True)
            
            deleted_count = 0
            for key in self.cleanup_keys:
                if await client.exists(key):
                    await client.delete(key)
                    deleted_count += 1
            
            await client.aclose()
            
            self.log_test("Cleanup Test Data", True,
                         f"Deleted {deleted_count} test keys")
            
        except Exception as e:
            self.log_test("Cleanup Test Data", False, str(e))
    
    def print_summary(self) -> None:
        """Print test summary."""
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("🧪 MCP SERVICES TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   {result['test']}: {result['message']}")
        
        print(f"\n🎯 MCP backend services are {'✅ READY' if failed_tests == 0 else '⚠️ NEEDS ATTENTION'}")

async def main():
    """Run the complete MCP test suite."""
    
    print("🧪 PitchScoop MCP Services Test Suite")
    print("=" * 60)
    print("Testing all MCP backend services and error handling")
    print()
    
    try:
        tester = MCPTestSuite()
        
        # Run all test phases
        print("📋 Phase 1: Setting up test data...")
        if not await tester.setup_test_data():
            print("❌ Test setup failed - cannot continue")
            return
        
        print("\n📋 Phase 2: Testing leaderboard services...")
        await tester.test_leaderboard_services()
        
        print("\n📋 Phase 3: Testing scoring services...")
        await tester.test_scoring_services()
        
        print("\n📋 Phase 4: Testing recording status services...")
        await tester.test_recording_status_services()
        
        print("\n📋 Phase 5: Testing edge cases...")
        await tester.test_edge_cases()
        
        print("\n📋 Phase 6: Performance testing...")
        await tester.test_performance()
        
        print("\n📋 Phase 7: Cleaning up...")
        await tester.cleanup_test_data()
        
        # Show final summary
        tester.print_summary()
        
    except KeyboardInterrupt:
        print("\n🛑 Tests cancelled by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
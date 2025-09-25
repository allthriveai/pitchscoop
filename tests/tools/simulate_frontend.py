#!/usr/bin/env python3
"""
Frontend Simulation Script

This script simulates how the frontend would interact with MCP backend
services for live leaderboard display, team lookup, and real-time updates.

Perfect for testing while Docker is running.
"""

import asyncio
import json
import sys
import os
from typing import Dict, List, Any, Optional
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

class FrontendSimulator:
    """Simulates frontend interactions with MCP backend."""
    
    def __init__(self):
        self.current_event_id = None
        self.refresh_interval = 5  # seconds
        self.simulation_running = False
        
    async def initialize(self):
        """Initialize the simulator and find active events."""
        
        # Import MCP handlers
        from api.domains.leaderboard.mcp.leaderboard_mcp_handler import leaderboard_mcp_handler
        
        print("🎮 Frontend Simulator Initialization")
        print("=" * 50)
        
        # Find available events
        import redis.asyncio as redis
        client = redis.from_url('redis://redis:6379/0', decode_responses=True)
        
        event_keys = []
        async for key in client.scan_iter(match='event:*:session:*'):
            event_id = key.split(':')[1]
            if event_id not in [ek.split(':')[1] for ek in event_keys]:
                event_keys.append(f'event:{event_id}')
        
        await client.aclose()
        
        if not event_keys:
            print("❌ No events found! Run batch scoring first.")
            return False
            
        # Use the first event for simulation
        self.current_event_id = event_keys[0].split(':')[1]
        print(f"📍 Using Event ID: {self.current_event_id}")
        
        return True
    
    async def fetch_leaderboard(self) -> Dict[str, Any]:
        """Simulate frontend fetching leaderboard data."""
        
        from api.domains.leaderboard.mcp.leaderboard_mcp_handler import leaderboard_mcp_handler
        
        try:
            result = await leaderboard_mcp_handler.get_event_leaderboard(
                event_id=self.current_event_id,
                limit=10,
                include_details=True
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch leaderboard: {str(e)}"
            }
    
    async def fetch_team_rank(self, team_name: str) -> Dict[str, Any]:
        """Simulate frontend looking up specific team rank."""
        
        from api.domains.leaderboard.mcp.leaderboard_mcp_handler import leaderboard_mcp_handler
        
        try:
            result = await leaderboard_mcp_handler.get_team_rank_in_event(
                event_id=self.current_event_id,
                team_name=team_name
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch team rank: {str(e)}"
            }
    
    async def fetch_competition_stats(self) -> Dict[str, Any]:
        """Simulate frontend fetching competition statistics."""
        
        from api.domains.leaderboard.mcp.leaderboard_mcp_handler import leaderboard_mcp_handler
        
        try:
            result = await leaderboard_mcp_handler.get_competition_statistics(
                event_id=self.current_event_id
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch stats: {str(e)}"
            }
    
    def render_leaderboard_ui(self, data: Dict[str, Any]) -> None:
        """Simulate rendering leaderboard in UI."""
        
        print("\n" + "=" * 60)
        print("🏆 LIVE LEADERBOARD")
        print(f"Event: {self.current_event_id} | Updated: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)
        
        if not data.get("success"):
            print(f"❌ Error: {data.get('error', 'Unknown error')}")
            return
        
        rankings = data.get("rankings", [])
        if not rankings:
            print("📭 No teams have been scored yet")
            return
        
        # Header
        print(f"{'Rank':<6} {'Team':<25} {'Score':<10} {'Status':<15}")
        print("-" * 60)
        
        # Team entries
        for i, team in enumerate(rankings, 1):
            rank_display = f"#{i}"
            team_name = team.get("team_name", "Unknown")[:24]
            
            # Extract score from nested structure
            score_data = team.get("total_score", "N/A")
            if isinstance(score_data, dict) and "overall" in score_data:
                score = score_data["overall"].get("total_score", "N/A")
            else:
                score = score_data
            
            score_display = f"{score}"
            
            # Status indicator
            scoring_time = team.get("scoring_timestamp")
            if scoring_time:
                status = "✅ Scored"
            else:
                status = "⏳ Pending"
            
            print(f"{rank_display:<6} {team_name:<25} {score_display:<10} {status:<15}")
        
        print("-" * 60)
        print(f"Total teams: {len(rankings)}")
    
    def render_stats_ui(self, data: Dict[str, Any]) -> None:
        """Simulate rendering competition statistics in UI."""
        
        print("\n📊 COMPETITION STATISTICS")
        print("-" * 40)
        
        if not data.get("success"):
            print(f"❌ Error: {data.get('error', 'Unknown error')}")
            return
        
        stats = data.get("statistics", {})
        
        print(f"Total Teams: {stats.get('total_teams', 0)}")
        print(f"Teams Scored: {stats.get('teams_scored', 0)}")
        print(f"Teams Pending: {stats.get('teams_pending', 0)}")
        print(f"Average Score: {stats.get('average_score', 'N/A')}")
        print(f"Highest Score: {stats.get('highest_score', 'N/A')}")
        print(f"Lowest Score: {stats.get('lowest_score', 'N/A')}")
    
    def render_team_lookup_ui(self, team_name: str, data: Dict[str, Any]) -> None:
        """Simulate rendering team lookup in UI."""
        
        print(f"\n🔍 TEAM LOOKUP: {team_name}")
        print("-" * 40)
        
        if not data.get("success"):
            print(f"❌ Error: {data.get('error', 'Unknown error')}")
            return
        
        rank_info = data.get("rank_info", {})
        
        if not rank_info:
            print("❌ Team not found or not scored yet")
            return
        
        print(f"Current Rank: #{rank_info.get('rank', 'N/A')}")
        print(f"Score: {rank_info.get('total_score', 'N/A')}")
        print(f"Out of {rank_info.get('total_teams', 'N/A')} teams")
        
        if rank_info.get('scoring_timestamp'):
            print(f"Scored at: {rank_info['scoring_timestamp']}")
    
    async def run_live_simulation(self) -> None:
        """Run continuous leaderboard simulation like a real frontend."""
        
        print(f"\n🔴 LIVE SIMULATION MODE")
        print(f"Refreshing every {self.refresh_interval} seconds...")
        print("Press Ctrl+C to stop")
        
        self.simulation_running = True
        cycle_count = 0
        
        try:
            while self.simulation_running:
                cycle_count += 1
                
                # Clear screen (optional)
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print(f"🎮 PitchScoop Live Dashboard (Cycle #{cycle_count})")
                
                # Fetch and display leaderboard
                leaderboard_data = await self.fetch_leaderboard()
                self.render_leaderboard_ui(leaderboard_data)
                
                # Fetch and display stats
                stats_data = await self.fetch_competition_stats()
                self.render_stats_ui(stats_data)
                
                # Example team lookup (rotate through teams)
                if leaderboard_data.get("success") and leaderboard_data.get("rankings"):
                    rankings = leaderboard_data["rankings"]
                    if rankings:
                        # Look up a different team each cycle
                        team_idx = (cycle_count - 1) % len(rankings)
                        team_name = rankings[team_idx]["team_name"]
                        
                        team_data = await self.fetch_team_rank(team_name)
                        self.render_team_lookup_ui(team_name, team_data)
                
                print(f"\n⏱️  Next update in {self.refresh_interval} seconds...")
                
                # Wait for next refresh
                await asyncio.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            self.simulation_running = False
            print("\n🛑 Live simulation stopped")
    
    async def run_interactive_mode(self) -> None:
        """Run interactive mode for manual testing."""
        
        print(f"\n⌨️  INTERACTIVE MODE")
        print("Available commands:")
        print("  1. Show leaderboard")
        print("  2. Lookup team")
        print("  3. Show statistics")
        print("  4. Start live mode")
        print("  5. Exit")
        
        while True:
            try:
                print(f"\n> ", end="")
                choice = input().strip()
                
                if choice == "1":
                    data = await self.fetch_leaderboard()
                    self.render_leaderboard_ui(data)
                    
                elif choice == "2":
                    team_name = input("Enter team name: ").strip()
                    if team_name:
                        data = await self.fetch_team_rank(team_name)
                        self.render_team_lookup_ui(team_name, data)
                    
                elif choice == "3":
                    data = await self.fetch_competition_stats()
                    self.render_stats_ui(data)
                    
                elif choice == "4":
                    await self.run_live_simulation()
                    
                elif choice == "5":
                    print("👋 Goodbye!")
                    break
                    
                else:
                    print("Invalid choice. Try 1-5.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break

async def main():
    """Main simulation entry point."""
    
    print("🎭 PitchScoop Frontend Simulator")
    print("=" * 60)
    print("This tool simulates how a frontend would interact with MCP services")
    print()
    
    try:
        simulator = FrontendSimulator()
        
        # Initialize
        if not await simulator.initialize():
            return
        
        # Check command line args
        if len(sys.argv) > 1 and sys.argv[1] == "--live":
            await simulator.run_live_simulation()
        else:
            await simulator.run_interactive_mode()
            
    except Exception as e:
        print(f"\n💥 Simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
"""
Leaderboard MCP Handler for AI-powered pitch competition rankings.

This handler queries existing scoring data from the scoring domain and
generates real-time leaderboards for events.
"""

import json
import redis.asyncio as redis
from typing import Dict, Any, List, Optional
from datetime import datetime
from ...shared.infrastructure.logging import get_logger, log_with_context


class LeaderboardMCPHandler:
    """MCP handler for leaderboard operations."""
    
    def __init__(self):
        """Initialize the leaderboard MCP handler."""
        self.redis_client: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis client connection."""
        if self.redis_client is None:
            # Try Docker internal network first, fallback to localhost
            try:
                redis_url = "redis://redis:6379/0"  # Docker internal network
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # Test connection
                await self.redis_client.ping()
            except Exception:
                # Fallback to localhost for local testing
                redis_url = "redis://localhost:6379/0"
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client
    
    async def update_team_score_in_leaderboard(
        self,
        event_id: str,
        session_id: str,
        team_name: str,
        total_score: float
    ) -> Dict[str, Any]:
        """
        Update a team's score in the Redis Sorted Set leaderboard.
        This should be called whenever a team gets scored.
        
        Args:
            event_id: Event identifier
            session_id: Team's session identifier
            team_name: Team name
            total_score: Team's total score
            
        Returns:
            Update confirmation with new rank
        """
        logger = get_logger("leaderboards.update_score")
        
        try:
            redis_client = await self.get_redis()
            leaderboard_key = f"event:{event_id}:leaderboard"
            
            # Update score in Redis Sorted Set - O(log n)
            await redis_client.zadd(leaderboard_key, {session_id: total_score})
            
            # Set expiration for cleanup
            await redis_client.expire(leaderboard_key, 86400 * 30)  # 30 days
            
            # Get new rank
            rank = await redis_client.zrevrank(leaderboard_key, session_id)
            total_teams = await redis_client.zcard(leaderboard_key)
            
            log_with_context(
                logger, "INFO", "Team score updated in leaderboard",
                event_id=event_id,
                session_id=session_id,
                team_name=team_name,
                score=total_score,
                new_rank=rank + 1 if rank is not None else None
            )
            
            return {
                "event_id": event_id,
                "session_id": session_id,
                "team_name": team_name,
                "total_score": total_score,
                "rank": rank + 1 if rank is not None else None,
                "total_teams": total_teams,
                "success": True
            }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Failed to update team score: {str(e)}",
                event_id=event_id,
                session_id=session_id,
                error_type=type(e).__name__
            )
            return {
                "error": f"Failed to update team score: {str(e)}",
                "success": False
            }
    
    async def generate_leaderboard(
        self,
        event_id: str,
        limit: int = 10,
        include_team_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate leaderboard using Redis Sorted Sets for instant rankings.
        
        Args:
            event_id: Event identifier for multi-tenant isolation
            limit: Number of top teams to return (default 10)
            include_team_details: Whether to include pitch titles and details
            
        Returns:
            Ranked leaderboard with team scores from Redis Sorted Set
        """
        logger = get_logger("leaderboards.generate")
        operation = "generate_leaderboard"
        
        log_with_context(
            logger, "INFO", "Starting Redis Sorted Set leaderboard generation",
            event_id=event_id,
            operation=operation,
            limit=limit,
            include_details=include_team_details
        )
        
        try:
            redis_client = await self.get_redis()
            leaderboard_key = f"event:{event_id}:leaderboard"
            
            # Get top teams from Redis Sorted Set - O(log n + m)
            top_teams_raw = await redis_client.zrevrange(
                leaderboard_key, 0, limit - 1, withscores=True
            )
            
            if not top_teams_raw:
                log_with_context(
                    logger, "WARNING", "No teams found in leaderboard",
                    event_id=event_id,
                    operation=operation
                )
                return {
                    "event_id": event_id,
                    "leaderboard": [],
                    "total_teams": 0,
                    "generated_at": datetime.utcnow().isoformat(),
                    "message": "No scored pitches found for this event"
                }
            
            # Get total team count
            total_teams = await redis_client.zcard(leaderboard_key)
            
            # Build leaderboard entries
            leaderboard_entries = []
            
            for rank, (session_id, score) in enumerate(top_teams_raw, 1):
                entry = {
                    "rank": rank,
                    "session_id": session_id,
                    "total_score": float(score),
                }
                
                # Get additional team details if requested
                if include_team_details:
                    try:
                        # Fetch team details from original scoring record
                        scoring_key = f"event:{event_id}:scoring:{session_id}"
                        scoring_json = await redis_client.get(scoring_key)
                        
                        if scoring_json:
                            scoring_data = json.loads(scoring_json)
                            analysis = scoring_data.get("analysis", {})
                            
                            entry.update({
                                "team_name": scoring_data.get("team_name", f"Team-{session_id}"),
                                "pitch_title": scoring_data.get("pitch_title", ""),
                                "scoring_timestamp": scoring_data.get("scoring_timestamp"),
                                "scoring_method": scoring_data.get("scoring_method", "ai_analysis"),
                                "category_scores": {
                                    "idea_score": float(analysis.get("idea", {}).get("score", 0)),
                                    "technical_score": float(analysis.get("technical_implementation", {}).get("score", 0)),
                                    "tool_use_score": float(analysis.get("tool_use", {}).get("score", 0)),
                                    "presentation_score": float(analysis.get("presentation", {}).get("score", 0))
                                }
                            })
                        else:
                            entry["team_name"] = f"Team-{session_id}"
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        log_with_context(
                            logger, "WARNING", f"Failed to get team details: {str(e)}",
                            event_id=event_id,
                            session_id=session_id
                        )
                        entry["team_name"] = f"Team-{session_id}"
                else:
                    entry["team_name"] = f"Team-{session_id}"
                
                leaderboard_entries.append(entry)
            
            log_with_context(
                logger, "INFO", "Redis Sorted Set leaderboard generated successfully",
                event_id=event_id,
                operation=operation,
                total_teams=total_teams,
                returned_teams=len(leaderboard_entries),
                top_score=leaderboard_entries[0]["total_score"] if leaderboard_entries else 0
            )
            
            return {
                "event_id": event_id,
                "leaderboard": leaderboard_entries,
                "total_teams": total_teams,
                "returned_count": len(leaderboard_entries),
                "generated_at": datetime.utcnow().isoformat(),
                "success": True
            }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Leaderboard generation failed: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "error": f"Failed to generate leaderboard: {str(e)}",
                "event_id": event_id,
                "success": False,
                "error_type": "leaderboard_generation_error"
            }
    
    async def get_team_rank(
        self,
        event_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get individual team's rank and position in the leaderboard.
        
        Args:
            event_id: Event identifier
            session_id: Team's session identifier
            
        Returns:
            Team's rank, score, and position details
        """
        logger = get_logger("leaderboards.team_rank")
        operation = "get_team_rank"
        
        try:
            # First check if this team has scoring data
            redis_client = await self.get_redis()
            scoring_key = f"event:{event_id}:scoring:{session_id}"
            scoring_json = await redis_client.get(scoring_key)
            
            if not scoring_json:
                return {
                    "error": f"No scoring data found for session {session_id}",
                    "event_id": event_id,
                    "session_id": session_id,
                    "error_type": "no_scoring_data"
                }
            
            scoring_data = json.loads(scoring_json)
            team_name = scoring_data.get("team_name")
            
            # Generate full leaderboard to determine rank
            leaderboard_result = await self.generate_leaderboard(
                event_id=event_id,
                limit=1000,  # Get all teams for accurate ranking
                include_team_details=True
            )
            
            if not leaderboard_result.get("success"):
                return {
                    "error": "Failed to generate leaderboard for ranking",
                    "event_id": event_id,
                    "session_id": session_id,
                    "error_type": "leaderboard_error"
                }
            
            # Find team's position
            team_entry = None
            for entry in leaderboard_result["leaderboard"]:
                if entry["session_id"] == session_id:
                    team_entry = entry
                    break
            
            if not team_entry:
                return {
                    "error": f"Team not found in leaderboard",
                    "event_id": event_id,
                    "session_id": session_id,
                    "team_name": team_name,
                    "error_type": "team_not_found"
                }
            
            log_with_context(
                logger, "INFO", "Team rank retrieved successfully",
                event_id=event_id,
                session_id=session_id,
                team_name=team_name,
                rank=team_entry["rank"],
                total_score=team_entry["total_score"]
            )
            
            return {
                "event_id": event_id,
                "session_id": session_id,
                "team_name": team_name,
                "rank": team_entry["rank"],
                "total_score": team_entry["total_score"],
                "category_scores": team_entry["category_scores"],
                "total_teams": leaderboard_result["total_teams"],
                "pitch_title": team_entry.get("pitch_title"),
                "scoring_timestamp": team_entry["scoring_timestamp"],
                "success": True
            }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Failed to get team rank: {str(e)}",
                event_id=event_id,
                session_id=session_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "error": f"Failed to get team rank: {str(e)}",
                "event_id": event_id,
                "session_id": session_id,
                "success": False,
                "error_type": "team_rank_error"
            }
    
    async def get_leaderboard_stats(
        self,
        event_id: str
    ) -> Dict[str, Any]:
        """
        Get statistical summary of the leaderboard.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Statistics about scores, teams, and competition
        """
        logger = get_logger("leaderboards.stats")
        operation = "get_stats"
        
        try:
            # Generate full leaderboard for statistics
            leaderboard_result = await self.generate_leaderboard(
                event_id=event_id,
                limit=1000,  # Get all teams for accurate stats
                include_team_details=False
            )
            
            if not leaderboard_result.get("success") or not leaderboard_result["leaderboard"]:
                return {
                    "event_id": event_id,
                    "total_teams": 0,
                    "stats": {},
                    "message": "No scoring data available for statistics"
                }
            
            leaderboard = leaderboard_result["leaderboard"]
            scores = [entry["total_score"] for entry in leaderboard]
            
            stats = {
                "total_teams": len(leaderboard),
                "highest_score": max(scores),
                "lowest_score": min(scores),
                "average_score": sum(scores) / len(scores),
                "score_distribution": {
                    "90_100": len([s for s in scores if s >= 90]),
                    "80_89": len([s for s in scores if 80 <= s < 90]),
                    "70_79": len([s for s in scores if 70 <= s < 80]),
                    "60_69": len([s for s in scores if 60 <= s < 70]),
                    "below_60": len([s for s in scores if s < 60])
                }
            }
            
            log_with_context(
                logger, "INFO", "Leaderboard statistics generated",
                event_id=event_id,
                operation=operation,
                total_teams=stats["total_teams"],
                avg_score=round(stats["average_score"], 2)
            )
            
            return {
                "event_id": event_id,
                "stats": stats,
                "generated_at": datetime.utcnow().isoformat(),
                "success": True
            }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Failed to generate statistics: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "error": f"Failed to generate statistics: {str(e)}",
                "event_id": event_id,
                "success": False,
                "error_type": "stats_generation_error"
            }
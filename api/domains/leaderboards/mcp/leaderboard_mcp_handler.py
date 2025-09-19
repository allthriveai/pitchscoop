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
    
    async def generate_leaderboard(
        self,
        event_id: str,
        limit: int = 10,
        include_team_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate leaderboard for an event based on AI scoring results.
        
        Args:
            event_id: Event identifier for multi-tenant isolation
            limit: Number of top teams to return (default 10)
            include_team_details: Whether to include pitch titles and details
            
        Returns:
            Ranked leaderboard with team scores
        """
        logger = get_logger("leaderboards.generate")
        operation = "generate_leaderboard"
        
        log_with_context(
            logger, "INFO", "Starting leaderboard generation",
            event_id=event_id,
            operation=operation,
            limit=limit,
            include_details=include_team_details
        )
        
        try:
            redis_client = await self.get_redis()
            
            # Query all scoring results for the event
            scoring_pattern = f"event:{event_id}:scoring:*"
            
            # Use keys() pattern for simpler approach (fine for 30-50 teams)
            scoring_keys = await redis_client.keys(scoring_pattern)
            
            if not scoring_keys:
                log_with_context(
                    logger, "WARNING", "No scoring data found for event",
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
            
            log_with_context(
                logger, "DEBUG", "Found scoring records",
                event_id=event_id,
                operation=operation,
                scoring_records_count=len(scoring_keys)
            )
            
            # Collect and process scoring data
            leaderboard_entries = []
            
            for scoring_key in scoring_keys:
                try:
                    scoring_json = await redis_client.get(scoring_key)
                    if not scoring_json:
                        continue
                        
                    scoring_data = json.loads(scoring_json)
                    analysis = scoring_data.get("analysis", {})
                    
                    # Extract the overall total score (primary ranking field)
                    overall = analysis.get("overall", {})
                    total_score = overall.get("total_score") or analysis.get("total_score", 0)
                    
                    if total_score == 0:
                        log_with_context(
                            logger, "WARNING", "Found scoring record with zero total score",
                            event_id=event_id,
                            session_id=scoring_data.get("session_id"),
                            team_name=scoring_data.get("team_name")
                        )
                        continue
                    
                    # Build leaderboard entry
                    entry = {
                        "session_id": scoring_data.get("session_id"),
                        "team_name": scoring_data.get("team_name"),
                        "total_score": float(total_score),
                        "scoring_timestamp": scoring_data.get("scoring_timestamp")
                    }
                    
                    # Add category scores
                    entry["category_scores"] = {
                        "idea_score": float(analysis.get("idea", {}).get("score", 0)),
                        "technical_score": float(analysis.get("technical_implementation", {}).get("score", 0)),
                        "tool_use_score": float(analysis.get("tool_use", {}).get("score", 0)),
                        "presentation_score": float(analysis.get("presentation", {}).get("score", 0))
                    }
                    
                    # Add team details if requested
                    if include_team_details:
                        entry["pitch_title"] = scoring_data.get("pitch_title")
                        entry["scoring_method"] = scoring_data.get("scoring_method", "ai_analysis")
                    
                    leaderboard_entries.append(entry)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    log_with_context(
                        logger, "ERROR", f"Failed to process scoring record: {str(e)}",
                        event_id=event_id,
                        scoring_key=scoring_key,
                        error_type=type(e).__name__
                    )
                    continue
            
            if not leaderboard_entries:
                log_with_context(
                    logger, "WARNING", "No valid scoring entries found",
                    event_id=event_id,
                    operation=operation,
                    processed_keys=len(scoring_keys)
                )
                return {
                    "event_id": event_id,
                    "leaderboard": [],
                    "total_teams": 0,
                    "generated_at": datetime.utcnow().isoformat(),
                    "message": "No valid scored pitches found"
                }
            
            # Sort by total_score descending (highest scores first)
            leaderboard_entries.sort(key=lambda x: x["total_score"], reverse=True)
            
            # Add rankings and limit results
            for i, entry in enumerate(leaderboard_entries[:limit], 1):
                entry["rank"] = i
            
            final_leaderboard = leaderboard_entries[:limit]
            
            log_with_context(
                logger, "INFO", "Leaderboard generation completed successfully",
                event_id=event_id,
                operation=operation,
                total_teams=len(leaderboard_entries),
                returned_teams=len(final_leaderboard),
                top_score=final_leaderboard[0]["total_score"] if final_leaderboard else 0
            )
            
            return {
                "event_id": event_id,
                "leaderboard": final_leaderboard,
                "total_teams": len(leaderboard_entries),
                "returned_count": len(final_leaderboard),
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
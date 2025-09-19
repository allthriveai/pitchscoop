"""
Background Market Intelligence Service

Handles market intelligence gathering in the background during pitch presentations
to provide instant enhanced scoring when judges need it.

Key Features:
- Predictive market analysis during pitch recording
- Progressive score enhancement pipeline  
- Smart caching for immediate access
- Real-time competition flow optimization
"""
import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis.asyncio as redis

from ..entities.market_enhanced_score import MarketEnhancedScore
from ...market.services.bright_data_service import bright_data_service
from ...shared.infrastructure.logging import get_logger, log_with_context


class BackgroundMarketIntelligenceService:
    """Service for background processing of market intelligence during competitions."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.logger = get_logger("background_market_intelligence")
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis client connection."""
        if self.redis_client is None:
            redis_url = "redis://redis:6379/0"
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client
    
    async def start_predictive_analysis(
        self,
        session_id: str,
        event_id: str,
        team_data: Dict[str, Any]
    ) -> bool:
        """
        Start market intelligence gathering as soon as pitch recording begins.
        
        This runs during the 3-minute pitch presentation so data is ready
        when judges need to score immediately after.
        """
        log_with_context(
            self.logger, "INFO", "Starting predictive market analysis",
            event_id=event_id,
            session_id=session_id,
            team_name=team_data.get("team_name"),
            operation="start_predictive_analysis"
        )
        
        # Extract what we can from team registration
        industry = team_data.get("industry", "technology")
        company_description = team_data.get("company_description", "")
        pitch_title = team_data.get("pitch_title", "")
        
        # Create unique task key
        task_key = f"{event_id}:{session_id}:market_analysis"
        
        # Cancel any existing task for this session
        if task_key in self.active_tasks:
            self.active_tasks[task_key].cancel()
        
        # Start background analysis task
        self.active_tasks[task_key] = asyncio.create_task(
            self._background_market_analysis(
                session_id=session_id,
                event_id=event_id,
                industry=industry,
                company_description=company_description,
                pitch_title=pitch_title,
                team_name=team_data.get("team_name", "Unknown Team")
            )
        )
        
        log_with_context(
            self.logger, "INFO", "Predictive analysis task created",
            event_id=event_id,
            session_id=session_id,
            operation="task_creation",
            industry=industry,
            task_key=task_key
        )
        
        return True
    
    async def _background_market_analysis(
        self,
        session_id: str,
        event_id: str,
        industry: str,
        company_description: str,
        pitch_title: str,
        team_name: str
    ):
        """Background task that runs market intelligence analysis."""
        
        start_time = time.time()
        
        log_with_context(
            self.logger, "INFO", "Executing background market analysis",
            event_id=event_id,
            session_id=session_id,
            team_name=team_name,
            operation="background_analysis",
            industry=industry
        )
        
        try:
            # Run all market intelligence requests in parallel
            # This typically takes 3-8 seconds, perfect for a 3-minute pitch
            market_tasks = [
                bright_data_service.validate_market_size("", industry, event_id),
                bright_data_service.analyze_competitors(company_description, industry, event_id),
                bright_data_service.get_industry_trends(industry, [], event_id)
            ]
            
            log_with_context(
                self.logger, "DEBUG", "Starting parallel market intelligence requests",
                event_id=event_id,
                session_id=session_id,
                operation="parallel_requests",
                request_count=len(market_tasks)
            )
            
            # Execute all requests in parallel
            market_validation, competitor_analysis, industry_trends = await asyncio.gather(
                *market_tasks, return_exceptions=True
            )
            
            # Handle any exceptions
            results = {
                "market_validation": market_validation if not isinstance(market_validation, Exception) else {"error": str(market_validation)},
                "competitor_analysis": competitor_analysis if not isinstance(competitor_analysis, Exception) else {"error": str(competitor_analysis)},
                "industry_trends": industry_trends if not isinstance(industry_trends, Exception) else {"error": str(industry_trends)}
            }
            
            # Store results in cache for immediate access
            await self._cache_market_intelligence(session_id, event_id, results, team_name)
            
            duration_ms = (time.time() - start_time) * 1000
            
            log_with_context(
                self.logger, "INFO", "Background market analysis completed successfully",
                event_id=event_id,
                session_id=session_id,
                team_name=team_name,
                operation="background_analysis",
                duration_ms=duration_ms,
                has_market_validation=bool(results["market_validation"].get("confidence")),
                competitors_found=len(results["competitor_analysis"].get("competitors", [])),
                trends_found=len(results["industry_trends"].get("trending_keywords", []))
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            log_with_context(
                self.logger, "ERROR", "Background market analysis failed",
                event_id=event_id,
                session_id=session_id,
                team_name=team_name,
                operation="background_analysis",
                duration_ms=duration_ms,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Store error state so scoring knows analysis failed
            await self._cache_analysis_error(session_id, event_id, str(e))
    
    async def _cache_market_intelligence(
        self,
        session_id: str,
        event_id: str,
        results: Dict[str, Any],
        team_name: str
    ):
        """Cache market intelligence results for immediate access during scoring."""
        
        cache_key = f"event:{event_id}:background_market:{session_id}"
        
        cache_data = {
            "session_id": session_id,
            "event_id": event_id,
            "team_name": team_name,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "market_intelligence": results,
            "status": "ready",
            "cache_expiry": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
        
        try:
            redis_client = await self.get_redis()
            await redis_client.setex(
                cache_key,
                7200,  # 2 hours TTL
                json.dumps(cache_data)
            )
            
            log_with_context(
                self.logger, "DEBUG", "Market intelligence cached successfully",
                event_id=event_id,
                session_id=session_id,
                operation="cache_storage",
                cache_key=cache_key,
                data_size=len(json.dumps(cache_data))
            )
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", "Failed to cache market intelligence",
                event_id=event_id,
                session_id=session_id,
                operation="cache_storage",
                error=str(e),
                cache_key=cache_key
            )
    
    async def _cache_analysis_error(self, session_id: str, event_id: str, error: str):
        """Cache analysis error state."""
        
        cache_key = f"event:{event_id}:background_market:{session_id}"
        
        error_data = {
            "session_id": session_id,
            "event_id": event_id,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": error
        }
        
        try:
            redis_client = await self.get_redis()
            await redis_client.setex(cache_key, 3600, json.dumps(error_data))  # 1 hour TTL for errors
        except Exception as cache_error:
            log_with_context(
                self.logger, "ERROR", "Failed to cache analysis error",
                event_id=event_id,
                session_id=session_id,
                operation="error_cache",
                original_error=error,
                cache_error=str(cache_error)
            )
    
    async def get_cached_market_intelligence(
        self,
        session_id: str,
        event_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached market intelligence if available.
        
        Returns immediately if analysis was completed in background,
        None if still processing or failed.
        """
        
        cache_key = f"event:{event_id}:background_market:{session_id}"
        
        try:
            redis_client = await self.get_redis()
            cached_json = await redis_client.get(cache_key)
            
            if not cached_json:
                log_with_context(
                    self.logger, "DEBUG", "No cached market intelligence found",
                    event_id=event_id,
                    session_id=session_id,
                    operation="cache_retrieval",
                    cache_key=cache_key
                )
                return None
            
            cached_data = json.loads(cached_json)
            
            if cached_data.get("status") == "ready":
                log_with_context(
                    self.logger, "INFO", "Retrieved cached market intelligence",
                    event_id=event_id,
                    session_id=session_id,
                    operation="cache_retrieval",
                    analysis_age_seconds=int((
                        datetime.utcnow() - 
                        datetime.fromisoformat(cached_data["analysis_timestamp"])
                    ).total_seconds())
                )
                return cached_data["market_intelligence"]
            
            elif cached_data.get("status") == "error":
                log_with_context(
                    self.logger, "WARNING", "Cached market intelligence shows error state",
                    event_id=event_id,
                    session_id=session_id,
                    operation="cache_retrieval",
                    cached_error=cached_data.get("error")
                )
                return None
            
            else:
                log_with_context(
                    self.logger, "DEBUG", "Market intelligence still processing",
                    event_id=event_id,
                    session_id=session_id,
                    operation="cache_retrieval",
                    status=cached_data.get("status", "unknown")
                )
                return None
                
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", "Failed to retrieve cached market intelligence",
                event_id=event_id,
                session_id=session_id,
                operation="cache_retrieval",
                error=str(e)
            )
            return None
    
    async def get_analysis_status(
        self,
        session_id: str,
        event_id: str
    ) -> Dict[str, Any]:
        """Get status of background market analysis."""
        
        cache_key = f"event:{event_id}:background_market:{session_id}"
        task_key = f"{event_id}:{session_id}:market_analysis"
        
        try:
            redis_client = await self.get_redis()
            cached_json = await redis_client.get(cache_key)
            
            if cached_json:
                cached_data = json.loads(cached_json)
                return {
                    "status": cached_data.get("status", "unknown"),
                    "analysis_timestamp": cached_data.get("analysis_timestamp"),
                    "error": cached_data.get("error"),
                    "has_cached_data": True
                }
            
            # Check if task is still running
            if task_key in self.active_tasks and not self.active_tasks[task_key].done():
                return {
                    "status": "processing",
                    "has_cached_data": False,
                    "estimated_completion": "30-60 seconds"
                }
            
            return {
                "status": "not_started",
                "has_cached_data": False
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "has_cached_data": False
            }
    
    async def cleanup_completed_tasks(self):
        """Clean up completed background tasks."""
        
        completed_tasks = [
            key for key, task in self.active_tasks.items() 
            if task.done()
        ]
        
        for task_key in completed_tasks:
            del self.active_tasks[task_key]
        
        if completed_tasks:
            log_with_context(
                self.logger, "DEBUG", "Cleaned up completed background tasks",
                operation="task_cleanup",
                cleaned_count=len(completed_tasks),
                remaining_count=len(self.active_tasks)
            )


# Global service instance
background_market_service = BackgroundMarketIntelligenceService()
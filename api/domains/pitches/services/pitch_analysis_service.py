"""
Pitch Analysis Service

Domain service for orchestrating pitch video analysis using Hume AI.
Coordinates between repositories and value objects to provide complete analysis.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from ..entities.pitch_session import PitchSession
from ..repositories.hume_api_repository import HumeAPIRepository, get_hume_client
from ..value_objects.video_intelligence import (
    VideoIntelligence, create_video_intelligence_from_hume_response
)

logger = logging.getLogger(__name__)


class PitchAnalysisService:
    """Domain service for pitch video analysis."""
    
    def __init__(self, hume_client: Optional[HumeAPIRepository] = None):
        """
        Initialize the pitch analysis service.
        
        Args:
            hume_client: Optional Hume API client (will use default factory if not provided)
        """
        self.hume_client = hume_client or get_hume_client()
    
    async def create_pitch_session(
        self, 
        user_id: str, 
        title: str, 
        pitch_category: Optional[str] = None,
        target_duration_seconds: Optional[int] = None
    ) -> PitchSession:
        """
        Create a new pitch session.
        
        Args:
            user_id: ID of the user creating the pitch
            title: Title of the pitch presentation
            pitch_category: Category of pitch (investor_pitch, sales_pitch, etc.)
            target_duration_seconds: Expected duration of the pitch
            
        Returns:
            New PitchSession entity
        """
        session_id = str(uuid.uuid4())
        
        pitch_session = PitchSession(
            session_id=session_id,
            user_id=user_id,
            title=title,
            pitch_category=pitch_category,
            target_duration_seconds=target_duration_seconds,
            analysis_status="pending"
        )
        
        logger.info(f"Created pitch session: {session_id} for user: {user_id}")
        return pitch_session
    
    async def analyze_pitch_video(
        self, 
        pitch_session: PitchSession,
        video_data: bytes,
        filename: Optional[str] = None
    ) -> PitchSession:
        """
        Analyze pitch video using Hume AI and update the session.
        
        Args:
            pitch_session: The pitch session to analyze
            video_data: Raw video file bytes
            filename: Optional filename for the video
            
        Returns:
            Updated PitchSession with analysis results
        """
        # Update status to processing
        pitch_session.update_status("processing")
        
        # Set filename
        video_filename = filename or f"pitch_{pitch_session.session_id}.mp4"
        pitch_session.video_filename = video_filename
        
        logger.info(f"Starting video analysis for pitch session: {pitch_session.session_id}")
        
        try:
            # Perform complete video analysis
            analysis_start = datetime.utcnow()
            hume_result = await self.hume_client.analyze_video_complete(
                video_data=video_data,
                filename=video_filename,
                max_wait_seconds=300
            )
            analysis_end = datetime.utcnow()
            processing_time = (analysis_end - analysis_start).total_seconds()
            
            if not hume_result.get("success"):
                error_msg = hume_result.get("error", "Unknown error")
                logger.error(f"Hume analysis failed for {pitch_session.session_id}: {error_msg}")
                pitch_session.update_status("failed")
                return pitch_session
            
            # Extract analysis results
            analysis_results = hume_result.get("analysis_results", {})
            hume_job_id = hume_result.get("job_id", "unknown")
            
            # Create VideoIntelligence object
            video_intelligence = create_video_intelligence_from_hume_response(
                session_id=pitch_session.session_id,
                hume_job_id=hume_job_id,
                hume_response=analysis_results,
                analysis_timestamp=analysis_end.isoformat(),
                processing_time_seconds=processing_time
            )
            
            # Update pitch session with results
            pitch_session.set_video_intelligence(video_intelligence)
            
            logger.info(f"Successfully analyzed pitch video: {pitch_session.session_id}")
            return pitch_session
            
        except Exception as e:
            logger.error(f"Exception during video analysis for {pitch_session.session_id}: {str(e)}")
            pitch_session.update_status("failed")
            return pitch_session
    
    async def get_coaching_insights(self, pitch_session: PitchSession) -> Optional[Dict[str, Any]]:
        """
        Get coaching insights for a pitch session.
        
        Args:
            pitch_session: The analyzed pitch session
            
        Returns:
            Coaching insights or None if analysis not complete
        """
        if not pitch_session.is_analysis_complete():
            logger.warning(f"Requested coaching insights for incomplete analysis: {pitch_session.session_id}")
            return None
        
        insights = pitch_session.get_coaching_feedback()
        
        # Enhance with pitch-specific insights
        if insights and pitch_session.pitch_category:
            insights["category_specific_tips"] = self._get_category_specific_tips(
                pitch_session.pitch_category,
                pitch_session.get_presentation_score() or 0.0
            )
        
        return insights
    
    def _get_category_specific_tips(self, pitch_category: str, score: float) -> list[str]:
        """Get category-specific coaching tips."""
        tips = []
        
        if pitch_category == "investor_pitch":
            if score < 15:
                tips.extend([
                    "Focus on clearly articulating your value proposition in the first 30 seconds",
                    "Practice presenting your financial projections with confidence",
                    "Emphasize market opportunity and competitive advantages"
                ])
            else:
                tips.extend([
                    "Great foundational delivery! Consider refining your ask and terms presentation",
                    "Strong confidence will help in due diligence discussions"
                ])
        
        elif pitch_category == "sales_pitch":
            if score < 15:
                tips.extend([
                    "Work on building rapport through authentic emotional connection",
                    "Practice handling objections with calm confidence",
                    "Focus on customer pain points and your solution's benefits"
                ])
            else:
                tips.extend([
                    "Excellent delivery! Your confidence will help close more deals",
                    "Consider tailoring emotional tone to different customer personalities"
                ])
        
        elif pitch_category == "elevator_pitch":
            if score < 15:
                tips.extend([
                    "Practice your 30-second hook to grab immediate attention",
                    "Work on memorable, clear value statements",
                    "Increase energy to make a lasting first impression"
                ])
            else:
                tips.extend([
                    "Strong elevator pitch delivery! You'll make great first impressions",
                    "Your confidence and energy are perfect for networking situations"
                ])
        
        return tips
    
    async def get_pitch_score_breakdown(self, pitch_session: PitchSession) -> Optional[Dict[str, Any]]:
        """
        Get detailed score breakdown for a pitch session.
        
        Args:
            pitch_session: The analyzed pitch session
            
        Returns:
            Detailed score breakdown or None if analysis not complete
        """
        if not pitch_session.is_analysis_complete() or not pitch_session.video_intelligence:
            return None
        
        vi = pitch_session.video_intelligence
        metrics = vi.delivery_metrics
        
        return {
            "overall_score": vi.get_presentation_score(),
            "confidence_score": {
                "level": metrics.confidence_level.value,
                "contribution": 35,  # 35% weight
                "description": "Projected confidence through facial expressions and engagement"
            },
            "engagement_consistency": {
                "score": metrics.engagement_consistency,
                "contribution": 25,  # 25% weight  
                "description": "Consistency of emotional engagement throughout presentation"
            },
            "authenticity_score": {
                "score": metrics.authenticity_score,
                "contribution": 20,  # 20% weight
                "description": "Natural vs forced expressions - authenticity of delivery"
            },
            "energy_level": {
                "level": metrics.energy_level.value,
                "contribution": 15,  # 15% weight
                "description": "Energy and enthusiasm level throughout presentation"
            },
            "emotional_range": {
                "score": metrics.emotional_range,
                "contribution": 5,  # 5% weight
                "description": "Variety of emotional expressions to keep presentation dynamic"
            },
            "analysis_metadata": {
                "snapshots_analyzed": len(vi.emotion_timeline.snapshots),
                "total_duration": vi.emotion_timeline.total_duration_seconds,
                "average_confidence": vi.emotion_timeline.get_average_confidence(),
                "processing_time": vi.processing_time_seconds
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the pitch analysis service is healthy."""
        try:
            hume_health = await self.hume_client.health_check()
            return {
                "service": "PitchAnalysisService",
                "status": "healthy" if hume_health.get("status") == "healthy" else "unhealthy",
                "hume_api": hume_health,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "service": "PitchAnalysisService", 
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
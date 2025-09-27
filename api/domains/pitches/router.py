"""
Pitches Domain Router

FastAPI router for pitch video analysis endpoints.
Provides REST API access to pitch analysis functionality.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, Optional
import base64
import logging

from .mcp.pitch_tools import pitch_tools

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/pitches",
    tags=["pitches"],
    responses={404: {"description": "Not found"}}
)


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check health of pitch analysis system."""
    try:
        return await pitch_tools.health_check()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions")
async def create_pitch_session(
    user_id: str,
    title: str,
    pitch_category: Optional[str] = None,
    target_duration: Optional[int] = None
) -> Dict[str, Any]:
    """Create a new pitch session."""
    try:
        result = await pitch_tools.create_pitch_session(
            user_id=user_id,
            title=title,
            pitch_category=pitch_category,
            target_duration=target_duration
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create session"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create pitch session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session_status(session_id: str) -> Dict[str, Any]:
    """Get pitch session status and details."""
    try:
        result = await pitch_tools.get_session_status(session_id)
        
        if result.get("status") != "success":
            raise HTTPException(status_code=404, detail=result.get("error", "Session not found"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/analyze")
async def analyze_video_upload(
    session_id: str,
    video: UploadFile = File(...)
) -> Dict[str, Any]:
    """Analyze uploaded video for pitch session."""
    try:
        # Read video file
        video_data = await video.read()
        
        # Convert to base64
        video_b64 = base64.b64encode(video_data).decode('utf-8')
        
        # Analyze video
        result = await pitch_tools.analyze_pitch_video(
            session_id=session_id,
            video_data_b64=video_b64,
            filename=video.filename
        )
        
        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/insights")
async def get_coaching_insights(session_id: str) -> Dict[str, Any]:
    """Get detailed coaching insights for a pitch session."""
    try:
        result = await pitch_tools.get_coaching_insights(session_id)
        
        if result.get("status") != "success":
            raise HTTPException(status_code=400, detail=result.get("error", "Insights not available"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get coaching insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(user_id: Optional[str] = None) -> Dict[str, Any]:
    """List active pitch sessions, optionally filtered by user."""
    try:
        result = await pitch_tools.list_active_sessions(user_id=user_id)
        
        if result.get("status") != "success":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to list sessions"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
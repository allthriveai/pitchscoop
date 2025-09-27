"""
PitchSession Entity

Represents a pitch presentation session with video analysis results.
Core domain entity for the pitches domain.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from ..value_objects.video_intelligence import VideoIntelligence


@dataclass
class PitchSession:
    """Represents a pitch presentation session with analysis results."""
    
    session_id: str
    user_id: str
    title: str
    video_filename: Optional[str] = None
    video_url: Optional[str] = None
    analysis_status: str = "pending"  # pending, processing, completed, failed
    video_intelligence: Optional[VideoIntelligence] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Pitch-specific metadata
    pitch_category: Optional[str] = None  # investor_pitch, sales_pitch, elevator_pitch
    target_duration_seconds: Optional[int] = None
    actual_duration_seconds: Optional[int] = None
    
    def __post_init__(self):
        """Set timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def is_analysis_complete(self) -> bool:
        """Check if video analysis is complete."""
        return self.analysis_status == "completed" and self.video_intelligence is not None
    
    def get_presentation_score(self) -> Optional[float]:
        """Get the presentation delivery score if available."""
        if self.video_intelligence:
            return self.video_intelligence.get_presentation_score()
        return None
    
    def get_emotional_summary(self) -> Optional[Dict[str, Any]]:
        """Get emotional analysis summary if available."""
        if self.video_intelligence:
            return self.video_intelligence.get_emotional_summary()
        return None
    
    def get_coaching_feedback(self) -> Optional[Dict[str, Any]]:
        """Get coaching feedback if available."""
        if self.video_intelligence:
            return self.video_intelligence.get_coaching_feedback()
        return None
    
    def update_status(self, new_status: str):
        """Update analysis status and timestamp."""
        self.analysis_status = new_status
        self.updated_at = datetime.utcnow()
    
    def set_video_intelligence(self, video_intelligence: VideoIntelligence):
        """Set video intelligence results and mark as completed."""
        self.video_intelligence = video_intelligence
        self.analysis_status = "completed"
        self.updated_at = datetime.utcnow()
        
        # Extract actual duration from analysis if not set
        if self.actual_duration_seconds is None and video_intelligence.emotion_timeline.total_duration_seconds:
            self.actual_duration_seconds = int(video_intelligence.emotion_timeline.total_duration_seconds)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "title": self.title,
            "video_filename": self.video_filename,
            "video_url": self.video_url,
            "analysis_status": self.analysis_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "pitch_category": self.pitch_category,
            "target_duration_seconds": self.target_duration_seconds,
            "actual_duration_seconds": self.actual_duration_seconds,
            "presentation_score": self.get_presentation_score(),
        }
        
        # Include analysis results if available
        if self.is_analysis_complete():
            result["emotional_summary"] = self.get_emotional_summary()
            result["coaching_feedback"] = self.get_coaching_feedback()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PitchSession":
        """Create PitchSession from dictionary."""
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            title=data["title"],
            video_filename=data.get("video_filename"),
            video_url=data.get("video_url"),
            analysis_status=data.get("analysis_status", "pending"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            pitch_category=data.get("pitch_category"),
            target_duration_seconds=data.get("target_duration_seconds"),
            actual_duration_seconds=data.get("actual_duration_seconds"),
            # Note: video_intelligence would need to be reconstructed separately
        )
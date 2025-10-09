"""
Onboarding Session Entity

Tracks user progress through onboarding flow.
Maintains state for multi-step onboarding process.
"""

from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum, Integer
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from domains.shared.infrastructure.database import Base


class OnboardingRole(str, enum.Enum):
    """User role during onboarding"""
    ORGANIZER = "organizer"
    PARTICIPANT = "participant"


class OnboardingStatus(str, enum.Enum):
    """Onboarding session status"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class OnboardingSession(Base):
    """Tracks user progress through onboarding"""
    
    __tablename__ = "onboarding_sessions"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User information
    user_id = Column(String(255), nullable=False, index=True)
    role = Column(SQLEnum(OnboardingRole), nullable=False)
    
    # Flow tracking
    current_flow = Column(String(100), nullable=False)  # e.g., "event_creation_flow", "participant_flow"
    current_step = Column(String(100), nullable=True)   # e.g., "event_details", "create_profile"
    completed_steps = Column(JSON, nullable=False, default=list)  # List of completed step IDs
    
    # Session data (accumulated form data)
    session_data = Column(JSON, nullable=False, default=dict)
    
    # Progress tracking
    total_steps = Column(Integer, nullable=True)
    status = Column(SQLEnum(OnboardingStatus), nullable=False, default=OnboardingStatus.IN_PROGRESS)
    
    # Event context (for participant onboarding)
    event_id = Column(String(255), nullable=True, index=True)
    
    # Metadata
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<OnboardingSession(user_id='{self.user_id}', role='{self.role}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role.value if self.role else None,
            "current_flow": self.current_flow,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "session_data": self.session_data,
            "progress": {
                "completed": len(self.completed_steps),
                "total": self.total_steps,
                "percentage": int((len(self.completed_steps) / self.total_steps * 100)) if self.total_steps else 0
            },
            "status": self.status.value if self.status else None,
            "event_id": self.event_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

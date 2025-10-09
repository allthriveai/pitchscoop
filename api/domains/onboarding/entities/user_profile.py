"""
User Profile Entity

Stores participant profile information collected during onboarding.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from domains.shared.infrastructure.database import Base


class UserProfile(Base):
    """User profile for participants"""
    
    __tablename__ = "user_profiles"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User identification
    user_id = Column(String(255), nullable=False, unique=True, index=True)  # From auth system
    user_name = Column(String(255), nullable=False)
    
    # Team and project information
    team_name = Column(String(255), nullable=False)
    project_name = Column(String(255), nullable=False)
    project_description = Column(Text, nullable=False)
    github_repo = Column(String(512), nullable=True)  # Optional
    
    # Additional custom fields (JSON would go here in future iterations)
    # custom_fields = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<UserProfile(user_name='{self.user_name}', team_name='{self.team_name}', project='{self.project_name}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "team_name": self.team_name,
            "project_name": self.project_name,
            "project_description": self.project_description,
            "github_repo": self.github_repo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

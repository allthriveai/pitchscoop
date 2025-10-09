"""
Event Customization Entity

Stores event organizer customizations for onboarding and judging criteria.
Each event can have custom:
- Welcome messages
- Required profile fields
- Judging categories and weights
- Custom judging criteria
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Float
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from domains.shared.infrastructure.database import Base


class EventCustomization(Base):
    """Event-specific onboarding and judging customizations"""
    
    __tablename__ = "event_customizations"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Link to event (stored in Redis currently)
    event_id = Column(String(255), nullable=False, unique=True, index=True)
    event_name = Column(String(255), nullable=False)
    
    # Onboarding customization
    welcome_message = Column(Text, nullable=True)
    required_fields = Column(JSON, nullable=True)  # List of required profile fields
    help_text = Column(JSON, nullable=True)  # Custom help text for fields
    
    # Judging criteria customization
    judging_categories = Column(JSON, nullable=False)  # Array of category objects
    # Example structure:
    # [
    #   {"id": "idea", "name": "Idea Category", "weight": 0.3, "criteria": [...]},
    #   {"id": "technical", "name": "Technical", "weight": 0.4, "criteria": [...]},
    #   {"id": "custom", "name": "Sustainability", "weight": 0.3, "criteria": [...]}
    # ]
    
    # Custom judging category (the "Other" category from onboarding flow)
    custom_category_name = Column(String(255), nullable=True)
    custom_category_description = Column(Text, nullable=True)
    custom_category_weight = Column(Float, nullable=True)
    
    # Metadata
    created_by = Column(String(255), nullable=False)  # Event organizer user_id
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    def __repr__(self):
        return f"<EventCustomization(event_name='{self.event_name}', event_id='{self.event_id}')>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "event_name": self.event_name,
            "welcome_message": self.welcome_message,
            "required_fields": self.required_fields,
            "help_text": self.help_text,
            "judging_categories": self.judging_categories,
            "custom_category": {
                "name": self.custom_category_name,
                "description": self.custom_category_description,
                "weight": self.custom_category_weight
            } if self.custom_category_name else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

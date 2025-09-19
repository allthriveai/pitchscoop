"""
Conversation Entity - Chat conversation management

Manages conversations within the PitchScoop application, providing
context tracking and session management for pitch-related discussions.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .chat_message import ChatMessage, MessageType


class ConversationType(Enum):
    """Types of conversations."""
    GENERAL_CHAT = "general_chat"
    PITCH_ANALYSIS = "pitch_analysis"  
    SCORING_REVIEW = "scoring_review"
    RUBRIC_DISCUSSION = "rubric_discussion"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


class ConversationStatus(Enum):
    """Status of conversations."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    ERROR = "error"


@dataclass
class ConversationContext:
    """Context information for a conversation."""
    session_ids: Optional[List[str]] = None  # Related pitch sessions
    rubric_ids: Optional[List[str]] = None   # Related rubrics
    focus_areas: Optional[List[str]] = None  # Areas of focus (idea, technical, tools, presentation)
    judge_id: Optional[str] = None           # Judge conducting the conversation
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.session_ids is None:
            self.session_ids = []
        if self.rubric_ids is None:
            self.rubric_ids = []
        if self.focus_areas is None:
            self.focus_areas = []
        if self.metadata is None:
            self.metadata = {}


@dataclass  
class Conversation:
    """Core conversation entity."""
    
    # Identifiers
    conversation_id: str
    event_id: str  # For multi-tenant isolation
    
    # Conversation metadata
    title: Optional[str]
    conversation_type: ConversationType
    status: ConversationStatus
    
    # Timestamps
    created_at: datetime
    last_message_at: Optional[datetime]
    
    # Context and participants
    context: ConversationContext
    user_id: Optional[str] = None
    
    # Message tracking
    message_count: int = 0
    
    def __post_init__(self):
        """Post-initialization setup."""
        if self.last_message_at is None:
            self.last_message_at = self.created_at
    
    @classmethod
    def create_new(
        cls,
        conversation_id: str,
        event_id: str,
        conversation_type: ConversationType = ConversationType.GENERAL_CHAT,
        title: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[ConversationContext] = None
    ) -> 'Conversation':
        """Create a new conversation."""
        return cls(
            conversation_id=conversation_id,
            event_id=event_id,
            title=title or f"Conversation {conversation_id[:8]}",
            conversation_type=conversation_type,
            status=ConversationStatus.ACTIVE,
            created_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
            context=context or ConversationContext(),
            user_id=user_id,
            message_count=0
        )
    
    @classmethod
    def create_pitch_analysis(
        cls,
        conversation_id: str,
        event_id: str,
        session_id: str,
        user_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> 'Conversation':
        """Create a pitch analysis conversation."""
        context = ConversationContext(session_ids=[session_id])
        
        return cls.create_new(
            conversation_id=conversation_id,
            event_id=event_id,
            conversation_type=ConversationType.PITCH_ANALYSIS,
            title=title or f"Pitch Analysis - {session_id[:8]}",
            user_id=user_id,
            context=context
        )
    
    @classmethod
    def create_scoring_review(
        cls,
        conversation_id: str,
        event_id: str,
        session_ids: List[str],
        judge_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> 'Conversation':
        """Create a scoring review conversation."""
        context = ConversationContext(
            session_ids=session_ids,
            judge_id=judge_id
        )
        
        return cls.create_new(
            conversation_id=conversation_id,
            event_id=event_id,
            conversation_type=ConversationType.SCORING_REVIEW,
            title=title or f"Scoring Review - {len(session_ids)} pitches",
            user_id=judge_id,
            context=context
        )
    
    def add_session_context(self, session_id: str):
        """Add a session to the conversation context."""
        if session_id not in self.context.session_ids:
            self.context.session_ids.append(session_id)
    
    def add_rubric_context(self, rubric_id: str):
        """Add a rubric to the conversation context."""
        if rubric_id not in self.context.rubric_ids:
            self.context.rubric_ids.append(rubric_id)
    
    def set_focus_areas(self, focus_areas: List[str]):
        """Set focus areas for the conversation."""
        valid_areas = {"idea", "technical", "tools", "presentation", "overall"}
        self.context.focus_areas = [area for area in focus_areas if area in valid_areas]
    
    def update_message_count(self, message_count: int):
        """Update the message count and last message timestamp."""
        self.message_count = message_count
        self.last_message_at = datetime.utcnow()
    
    def pause(self):
        """Pause the conversation."""
        self.status = ConversationStatus.PAUSED
    
    def resume(self):
        """Resume a paused conversation."""
        if self.status == ConversationStatus.PAUSED:
            self.status = ConversationStatus.ACTIVE
    
    def archive(self):
        """Archive the conversation."""
        self.status = ConversationStatus.ARCHIVED
    
    def mark_error(self):
        """Mark conversation as having errors."""
        self.status = ConversationStatus.ERROR
    
    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == ConversationStatus.ACTIVE
    
    def has_session_context(self, session_id: str) -> bool:
        """Check if conversation includes specific session."""
        return session_id in self.context.session_ids
    
    def has_rubric_context(self, rubric_id: str) -> bool:
        """Check if conversation includes specific rubric."""  
        return rubric_id in self.context.rubric_ids
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "conversation_id": self.conversation_id,
            "event_id": self.event_id,
            "title": self.title,
            "conversation_type": self.conversation_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "context": {
                "session_ids": self.context.session_ids,
                "rubric_ids": self.context.rubric_ids,
                "focus_areas": self.context.focus_areas,
                "judge_id": self.context.judge_id,
                "metadata": self.context.metadata
            },
            "user_id": self.user_id,
            "message_count": self.message_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create Conversation from dictionary."""
        context = ConversationContext(
            session_ids=data.get("context", {}).get("session_ids", []),
            rubric_ids=data.get("context", {}).get("rubric_ids", []),
            focus_areas=data.get("context", {}).get("focus_areas", []),
            judge_id=data.get("context", {}).get("judge_id"),
            metadata=data.get("context", {}).get("metadata", {})
        )
        
        return cls(
            conversation_id=data["conversation_id"],
            event_id=data["event_id"],
            title=data.get("title"),
            conversation_type=ConversationType(data["conversation_type"]),
            status=ConversationStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_message_at=datetime.fromisoformat(data["last_message_at"]) if data.get("last_message_at") else None,
            context=context,
            user_id=data.get("user_id"),
            message_count=data.get("message_count", 0)
        )
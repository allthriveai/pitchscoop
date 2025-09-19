"""
Chat Message Entity - Core chat message representation

Represents individual messages within conversations, supporting both
user queries and AI responses with proper source attribution.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """Types of chat messages."""
    USER_QUERY = "user_query"
    AI_RESPONSE = "ai_response"
    SYSTEM_MESSAGE = "system_message"


class MessageStatus(Enum):
    """Status of chat messages."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SourceReference:
    """Reference to a source document used in AI response."""
    document_type: str  # e.g., "transcript", "rubric", "pitch_data"
    document_id: str
    session_id: Optional[str] = None
    content_snippet: Optional[str] = None
    relevance_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatMessage:
    """Core chat message entity."""
    
    # Identifiers
    message_id: str
    conversation_id: str
    event_id: str  # For multi-tenant isolation
    
    # Message content
    content: str
    message_type: MessageType
    timestamp: datetime
    
    # Status and metadata
    status: MessageStatus = MessageStatus.PENDING
    error_message: Optional[str] = None
    processing_duration_ms: Optional[int] = None
    
    # AI-specific fields
    sources: Optional[List[SourceReference]] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    
    # User context
    user_id: Optional[str] = None
    session_context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.sources is None:
            self.sources = []
        if self.session_context is None:
            self.session_context = {}
    
    @classmethod
    def create_user_query(
        cls,
        message_id: str,
        conversation_id: str,
        event_id: str,
        content: str,
        user_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None
    ) -> 'ChatMessage':
        """Create a new user query message."""
        return cls(
            message_id=message_id,
            conversation_id=conversation_id,
            event_id=event_id,
            content=content,
            message_type=MessageType.USER_QUERY,
            timestamp=datetime.utcnow(),
            status=MessageStatus.PENDING,
            user_id=user_id,
            session_context=session_context or {}
        )
    
    @classmethod
    def create_ai_response(
        cls,
        message_id: str,
        conversation_id: str,
        event_id: str,
        content: str,
        sources: Optional[List[SourceReference]] = None,
        model_used: Optional[str] = None,
        tokens_used: Optional[int] = None,
        processing_duration_ms: Optional[int] = None
    ) -> 'ChatMessage':
        """Create a new AI response message."""
        return cls(
            message_id=message_id,
            conversation_id=conversation_id,
            event_id=event_id,
            content=content,
            message_type=MessageType.AI_RESPONSE,
            timestamp=datetime.utcnow(),
            status=MessageStatus.COMPLETED,
            sources=sources or [],
            model_used=model_used,
            tokens_used=tokens_used,
            processing_duration_ms=processing_duration_ms
        )
    
    def add_source(self, source: SourceReference):
        """Add a source reference to the message."""
        if self.sources is None:
            self.sources = []
        self.sources.append(source)
    
    def mark_processing(self):
        """Mark message as processing."""
        self.status = MessageStatus.PROCESSING
    
    def mark_completed(self, processing_duration_ms: Optional[int] = None):
        """Mark message as completed."""
        self.status = MessageStatus.COMPLETED
        if processing_duration_ms:
            self.processing_duration_ms = processing_duration_ms
    
    def mark_error(self, error_message: str):
        """Mark message as error."""
        self.status = MessageStatus.ERROR
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "event_id": self.event_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "error_message": self.error_message,
            "processing_duration_ms": self.processing_duration_ms,
            "sources": [
                {
                    "document_type": src.document_type,
                    "document_id": src.document_id,
                    "session_id": src.session_id,
                    "content_snippet": src.content_snippet,
                    "relevance_score": src.relevance_score,
                    "metadata": src.metadata
                }
                for src in (self.sources or [])
            ],
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "user_id": self.user_id,
            "session_context": self.session_context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create ChatMessage from dictionary."""
        sources = [
            SourceReference(
                document_type=src["document_type"],
                document_id=src["document_id"],
                session_id=src.get("session_id"),
                content_snippet=src.get("content_snippet"),
                relevance_score=src.get("relevance_score"),
                metadata=src.get("metadata")
            )
            for src in data.get("sources", [])
        ]
        
        return cls(
            message_id=data["message_id"],
            conversation_id=data["conversation_id"],
            event_id=data["event_id"],
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=MessageStatus(data["status"]),
            error_message=data.get("error_message"),
            processing_duration_ms=data.get("processing_duration_ms"),
            sources=sources,
            model_used=data.get("model_used"),
            tokens_used=data.get("tokens_used"),
            user_id=data.get("user_id"),
            session_context=data.get("session_context", {})
        )
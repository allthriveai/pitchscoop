from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime

from ..entities.stt_session import STTSession, SessionStatus
from ..value_objects.session_id import SessionId


class STTSessionRepository(ABC):
    """Repository interface for STT sessions."""
    
    @abstractmethod
    async def save(self, session: STTSession) -> None:
        """Save or update a session."""
        pass
    
    @abstractmethod
    async def get_by_id(self, session_id: SessionId) -> Optional[STTSession]:
        """Get session by ID."""
        pass
    
    @abstractmethod
    async def delete(self, session_id: SessionId) -> bool:
        """Delete a session."""
        pass
    
    @abstractmethod
    async def get_all_active(self) -> List[STTSession]:
        """Get all active sessions."""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: SessionStatus) -> List[STTSession]:
        """Get sessions by status."""
        pass
    
    @abstractmethod
    async def get_sessions_created_before(self, timestamp: datetime) -> List[STTSession]:
        """Get sessions created before a timestamp."""
        pass
    
    @abstractmethod
    async def count_active_sessions(self) -> int:
        """Count active sessions."""
        pass
    
    @abstractmethod
    async def get_session_statuses(self) -> Dict[str, str]:
        """Get status of all sessions."""
        pass
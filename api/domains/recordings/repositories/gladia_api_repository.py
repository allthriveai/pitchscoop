from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncGenerator

from ..value_objects.audio_configuration import AudioConfiguration


class GladiaAPIRepository(ABC):
    """Repository interface for Gladia API operations."""
    
    @abstractmethod
    async def create_session(self, config: AudioConfiguration) -> Dict[str, Any]:
        """Create a new Gladia session."""
        pass
    
    @abstractmethod
    async def connect_websocket(self, websocket_url: str) -> 'GladiaWebSocketConnection':
        """Connect to Gladia WebSocket."""
        pass
    
    @abstractmethod
    async def get_session_results(self, gladia_session_id: str) -> Optional[Dict[str, Any]]:
        """Get final results for a completed session."""
        pass


class GladiaWebSocketConnection(ABC):
    """Interface for Gladia WebSocket connection."""
    
    @abstractmethod
    async def send_audio(self, audio_data: bytes) -> None:
        """Send audio data."""
        pass
    
    @abstractmethod
    async def send_stop_recording(self) -> None:
        """Send stop recording message."""
        pass
    
    @abstractmethod
    async def receive_messages(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Receive messages from WebSocket."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the WebSocket connection."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        pass
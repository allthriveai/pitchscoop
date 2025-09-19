from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum

from ..value_objects.session_id import SessionId
from ..value_objects.audio_configuration import AudioConfiguration
from ..value_objects.transcript import TranscriptSegment, TranscriptCollection


class SessionStatus(Enum):
    """STT Session status enumeration."""
    INITIALIZING = "initializing"
    CONNECTED = "connected"
    RECORDING = "recording"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class STTSession:
    """Domain entity representing a Speech-to-Text session."""
    
    session_id: SessionId
    audio_config: AudioConfiguration
    status: SessionStatus = field(default=SessionStatus.INITIALIZING)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    gladia_session_id: Optional[str] = field(default=None)
    gladia_websocket_url: Optional[str] = field(default=None)
    transcripts: TranscriptCollection = field(default_factory=TranscriptCollection.empty)
    error_message: Optional[str] = field(default=None)
    session_name: Optional[str] = field(default=None)
    
    # Event handlers
    _on_transcript_callback: Optional[Callable[[TranscriptSegment], None]] = field(default=None, init=False, repr=False)
    _on_status_change_callback: Optional[Callable[['STTSession'], None]] = field(default=None, init=False, repr=False)
    _on_error_callback: Optional[Callable[[Exception], None]] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Validate session after initialization."""
        if self.created_at > datetime.utcnow() + timedelta(minutes=1):
            raise ValueError("Created date cannot be in the future")
    
    @property
    def is_active(self) -> bool:
        """Check if session is in an active state."""
        return self.status in [
            SessionStatus.INITIALIZING,
            SessionStatus.CONNECTED,
            SessionStatus.RECORDING
        ]
    
    @property
    def can_receive_audio(self) -> bool:
        """Check if session can receive audio data."""
        return self.status in [SessionStatus.CONNECTED, SessionStatus.RECORDING]
    
    @property
    def duration(self) -> timedelta:
        """Get session duration."""
        return self.updated_at - self.created_at
    
    @property
    def has_transcripts(self) -> bool:
        """Check if session has any transcripts."""
        return len(self.transcripts.segments) > 0
    
    @property
    def final_transcripts_only(self) -> TranscriptCollection:
        """Get only final transcripts."""
        return self.transcripts.final_segments_only
    
    def set_gladia_connection(self, session_id: str, websocket_url: str) -> None:
        """Set Gladia connection details."""
        self.gladia_session_id = session_id
        self.gladia_websocket_url = websocket_url
        self._update_timestamp()
    
    def change_status(self, new_status: SessionStatus, error_message: Optional[str] = None) -> None:
        """Change session status with validation."""
        if not self._is_valid_status_transition(self.status, new_status):
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")
        
        old_status = self.status
        self.status = new_status
        self.error_message = error_message
        self._update_timestamp()
        
        # Trigger status change callback
        if self._on_status_change_callback:
            try:
                self._on_status_change_callback(self)
            except Exception as e:
                # Log error but don't fail the status change
                print(f"Error in status change callback: {e}")
    
    def add_transcript(self, segment: TranscriptSegment) -> None:
        """Add a new transcript segment."""
        if not self.is_active:
            raise ValueError("Cannot add transcript to inactive session")
        
        self.transcripts = self.transcripts.add_segment(segment)
        self._update_timestamp()
        
        # Trigger transcript callback
        if self._on_transcript_callback:
            try:
                self._on_transcript_callback(segment)
            except Exception as e:
                # Log error but don't fail the transcript addition
                print(f"Error in transcript callback: {e}")
    
    def set_error(self, error_message: str) -> None:
        """Set session to error state."""
        self.change_status(SessionStatus.ERROR, error_message)
        
        # Trigger error callback
        if self._on_error_callback:
            try:
                self._on_error_callback(Exception(error_message))
            except Exception as e:
                print(f"Error in error callback: {e}")
    
    def start_recording(self) -> None:
        """Transition to recording state."""
        if self.status == SessionStatus.CONNECTED:
            self.change_status(SessionStatus.RECORDING)
        else:
            raise ValueError(f"Cannot start recording from status {self.status}")
    
    def stop_recording(self) -> None:
        """Transition to stopping state."""
        if self.status in [SessionStatus.CONNECTED, SessionStatus.RECORDING]:
            self.change_status(SessionStatus.STOPPING)
        else:
            raise ValueError(f"Cannot stop recording from status {self.status}")
    
    def mark_as_stopped(self) -> None:
        """Mark session as stopped."""
        if self.status == SessionStatus.STOPPING:
            self.change_status(SessionStatus.STOPPED)
        else:
            raise ValueError(f"Cannot mark as stopped from status {self.status}")
    
    def set_transcript_callback(self, callback: Callable[[TranscriptSegment], None]) -> None:
        """Set transcript callback."""
        self._on_transcript_callback = callback
    
    def set_status_change_callback(self, callback: Callable[['STTSession'], None]) -> None:
        """Set status change callback."""
        self._on_status_change_callback = callback
    
    def set_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """Set error callback."""
        self._on_error_callback = callback
    
    def get_transcripts_by_channel(self, channel: int) -> TranscriptCollection:
        """Get transcripts for specific channel."""
        return self.transcripts.get_segments_by_channel(channel)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            'session_id': str(self.session_id),
            'audio_config': self.audio_config.to_gladia_config(),
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'gladia_session_id': self.gladia_session_id,
            'gladia_websocket_url': self.gladia_websocket_url,
            'transcripts': self.transcripts.to_dict(),
            'error_message': self.error_message,
            'session_name': self.session_name,
            'duration_seconds': self.duration.total_seconds(),
            'has_transcripts': self.has_transcripts
        }
    
    def _update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def _is_valid_status_transition(self, from_status: SessionStatus, to_status: SessionStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions = {
            SessionStatus.INITIALIZING: [SessionStatus.CONNECTED, SessionStatus.ERROR],
            SessionStatus.CONNECTED: [SessionStatus.RECORDING, SessionStatus.STOPPING, SessionStatus.ERROR],
            SessionStatus.RECORDING: [SessionStatus.STOPPING, SessionStatus.ERROR],
            SessionStatus.STOPPING: [SessionStatus.STOPPED, SessionStatus.ERROR],
            SessionStatus.STOPPED: [],  # Terminal state
            SessionStatus.ERROR: []     # Terminal state
        }
        
        return to_status in valid_transitions.get(from_status, [])
    
    @classmethod
    def create_new(
        cls,
        audio_config: AudioConfiguration,
        session_name: Optional[str] = None
    ) -> 'STTSession':
        """Create a new STT session."""
        return cls(
            session_id=SessionId.generate(),
            audio_config=audio_config,
            session_name=session_name
        )
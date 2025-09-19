#!/usr/bin/env python3
"""
Recording Version Entity

Domain entity representing a single version of a team's pitch recording.
Used for tracking how recordings evolve over time in the progression analysis system.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

from ..value_objects.session_id import SessionId
from ..value_objects.transcript import TranscriptCollection
from ..value_objects.recording_version_id import RecordingVersionId
from ..value_objects.team_id import TeamId
from ..value_objects.recording_scores import RecordingScores
from ..value_objects.audio_intelligence import AudioIntelligence


@dataclass
class RecordingVersion:
    """Domain entity representing a single version of a team's pitch recording."""
    
    version_id: RecordingVersionId
    team_id: TeamId
    team_name: str
    recording_title: str
    session_id: SessionId
    transcripts: TranscriptCollection
    version_number: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional contextual data
    event_id: Optional[str] = field(default=None)
    scores: Optional[RecordingScores] = field(default=None)
    audio_intelligence: Optional[AudioIntelligence] = field(default=None)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate recording version after initialization."""
        if not self.recording_title.strip():
            raise ValueError("Recording title cannot be empty")
        
        if not self.team_name.strip():
            raise ValueError("Team name cannot be empty")
        
        if self.version_number < 1:
            raise ValueError("Version number must be at least 1")
        
        if self.created_at > datetime.utcnow():
            raise ValueError("Created date cannot be in the future")
    
    @property
    def full_transcript_text(self) -> str:
        """Get the full transcript text from all segments."""
        return self.transcripts.full_text
    
    @property
    def final_transcript_text(self) -> str:
        """Get only final transcript text."""
        return self.transcripts.final_segments_only.full_text
    
    @property
    def word_count(self) -> int:
        """Get total word count of the transcript."""
        return self.transcripts.word_count
    
    @property
    def duration_seconds(self) -> float:
        """Get total duration in seconds."""
        return self.transcripts.total_duration
    
    @property
    def has_scores(self) -> bool:
        """Check if this version has scoring data."""
        return self.scores is not None
    
    @property
    def has_audio_intelligence(self) -> bool:
        """Check if this version has audio intelligence data."""
        return self.audio_intelligence is not None
    
    def get_score_by_category(self, category: str) -> Optional[float]:
        """Get score for a specific category."""
        if not self.has_scores:
            return None
        return self.scores.get_score(category)
    
    def get_total_score(self) -> Optional[float]:
        """Get total score if available."""
        if not self.has_scores:
            return None
        return self.scores.total_score
    
    def update_scores(self, new_scores: RecordingScores) -> 'RecordingVersion':
        """Create a new version with updated scores."""
        return RecordingVersion(
            version_id=self.version_id,
            team_id=self.team_id,
            team_name=self.team_name,
            recording_title=self.recording_title,
            session_id=self.session_id,
            transcripts=self.transcripts,
            version_number=self.version_number,
            created_at=self.created_at,
            event_id=self.event_id,
            scores=new_scores,
            audio_intelligence=self.audio_intelligence,
            metadata=self.metadata
        )
    
    def update_audio_intelligence(self, new_intelligence: AudioIntelligence) -> 'RecordingVersion':
        """Create a new version with updated audio intelligence."""
        return RecordingVersion(
            version_id=self.version_id,
            team_id=self.team_id,
            team_name=self.team_name,
            recording_title=self.recording_title,
            session_id=self.session_id,
            transcripts=self.transcripts,
            version_number=self.version_number,
            created_at=self.created_at,
            event_id=self.event_id,
            scores=self.scores,
            audio_intelligence=new_intelligence,
            metadata=self.metadata
        )
    
    def add_metadata(self, key: str, value: Any) -> 'RecordingVersion':
        """Create a new version with additional metadata."""
        new_metadata = {**self.metadata, key: value}
        return RecordingVersion(
            version_id=self.version_id,
            team_id=self.team_id,
            team_name=self.team_name,
            recording_title=self.recording_title,
            session_id=self.session_id,
            transcripts=self.transcripts,
            version_number=self.version_number,
            created_at=self.created_at,
            event_id=self.event_id,
            scores=self.scores,
            audio_intelligence=self.audio_intelligence,
            metadata=new_metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "version_id": str(self.version_id),
            "team_id": str(self.team_id),
            "team_name": self.team_name,
            "recording_title": self.recording_title,
            "session_id": str(self.session_id),
            "version_number": self.version_number,
            "created_at": self.created_at.isoformat(),
            "transcripts": self.transcripts.to_dict(),
            "word_count": self.word_count,
            "duration_seconds": self.duration_seconds,
            "event_id": self.event_id,
            "metadata": self.metadata
        }
        
        if self.scores:
            result["scores"] = self.scores.to_dict()
        
        if self.audio_intelligence:
            result["audio_intelligence"] = self.audio_intelligence.to_dict()
        
        return result
    
    @classmethod
    def create_new(
        cls,
        team_id: TeamId,
        team_name: str,
        recording_title: str,
        session_id: SessionId,
        transcripts: TranscriptCollection,
        version_number: int,
        event_id: Optional[str] = None,
        scores: Optional[RecordingScores] = None,
        audio_intelligence: Optional[AudioIntelligence] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'RecordingVersion':
        """Create a new recording version."""
        return cls(
            version_id=RecordingVersionId.generate(),
            team_id=team_id,
            team_name=team_name,
            recording_title=recording_title,
            session_id=session_id,
            transcripts=transcripts,
            version_number=version_number,
            event_id=event_id,
            scores=scores,
            audio_intelligence=audio_intelligence,
            metadata=metadata or {}
        )
    
    @classmethod
    def from_stt_session(
        cls,
        stt_session: 'STTSession',
        team_id: TeamId,
        team_name: str,
        recording_title: str,
        version_number: int,
        scores: Optional[RecordingScores] = None,
        audio_intelligence: Optional[AudioIntelligence] = None
    ) -> 'RecordingVersion':
        """Create recording version from STT session."""
        from ..entities.stt_session import STTSession
        
        if not isinstance(stt_session, STTSession):
            raise ValueError("Invalid STT session provided")
        
        return cls.create_new(
            team_id=team_id,
            team_name=team_name,
            recording_title=recording_title,
            session_id=stt_session.session_id,
            transcripts=stt_session.final_transcripts_only,
            version_number=version_number,
            event_id=stt_session.event_id,
            scores=scores,
            audio_intelligence=audio_intelligence
        )
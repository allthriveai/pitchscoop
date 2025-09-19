from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass(frozen=True)
class TranscriptSegment:
    """Value object representing a single transcript segment."""
    
    id: str
    text: str
    start_time: float
    end_time: float
    language: str
    channel: Optional[int] = None
    confidence: Optional[float] = None
    is_final: bool = False
    
    def __post_init__(self):
        """Validate transcript segment."""
        if not self.text.strip():
            raise ValueError("Transcript text cannot be empty")
        
        if self.start_time < 0:
            raise ValueError("Start time cannot be negative")
        
        if self.end_time < self.start_time:
            raise ValueError("End time must be greater than start time")
        
        if self.confidence is not None and (self.confidence < 0 or self.confidence > 1):
            raise ValueError("Confidence must be between 0 and 1")
        
        if self.channel is not None and self.channel < 0:
            raise ValueError("Channel must be non-negative")
    
    @property
    def duration(self) -> float:
        """Get duration of transcript segment."""
        return self.end_time - self.start_time
    
    @property
    def word_count(self) -> int:
        """Get word count of transcript text."""
        return len(self.text.split())
    
    def has_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if transcript has high confidence."""
        if self.confidence is None:
            return True  # Assume high confidence if not provided
        return self.confidence >= threshold
    
    @classmethod
    def from_gladia_message(cls, message: Dict[str, Any]) -> Optional['TranscriptSegment']:
        """Create from Gladia WebSocket message."""
        try:
            if message.get('type') != 'transcript':
                return None
                
            data = message.get('data', {})
            utterance = data.get('utterance', {})
            
            return cls(
                id=data.get('id', ''),
                text=utterance.get('text', ''),
                start_time=utterance.get('start', 0.0),
                end_time=utterance.get('end', 0.0),
                language=utterance.get('language', 'en'),
                channel=utterance.get('channel'),
                confidence=utterance.get('confidence'),
                is_final=data.get('is_final', False)
            )
        except (KeyError, TypeError, ValueError):
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'text': self.text,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'language': self.language,
            'channel': self.channel,
            'confidence': self.confidence,
            'is_final': self.is_final,
            'duration': self.duration,
            'word_count': self.word_count
        }


@dataclass(frozen=True)
class TranscriptCollection:
    """Value object representing a collection of transcript segments."""
    
    segments: tuple[TranscriptSegment, ...]
    created_at: datetime
    
    def __post_init__(self):
        """Validate transcript collection."""
        # Convert list to tuple for immutability
        if isinstance(self.segments, list):
            object.__setattr__(self, 'segments', tuple(self.segments))
    
    @property
    def total_duration(self) -> float:
        """Get total duration of all segments."""
        if not self.segments:
            return 0.0
        return max(segment.end_time for segment in self.segments) - \
               min(segment.start_time for segment in self.segments)
    
    @property
    def word_count(self) -> int:
        """Get total word count of all segments."""
        return sum(segment.word_count for segment in self.segments)
    
    @property
    def full_text(self) -> str:
        """Get concatenated text of all segments."""
        return ' '.join(segment.text for segment in self.segments)
    
    @property
    def final_segments_only(self) -> 'TranscriptCollection':
        """Get collection with only final segments."""
        final_segments = [seg for seg in self.segments if seg.is_final]
        return TranscriptCollection(
            segments=tuple(final_segments),
            created_at=self.created_at
        )
    
    def get_segments_by_channel(self, channel: int) -> 'TranscriptCollection':
        """Get segments for specific channel."""
        channel_segments = [
            seg for seg in self.segments 
            if seg.channel == channel
        ]
        return TranscriptCollection(
            segments=tuple(channel_segments),
            created_at=self.created_at
        )
    
    def add_segment(self, segment: TranscriptSegment) -> 'TranscriptCollection':
        """Create new collection with additional segment."""
        new_segments = list(self.segments) + [segment]
        # Sort by start time
        new_segments.sort(key=lambda s: s.start_time)
        return TranscriptCollection(
            segments=tuple(new_segments),
            created_at=self.created_at
        )
    
    @classmethod
    def empty(cls) -> 'TranscriptCollection':
        """Create empty transcript collection."""
        return cls(segments=tuple(), created_at=datetime.utcnow())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'segments': [segment.to_dict() for segment in self.segments],
            'created_at': self.created_at.isoformat(),
            'total_duration': self.total_duration,
            'word_count': self.word_count,
            'full_text': self.full_text
        }
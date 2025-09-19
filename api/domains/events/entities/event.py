"""
Event Entity - Core business entity for PitchScoop events

Represents events (hackathons, VC pitches, practice sessions) with complete
metadata including sponsors, audience, and event types.
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum


class EventStatus(Enum):
    """Event status enumeration."""
    DRAFT = "draft"
    UPCOMING = "upcoming" 
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventType(Enum):
    """Event type enumeration."""
    HACKATHON = "hackathon"
    VC_PITCH = "vc_pitch"
    STARTUP_COMPETITION = "startup_competition"
    DEMO_DAY = "demo_day"
    PRACTICE_SESSION = "practice_session"  # Covers both individual and team practice
    INVESTOR_SHOWCASE = "investor_showcase"
    ACCELERATOR_PITCH = "accelerator_pitch"


class AudienceType(Enum):
    """Intended audience types."""
    EARLY_STAGE_STARTUPS = "early_stage_startups"
    GROWTH_STAGE_COMPANIES = "growth_stage_companies"
    STUDENTS = "students"
    PROFESSIONALS = "professionals"
    INVESTORS = "investors"
    ENTREPRENEURS = "entrepreneurs"
    DEVELOPERS = "developers"
    DESIGNERS = "designers"
    CORPORATE_INNOVATORS = "corporate_innovators"
    GENERAL_PUBLIC = "general_public"


@dataclass
class Sponsor:
    """Event sponsor information."""
    name: str
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    sponsor_tier: str = "standard"  # platinum, gold, silver, bronze, standard
    description: Optional[str] = None
    contact_email: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "logo_url": self.logo_url,
            "website_url": self.website_url,
            "sponsor_tier": self.sponsor_tier,
            "description": self.description,
            "contact_email": self.contact_email
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sponsor':
        """Create from dictionary."""
        return cls(
            name=data["name"],
            logo_url=data.get("logo_url"),
            website_url=data.get("website_url"),
            sponsor_tier=data.get("sponsor_tier", "standard"),
            description=data.get("description"),
            contact_email=data.get("contact_email")
        )


@dataclass
class EventConfiguration:
    """Event-specific configuration."""
    judging_enabled: bool = True
    public_leaderboard: bool = True
    allow_multiple_attempts: bool = False
    team_based: bool = True
    scoring_criteria: List[str] = field(default_factory=list)
    pitch_duration_minutes: int = 5
    max_team_size: int = 5
    registration_required: bool = True
    live_streaming: bool = False
    recording_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "judging_enabled": self.judging_enabled,
            "public_leaderboard": self.public_leaderboard,
            "allow_multiple_attempts": self.allow_multiple_attempts,
            "team_based": self.team_based,
            "scoring_criteria": self.scoring_criteria,
            "pitch_duration_minutes": self.pitch_duration_minutes,
            "max_team_size": self.max_team_size,
            "registration_required": self.registration_required,
            "live_streaming": self.live_streaming,
            "recording_enabled": self.recording_enabled
        }


@dataclass
class Event:
    """Core Event domain entity."""
    
    # Core identifiers
    event_id: str
    event_name: str
    
    # Event metadata
    event_date: date
    description: str
    
    # Multiple sponsors
    sponsors: List[Sponsor] = field(default_factory=list)
    
    # Multiple intended audiences
    intended_audience: List[AudienceType] = field(default_factory=list)
    
    # Multiple event types (e.g., hackathon + demo_day)
    event_types: List[EventType] = field(default_factory=list)
    
    # Status and lifecycle
    status: EventStatus = EventStatus.DRAFT
    
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Capacity and participation
    max_participants: int = 50
    current_participant_count: int = 0
    max_teams: Optional[int] = None
    
    # Configuration
    configuration: EventConfiguration = field(default_factory=EventConfiguration)
    
    # Additional metadata
    location: Optional[str] = None
    virtual_event: bool = False
    timezone: str = "UTC"
    registration_deadline: Optional[datetime] = None
    
    # Contact and organization
    organizer_name: Optional[str] = None
    organizer_email: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None
    
    # External links
    website_url: Optional[str] = None
    registration_url: Optional[str] = None
    
    # Internal tracking
    session_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # User relationships
    participant_ids: List[str] = field(default_factory=list)  # Users who participate/pitch
    organizer_ids: List[str] = field(default_factory=list)    # Users who organize the event
    judge_ids: List[str] = field(default_factory=list)        # Users who judge/score pitches
    recording_ids: List[str] = field(default_factory=list)    # Recording sessions for this event
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        # Ensure at least one event type
        if not self.event_types:
            self.event_types = [EventType.HACKATHON]
        
        # Ensure at least one audience type
        if not self.intended_audience:
            self.intended_audience = [AudienceType.ENTREPRENEURS]
        
        # Set default configuration based on event types
        if EventType.PRACTICE_SESSION in self.event_types:
            self.configuration.judging_enabled = False
            self.configuration.public_leaderboard = False
            # team_based remains configurable for practice sessions
        
        # Validate dates
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValueError("End time must be after start time")
    
    @property
    def is_active(self) -> bool:
        """Check if event is currently active."""
        return self.status == EventStatus.ACTIVE
    
    @property
    def is_upcoming(self) -> bool:
        """Check if event is upcoming."""
        return self.status == EventStatus.UPCOMING
    
    @property
    def is_completed(self) -> bool:
        """Check if event is completed."""
        return self.status == EventStatus.COMPLETED
    
    @property 
    def has_capacity(self) -> bool:
        """Check if event has remaining capacity."""
        return self.current_participant_count < self.max_participants
    
    @property
    def capacity_percentage(self) -> float:
        """Get capacity utilization percentage."""
        if self.max_participants == 0:
            return 0.0
        return (self.current_participant_count / self.max_participants) * 100
    
    @property
    def primary_event_type(self) -> EventType:
        """Get the primary event type."""
        return self.event_types[0] if self.event_types else EventType.HACKATHON
    
    @property
    def sponsor_names(self) -> List[str]:
        """Get list of sponsor names."""
        return [sponsor.name for sponsor in self.sponsors]
    
    @property
    def audience_names(self) -> List[str]:
        """Get list of audience type names."""
        return [audience.value for audience in self.intended_audience]
    
    @property
    def event_type_names(self) -> List[str]:
        """Get list of event type names."""
        return [event_type.value for event_type in self.event_types]
    
    @property
    def participant_count_actual(self) -> int:
        """Get actual participant count from participant_ids."""
        return len(self.participant_ids)
    
    @property
    def organizer_count(self) -> int:
        """Get count of event organizers."""
        return len(self.organizer_ids)
    
    @property
    def judge_count(self) -> int:
        """Get count of event judges."""
        return len(self.judge_ids)
    
    @property
    def total_recordings(self) -> int:
        """Get total number of recordings for this event."""
        return len(self.recording_ids)
    
    def add_sponsor(self, sponsor: Sponsor):
        """Add a sponsor to the event."""
        if sponsor not in self.sponsors:
            self.sponsors.append(sponsor)
            self._update_timestamp()
    
    def remove_sponsor(self, sponsor_name: str):
        """Remove a sponsor by name."""
        self.sponsors = [s for s in self.sponsors if s.name != sponsor_name]
        self._update_timestamp()
    
    def add_audience_type(self, audience_type: AudienceType):
        """Add an audience type."""
        if audience_type not in self.intended_audience:
            self.intended_audience.append(audience_type)
            self._update_timestamp()
    
    def add_event_type(self, event_type: EventType):
        """Add an event type."""
        if event_type not in self.event_types:
            self.event_types.append(event_type)
            self._update_timestamp()
    
    def update_status(self, new_status: EventStatus):
        """Update event status."""
        old_status = self.status
        self.status = new_status
        self._update_timestamp()
        
        # Log status change in metadata
        if "status_history" not in self.metadata:
            self.metadata["status_history"] = []
        
        self.metadata["status_history"].append({
            "from_status": old_status.value,
            "to_status": new_status.value,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def increment_participants(self, count: int = 1):
        """Increment participant count."""
        if self.current_participant_count + count <= self.max_participants:
            self.current_participant_count += count
            self._update_timestamp()
        else:
            raise ValueError("Would exceed maximum participants")
    
    def decrement_participants(self, count: int = 1):
        """Decrement participant count."""
        if self.current_participant_count - count >= 0:
            self.current_participant_count -= count
            self._update_timestamp()
        else:
            raise ValueError("Cannot have negative participants")
    
    def increment_sessions(self, count: int = 1):
        """Increment session count."""
        self.session_count += count
        self._update_timestamp()
    
    def add_participant(self, user_id: str):
        """Add a participant to the event."""
        if user_id not in self.participant_ids:
            if len(self.participant_ids) >= self.max_participants:
                raise ValueError("Event is full")
            self.participant_ids.append(user_id)
            self.current_participant_count = len(self.participant_ids)
            self._update_timestamp()
    
    def remove_participant(self, user_id: str):
        """Remove a participant from the event."""
        if user_id in self.participant_ids:
            self.participant_ids.remove(user_id)
            self.current_participant_count = len(self.participant_ids)
            self._update_timestamp()
    
    def add_organizer(self, user_id: str):
        """Add an organizer to the event."""
        if user_id not in self.organizer_ids:
            self.organizer_ids.append(user_id)
            self._update_timestamp()
    
    def remove_organizer(self, user_id: str):
        """Remove an organizer from the event."""
        if user_id in self.organizer_ids:
            self.organizer_ids.remove(user_id)
            self._update_timestamp()
    
    def add_judge(self, user_id: str):
        """Add a judge to the event."""
        if user_id not in self.judge_ids:
            self.judge_ids.append(user_id)
            self._update_timestamp()
    
    def remove_judge(self, user_id: str):
        """Remove a judge from the event."""
        if user_id in self.judge_ids:
            self.judge_ids.remove(user_id)
            self._update_timestamp()
    
    def add_recording(self, recording_id: str):
        """Add a recording to the event."""
        if recording_id not in self.recording_ids:
            self.recording_ids.append(recording_id)
            self.session_count = len(self.recording_ids)
            self._update_timestamp()
    
    def remove_recording(self, recording_id: str):
        """Remove a recording from the event."""
        if recording_id in self.recording_ids:
            self.recording_ids.remove(recording_id)
            self.session_count = len(self.recording_ids)
            self._update_timestamp()
    
    def has_participant(self, user_id: str) -> bool:
        """Check if user is a participant in this event."""
        return user_id in self.participant_ids
    
    def has_organizer(self, user_id: str) -> bool:
        """Check if user is an organizer of this event."""
        return user_id in self.organizer_ids
    
    def has_judge(self, user_id: str) -> bool:
        """Check if user is a judge for this event."""
        return user_id in self.judge_ids
    
    def has_recording(self, recording_id: str) -> bool:
        """Check if recording belongs to this event."""
        return recording_id in self.recording_ids
    
    def _update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            # Core fields
            "event_id": self.event_id,
            "event_name": self.event_name,
            "event_date": self.event_date.isoformat(),
            "description": self.description,
            
            # Multiple values
            "sponsors": [sponsor.to_dict() for sponsor in self.sponsors],
            "intended_audience": [audience.value for audience in self.intended_audience],
            "event_types": [event_type.value for event_type in self.event_types],
            
            # Status and timing
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            
            # Capacity
            "max_participants": self.max_participants,
            "current_participant_count": self.current_participant_count,
            "max_teams": self.max_teams,
            "session_count": self.session_count,
            
            # Configuration
            "configuration": self.configuration.to_dict(),
            
            # Additional metadata
            "location": self.location,
            "virtual_event": self.virtual_event,
            "timezone": self.timezone,
            "registration_deadline": self.registration_deadline.isoformat() if self.registration_deadline else None,
            "organizer_name": self.organizer_name,
            "organizer_email": self.organizer_email,
            "contact_info": self.contact_info or {},
            "website_url": self.website_url,
            "registration_url": self.registration_url,
            "metadata": self.metadata,
            
            # User relationships
            "participant_ids": self.participant_ids,
            "organizer_ids": self.organizer_ids,
            "judge_ids": self.judge_ids,
            "recording_ids": self.recording_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create Event from dictionary."""
        # Parse sponsors
        sponsors = [
            Sponsor.from_dict(sponsor_data) 
            for sponsor_data in data.get("sponsors", [])
        ]
        
        # Parse audience types
        intended_audience = [
            AudienceType(audience) 
            for audience in data.get("intended_audience", [])
        ]
        
        # Parse event types
        event_types = [
            EventType(event_type) 
            for event_type in data.get("event_types", [])
        ]
        
        # Parse configuration
        config_data = data.get("configuration", {})
        configuration = EventConfiguration(
            judging_enabled=config_data.get("judging_enabled", True),
            public_leaderboard=config_data.get("public_leaderboard", True),
            allow_multiple_attempts=config_data.get("allow_multiple_attempts", False),
            team_based=config_data.get("team_based", True),
            scoring_criteria=config_data.get("scoring_criteria", []),
            pitch_duration_minutes=config_data.get("pitch_duration_minutes", 5),
            max_team_size=config_data.get("max_team_size", 5),
            registration_required=config_data.get("registration_required", True),
            live_streaming=config_data.get("live_streaming", False),
            recording_enabled=config_data.get("recording_enabled", True)
        )
        
        return cls(
            event_id=data["event_id"],
            event_name=data["event_name"],
            event_date=date.fromisoformat(data["event_date"]),
            description=data["description"],
            sponsors=sponsors,
            intended_audience=intended_audience,
            event_types=event_types,
            status=EventStatus(data.get("status", "draft")),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
            max_participants=data.get("max_participants", 50),
            current_participant_count=data.get("current_participant_count", 0),
            max_teams=data.get("max_teams"),
            configuration=configuration,
            location=data.get("location"),
            virtual_event=data.get("virtual_event", False),
            timezone=data.get("timezone", "UTC"),
            registration_deadline=datetime.fromisoformat(data["registration_deadline"]) if data.get("registration_deadline") else None,
            organizer_name=data.get("organizer_name"),
            organizer_email=data.get("organizer_email"),
            contact_info=data.get("contact_info", {}),
            website_url=data.get("website_url"),
            registration_url=data.get("registration_url"),
            session_count=data.get("session_count", 0),
            metadata=data.get("metadata", {}),
            
            # User relationships
            participant_ids=data.get("participant_ids", []),
            organizer_ids=data.get("organizer_ids", []),
            judge_ids=data.get("judge_ids", []),
            recording_ids=data.get("recording_ids", [])
        )
    
    @classmethod
    def create_new(
        cls,
        event_name: str,
        event_date: date,
        description: str,
        sponsors: Optional[List[Sponsor]] = None,
        intended_audience: Optional[List[AudienceType]] = None,
        event_types: Optional[List[EventType]] = None,
        **kwargs
    ) -> 'Event':
        """Create a new event with sensible defaults."""
        import uuid
        
        return cls(
            event_id=str(uuid.uuid4()),
            event_name=event_name,
            event_date=event_date,
            description=description,
            sponsors=sponsors or [],
            intended_audience=intended_audience or [AudienceType.ENTREPRENEURS],
            event_types=event_types or [EventType.HACKATHON],
            **kwargs
        )
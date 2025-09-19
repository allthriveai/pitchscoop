"""
User Entity - Core business entity for PitchScoop users

Represents users with their basic information and relationships to 
recordings and events in the PitchScoop system.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import re


class UserRole(Enum):
    """User role enumeration."""
    ORGANIZER = "organizer"        # Event organizers
    PARTICIPANT = "participant"    # Event participants/pitchers
    JUDGE = "judge"               # Judges and evaluators
    MENTOR = "mentor"             # Mentors and advisors
    SPECTATOR = "spectator"       # Viewers/audience
    ADMIN = "admin"               # System administrators


class UserStatus(Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"           # Email verification pending
    SUSPENDED = "suspended"       # Temporarily suspended
    DELETED = "deleted"           # Soft deleted


@dataclass
class UserProfile:
    """User profile information."""
    bio: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    github: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bio": self.bio,
            "company": self.company,
            "position": self.position,
            "website": self.website,
            "linkedin": self.linkedin,
            "twitter": self.twitter,
            "github": self.github,
            "avatar_url": self.avatar_url,
            "location": self.location,
            "skills": self.skills,
            "interests": self.interests
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create from dictionary."""
        return cls(
            bio=data.get("bio"),
            company=data.get("company"),
            position=data.get("position"),
            website=data.get("website"),
            linkedin=data.get("linkedin"),
            twitter=data.get("twitter"),
            github=data.get("github"),
            avatar_url=data.get("avatar_url"),
            location=data.get("location"),
            skills=data.get("skills", []),
            interests=data.get("interests", [])
        )


@dataclass
class User:
    """Core User domain entity."""
    
    # Core identifiers
    user_id: str
    name: str
    email: str
    
    # Relationships to other entities
    recording_ids: List[str] = field(default_factory=list)  # User's recordings
    event_ids: List[str] = field(default_factory=list)      # User's events (participant or organizer)
    
    # User attributes
    role: UserRole = UserRole.PARTICIPANT
    status: UserStatus = UserStatus.ACTIVE
    
    # Profile information
    profile: UserProfile = field(default_factory=UserProfile)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    
    # Settings and preferences
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        # Validate email format
        if not self._is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        
        # Normalize email to lowercase
        self.email = self.email.lower().strip()
        
        # Validate name
        if not self.name or len(self.name.strip()) < 1:
            raise ValueError("Name cannot be empty")
        
        self.name = self.name.strip()
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE
    
    @property
    def is_verified(self) -> bool:
        """Check if user email is verified."""
        return self.email_verified_at is not None
    
    @property
    def is_organizer(self) -> bool:
        """Check if user is an organizer."""
        return self.role == UserRole.ORGANIZER
    
    @property
    def is_judge(self) -> bool:
        """Check if user is a judge."""
        return self.role == UserRole.JUDGE
    
    @property
    def is_participant(self) -> bool:
        """Check if user is a participant."""
        return self.role == UserRole.PARTICIPANT
    
    @property
    def recording_count(self) -> int:
        """Get count of user's recordings."""
        return len(self.recording_ids)
    
    @property
    def event_count(self) -> int:
        """Get count of user's events."""
        return len(self.event_ids)
    
    @property
    def display_name(self) -> str:
        """Get display name for the user."""
        if self.profile.company and self.profile.position:
            return f"{self.name} - {self.profile.position} at {self.profile.company}"
        elif self.profile.company:
            return f"{self.name} - {self.profile.company}"
        elif self.profile.position:
            return f"{self.name} - {self.profile.position}"
        else:
            return self.name
    
    def add_recording(self, recording_id: str):
        """Add a recording to the user's collection."""
        if recording_id not in self.recording_ids:
            self.recording_ids.append(recording_id)
            self._update_timestamp()
    
    def remove_recording(self, recording_id: str):
        """Remove a recording from the user's collection."""
        if recording_id in self.recording_ids:
            self.recording_ids.remove(recording_id)
            self._update_timestamp()
    
    def add_event(self, event_id: str):
        """Add an event to the user's collection."""
        if event_id not in self.event_ids:
            self.event_ids.append(event_id)
            self._update_timestamp()
    
    def remove_event(self, event_id: str):
        """Remove an event from the user's collection."""
        if event_id in self.event_ids:
            self.event_ids.remove(event_id)
            self._update_timestamp()
    
    def update_role(self, new_role: UserRole):
        """Update user role."""
        old_role = self.role
        self.role = new_role
        self._update_timestamp()
        
        # Log role change in metadata
        if "role_history" not in self.metadata:
            self.metadata["role_history"] = []
        
        self.metadata["role_history"].append({
            "from_role": old_role.value,
            "to_role": new_role.value,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def update_status(self, new_status: UserStatus):
        """Update user status."""
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
    
    def verify_email(self):
        """Mark email as verified."""
        self.email_verified_at = datetime.utcnow()
        self._update_timestamp()
    
    def record_login(self):
        """Record user login."""
        self.last_login_at = datetime.utcnow()
        self._update_timestamp()
    
    def update_profile(self, **profile_updates):
        """Update profile information."""
        for key, value in profile_updates.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
        self._update_timestamp()
    
    def set_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.preferences[key] = value
        self._update_timestamp()
    
    def get_preference(self, key: str, default: Any = None):
        """Get a user preference."""
        return self.preferences.get(key, default)
    
    def has_recording(self, recording_id: str) -> bool:
        """Check if user has a specific recording."""
        return recording_id in self.recording_ids
    
    def has_event(self, event_id: str) -> bool:
        """Check if user is associated with a specific event."""
        return event_id in self.event_ids
    
    def _update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            # Core fields
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            
            # Relationships
            "recording_ids": self.recording_ids,
            "event_ids": self.event_ids,
            
            # Attributes
            "role": self.role.value,
            "status": self.status.value,
            "profile": self.profile.to_dict(),
            
            # Timestamps
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "email_verified_at": self.email_verified_at.isoformat() if self.email_verified_at else None,
            
            # Settings
            "preferences": self.preferences,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary."""
        # Parse profile
        profile_data = data.get("profile", {})
        profile = UserProfile.from_dict(profile_data)
        
        return cls(
            user_id=data["user_id"],
            name=data["name"],
            email=data["email"],
            recording_ids=data.get("recording_ids", []),
            event_ids=data.get("event_ids", []),
            role=UserRole(data.get("role", "participant")),
            status=UserStatus(data.get("status", "active")),
            profile=profile,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.utcnow().isoformat())),
            last_login_at=datetime.fromisoformat(data["last_login_at"]) if data.get("last_login_at") else None,
            email_verified_at=datetime.fromisoformat(data["email_verified_at"]) if data.get("email_verified_at") else None,
            preferences=data.get("preferences", {}),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def create_new(
        cls,
        name: str,
        email: str,
        role: UserRole = UserRole.PARTICIPANT,
        **kwargs
    ) -> 'User':
        """Create a new user with sensible defaults."""
        import uuid
        
        return cls(
            user_id=str(uuid.uuid4()),
            name=name,
            email=email,
            role=role,
            **kwargs
        )
    
    @classmethod
    def create_organizer(
        cls,
        name: str,
        email: str,
        **kwargs
    ) -> 'User':
        """Create a new organizer user."""
        return cls.create_new(
            name=name,
            email=email,
            role=UserRole.ORGANIZER,
            **kwargs
        )
    
    @classmethod
    def create_judge(
        cls,
        name: str,
        email: str,
        **kwargs
    ) -> 'User':
        """Create a new judge user."""
        return cls.create_new(
            name=name,
            email=email,
            role=UserRole.JUDGE,
            **kwargs
        )
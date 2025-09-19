import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionId:
    """Value object representing a session identifier."""
    
    value: str
    
    def __post_init__(self):
        """Validate session ID format."""
        if not self.value:
            raise ValueError("Session ID cannot be empty")
        
        if len(self.value) < 8:
            raise ValueError("Session ID must be at least 8 characters")
    
    @classmethod
    def generate(cls) -> 'SessionId':
        """Generate a new session ID."""
        return cls(str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, value: str) -> 'SessionId':
        """Create from string value."""
        return cls(value)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"SessionId({self.value})"
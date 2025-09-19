#!/usr/bin/env python3
"""
Team ID Value Object

Represents a unique identifier for a team in the recording progression system.
"""
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class TeamId:
    """Value object representing a team identifier."""
    
    value: str
    
    def __post_init__(self):
        """Validate team ID format."""
        if not self.value:
            raise ValueError("Team ID cannot be empty")
        
        if len(self.value) < 3:
            raise ValueError("Team ID must be at least 3 characters")
    
    @classmethod
    def generate(cls) -> 'TeamId':
        """Generate a new team ID."""
        return cls(str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, value: str) -> 'TeamId':
        """Create from string value."""
        return cls(value)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"TeamId({self.value})"
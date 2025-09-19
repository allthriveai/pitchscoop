#!/usr/bin/env python3
"""
Recording Version ID Value Object

Represents a unique identifier for a recording version in the progression tracking system.
"""
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class RecordingVersionId:
    """Value object representing a recording version identifier."""
    
    value: str
    
    def __post_init__(self):
        """Validate recording version ID format."""
        if not self.value:
            raise ValueError("Recording version ID cannot be empty")
        
        if len(self.value) < 8:
            raise ValueError("Recording version ID must be at least 8 characters")
    
    @classmethod
    def generate(cls) -> 'RecordingVersionId':
        """Generate a new recording version ID."""
        return cls(str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, value: str) -> 'RecordingVersionId':
        """Create from string value."""
        return cls(value)
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"RecordingVersionId({self.value})"
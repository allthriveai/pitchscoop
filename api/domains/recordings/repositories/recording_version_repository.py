#!/usr/bin/env python3
"""
Recording Version Repository

Repository interface for persisting and retrieving recording versions
for progression analysis.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.recording_version import RecordingVersion
from ..value_objects.team_id import TeamId
from ..value_objects.recording_version_id import RecordingVersionId


class RecordingVersionRepository(ABC):
    """Abstract repository for recording version persistence."""
    
    @abstractmethod
    async def save(self, recording_version: RecordingVersion) -> None:
        """Save a recording version."""
        pass
    
    @abstractmethod
    async def get_by_id(self, version_id: RecordingVersionId) -> Optional[RecordingVersion]:
        """Get a recording version by its ID."""
        pass
    
    @abstractmethod
    async def get_versions_by_team(self, team_id: TeamId) -> List[RecordingVersion]:
        """Get all recording versions for a specific team."""
        pass
    
    @abstractmethod
    async def get_versions_by_event(self, event_id: str) -> List[RecordingVersion]:
        """Get all recording versions for a specific event."""
        pass
    
    @abstractmethod
    async def delete(self, version_id: RecordingVersionId) -> bool:
        """Delete a recording version."""
        pass
    
    @abstractmethod
    async def get_latest_version_for_team(self, team_id: TeamId) -> Optional[RecordingVersion]:
        """Get the latest recording version for a team."""
        pass
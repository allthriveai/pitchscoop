#!/usr/bin/env python3
"""
Redis Recording Version Repository

Redis implementation of the recording version repository for progression analysis.
Uses Redis for fast storage and retrieval of recording versions with LlamaIndex integration.
"""
import json
from datetime import datetime, timedelta
from typing import List, Optional
import redis.asyncio as redis

# LlamaIndex imports for vector storage
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.redis import RedisVectorStore

from ..entities.recording_version import RecordingVersion
from ..value_objects.team_id import TeamId
from ..value_objects.recording_version_id import RecordingVersionId
from ..value_objects.recording_scores import RecordingScores
from ..value_objects.audio_intelligence import AudioIntelligence
from ..value_objects.session_id import SessionId
from ..value_objects.transcript import TranscriptCollection, TranscriptSegment
from ..repositories.recording_version_repository import RecordingVersionRepository


class RedisRecordingVersionRepository(RecordingVersionRepository):
    """Redis implementation of recording version repository with LlamaIndex integration."""
    
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.redis_url = redis_url
        self.redis_client = None
        self.vector_store = None
        self.vector_index = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection and LlamaIndex vector store."""
        if self._initialized:
            return
        
        # Initialize Redis client
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        
        # Initialize LlamaIndex Redis vector store
        self.vector_store = RedisVectorStore(
            index_name="recording_versions",
            index_prefix="recording_version",
            redis_url=self.redis_url,
            overwrite=False
        )
        
        # Create storage context and index
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        try:
            # Try to load existing index
            self.vector_index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=storage_context
            )
        except Exception:
            # Create new index if none exists
            self.vector_index = VectorStoreIndex(
                [],
                storage_context=storage_context
            )
        
        self._initialized = True
    
    async def save(self, recording_version: RecordingVersion) -> None:
        """Save a recording version to Redis and vector store."""
        await self._ensure_initialized()
        
        # Save to Redis
        key = f"recording_version:{recording_version.version_id}"
        data = recording_version.to_dict()
        
        # Store with 30 days TTL
        await self.redis_client.setex(key, 86400 * 30, json.dumps(data))
        
        # Add to team index
        team_key = f"team_versions:{recording_version.team_id}"
        await self.redis_client.sadd(team_key, str(recording_version.version_id))
        await self.redis_client.expire(team_key, 86400 * 30)
        
        # Add to event index if event_id exists
        if recording_version.event_id:
            event_key = f"event_versions:{recording_version.event_id}"
            await self.redis_client.sadd(event_key, str(recording_version.version_id))
            await self.redis_client.expire(event_key, 86400 * 30)
        
        # Add to LlamaIndex for semantic search
        await self._add_to_vector_store(recording_version)
    
    async def get_by_id(self, version_id: RecordingVersionId) -> Optional[RecordingVersion]:
        """Get recording version by ID."""
        await self._ensure_initialized()
        
        key = f"recording_version:{version_id}"
        data = await self.redis_client.get(key)
        
        if not data:
            return None
        
        return self._deserialize_recording_version(json.loads(data))
    
    async def get_versions_by_team(self, team_id: TeamId) -> List[RecordingVersion]:
        """Get all recording versions for a team."""
        await self._ensure_initialized()
        
        team_key = f"team_versions:{team_id}"
        version_ids = await self.redis_client.smembers(team_key)
        
        versions = []
        for version_id_str in version_ids:
            version = await self.get_by_id(RecordingVersionId.from_string(version_id_str))
            if version:
                versions.append(version)
        
        # Sort by version number
        versions.sort(key=lambda v: v.version_number)
        return versions
    
    async def get_versions_by_event(self, event_id: str) -> List[RecordingVersion]:
        """Get all recording versions for an event."""
        await self._ensure_initialized()
        
        event_key = f"event_versions:{event_id}"
        version_ids = await self.redis_client.smembers(event_key)
        
        versions = []
        for version_id_str in version_ids:
            version = await self.get_by_id(RecordingVersionId.from_string(version_id_str))
            if version:
                versions.append(version)
        
        # Sort by creation date and version number
        versions.sort(key=lambda v: (v.created_at, v.version_number))
        return versions
    
    async def delete(self, version_id: RecordingVersionId) -> bool:
        """Delete a recording version."""
        await self._ensure_initialized()
        
        # Get version first to clean up indexes
        version = await self.get_by_id(version_id)
        if not version:
            return False
        
        # Remove from Redis
        key = f"recording_version:{version_id}"
        deleted = await self.redis_client.delete(key) > 0
        
        if deleted:
            # Clean up team index
            team_key = f"team_versions:{version.team_id}"
            await self.redis_client.srem(team_key, str(version_id))
            
            # Clean up event index if applicable
            if version.event_id:
                event_key = f"event_versions:{version.event_id}"
                await self.redis_client.srem(event_key, str(version_id))
            
            # Remove from vector store
            try:
                self.vector_index.delete_ref_doc(str(version_id))
            except Exception:
                # Vector deletion failed, but Redis deletion succeeded
                pass
        
        return deleted
    
    async def get_latest_version_for_team(self, team_id: TeamId) -> Optional[RecordingVersion]:
        """Get the latest recording version for a team."""
        versions = await self.get_versions_by_team(team_id)
        if not versions:
            return None
        
        # Return the version with the highest version number
        return max(versions, key=lambda v: v.version_number)
    
    async def semantic_search(self, query: str, team_id: Optional[TeamId] = None, limit: int = 10) -> List[RecordingVersion]:
        """Perform semantic search across recording versions."""
        await self._ensure_initialized()
        
        # Use LlamaIndex query engine for semantic search
        query_engine = self.vector_index.as_query_engine(similarity_top_k=limit)
        
        # Add team filter if specified
        search_query = query
        if team_id:
            search_query = f"team_id:{team_id} {query}"
        
        response = query_engine.query(search_query)
        
        # Extract recording versions from response
        versions = []
        for node in response.source_nodes:
            version_id = RecordingVersionId.from_string(node.metadata.get("version_id"))
            version = await self.get_by_id(version_id)
            if version:
                versions.append(version)
        
        return versions
    
    async def _ensure_initialized(self):
        """Ensure repository is initialized."""
        if not self._initialized:
            await self.initialize()
    
    async def _add_to_vector_store(self, recording_version: RecordingVersion):
        """Add recording version to LlamaIndex vector store for semantic search."""
        # Create document text combining title, transcript, and metadata
        doc_text = f"""
RECORDING VERSION {recording_version.version_number} - {recording_version.team_name}: {recording_version.recording_title}

Transcript: {recording_version.final_transcript_text}
""".strip()
        
        # Prepare metadata
        metadata = {
            "version_id": str(recording_version.version_id),
            "team_id": str(recording_version.team_id),
            "team_name": recording_version.team_name,
            "recording_title": recording_version.recording_title,
            "version_number": recording_version.version_number,
            "created_at": recording_version.created_at.isoformat(),
            "session_id": str(recording_version.session_id),
            "event_id": recording_version.event_id or "",
            "word_count": recording_version.word_count,
            "duration_seconds": recording_version.duration_seconds,
            "document_type": "recording_version"
        }
        
        # Add scores to metadata
        if recording_version.has_scores:
            scores = recording_version.scores
            metadata.update({
                "total_score": scores.total_score,
                "idea_score": scores.idea_score,
                "technical_score": scores.technical_score,
                "presentation_score": scores.presentation_score,
                "tool_use_score": scores.tool_use_score,
                "ranking_tier": scores.ranking_tier
            })
        
        # Add audio intelligence to metadata
        if recording_version.has_audio_intelligence:
            ai = recording_version.audio_intelligence
            metadata.update({
                "confidence_score": ai.confidence_metrics.confidence_score,
                "filler_percentage": ai.filler_analysis.filler_percentage,
                "words_per_minute": ai.speech_metrics.words_per_minute,
                "energy_level": ai.confidence_metrics.energy_level.value
            })
        
        # Create document and add to index
        document = Document(
            text=doc_text,
            metadata=metadata,
            doc_id=str(recording_version.version_id)
        )
        
        self.vector_index.insert(document)
    
    def _deserialize_recording_version(self, data: dict) -> RecordingVersion:
        """Convert dictionary data back to RecordingVersion entity."""
        # Deserialize transcripts
        transcripts_data = data["transcripts"]
        segments = []
        for seg_data in transcripts_data["segments"]:
            segment = TranscriptSegment(
                id=seg_data["id"],
                text=seg_data["text"],
                start_time=seg_data["start_time"],
                end_time=seg_data["end_time"],
                language=seg_data["language"],
                channel=seg_data.get("channel"),
                confidence=seg_data.get("confidence"),
                is_final=seg_data.get("is_final", False)
            )
            segments.append(segment)
        
        transcripts = TranscriptCollection(
            segments=tuple(segments),
            created_at=datetime.fromisoformat(transcripts_data["created_at"])
        )
        
        # Deserialize scores if present
        scores = None
        if "scores" in data and data["scores"]:
            scores = RecordingScores.from_dict(data["scores"])
        
        # Deserialize audio intelligence if present
        audio_intelligence = None
        if "audio_intelligence" in data and data["audio_intelligence"]:
            # This would need more complex deserialization logic
            # For now, we'll skip the full deserialization of AudioIntelligence
            pass
        
        return RecordingVersion(
            version_id=RecordingVersionId.from_string(data["version_id"]),
            team_id=TeamId.from_string(data["team_id"]),
            team_name=data["team_name"],
            recording_title=data["recording_title"],
            session_id=SessionId.from_string(data["session_id"]),
            transcripts=transcripts,
            version_number=data["version_number"],
            created_at=datetime.fromisoformat(data["created_at"]),
            event_id=data.get("event_id"),
            scores=scores,
            audio_intelligence=audio_intelligence,
            metadata=data.get("metadata", {})
        )
    
    async def cleanup(self):
        """Clean up resources."""
        if self.redis_client:
            await self.redis_client.aclose()
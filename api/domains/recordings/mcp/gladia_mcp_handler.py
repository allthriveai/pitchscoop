"""
Gladia MCP Handler - Exposes Speech-to-Text tools for AI assistants.

This handler provides MCP tools for the complete audio recording workflow:
- Start/stop recording with Gladia STT
- Store audio files in MinIO
- Cache session data in Redis
- Generate playback URLs for website integration
"""
import json
import asyncio
import uuid
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone

import redis.asyncio as redis
from minio.error import S3Error
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

from ..infrastructure.minio_audio_storage import minio_audio_storage
from ..value_objects.session_id import SessionId
from ..value_objects.audio_configuration import AudioConfiguration
from ..value_objects.transcript import TranscriptSegment, TranscriptCollection


class GladiaMCPHandler:
    """MCP handler for Gladia Speech-to-Text operations."""
    
    def __init__(self):
        """Initialize the MCP handler."""
        self.redis_client: Optional[redis.Redis] = None
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Dict[str, Any] = {}  # Store WebSocket connections
        
    def _validate_required_params(self, params: Dict[str, Any], required: List[str]) -> Optional[str]:
        """Validate that required parameters are present and non-empty."""
        for param in required:
            if param not in params:
                return f"Missing required parameter: {param}"
            if not params[param] or (isinstance(params[param], str) and not params[param].strip()):
                return f"Parameter '{param}' cannot be empty"
        return None
        
    async def get_redis(self) -> redis.Redis:
        """Get Redis client connection."""
        if self.redis_client is None:
            # Use environment variable, fallback to Docker internal network
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client
    
    async def _find_session_key(self, session_id: str) -> Optional[str]:
        """Find the Redis key for a session by scanning all events."""
        redis_client = await self.get_redis()
        
        # Try common patterns first for efficiency
        # Check if we have the session in active_sessions (contains event_id)
        if session_id in self.active_sessions:
            event_id = self.active_sessions[session_id]["event_id"]
            test_key = f"event:{event_id}:session:{session_id}"
            if await redis_client.exists(test_key):
                return test_key
        
        # Fall back to scanning all events
        async for key in redis_client.scan_iter(match="event:*:session:*"):
            if f":session:{session_id}" in key:
                if await redis_client.exists(key):
                    return key
        
        return None
    
    async def start_pitch_recording(
        self, 
        team_name: str, 
        pitch_title: str,
        event_id: Optional[str] = None,
        audio_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start a new pitch recording session.
        
        Args:
            team_name: Name of the team/participant
            pitch_title: Title of the pitch presentation  
            event_id: Optional event identifier to associate recording with (defaults to 'default')
            audio_config: Optional audio configuration override
            
        Returns:
            Session information with WebSocket details for recording
        """
        # Use default event if none provided
        if not event_id:
            event_id = "default"
        
        # Validate required parameters
        validation_error = self._validate_required_params(
            {"team_name": team_name, "pitch_title": pitch_title},
            ["team_name", "pitch_title"]
        )
        if validation_error:
            return {
                "error": validation_error,
                "status": "validation_error"
            }
        
        try:
            redis_client = await self.get_redis()
            
            # Handle default event or validate existing event
            if event_id == "default":
                # Create or use default event data
                event_data = {
                    "event_name": "Default Event",
                    "event_type": "practice",
                    "status": "active",
                    "duration_minutes": 30  # Default 30 minutes
                }
            else:
                # First, validate the event exists and is active
                event_json = await redis_client.get(f"event:{event_id}")
                if not event_json:
                    return {
                        "error": f"Event not found: {event_id}",
                        "event_id": event_id
                    }
                
                event_data = json.loads(event_json)
                if event_data["status"] not in ["active"]:
                    return {
                        "error": f"Event is not active (status: {event_data['status']})",
                        "event_id": event_id,
                        "event_status": event_data["status"]
                    }
            
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Create audio configuration
            if audio_config:
                config = AudioConfiguration.from_dict(audio_config)
            else:
                config = AudioConfiguration.create_default()
            
            # Initialize session data with event context
            session_data = {
                "session_id": session_id,
                "event_id": event_id,
                "event_name": event_data["event_name"],
                "event_type": event_data["event_type"],
                "team_name": team_name,
                "pitch_title": pitch_title,
                "status": "initializing",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "audio_config": config.to_gladia_config(),
                "transcript_segments": [],
                "has_audio": False,
                "gladia_session_id": None,
                "websocket_url": None,
                "duration_limit_minutes": event_data["duration_minutes"]
            }
            
            # Store in Redis with event-scoped key
            await redis_client.setex(
                f"event:{event_id}:session:{session_id}",
                3600,  # 1 hour TTL
                json.dumps(session_data)
            )
            
            # Initialize Gladia session - REQUIRE API key
            gladia_response = await self._create_gladia_session(config)
            if not gladia_response:
                api_key = os.getenv('GLADIA_API_KEY')
                if not api_key:
                    return {
                        "error": "Gladia API key is required but not found in environment variables. Please set GLADIA_API_KEY in your .env file.",
                        "session_id": session_id,
                        "status": "error"
                    }
                else:
                    return {
                        "error": "Failed to create Gladia session - API call failed",
                        "session_id": session_id, 
                        "status": "error"
                    }
            
            # Update session with Gladia details
            session_data.update({
                "status": "ready_to_record",
                "gladia_session_id": gladia_response["id"],
                "websocket_url": gladia_response["url"]
            })
            
            # Update Redis
            await redis_client.setex(
                f"event:{event_id}:session:{session_id}",
                3600,
                json.dumps(session_data)
            )
            
            # Store in active sessions for WebSocket management
            self.active_sessions[session_id] = {
                "event_id": event_id,
                "gladia_session_id": gladia_response["id"],
                "websocket_url": gladia_response["url"],
                "team_name": team_name,
                "pitch_title": pitch_title,
                "audio_buffer": []
            }
            
            # Add session to event's session list
            sessions_json = await redis_client.get(f"event:{event_id}:sessions")
            sessions = json.loads(sessions_json) if sessions_json else []
            sessions.append({
                "session_id": session_id,
                "team_name": team_name,
                "pitch_title": pitch_title,
                "created_at": session_data["created_at"],
                "status": "ready_to_record"
            })
            await redis_client.setex(
                f"event:{event_id}:sessions",
                86400 * 30,
                json.dumps(sessions)
            )
            
            return {
                "session_id": session_id,
                "event_id": event_id,
                "event_name": event_data["event_name"],
                "event_type": event_data["event_type"],
                "team_name": team_name,
                "pitch_title": pitch_title,
                "status": "ready_to_record",
                "websocket_url": gladia_response["url"],
                "gladia_session_id": gladia_response["id"],
                "audio_config": config.to_gladia_config(),
                "duration_limit_minutes": event_data["duration_minutes"],
                "instructions": {
                    "next_step": "Connect to WebSocket and start sending audio chunks",
                    "websocket_format": "Send raw audio bytes or base64 encoded chunks",
                    "stop_method": "Call pitches.stop_recording when demo is complete",
                    "duration_warning": f"Recording limited to {event_data['duration_minutes']} minutes for this {event_data['event_type']} event"
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to start recording: {str(e)}",
                "session_id": None,
                "status": "error"
            }
    
    async def stop_pitch_recording(
        self, 
        session_id: str,
        audio_data: Optional[bytes] = None,
        audio_data_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stop pitch recording and finalize the session.
        
        Args:
            session_id: Session identifier
            audio_data: Optional complete audio data as bytes
            audio_data_base64: Optional complete audio data as base64 string
            
        Returns:
            Final session summary with transcript and audio URLs
        """
        # Validate required parameters
        validation_error = self._validate_required_params(
            {"session_id": session_id},
            ["session_id"]
        )
        if validation_error:
            return {
                "error": validation_error,
                "status": "validation_error"
            }
        
        try:
            # Get session from Redis - need to find which event it belongs to
            redis_client = await self.get_redis()
            session_json = None
            event_id = None
            
            # Search for session across all events
            async for key in redis_client.scan_iter(match="event:*:session:*"):
                if f":session:{session_id}" in key:
                    session_json = await redis_client.get(key)
                    if session_json:
                        event_id = key.split(':')[1]  # Extract event_id from key
                        break
            
            if not session_json:
                return {"error": "Session not found", "session_id": session_id}
            
            session_data = json.loads(session_json)
            
            # Update status
            session_data["status"] = "processing"
            session_data["recording_ended_at"] = datetime.now(timezone.utc).isoformat()
            
            # Handle audio storage if provided - convert base64 if needed
            final_audio_data = None
            if audio_data_base64:
                try:
                    import base64
                    final_audio_data = base64.b64decode(audio_data_base64)
                    logger.info(f"Converted base64 audio data, size: {len(final_audio_data)} bytes")
                except Exception as e:
                    logger.error(f"Failed to decode base64 audio data: {e}")
                    session_data["audio_decode_error"] = str(e)
            elif audio_data:
                final_audio_data = audio_data
            
            audio_info = {}
            if final_audio_data:
                try:
                    # Upload to MinIO
                    object_key = await minio_audio_storage.upload_audio(
                        session_id=session_id,
                        audio_data=final_audio_data,
                        file_format="wav"
                    )
                    
                    # Generate playback URL
                    playback_url = await minio_audio_storage.get_playback_url(
                        session_id=session_id,
                        expires=timedelta(hours=24)  # 24-hour expiry for playback
                    )
                    
                    # Get audio info
                    audio_file_info = await minio_audio_storage.get_audio_info(session_id)
                    
                    audio_info = {
                        "has_audio": True,
                        "audio_size": len(final_audio_data),
                        "minio_object_key": object_key,
                        "playback_url": playback_url,
                        "audio_info": audio_file_info
                    }
                    
                    session_data.update(audio_info)
                    
                except Exception as e:
                    audio_info = {
                        "has_audio": False,
                        "audio_error": f"Failed to store audio: {str(e)}"
                    }
                    session_data.update(audio_info)
            
            # Stop Gladia session
            if session_id in self.active_sessions:
                # Send stop message to Gladia WebSocket
                await self._stop_gladia_session(session_id)
                del self.active_sessions[session_id]
            
            # Finalize transcript
            transcript_segments = session_data.get("transcript_segments", [])
            final_transcript = {
                "segments_count": len(transcript_segments),
                "total_text": " ".join([seg.get("text", "") for seg in transcript_segments]),
                "segments": transcript_segments
            }
            
            # Update session
            session_data.update({
                "status": "completed",
                "final_transcript": final_transcript,
                "completed_at": datetime.now(timezone.utc).isoformat()
            })
            
            # Update Redis with longer TTL for completed sessions
            await redis_client.setex(
                f"event:{event_id}:session:{session_id}",
                86400,  # 24 hours for completed sessions
                json.dumps(session_data)
            )
            
            return {
                "session_id": session_id,
                "team_name": session_data["team_name"],
                "pitch_title": session_data["pitch_title"],
                "status": "completed",
                "transcript": final_transcript,
                "audio": audio_info,
                "duration_seconds": self._calculate_session_duration(session_data),
                "completed_at": session_data["completed_at"]
            }
            
        except Exception as e:
            return {
                "error": f"Failed to stop recording: {str(e)}",
                "session_id": session_id,
                "status": "error"
            }
    
    async def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """
        Get complete session details including transcript and audio URLs.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Complete session information
        """
        try:
            # Find session using efficient lookup
            session_key = await self._find_session_key(session_id)
            if not session_key:
                return {"error": "Session not found", "session_id": session_id}
            
            redis_client = await self.get_redis()
            session_json = await redis_client.get(session_key)
            
            session_data = json.loads(session_json)
            
            # Add fresh playback URL if audio exists
            if session_data.get("has_audio", False):
                try:
                    fresh_playback_url = await minio_audio_storage.get_playback_url(
                        session_id=session_id,
                        expires=timedelta(hours=1)
                    )
                    session_data["current_playback_url"] = fresh_playback_url
                    
                    # Get current audio info
                    audio_info = await minio_audio_storage.get_audio_info(session_id)
                    session_data["current_audio_info"] = audio_info
                    
                except Exception as e:
                    session_data["playback_url_error"] = str(e)
            
            return session_data
            
        except Exception as e:
            return {
                "error": f"Failed to get session details: {str(e)}",
                "session_id": session_id
            }
    
    async def get_playback_url(
        self, 
        session_id: str, 
        expires_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Generate a fresh playback URL for the session's audio.
        
        Args:
            session_id: Session identifier
            expires_hours: URL expiry time in hours
            
        Returns:
            Playback URL information
        """
        try:
            # Find session using efficient lookup
            session_key = await self._find_session_key(session_id)
            if not session_key:
                return {"error": "Session not found", "session_id": session_id}
            
            redis_client = await self.get_redis()
            session_json = await redis_client.get(session_key)
            
            if not session_json:
                return {"error": "Session not found", "session_id": session_id}
            
            session_data = json.loads(session_json)
            
            # Check if audio exists
            if not session_data.get("has_audio", False):
                return {
                    "error": "No audio available for this session",
                    "session_id": session_id,
                    "has_audio": False
                }
            
            # Generate fresh playback URL
            playback_url = await minio_audio_storage.get_playback_url(
                session_id=session_id,
                expires=timedelta(hours=expires_hours)
            )
            
            if not playback_url:
                return {
                    "error": "Audio file not found in storage",
                    "session_id": session_id
                }
            
            return {
                "session_id": session_id,
                "playback_url": playback_url,
                "expires_in_seconds": expires_hours * 3600,
                "team_name": session_data.get("team_name"),
                "pitch_title": session_data.get("pitch_title")
            }
            
        except Exception as e:
            return {
                "error": f"Failed to generate playback URL: {str(e)}",
                "session_id": session_id
            }
    
    async def list_sessions(
        self, 
        event_id: Optional[str] = None,
        team_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List all sessions, optionally filtered by event, team or status.
        
        Args:
            event_id: Optional event ID filter - show only sessions for this event
            team_name: Optional team name filter
            status: Optional status filter
            
        Returns:
            List of session summaries
        """
        try:
            redis_client = await self.get_redis()
            
            # Get session keys - use correct pattern based on event filter
            session_keys = []
            if event_id:
                # Search for sessions within specific event
                async for key in redis_client.scan_iter(match=f"event:{event_id}:session:*"):
                    session_keys.append(key)
            else:
                # Search all events for sessions
                async for key in redis_client.scan_iter(match="event:*:session:*"):
                    session_keys.append(key)
            
            sessions = []
            for key in session_keys:
                try:
                    session_json = await redis_client.get(key)
                    if session_json:
                        session_data = json.loads(session_json)
                        
                        # Apply filters
                        if team_name and session_data.get("team_name") != team_name:
                            continue
                        if status and session_data.get("status") != status:
                            continue
                        
                        # Create summary
                        session_summary = {
                            "session_id": session_data["session_id"],
                            "team_name": session_data["team_name"],
                            "pitch_title": session_data["pitch_title"],
                            "status": session_data["status"],
                            "created_at": session_data["created_at"],
                            "has_audio": session_data.get("has_audio", False),
                            "transcript_segments": len(session_data.get("transcript_segments", []))
                        }
                        
                        # Add completion info if available
                        if "completed_at" in session_data:
                            session_summary["completed_at"] = session_data["completed_at"]
                            session_summary["duration_seconds"] = self._calculate_session_duration(session_data)
                        
                        sessions.append(session_summary)
                        
                except Exception as e:
                    # Skip invalid sessions
                    continue
            
            # Sort by creation time (newest first)
            sessions.sort(key=lambda x: x["created_at"], reverse=True)
            
            return {
                "sessions": sessions,
                "total_count": len(sessions),
                "filters_applied": {
                    "team_name": team_name,
                    "status": status
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to list sessions: {str(e)}",
                "sessions": []
            }
    
    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete a session and its associated audio file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Deletion status
        """
        try:
            redis_client = await self.get_redis()
            
            # Find session using efficient lookup
            session_key = await self._find_session_key(session_id)
            if not session_key:
                return {"error": "Session not found", "session_id": session_id}
            
            session_json = await redis_client.get(session_key)
            
            session_data = json.loads(session_json)
            
            # Delete audio file if it exists
            audio_deleted = False
            if session_data.get("has_audio", False):
                audio_deleted = await minio_audio_storage.delete_audio(session_id)
            
            # Delete from Redis using the found key
            redis_deleted = await redis_client.delete(session_key) if session_key else False
            
            # Clean up active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            return {
                "session_id": session_id,
                "team_name": session_data.get("team_name"),
                "deleted": True,
                "redis_deleted": bool(redis_deleted),
                "audio_deleted": audio_deleted
            }
            
        except Exception as e:
            return {
                "error": f"Failed to delete session: {str(e)}",
                "session_id": session_id,
                "deleted": False
            }
    
    async def _create_gladia_session(self, config: AudioConfiguration) -> Optional[Dict[str, Any]]:
        """Create a new Gladia STT session."""
        import aiohttp
        
        # Get Gladia API key from environment - REQUIRED
        api_key = os.getenv('GLADIA_API_KEY')
        if not api_key:
            logger.error("No Gladia API key found in environment variable GLADIA_API_KEY")
            logger.error("Please add GLADIA_API_KEY to your .env file")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.gladia.io/v2/live",
                    headers={
                        'Content-Type': 'application/json',
                        'X-Gladia-Key': api_key
                    },
                    json=config.to_gladia_config(),
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201]:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Gladia API error {response.status}: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Failed to create Gladia session: {e}")
            return None
    
    async def _stop_gladia_session(self, session_id: str):
        """Send stop message to Gladia WebSocket and clean up connection."""
        try:
            # Clean up WebSocket connection if exists
            if session_id in self.websocket_connections:
                websocket = self.websocket_connections[session_id]
                try:
                    if hasattr(websocket, 'close'):
                        await websocket.close()
                    logger.info(f"Closed WebSocket connection for session {session_id}")
                except Exception as e:
                    logger.warning(f"Error closing WebSocket for session {session_id}: {e}")
                finally:
                    del self.websocket_connections[session_id]
            
            # Clean up active session state
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up session state for {session_id}")
        
        except Exception as e:
            logger.error(f"Error during session cleanup for {session_id}: {e}")
    
    def _calculate_session_duration(self, session_data: Dict[str, Any]) -> Optional[float]:
        """Calculate session duration in seconds."""
        try:
            created_at = datetime.fromisoformat(session_data["created_at"])
            if "completed_at" in session_data:
                completed_at = datetime.fromisoformat(session_data["completed_at"])
                return (completed_at - created_at).total_seconds()
            elif "recording_ended_at" in session_data:
                ended_at = datetime.fromisoformat(session_data["recording_ended_at"])
                return (ended_at - created_at).total_seconds()
        except Exception:
            pass
        return None


# Global instance
gladia_mcp_handler = GladiaMCPHandler()
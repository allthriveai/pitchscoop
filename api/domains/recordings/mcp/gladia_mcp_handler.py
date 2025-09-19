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
            
            # Create audio configuration with Audio Intelligence enabled for pitch analysis
            if audio_config:
                config = AudioConfiguration.from_dict(audio_config)
            else:
                # Use full Audio Intelligence configuration for maximum accuracy
                # This forces batch processing which is more accurate than WebSocket
                config = AudioConfiguration.create_full_intelligence()
            
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
                "audio_config": {
                    "encoding": config.encoding.value,
                    "sample_rate": config.sample_rate.value,
                    "bit_depth": config.bit_depth.value,
                    "channels": config.channels,
                    "sentiment_analysis": config.sentiment_analysis,
                    "emotion_analysis": config.emotion_analysis,
                    "speaker_identification": config.speaker_identification,
                    "summarization": config.summarization,
                    "named_entity_recognition": config.named_entity_recognition,
                    "chapterization": config.chapterization,
                    "translation": config.translation,
                    "target_language": config.target_language
                },
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
            logger.info(f"Starting stop_pitch_recording for session: {session_id}")
            
            # Get session from Redis - need to find which event it belongs to
            logger.info("Step 1: Connecting to Redis and finding session")
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
                logger.error(f"Session not found: {session_id}")
                return {"error": "Session not found", "session_id": session_id}
            
            logger.info("Step 2: Session found, parsing data")
            session_data = json.loads(session_json)
            
            # Update status
            session_data["status"] = "processing"
            session_data["recording_ended_at"] = datetime.now(timezone.utc).isoformat()
            
            # Handle audio storage if provided - convert base64 if needed
            logger.info("Step 3: Processing audio data")
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
            
            # Process audio with Hybrid Gladia + Enhanced AI Analysis if we have audio data
            transcript_segments = session_data.get("transcript_segments", [])
            audio_intelligence_data = {}
            enhanced_intelligence_data = {}
            
            if final_audio_data:
                # Use Gladia batch processing for Audio Intelligence features
                audio_config = AudioConfiguration.from_dict(session_data.get("audio_config", {}))
                
                # Always try WebSocket first for better reliability with microphone audio
                logger.info("Processing microphone audio with Gladia WebSocket (primary method)")
                if session_data.get("gladia_session_id") and session_data.get("websocket_url"):
                    logger.info(f"WebSocket processing with session: {session_data.get('gladia_session_id')[:8]}...")
                    gladia_transcript = await self._process_audio_with_gladia(
                        session_data["gladia_session_id"],
                        session_data["websocket_url"],
                        final_audio_data
                    )
                    
                    if gladia_transcript:
                        logger.info(f"WebSocket returned {len(gladia_transcript)} transcript segments")
                        transcript_segments.extend(gladia_transcript)
                        session_data["transcript_segments"] = transcript_segments
                    else:
                        logger.warning("WebSocket processing returned no transcript segments")
                else:
                    logger.error(f"WebSocket processing failed: missing gladia_session_id or websocket_url")
                
                # Only try batch processing if WebSocket failed AND we have AI features enabled
                if (not transcript_segments and 
                    (audio_config.sentiment_analysis or audio_config.emotion_analysis or 
                     audio_config.summarization or audio_config.named_entity_recognition or 
                     audio_config.chapterization)):
                    
                    logger.info("WebSocket failed, trying Gladia batch mode for Audio Intelligence")
                    batch_result = await self._process_audio_with_intelligence(
                        final_audio_data, audio_config
                    )
                    
                    if batch_result:
                        transcript_segments = batch_result.get('transcript_segments', [])
                        # Keep basic Gladia intelligence for comparison
                        audio_intelligence_data = batch_result.get('intelligence_data', {})
                        session_data["transcript_segments"] = transcript_segments
                        session_data["gladia_audio_intelligence"] = audio_intelligence_data
                        logger.info(f"Gladia batch processing complete: {len(transcript_segments)} segments")
                    else:
                        logger.warning("Both WebSocket and batch processing failed")
                
                # Step 2: Enhanced AI Analysis using Azure OpenAI (HYBRID APPROACH)
                if transcript_segments:
                    logger.info("Starting Enhanced Audio Intelligence analysis with Azure OpenAI")
                    try:
                        from ..services.enhanced_audio_intelligence import enhanced_audio_intelligence
                        
                        # Get event_id for multi-tenant isolation
                        event_id = session_data.get("event_id")
                        
                        enhanced_result = await enhanced_audio_intelligence.analyze_pitch_transcript(
                            transcript_segments, event_id=event_id, session_id=session_id
                        )
                        
                        if enhanced_result.get("success"):
                            enhanced_intelligence_data = enhanced_result
                            session_data["enhanced_audio_intelligence"] = enhanced_intelligence_data
                            logger.info(f"Enhanced AI analysis complete: confidence improved from ~0.3 to {enhanced_result.get('sentiment_analysis', {}).get('sentiment_confidence', 'N/A')}")
                            
                            # Log quality improvements
                            logger.info(f"Analysis quality improvements: {enhanced_result.get('confidence_improvement', {})}")
                        else:
                            logger.error(f"Enhanced AI analysis failed: {enhanced_result.get('error')}")
                            enhanced_intelligence_data = {"error": enhanced_result.get("error"), "success": False}
                            
                    except Exception as e:
                        logger.error(f"Enhanced AI analysis exception: {str(e)}")
                        enhanced_intelligence_data = {"error": f"Enhanced analysis exception: {str(e)}", "success": False}
                else:
                    logger.warning("No transcript segments available for enhanced analysis")
            
            # Stop Gladia session
            logger.info("Step 4: Cleaning up Gladia session")
            if session_id in self.active_sessions:
                # Send stop message to Gladia WebSocket
                await self._stop_gladia_session(session_id)
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up active session: {session_id}")
            else:
                logger.info(f"Session {session_id} not in active_sessions, skipping cleanup")
            
            # Finalize transcript with Enhanced Audio Intelligence data
            final_transcript = {
                "segments_count": len(transcript_segments),
                "total_text": " ".join([seg.get("text", "") for seg in transcript_segments if seg.get("text")]),
                "segments": transcript_segments,
                # Keep both analyses for comparison and debugging
                "gladia_audio_intelligence": audio_intelligence_data,
                "enhanced_audio_intelligence": enhanced_intelligence_data,
                # Use enhanced analysis as primary (backward compatibility)
                "audio_intelligence": enhanced_intelligence_data if enhanced_intelligence_data.get("success") else audio_intelligence_data,
                "analysis_method": "hybrid_gladia_azure_openai" if enhanced_intelligence_data.get("success") else "gladia_only",
                "quality_improvements": enhanced_intelligence_data.get("confidence_improvement") if enhanced_intelligence_data.get("success") else None
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
            
            # Step 5: Automatic AI Scoring (NEW - COMPLETE AUTOMATION)
            if final_transcript.get("total_text") and len(final_transcript["total_text"].strip()) > 50:
                logger.info("Step 5: Starting automatic AI scoring after recording completion")
                await self._trigger_automatic_scoring(
                    session_id=session_id,
                    event_id=event_id,
                    team_name=session_data["team_name"],
                    logger=logger
                )
            else:
                logger.warning("Skipping automatic scoring: transcript too short or missing")
            
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
            import traceback
            logger.error(f"Failed to stop recording {session_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "error": f"Failed to stop recording: {str(e)}",
                "session_id": session_id,
                "status": "error",
                "traceback": traceback.format_exc()
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
    
    async def _process_audio_with_intelligence(self, audio_data: bytes, config: AudioConfiguration) -> Optional[Dict[str, Any]]:
        """Process audio with Gladia Audio Intelligence using batch API with proper file upload."""
        import aiohttp
        import tempfile
        import os
        
        api_key = os.getenv('GLADIA_API_KEY')
        if not api_key:
            logger.error("No Gladia API key for Audio Intelligence processing")
            return None
        
        try:
            # Debug: Check audio_data type and size
            audio_size = len(audio_data) if hasattr(audio_data, '__len__') else 0
            logger.info(f"Audio data type: {type(audio_data)}, size: {audio_size} bytes")
            
            # Increase size limit now that we're using proper multipart upload instead of base64
            # 3 minute pitch at 16kHz 16-bit mono = ~5.76MB, which should be fine
            max_size_mb = 10  # 10MB limit for safety
            if audio_size > max_size_mb * 1024 * 1024:
                logger.warning(f"Audio too large for batch processing ({audio_size / (1024*1024):.1f}MB), will use WebSocket fallback")
                return None
            
            # Ensure audio_data is bytes
            if isinstance(audio_data, str):
                logger.warning("Audio data is string, converting to bytes")
                import base64
                try:
                    audio_data = base64.b64decode(audio_data)
                    audio_size = len(audio_data)
                    logger.info(f"Converted to bytes, new size: {audio_size} bytes")
                except Exception as e:
                    logger.error(f"Failed to decode base64 audio data: {e}")
                    return None
            
            # Create temporary audio file for upload
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file_path = tmp_file.name
            
            logger.info(f"Processing audio with Gladia Audio Intelligence: {audio_size / 1024:.1f}KB")
            
            # Step 1: Upload file using proper multipart/form-data
            audio_url = await self._upload_audio_to_gladia(tmp_file_path, api_key)
            if not audio_url:
                logger.error("Failed to upload audio file to Gladia")
                return None
            
            logger.info(f"Audio uploaded successfully, got URL: {audio_url[:60]}...")
            
            # Step 2: Submit transcription job with Audio Intelligence features
            return await self._submit_gladia_transcription_job(audio_url, config, api_key)
            
        except Exception as e:
            logger.error(f"Error processing audio with Gladia Audio Intelligence: {e}")
            return None
        finally:
            # Clean up temporary file
            try:
                if 'tmp_file_path' in locals():
                    os.unlink(tmp_file_path)
            except Exception:
                pass
    
    async def _upload_audio_to_gladia(self, file_path: str, api_key: str) -> Optional[str]:
        """Upload audio file to Gladia using proper multipart/form-data."""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                with open(file_path, 'rb') as audio_file:
                    # Create multipart form data
                    data = aiohttp.FormData()
                    data.add_field('audio', audio_file, filename='audio.wav', content_type='audio/wav')
                    
                    async with session.post(
                        "https://api.gladia.io/v2/upload",
                        headers={
                            'X-Gladia-Key': api_key,
                        },
                        data=data,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        
                        if response.status in [200, 201]:
                            result = await response.json()
                            audio_url = result.get('audio_url')
                            
                            if audio_url:
                                logger.info(f"File uploaded successfully: {result.get('audio_metadata', {}).get('filename', 'unknown')}")
                                return audio_url
                            else:
                                logger.error("Upload successful but no audio_url in response")
                                return None
                        else:
                            error_text = await response.text()
                            logger.error(f"Gladia upload API error {response.status}: {error_text}")
                            return None
                            
        except Exception as e:
            logger.error(f"Error uploading audio to Gladia: {e}")
            return None
    
    async def _submit_gladia_transcription_job(self, audio_url: str, config: AudioConfiguration, api_key: str) -> Optional[Dict[str, Any]]:
        """Submit transcription job to Gladia with Audio Intelligence features."""
        import aiohttp
        
        try:
            # Get Audio Intelligence configuration
            ai_config = config.to_gladia_config(include_ai_features=True)
            
            # Prepare payload for pre-recorded API
            payload = {
                'audio_url': audio_url,
                'language': 'en',  # Can be made configurable
            }
            
            # Add Audio Intelligence features
            if ai_config.get('sentiment_analysis'):
                payload['sentiment_analysis'] = True
            if ai_config.get('summarization'):
                payload['summarization'] = True
            if ai_config.get('named_entity_recognition'):
                payload['named_entity_recognition'] = True
            if ai_config.get('chapterization'):
                payload['chapterization'] = True
            
            logger.info(f"Submitting transcription job with features: {[k for k, v in payload.items() if v is True and k != 'audio_url']}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.gladia.io/v2/pre-recorded/",
                    headers={
                        'Content-Type': 'application/json',
                        'X-Gladia-Key': api_key,
                    },
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    if response.status in [200, 201]:
                        result = await response.json()
                        result_url = result.get('result_url')
                        
                        if result_url:
                            logger.info(f"Transcription job submitted, polling for results...")
                            return await self._poll_gladia_results(result_url, api_key)
                        else:
                            logger.error("Transcription job submitted but no result_url received")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Gladia pre-recorded API error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error submitting Gladia transcription job: {e}")
            return None
    
    async def _poll_gladia_results(self, result_url: str, api_key: str, max_attempts: int = 30) -> Optional[Dict[str, Any]]:
        """Poll Gladia for Audio Intelligence results."""
        import aiohttp
        
        for attempt in range(max_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        result_url,
                        headers={'X-Gladia-Key': api_key},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        
                        if response.status == 200:
                            result = await response.json()
                            status = result.get('status')
                            
                            if status == 'done':
                                # Extract transcript and intelligence data
                                return self._extract_intelligence_data(result)
                                
                            elif status == 'error':
                                logger.error(f"Gladia processing error: {result.get('error', 'Unknown error')}")
                                return None
                                
                            else:
                                # Still processing, wait and retry
                                logger.info(f"Gladia processing status: {status} (attempt {attempt + 1}/{max_attempts})")
                                await asyncio.sleep(2)  # Wait 2 seconds between polls
                        else:
                            logger.warning(f"Gladia polling error {response.status}, retrying...")
                            await asyncio.sleep(2)
                            
            except Exception as e:
                logger.warning(f"Error polling Gladia results: {e}")
                await asyncio.sleep(2)
        
        logger.error("Gladia Audio Intelligence processing timed out")
        return None
    
    def _extract_intelligence_data(self, gladia_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract transcript and Audio Intelligence data from Gladia result."""
        transcript_segments = []
        intelligence_data = {}
        
        # Extract transcript with Audio Intelligence annotations
        prediction = gladia_result.get('prediction', {})
        
        # Get transcript segments
        for utterance in prediction.get('utterances', []):
            segment = {
                "text": utterance.get('text', ''),
                "confidence": utterance.get('confidence', 0.0),
                "start_time": utterance.get('start', 0.0),
                "end_time": utterance.get('end', 0.0),
                "speaker": utterance.get('speaker', None),
                "sentiment": utterance.get('sentiment', None),
                "emotion": utterance.get('emotion', None),
                "is_final": True  # Batch results are always final
            }
            if segment['text'].strip():  # Only add non-empty segments
                transcript_segments.append(segment)
        
        # Extract Audio Intelligence insights
        if 'sentiment_analysis' in prediction:
            intelligence_data['sentiment_analysis'] = prediction['sentiment_analysis']
            
        if 'emotion_analysis' in prediction:
            intelligence_data['emotion_analysis'] = prediction['emotion_analysis']
            
        if 'summarization' in prediction:
            intelligence_data['summarization'] = prediction['summarization']
            
        if 'named_entity_recognition' in prediction:
            intelligence_data['named_entity_recognition'] = prediction['named_entity_recognition']
            
        if 'chapterization' in prediction:
            intelligence_data['chapterization'] = prediction['chapterization']
        
        logger.info(f"Extracted {len(transcript_segments)} segments and {len(intelligence_data)} AI insights")
        
        return {
            'transcript_segments': transcript_segments,
            'intelligence_data': intelligence_data
        }
    
    async def _process_audio_with_gladia(self, gladia_session_id: str, websocket_url: str, audio_data: bytes) -> List[Dict[str, Any]]:
        """Process audio with Gladia WebSocket and return transcript segments."""
        import websockets
        import json
        
        transcript_segments = []
        
        try:
            logger.info(f"Connecting to Gladia WebSocket for transcription: {websocket_url[:50]}...")
            logger.info(f"Audio data size: {len(audio_data)} bytes ({len(audio_data) / 1024:.1f}KB)")
            
            # Use ping/pong to maintain connection stability
            async with websockets.connect(
                websocket_url, 
                timeout=15,
                ping_interval=30,  # Send ping every 30 seconds
                ping_timeout=10    # Wait 10 seconds for pong
            ) as websocket:
                logger.info("Connected to Gladia WebSocket with connection stability features")
                
                # Send audio data in smaller chunks for better real-time processing
                chunk_size = 4096  # 4KB chunks (smaller for better responsiveness)
                total_chunks = len(audio_data) // chunk_size + (1 if len(audio_data) % chunk_size else 0)
                
                logger.info(f"Sending {len(audio_data)} bytes in {total_chunks} chunks of {chunk_size} bytes each")
                
                # Send audio chunks with realistic timing
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    await websocket.send(chunk)
                    logger.debug(f"Sent chunk {i // chunk_size + 1}/{total_chunks} ({len(chunk)} bytes)")
                    
                    # Realistic delay: 4KB at 16kHz 16-bit mono = ~125ms of audio
                    # Send slightly faster than real-time for processing efficiency
                    await asyncio.sleep(0.05)  # 50ms delay
                
                logger.info("Finished sending audio chunks, waiting before stop message...")
                # Wait a bit before sending stop to allow processing
                await asyncio.sleep(0.5)
                
                # Send stop recording message
                stop_message = json.dumps({"type": "stop_recording"})
                await websocket.send(stop_message)
                logger.info("Sent stop recording message, waiting for final transcripts...")
                
                # Listen for transcript messages with improved handling for microphone audio
                messages_received = 0
                timeout_count = 0
                max_messages = 100  # Allow more messages for longer audio
                max_timeouts = 10   # Allow more timeouts for microphone processing
                transcript_found = False
                
                logger.info("Listening for transcription messages...")
                
                while messages_received < max_messages and timeout_count < max_timeouts:
                    try:
                        # Wait for messages with longer timeout for microphone processing
                        message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        messages_received += 1
                        timeout_count = 0  # Reset timeout count on successful message
                        
                        try:
                            parsed_message = json.loads(message)
                            message_type = parsed_message.get('type')
                            
                            logger.debug(f"Received Gladia message: {message_type}")
                            
                            if message_type == 'transcript':
                                data = parsed_message.get('data', {})
                                utterance = data.get('utterance', {})
                                text = utterance.get('text', '').strip()
                                is_final = data.get('is_final', False)
                                confidence = utterance.get('confidence', 0.0)
                                
                                # Log all transcript messages for debugging (even empty ones)
                                logger.info(f"Transcript message: text='{text}', final={is_final}, confidence={confidence:.3f}")
                                
                                if text:  # Only process non-empty transcripts
                                    transcript_found = True
                                    segment = {
                                        "text": text,
                                        "confidence": confidence,
                                        "is_final": is_final,
                                        "start_time": utterance.get('start', 0.0),
                                        "end_time": utterance.get('end', 0.0),
                                        "channel": utterance.get('channel', 0),
                                        # Audio Intelligence data
                                        "sentiment": utterance.get('sentiment', None),
                                        "emotion": utterance.get('emotion', None),
                                        "speaker": utterance.get('speaker', None)
                                    }
                                    transcript_segments.append(segment)
                                    
                                    # Enhanced logging for Audio Intelligence
                                    log_parts = [f"'{text}' (confidence: {confidence:.3f})"]
                                    if segment['sentiment']:
                                        log_parts.append(f"sentiment: {segment['sentiment']}")
                                    if segment['emotion']:
                                        log_parts.append(f"emotion: {segment['emotion']}")
                                    if segment['speaker'] is not None:
                                        log_parts.append(f"speaker: {segment['speaker']}")
                                    
                                    logger.info(f"✅ Added transcript segment: {', '.join(log_parts)}")
                                else:
                                    logger.debug(f"Empty transcript message (final={is_final}, confidence={confidence:.3f})")
                            
                            elif message_type == 'session_ends':
                                logger.info("Gladia session ended")
                                break
                                
                            elif message_type == 'error':
                                error_msg = parsed_message.get('data', {}).get('message', 'Unknown error')
                                logger.error(f"Gladia error: {error_msg}")
                                break
                            
                            elif message_type in ['sentiment_analysis', 'emotion_analysis', 'summarization', 'named_entity_recognition', 'chapterization']:
                                # Handle Audio Intelligence specific messages
                                logger.info(f"Audio Intelligence {message_type}: {parsed_message.get('data', {})}")
                                # Store AI insights in segments for later processing
                                ai_segment = {
                                    "type": message_type,
                                    "data": parsed_message.get('data', {}),
                                    "timestamp": parsed_message.get('timestamp', None)
                                }
                                transcript_segments.append(ai_segment)
                            
                            else:
                                logger.debug(f"Received Gladia message: {message_type}")
                        
                        except json.JSONDecodeError:
                            logger.warning("Received non-JSON message from Gladia")
                            continue
                    
                    except asyncio.TimeoutError:
                        timeout_count += 1
                        logger.debug(f"WebSocket timeout {timeout_count}/{max_timeouts}")
                        if timeout_count >= max_timeouts:
                            logger.info("Max timeouts reached, ending transcription")
                            break
                
                logger.info(f"WebSocket transcription complete:")
                logger.info(f"  - Messages received: {messages_received}")
                logger.info(f"  - Transcript segments: {len(transcript_segments)}")
                logger.info(f"  - Transcript found: {transcript_found}")
                logger.info(f"  - Final timeout count: {timeout_count}/{max_timeouts}")
                
                if transcript_segments:
                    total_text = ' '.join([seg.get('text', '') for seg in transcript_segments if seg.get('text')])
                    avg_confidence = sum([seg.get('confidence', 0) for seg in transcript_segments]) / len(transcript_segments)
                    logger.info(f"  - Total text: '{total_text[:100]}{'...' if len(total_text) > 100 else ''}'")
                    logger.info(f"  - Average confidence: {avg_confidence:.3f}")
                else:
                    logger.warning("  - No transcript segments generated from microphone audio")
                
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
        except Exception as e:
            logger.error(f"Error processing audio with Gladia: {e}")
        
        return transcript_segments
    
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
            
            # Note: active_sessions cleanup is handled by stop_pitch_recording
            # Don't delete here to avoid KeyError conflicts
        
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
    
    async def get_audio_intelligence(
        self, 
        session_id: str, 
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Get Audio Intelligence analysis for a completed session.
        
        This method retrieves comprehensive audio analysis including:
        - Speech metrics (WPM, pauses, speaking rate)
        - Filler word analysis (um, uh, like detection)
        - Confidence and energy level assessment
        - Presentation delivery insights
        
        Args:
            session_id: Session identifier
            force_reprocess: Whether to force reprocessing with Gladia API
            
        Returns:
            Audio Intelligence analysis results or error information
        """
        try:
            # Find session using efficient lookup
            session_key = await self._find_session_key(session_id)
            if not session_key:
                return {
                    "error": "Session not found", 
                    "session_id": session_id,
                    "error_type": "session_not_found"
                }
            
            redis_client = await self.get_redis()
            session_json = await redis_client.get(session_key)
            
            if not session_json:
                return {
                    "error": "Session data not found", 
                    "session_id": session_id,
                    "error_type": "session_data_not_found"
                }
            
            session_data = json.loads(session_json)
            
            # Check if session is completed
            if session_data.get("status") not in ["completed", "stopped"]:
                return {
                    "error": "Session must be completed to get Audio Intelligence",
                    "session_id": session_id,
                    "status": session_data.get("status"),
                    "error_type": "session_not_completed"
                }
            
            # Extract event_id for proper key structure
            event_id = session_data.get("event_id", "default")
            
            # Check if we already have Audio Intelligence data cached
            ai_cache_key = f"event:{event_id}:audio_intelligence:{session_id}"
            
            if not force_reprocess:
                cached_ai = await redis_client.get(ai_cache_key)
                if cached_ai:
                    logger.info(f"Returning cached Audio Intelligence for session {session_id}")
                    ai_data = json.loads(cached_ai)
                    ai_data["from_cache"] = True
                    return ai_data
            
            # Check if we have Gladia session ID for API call
            gladia_session_id = session_data.get("gladia_session_id")
            if not gladia_session_id:
                # Try to extract from intelligence data if available
                intelligence_data = session_data.get("intelligence_data", {})
                if intelligence_data:
                    # We have some intelligence data from batch processing
                    ai_analysis = self._create_audio_intelligence_from_session_data(
                        session_id, session_data
                    )
                    
                    # Cache the results
                    await redis_client.setex(
                        ai_cache_key,
                        3600,  # 1 hour cache
                        json.dumps(ai_analysis)
                    )
                    
                    return ai_analysis
                else:
                    return {
                        "error": "No Gladia session ID or intelligence data available",
                        "session_id": session_id,
                        "has_gladia_session": False,
                        "has_intelligence_data": False,
                        "error_type": "no_intelligence_source"
                    }
            
            # Try to get Audio Intelligence from Gladia API
            logger.info(f"Fetching Audio Intelligence from Gladia API for session {session_id}")
            gladia_intelligence = await self._fetch_gladia_audio_intelligence(gladia_session_id)
            
            if gladia_intelligence:
                # Create structured Audio Intelligence analysis
                ai_analysis = self._create_audio_intelligence_analysis(
                    session_id, gladia_session_id, gladia_intelligence, session_data
                )
                
                # Cache the results for future requests
                await redis_client.setex(
                    ai_cache_key,
                    3600,  # 1 hour cache
                    json.dumps(ai_analysis)
                )
                
                logger.info(f"Audio Intelligence analysis completed for session {session_id}")
                return ai_analysis
            else:
                return {
                    "error": "Failed to fetch Audio Intelligence from Gladia API",
                    "session_id": session_id,
                    "gladia_session_id": gladia_session_id,
                    "error_type": "gladia_api_error"
                }
            
        except json.JSONDecodeError as e:
            return {
                "error": f"Invalid session data format: {str(e)}",
                "session_id": session_id,
                "error_type": "data_parsing_error"
            }
        except Exception as e:
            logger.error(f"Error getting Audio Intelligence for session {session_id}: {e}")
            return {
                "error": f"Failed to get Audio Intelligence: {str(e)}",
                "session_id": session_id,
                "error_type": "unexpected_error"
            }
    
    async def _fetch_gladia_audio_intelligence(self, gladia_session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch Audio Intelligence data from Gladia API."""
        import aiohttp
        
        api_key = os.getenv('GLADIA_API_KEY')
        if not api_key:
            logger.error("No Gladia API key for Audio Intelligence fetch")
            return None
        
        try:
            # Use Gladia's session results endpoint which should include Audio Intelligence
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.gladia.io/v2/transcription/{gladia_session_id}",
                    headers={'X-Gladia-Key': api_key},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Check if the result includes Audio Intelligence features
                        prediction = result.get('prediction', {})
                        if 'utterances' in prediction:
                            return result
                        else:
                            logger.warning("No Audio Intelligence data in Gladia response")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Gladia API error {response.status}: {error_text}")
                        return None
        
        except Exception as e:
            logger.error(f"Error fetching Audio Intelligence from Gladia: {e}")
            return None
    
    def _create_audio_intelligence_analysis(
        self, 
        session_id: str, 
        gladia_session_id: str, 
        gladia_result: Dict[str, Any],
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create structured Audio Intelligence analysis from Gladia result."""
        prediction = gladia_result.get('prediction', {})
        metadata = gladia_result.get('metadata', {})
        
        # Calculate speech metrics from utterances
        utterances = prediction.get('utterances', [])
        total_words = 0
        total_duration = float(metadata.get('duration', 0))
        speaking_duration = 0.0
        pause_count = 0
        filler_words = []
        
        # Common filler words to detect
        filler_patterns = ['um', 'uh', 'like', 'you know', 'actually', 'basically', 'literally']
        
        for utterance in utterances:
            text = utterance.get('text', '').lower()
            words = text.split()
            total_words += len(words)
            
            # Calculate speaking duration (end - start)
            start_time = float(utterance.get('start', 0))
            end_time = float(utterance.get('end', 0))
            speaking_duration += (end_time - start_time)
            
            # Detect filler words
            for word in words:
                if word.strip('.,!?') in filler_patterns:
                    filler_words.append(word)
        
        # Calculate metrics
        words_per_minute = (total_words / total_duration * 60) if total_duration > 0 else 0
        pause_duration = max(0, total_duration - speaking_duration)
        filler_percentage = (len(filler_words) / total_words * 100) if total_words > 0 else 0
        
        # Estimate confidence from speech patterns (simplified)
        confidence_score = max(0.3, min(1.0, 1.0 - (filler_percentage / 100) * 2))
        
        # Determine energy level based on speaking pace
        if words_per_minute > 160:
            energy_level = "high"
        elif words_per_minute > 120:
            energy_level = "moderate"
        else:
            energy_level = "low"
        
        # Create Audio Intelligence structure using our value objects format
        analysis_timestamp = datetime.now(timezone.utc).isoformat()
        
        ai_analysis = {
            "session_id": session_id,
            "gladia_session_id": gladia_session_id,
            "analysis_timestamp": analysis_timestamp,
            "team_name": session_data.get("team_name"),
            "pitch_title": session_data.get("pitch_title"),
            
            "speech_metrics": {
                "words_per_minute": round(words_per_minute, 1),
                "total_duration_seconds": total_duration,
                "speaking_duration_seconds": round(speaking_duration, 1),
                "total_pause_duration_seconds": round(pause_duration, 1),
                "pause_count": pause_count,
                "speaking_rate_assessment": self._assess_speaking_rate(words_per_minute)
            },
            
            "filler_analysis": {
                "total_filler_count": len(filler_words),
                "filler_words_detected": list(set(filler_words))[:10],  # Unique fillers, limit display
                "filler_percentage": round(filler_percentage, 2),
                "most_common_filler": max(set(filler_words), key=filler_words.count) if filler_words else None,
                "filler_frequency_per_minute": round(len(filler_words) / total_duration * 60, 1) if total_duration > 0 else 0,
                "professionalism_grade": self._grade_professionalism(filler_percentage)
            },
            
            "confidence_metrics": {
                "confidence_score": round(confidence_score, 2),
                "energy_level": energy_level,
                "vocal_stability": round(min(1.0, speaking_duration / total_duration), 2) if total_duration > 0 else 0.5,
                "pace_consistency": 0.8,  # Placeholder - would need more detailed analysis
                "confidence_assessment": self._assess_confidence(confidence_score)
            },
            
            "presentation_insights": {
                "overall_delivery_score": self._calculate_delivery_score(words_per_minute, filler_percentage, confidence_score),
                "strengths": self._identify_strengths(words_per_minute, filler_percentage, confidence_score),
                "areas_of_improvement": self._identify_improvements(words_per_minute, filler_percentage, confidence_score),
                "coaching_recommendations": self._generate_coaching_insights(words_per_minute, filler_percentage, pause_duration, total_duration)
            },
            
            "success": True,
            "from_cache": False
        }
        
        return ai_analysis
    
    def _create_audio_intelligence_from_session_data(self, session_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Audio Intelligence analysis from existing session intelligence data."""
        intelligence_data = session_data.get("intelligence_data", {})
        transcript_segments = session_data.get("transcript_segments", [])
        
        # Basic analysis from transcript segments
        total_words = 0
        total_text = ""
        
        for segment in transcript_segments:
            if isinstance(segment, dict) and "text" in segment:
                text = segment["text"]
                total_text += text + " "
                total_words += len(text.split())
        
        # Estimate duration from session timing
        duration = self._calculate_session_duration(session_data) or 180  # Default 3 minutes
        words_per_minute = (total_words / duration * 60) if duration > 0 else 0
        
        # Simple filler detection
        filler_patterns = ['um', 'uh', 'like', 'you know', 'actually', 'basically']
        filler_words = []
        for word in total_text.lower().split():
            if word.strip('.,!?') in filler_patterns:
                filler_words.append(word)
        
        filler_percentage = (len(filler_words) / total_words * 100) if total_words > 0 else 0
        confidence_score = max(0.4, min(1.0, 1.0 - (filler_percentage / 100) * 1.5))
        
        return {
            "session_id": session_id,
            "gladia_session_id": session_data.get("gladia_session_id"),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "team_name": session_data.get("team_name"),
            "pitch_title": session_data.get("pitch_title"),
            
            "speech_metrics": {
                "words_per_minute": round(words_per_minute, 1),
                "total_duration_seconds": duration,
                "speaking_rate_assessment": self._assess_speaking_rate(words_per_minute)
            },
            
            "filler_analysis": {
                "total_filler_count": len(filler_words),
                "filler_percentage": round(filler_percentage, 2),
                "professionalism_grade": self._grade_professionalism(filler_percentage)
            },
            
            "confidence_metrics": {
                "confidence_score": round(confidence_score, 2),
                "confidence_assessment": self._assess_confidence(confidence_score)
            },
            
            "success": True,
            "from_cache": False,
            "data_source": "session_intelligence_data"
        }
    
    def _assess_speaking_rate(self, wpm: float) -> str:
        """Assess speaking rate for pitch presentations."""
        if wpm < 120:
            return "too_slow"
        elif wpm > 180:
            return "too_fast"
        else:
            return "appropriate"
    
    def _grade_professionalism(self, filler_percentage: float) -> str:
        """Grade professionalism based on filler usage."""
        if filler_percentage <= 2.0:
            return "excellent"
        elif filler_percentage <= 5.0:
            return "good"
        else:
            return "needs_improvement"
    
    def _assess_confidence(self, confidence_score: float) -> str:
        """Assess confidence level."""
        if confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.6:
            return "moderate"
        else:
            return "low"
    
    def _calculate_delivery_score(self, wpm: float, filler_percentage: float, confidence_score: float) -> float:
        """Calculate overall delivery score (0-100)."""
        pace_score = 100 if 140 <= wpm <= 160 else max(60, 100 - abs(wpm - 150) * 2)
        filler_score = max(30, 100 - filler_percentage * 15)
        confidence_score_pct = confidence_score * 100
        
        return round((pace_score * 0.3 + filler_score * 0.4 + confidence_score_pct * 0.3), 1)
    
    def _identify_strengths(self, wpm: float, filler_percentage: float, confidence_score: float) -> List[str]:
        """Identify presentation strengths."""
        strengths = []
        
        if 140 <= wpm <= 160:
            strengths.append(f"Excellent pacing at {wpm:.0f} WPM - ideal for technical presentations")
        
        if filler_percentage <= 2.0:
            strengths.append(f"Professional delivery with only {filler_percentage:.1f}% filler words")
        
        if confidence_score >= 0.8:
            strengths.append("High vocal confidence and presentation energy")
        
        return strengths if strengths else ["Completed full presentation delivery"]
    
    def _identify_improvements(self, wpm: float, filler_percentage: float, confidence_score: float) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        
        if wpm < 120:
            improvements.append(f"Increase speaking pace from {wpm:.0f} to 140-160 WPM for better engagement")
        elif wpm > 180:
            improvements.append(f"Slow down from {wpm:.0f} to 140-160 WPM for better comprehension")
        
        if filler_percentage > 3.0:
            improvements.append(f"Reduce filler words from {filler_percentage:.1f}% to under 2% (practice with strategic pauses)")
        
        if confidence_score < 0.7:
            improvements.append("Practice delivery to improve vocal confidence and stability")
        
        return improvements
    
    def _generate_coaching_insights(self, wpm: float, filler_percentage: float, pause_duration: float, total_duration: float) -> List[str]:
        """Generate actionable coaching recommendations."""
        insights = []
        
        # Pacing insights
        if wpm < 130:
            insights.append("Practice speaking with more energy and conviction to increase engagement")
        elif wpm > 170:
            insights.append("Focus on clear articulation - slower pace improves understanding")
        
        # Pause effectiveness
        if pause_duration > 0 and total_duration > 0:
            pause_percentage = (pause_duration / total_duration) * 100
            if pause_percentage < 10:
                insights.append("Add strategic pauses after key points for emphasis and audience comprehension")
            elif pause_percentage > 25:
                insights.append("Reduce excessive pausing - maintain momentum while still allowing for emphasis")
        
        # Professional delivery
        if filler_percentage > 2:
            insights.append("Practice replacing filler words with brief pauses - builds confidence and professionalism")
        
        return insights
    
    async def _trigger_automatic_scoring(
        self,
        session_id: str,
        event_id: str,
        team_name: str,
        logger
    ) -> None:
        """
        Trigger automatic AI scoring after recording completion.
        
        This method is called automatically when a recording is completed with a valid transcript.
        It runs the scoring process asynchronously without blocking the recording completion.
        
        Args:
            session_id: Recording session identifier
            event_id: Event identifier for multi-tenant isolation
            team_name: Team name for logging context
            logger: Logger instance for consistent logging
        """
        try:
            # Import scoring handler (lazy import to avoid circular dependencies)
            from ...scoring.mcp.scoring_mcp_handler import scoring_mcp_handler
            
            logger.info(
                f"Triggering automatic AI scoring for {team_name}",
                operation="automatic_scoring_trigger",
                team_name=team_name,
                session_id=session_id
            )
            
            # Call the scoring system asynchronously
            scoring_result = await scoring_mcp_handler.score_complete_pitch(
                session_id=session_id,
                event_id=event_id,
                judge_id=None,  # Automatic scoring, no specific judge
                scoring_context={
                    "triggered_by": "automatic_recording_completion",
                    "trigger_timestamp": datetime.now(timezone.utc).isoformat(),
                    "automation_enabled": True
                }
            )
            
            if scoring_result.get("success"):
                total_score = "N/A"
                scores = scoring_result.get("scores", {})
                if isinstance(scores, dict) and "overall" in scores:
                    total_score = scores["overall"].get("total_score", "N/A")
                
                logger.info(
                    f"Automatic scoring completed successfully for {team_name}",
                    operation="automatic_scoring_success",
                    team_name=team_name,
                    total_score=total_score,
                    scoring_timestamp=scoring_result.get("scoring_timestamp")
                )
                
                # Log that the team is now eligible for leaderboard
                logger.info(
                    f"Team {team_name} is now eligible for leaderboard rankings",
                    operation="leaderboard_eligibility",
                    team_name=team_name,
                    session_id=session_id
                )
                
            else:
                error_msg = scoring_result.get("error", "Unknown error")
                logger.error(
                    f"Automatic scoring failed for {team_name}: {error_msg}",
                    operation="automatic_scoring_failure",
                    team_name=team_name,
                    error=error_msg,
                    error_type=scoring_result.get("error_type", "unknown")
                )
                
                # Note: We don't raise an exception here because recording completion
                # should still succeed even if automatic scoring fails
                
        except Exception as e:
            logger.error(
                f"Exception in automatic scoring trigger for {team_name}: {str(e)}",
                operation="automatic_scoring_exception",
                team_name=team_name,
                exception=e,
                traceback=True
            )
            # Don't raise - recording completion should succeed even if scoring fails


# Global instance
gladia_mcp_handler = GladiaMCPHandler()

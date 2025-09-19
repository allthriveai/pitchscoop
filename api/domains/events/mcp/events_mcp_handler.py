"""
Events MCP Handler - Business logic for event management

This handler manages events (hackathons, VC pitches, individual practice)
and their participants using Redis for persistence.

Events are stored with the following structure:
- event:{event_id} - Main event data
- event:{event_id}:participants - List of participants 
- event:{event_id}:sessions - Recording sessions for this event
"""
import json
import uuid
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import redis.asyncio as redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EventsMCPHandler:
    """MCP handler for Events domain operations."""
    
    def __init__(self):
        """Initialize the Events MCP handler."""
        self.redis_client: Optional[redis.Redis] = None
        
    async def get_redis(self) -> redis.Redis:
        """Get Redis client connection."""
        if self.redis_client is None:
            # Use environment variable, fallback to Docker internal network
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client
    
    async def create_event(
        self,
        event_type: str,
        event_name: str, 
        description: str,
        max_participants: int = 50,
        duration_minutes: int = 5,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        event_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new event.
        
        Args:
            event_type: Type of event (hackathon, vc_pitch, individual_practice)
            event_name: Display name for the event
            description: Event description
            max_participants: Maximum number of participants
            duration_minutes: Pitch duration limit
            start_time: Optional start time (ISO format)
            end_time: Optional end time (ISO format)
            event_config: Event-specific configuration
            
        Returns:
            Created event information
        """
        try:
            # DEMO: Hardcode event ID to mcp-hackathon for today's demo
            event_id = "mcp-hackathon"
            
            # Set default event config based on type
            default_configs = {
                "hackathon": {
                    "judging_enabled": True,
                    "public_leaderboard": True,
                    "allow_multiple_attempts": False,
                    "scoring_criteria": ["Innovation", "Technical Implementation", "Presentation"],
                    "team_based": True
                },
                "vc_pitch": {
                    "judging_enabled": True,
                    "public_leaderboard": False,
                    "allow_multiple_attempts": True,
                    "scoring_criteria": ["Market Opportunity", "Business Model", "Team"],
                    "team_based": False
                },
                "individual_practice": {
                    "judging_enabled": False,
                    "public_leaderboard": False,
                    "allow_multiple_attempts": True,
                    "scoring_criteria": ["Self Assessment"],
                    "team_based": False
                }
            }
            
            # Merge default config with provided config
            final_config = default_configs.get(event_type, {})
            if event_config:
                final_config.update(event_config)
            
            # Determine initial status
            current_time = datetime.utcnow()
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                status = "active" if start_dt <= current_time else "upcoming"
            else:
                status = "active"  # Start immediately if no start time
            
            # Create event data
            event_data = {
                "event_id": event_id,
                "event_type": event_type,
                "event_name": event_name,
                "description": description,
                "status": status,
                "max_participants": max_participants,
                "duration_minutes": duration_minutes,
                "created_at": current_time.isoformat(),
                "start_time": start_time,
                "end_time": end_time,
                "event_config": final_config,
                "participant_count": 0,
                "session_count": 0
            }
            
            # Store in Redis
            redis_client = await self.get_redis()
            await redis_client.setex(
                f"event:{event_id}",
                86400 * 30,  # 30 days TTL
                json.dumps(event_data)
            )
            
            # Initialize empty participant list
            await redis_client.setex(
                f"event:{event_id}:participants",
                86400 * 30,
                json.dumps([])
            )
            
            # Initialize empty session list  
            await redis_client.setex(
                f"event:{event_id}:sessions",
                86400 * 30,
                json.dumps([])
            )
            
            return {
                "event_id": event_id,
                "event_name": event_name,
                "event_type": event_type,
                "status": status,
                "max_participants": max_participants,
                "duration_minutes": duration_minutes,
                "event_config": final_config,
                "created_at": event_data["created_at"],
                "instructions": {
                    "next_step": "Add participants with events.join_event, then start recording sessions",
                    "recording_integration": "Use pitches.start_recording with this event_id",
                    "management": "Use events.start_event when ready to begin competition"
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to create event: {str(e)}",
                "event_id": None
            }
    
    async def list_events(
        self,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List events with optional filtering.
        
        Args:
            event_type: Filter by event type
            status: Filter by event status
            limit: Maximum number of results
            
        Returns:
            List of event summaries
        """
        try:
            redis_client = await self.get_redis()
            
            # Get all event keys
            event_keys = []
            async for key in redis_client.scan_iter(match="event:*"):
                # Skip participant and session keys
                if not (":participants" in key or ":sessions" in key):
                    event_keys.append(key)
            
            events = []
            for key in event_keys[:limit * 2]:  # Get extra in case some are filtered out
                try:
                    event_json = await redis_client.get(key)
                    if event_json:
                        event_data = json.loads(event_json)
                        
                        # Apply filters
                        if event_type and event_data.get("event_type") != event_type:
                            continue
                        if status and event_data.get("status") != status:
                            continue
                        
                        # Create event summary
                        event_summary = {
                            "event_id": event_data["event_id"],
                            "event_name": event_data["event_name"],
                            "event_type": event_data["event_type"],
                            "status": event_data["status"],
                            "created_at": event_data["created_at"],
                            "participant_count": event_data.get("participant_count", 0),
                            "session_count": event_data.get("session_count", 0),
                            "max_participants": event_data["max_participants"],
                            "duration_minutes": event_data["duration_minutes"]
                        }
                        
                        # Add time info if available
                        if event_data.get("start_time"):
                            event_summary["start_time"] = event_data["start_time"]
                        if event_data.get("end_time"):
                            event_summary["end_time"] = event_data["end_time"]
                        
                        events.append(event_summary)
                        
                        if len(events) >= limit:
                            break
                            
                except Exception as e:
                    # Skip invalid events
                    continue
            
            # Sort by creation time (newest first)
            events.sort(key=lambda x: x["created_at"], reverse=True)
            
            return {
                "events": events,
                "total_count": len(events),
                "filters_applied": {
                    "event_type": event_type,
                    "status": status,
                    "limit": limit
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to list events: {str(e)}",
                "events": []
            }
    
    async def get_event_details(self, event_id: str) -> Dict[str, Any]:
        """
        Get complete event details.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Complete event information with participants and sessions
        """
        try:
            redis_client = await self.get_redis()
            
            # Get event data
            event_json = await redis_client.get(f"event:{event_id}")
            if not event_json:
                return {"error": "Event not found", "event_id": event_id}
            
            event_data = json.loads(event_json)
            
            # Get participants
            participants_json = await redis_client.get(f"event:{event_id}:participants")
            participants = json.loads(participants_json) if participants_json else []
            
            # Get sessions
            sessions_json = await redis_client.get(f"event:{event_id}:sessions")
            sessions = json.loads(sessions_json) if sessions_json else []
            
            # Add participant and session data to event
            event_data["participants"] = participants
            event_data["sessions"] = sessions
            event_data["participant_count"] = len(participants)
            event_data["session_count"] = len(sessions)
            
            return event_data
            
        except Exception as e:
            return {
                "error": f"Failed to get event details: {str(e)}",
                "event_id": event_id
            }
    
    async def join_event(
        self,
        event_id: str,
        participant_name: str,
        contact_info: Dict[str, str],
        team_members: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Add a participant to an event.
        
        Args:
            event_id: Event identifier
            participant_name: Team/individual name
            contact_info: Contact information (email required)
            team_members: List of team member names (for hackathons)
            
        Returns:
            Participant registration information
        """
        try:
            redis_client = await self.get_redis()
            
            # Get event data
            event_json = await redis_client.get(f"event:{event_id}")
            if not event_json:
                return {"error": "Event not found", "event_id": event_id}
            
            event_data = json.loads(event_json)
            
            # Check if event accepts new participants
            if event_data["status"] not in ["upcoming", "active"]:
                return {
                    "error": "Event is not accepting new participants",
                    "event_status": event_data["status"]
                }
            
            # Get current participants
            participants_json = await redis_client.get(f"event:{event_id}:participants")
            participants = json.loads(participants_json) if participants_json else []
            
            # Check participant limit
            if len(participants) >= event_data["max_participants"]:
                return {
                    "error": "Event is full",
                    "max_participants": event_data["max_participants"],
                    "current_count": len(participants)
                }
            
            # Check for duplicate participant names
            existing_names = [p["participant_name"] for p in participants]
            if participant_name in existing_names:
                return {
                    "error": "Participant name already registered",
                    "participant_name": participant_name
                }
            
            # Create participant record
            participant_data = {
                "participant_id": str(uuid.uuid4()),
                "participant_name": participant_name,
                "contact_info": contact_info,
                "joined_at": datetime.utcnow().isoformat(),
                "team_members": team_members or [],
                "session_count": 0
            }
            
            # Add to participants list
            participants.append(participant_data)
            
            # Update participants in Redis
            await redis_client.setex(
                f"event:{event_id}:participants",
                86400 * 30,
                json.dumps(participants)
            )
            
            # Update participant count in event
            event_data["participant_count"] = len(participants)
            await redis_client.setex(
                f"event:{event_id}",
                86400 * 30,
                json.dumps(event_data)
            )
            
            return {
                "event_id": event_id,
                "event_name": event_data["event_name"],
                "participant_id": participant_data["participant_id"],
                "participant_name": participant_name,
                "registered_at": participant_data["joined_at"],
                "team_members": team_members or [],
                "total_participants": len(participants),
                "instructions": {
                    "next_step": "Wait for event to start, then use pitches.start_recording",
                    "recording_format": f"pitches.start_recording(event_id='{event_id}', team_name='{participant_name}', ...)",
                    "event_status": event_data["status"]
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to join event: {str(e)}",
                "event_id": event_id
            }
    
    async def start_event(self, event_id: str) -> Dict[str, Any]:
        """
        Start an event and open it for recordings.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Event start confirmation
        """
        try:
            redis_client = await self.get_redis()
            
            # Get event data
            event_json = await redis_client.get(f"event:{event_id}")
            if not event_json:
                return {"error": "Event not found", "event_id": event_id}
            
            event_data = json.loads(event_json)
            
            # Check current status
            if event_data["status"] == "active":
                return {
                    "message": "Event is already active",
                    "event_id": event_id,
                    "status": "active"
                }
            
            if event_data["status"] not in ["upcoming"]:
                return {
                    "error": f"Cannot start event with status: {event_data['status']}",
                    "current_status": event_data["status"]
                }
            
            # Update status
            event_data["status"] = "active"
            event_data["actual_start_time"] = datetime.utcnow().isoformat()
            
            # Save updated event
            await redis_client.setex(
                f"event:{event_id}",
                86400 * 30,
                json.dumps(event_data)
            )
            
            return {
                "event_id": event_id,
                "event_name": event_data["event_name"],
                "status": "active",
                "started_at": event_data["actual_start_time"],
                "participant_count": event_data.get("participant_count", 0),
                "message": "Event started successfully. Participants can now begin recording.",
                "instructions": {
                    "participants": "Can now use pitches.start_recording to record pitches",
                    "duration_limit": f"{event_data['duration_minutes']} minutes per pitch",
                    "event_type": event_data["event_type"]
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to start event: {str(e)}",
                "event_id": event_id
            }
    
    async def end_event(self, event_id: str) -> Dict[str, Any]:
        """
        End an event and finalize results.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Event completion summary
        """
        try:
            redis_client = await self.get_redis()
            
            # Get event data
            event_json = await redis_client.get(f"event:{event_id}")
            if not event_json:
                return {"error": "Event not found", "event_id": event_id}
            
            event_data = json.loads(event_json)
            
            # Check current status
            if event_data["status"] == "completed":
                return {
                    "message": "Event is already completed",
                    "event_id": event_id,
                    "status": "completed"
                }
            
            # Update status
            event_data["status"] = "completed"
            event_data["completed_at"] = datetime.utcnow().isoformat()
            
            # Get final counts
            participants_json = await redis_client.get(f"event:{event_id}:participants")
            participants = json.loads(participants_json) if participants_json else []
            
            sessions_json = await redis_client.get(f"event:{event_id}:sessions")
            sessions = json.loads(sessions_json) if sessions_json else []
            
            event_data["final_participant_count"] = len(participants)
            event_data["final_session_count"] = len(sessions)
            
            # Save updated event
            await redis_client.setex(
                f"event:{event_id}",
                86400 * 30,
                json.dumps(event_data)
            )
            
            return {
                "event_id": event_id,
                "event_name": event_data["event_name"],
                "status": "completed",
                "completed_at": event_data["completed_at"],
                "final_stats": {
                    "participants": len(participants),
                    "recording_sessions": len(sessions),
                    "event_type": event_data["event_type"]
                },
                "message": "Event completed successfully. No new recordings will be accepted.",
                "next_steps": {
                    "scoring": "Results available for analysis and leaderboard generation",
                    "recordings": "All pitch recordings remain available for playback"
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to end event: {str(e)}",
                "event_id": event_id
            }
    
    async def delete_event(self, event_id: str, confirm_deletion: bool) -> Dict[str, Any]:
        """
        Delete an event and all associated data.
        
        Args:
            event_id: Event identifier
            confirm_deletion: Must be True to confirm deletion
            
        Returns:
            Deletion confirmation
        """
        try:
            if not confirm_deletion:
                return {
                    "error": "Deletion not confirmed",
                    "message": "Set confirm_deletion=True to permanently delete this event"
                }
            
            redis_client = await self.get_redis()
            
            # Get event data before deletion
            event_json = await redis_client.get(f"event:{event_id}")
            if not event_json:
                return {"error": "Event not found", "event_id": event_id}
            
            event_data = json.loads(event_json)
            
            # Delete all related keys
            keys_to_delete = [
                f"event:{event_id}",
                f"event:{event_id}:participants",
                f"event:{event_id}:sessions"
            ]
            
            deleted_count = await redis_client.delete(*keys_to_delete)
            
            return {
                "event_id": event_id,
                "event_name": event_data["event_name"],
                "deleted": True,
                "keys_deleted": deleted_count,
                "message": "Event and all associated data deleted permanently",
                "warning": "This action cannot be undone. All recordings associated with this event should be manually cleaned up."
            }
            
        except Exception as e:
            return {
                "error": f"Failed to delete event: {str(e)}",
                "event_id": event_id,
                "deleted": False
            }


# Global instance
events_mcp_handler = EventsMCPHandler()
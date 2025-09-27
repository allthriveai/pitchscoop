"""
WebSocket Service with Redis Streams Integration
Real-time updates for PitchScoop competitions
"""
import asyncio
import json
import logging
from typing import Dict, List, Set, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis
import uuid

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and Redis Streams integration"""
    
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Store active connections by event_id
        self.connections: Dict[str, Set[WebSocket]] = {}
        
        # Store connection metadata
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
        # Stream consumers (background tasks)
        self.stream_consumers: Dict[str, asyncio.Task] = {}
        
        logger.info("WebSocket manager initialized with Redis Streams")
    
    async def connect(self, websocket: WebSocket, event_id: str, user_type: str = "viewer"):
        """Connect a new WebSocket client"""
        await websocket.accept()
        
        # Add to connections
        if event_id not in self.connections:
            self.connections[event_id] = set()
        self.connections[event_id].add(websocket)
        
        # Store connection metadata
        self.connection_info[websocket] = {
            "event_id": event_id,
            "user_type": user_type,
            "connected_at": datetime.utcnow().isoformat(),
            "connection_id": str(uuid.uuid4())
        }
        
        # Start stream consumer for this event if not already running
        if event_id not in self.stream_consumers:
            self.stream_consumers[event_id] = asyncio.create_task(
                self._consume_event_streams(event_id)
            )
        
        logger.info(f"WebSocket connected: {user_type} for event {event_id}")
        
        # Send welcome message
        await self._send_to_websocket(websocket, {
            "type": "connection_established",
            "event_id": event_id,
            "message": f"Connected to {event_id} as {user_type}",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client"""
        if websocket in self.connection_info:
            event_id = self.connection_info[websocket]["event_id"]
            
            # Remove from connections
            if event_id in self.connections:
                self.connections[event_id].discard(websocket)
                
                # If no more connections for this event, stop the consumer
                if not self.connections[event_id]:
                    if event_id in self.stream_consumers:
                        self.stream_consumers[event_id].cancel()
                        del self.stream_consumers[event_id]
                    del self.connections[event_id]
            
            # Remove metadata
            del self.connection_info[websocket]
            
            logger.info(f"WebSocket disconnected from event {event_id}")
    
    async def _consume_event_streams(self, event_id: str):
        """Background task that consumes Redis Streams for an event"""
        streams = {
            f"stream:event:{event_id}:leaderboard": "$",
            f"stream:event:{event_id}:activity": "$",
            f"stream:event:{event_id}:judges": "$",
            f"stream:event:{event_id}:announcements": "$"
        }
        
        logger.info(f"Starting stream consumer for event {event_id}")
        
        try:
            while event_id in self.connections:
                try:
                    messages = await self.redis_client.xread(
                        streams, 
                        count=10, 
                        block=1000  # Block for 1 second
                    )
                    
                    for stream, stream_messages in messages:
                        for message_id, fields in stream_messages:
                            # Broadcast to all connected WebSocket clients
                            await self._broadcast_to_event(event_id, {
                                "type": self._get_message_type(stream),
                                "stream": stream,
                                "message_id": message_id,
                                "data": fields,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            
                            # Update stream position
                            streams[stream] = message_id
                
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Stream consumer error for {event_id}: {e}")
                    await asyncio.sleep(1)
        
        except asyncio.CancelledError:
            logger.info(f"Stream consumer cancelled for event {event_id}")
        finally:
            logger.info(f"Stream consumer stopped for event {event_id}")
    
    def _get_message_type(self, stream: str) -> str:
        """Extract message type from stream name"""
        if "leaderboard" in stream:
            return "leaderboard_update"
        elif "activity" in stream:
            return "competition_activity"
        elif "judges" in stream:
            return "judge_activity"
        elif "announcements" in stream:
            return "announcement"
        else:
            return "general_update"
    
    async def _broadcast_to_event(self, event_id: str, message: Dict[str, Any]):
        """Broadcast message to all WebSocket connections for an event"""
        if event_id not in self.connections:
            return
        
        # Get all connections for this event
        connections = self.connections[event_id].copy()
        
        # Send to each connection
        disconnected = []
        for websocket in connections:
            try:
                await self._send_to_websocket(websocket, message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected WebSockets
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def _send_to_websocket(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            raise
    
    async def get_connection_stats(self, event_id: str) -> Dict[str, Any]:
        """Get connection statistics for an event"""
        if event_id not in self.connections:
            return {"event_id": event_id, "connections": 0, "user_types": {}}
        
        connections = self.connections[event_id]
        user_types = {}
        
        for websocket in connections:
            if websocket in self.connection_info:
                user_type = self.connection_info[websocket]["user_type"]
                user_types[user_type] = user_types.get(user_type, 0) + 1
        
        return {
            "event_id": event_id,
            "total_connections": len(connections),
            "user_types": user_types,
            "has_stream_consumer": event_id in self.stream_consumers
        }


class RedisStreamsService:
    """Service for publishing to Redis Streams"""
    
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        logger.info("Redis Streams service initialized")
    
    async def publish_leaderboard_update(self, event_id: str, update: Dict[str, Any]):
        """Publish leaderboard update to Redis Stream"""
        stream_key = f"stream:event:{event_id}:leaderboard"
        
        message = {
            "update_id": str(uuid.uuid4()),
            "team_name": update["team_name"],
            "new_score": str(update["score"]),
            "new_rank": str(update["rank"]),
            "previous_rank": str(update.get("previous_rank", 0)),
            "action": "score_update",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.xadd(stream_key, message)
        await self.redis_client.expire(stream_key, 86400 * 7)  # 1 week
        
        logger.info(f"Published leaderboard update: {update['team_name']} rank #{update['rank']}")
    
    async def publish_activity(self, event_id: str, activity: Dict[str, Any]):
        """Publish competition activity to Redis Stream"""
        stream_key = f"stream:event:{event_id}:activity"
        
        message = {
            "activity_id": str(uuid.uuid4()),
            "event_type": activity["type"],
            "team_name": activity.get("team_name", ""),
            "session_id": activity.get("session_id", ""),
            "message": activity.get("message", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.xadd(stream_key, message)
        await self.redis_client.expire(stream_key, 86400 * 7)
        
        logger.info(f"Published activity: {activity['type']} - {activity.get('message', '')}")
    
    async def publish_judge_activity(self, event_id: str, judge_action: Dict[str, Any]):
        """Publish judge activity to Redis Stream"""
        stream_key = f"stream:event:{event_id}:judges"
        
        message = {
            "action_id": str(uuid.uuid4()),
            "judge_id": judge_action["judge_id"],
            "action": judge_action["action"],
            "session_id": judge_action.get("session_id", ""),
            "team_name": judge_action.get("team_name", ""),
            "status": judge_action.get("status", "active"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.xadd(stream_key, message)
        await self.redis_client.expire(stream_key, 86400 * 7)
        
        logger.info(f"Published judge activity: {judge_action['judge_id']} {judge_action['action']}")
    
    async def publish_announcement(self, event_id: str, announcement: Dict[str, Any]):
        """Publish announcement to Redis Stream"""
        stream_key = f"stream:event:{event_id}:announcements"
        
        message = {
            "announcement_id": str(uuid.uuid4()),
            "title": announcement.get("title", ""),
            "message": announcement.get("message", ""),
            "priority": announcement.get("priority", "normal"),
            "sender": announcement.get("sender", "system"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.xadd(stream_key, message)
        await self.redis_client.expire(stream_key, 86400 * 7)
        
        logger.info(f"Published announcement: {announcement.get('title', 'Untitled')}")
    
    async def publish_transcript_segment(self, session_id: str, segment: Dict[str, Any]):
        """Publish real-time transcript segment"""
        stream_key = f"stream:session:{session_id}:transcript"
        
        message = {
            "segment_id": segment["id"],
            "text": segment["text"],
            "start_time": str(segment["start_time"]),
            "confidence": str(segment.get("confidence", 1.0)),
            "is_final": str(segment.get("is_final", False)),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.xadd(stream_key, message)
        await self.redis_client.expire(stream_key, 86400)  # 24 hours
        
        logger.info(f"Published transcript: {segment['text'][:50]}...")


# Global instances
websocket_manager = WebSocketManager()
redis_streams = RedisStreamsService()
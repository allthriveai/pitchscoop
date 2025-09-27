"""
WebSocket Router for Real-time PitchScoop Updates
Handles WebSocket connections and integrates with Redis Streams
"""
import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.responses import HTMLResponse

from .websocket_service import websocket_manager, redis_streams

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websockets"])


@router.websocket("/event/{event_id}")
async def websocket_event_endpoint(
    websocket: WebSocket,
    event_id: str,
    user_type: str = Query("viewer", description="User type: viewer, judge, organizer"),
    user_id: Optional[str] = Query(None, description="Optional user identifier")
):
    """
    WebSocket endpoint for real-time event updates.
    
    Connects clients to Redis Streams for:
    - Live leaderboard updates
    - Competition activity feed
    - Judge coordination
    - Announcements
    """
    try:
        # Connect to WebSocket manager
        await websocket_manager.connect(websocket, event_id, user_type)
        
        logger.info(f"WebSocket connected: {user_type} for event {event_id}")
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Listen for messages from client (optional)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types from client
                await handle_client_message(websocket, event_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {user_type} from event {event_id}")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }))
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # Clean up connection
        await websocket_manager.disconnect(websocket)


@router.websocket("/transcript/{session_id}")
async def websocket_transcript_endpoint(
    websocket: WebSocket,
    session_id: str,
    user_type: str = Query("viewer", description="User type for transcript viewing")
):
    """
    WebSocket endpoint for real-time transcript updates.
    
    Streams live transcript segments as they are processed.
    """
    try:
        await websocket.accept()
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "transcript_connection_established",
            "session_id": session_id,
            "message": f"Connected to transcript stream for session {session_id}"
        }))
        
        # Consumer for transcript stream
        stream_key = f"stream:session:{session_id}:transcript"
        last_id = "$"  # Start from newest messages
        
        logger.info(f"Transcript WebSocket connected for session {session_id}")
        
        while True:
            try:
                # Read from transcript stream
                messages = await redis_streams.redis_client.xread(
                    {stream_key: last_id},
                    count=5,
                    block=2000  # Block for 2 seconds
                )
                
                for stream, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        # Send transcript update to client
                        await websocket.send_text(json.dumps({
                            "type": "transcript_update",
                            "session_id": session_id,
                            "message_id": message_id,
                            "data": {
                                "segment_id": fields.get("segment_id"),
                                "text": fields.get("text"),
                                "start_time": float(fields.get("start_time", 0)),
                                "confidence": float(fields.get("confidence", 1.0)),
                                "is_final": fields.get("is_final") == "True"
                            }
                        }))
                        
                        last_id = message_id
                
            except WebSocketDisconnect:
                logger.info(f"Transcript WebSocket disconnected for session {session_id}")
                break
            except Exception as e:
                logger.error(f"Transcript WebSocket error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Transcript stream error: {str(e)}"
                }))
                break
    
    except Exception as e:
        logger.error(f"Transcript WebSocket connection error: {e}")


async def handle_client_message(websocket: WebSocket, event_id: str, message: dict):
    """Handle messages sent from WebSocket clients"""
    message_type = message.get("type")
    
    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": message.get("timestamp")
        }))
    
    elif message_type == "subscribe_transcript":
        # Client wants to subscribe to transcript updates for a session
        session_id = message.get("session_id")
        if session_id:
            # Note: This would require additional logic to handle multiple subscriptions
            await websocket.send_text(json.dumps({
                "type": "transcript_subscription_confirmed",
                "session_id": session_id
            }))
    
    elif message_type == "request_stats":
        # Client wants connection statistics
        stats = await websocket_manager.get_connection_stats(event_id)
        await websocket.send_text(json.dumps({
            "type": "connection_stats",
            "data": stats
        }))
    
    else:
        # Unknown message type
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))


# REST endpoints for managing streams (for testing and admin)

@router.post("/publish/leaderboard/{event_id}")
async def publish_test_leaderboard_update(
    event_id: str,
    update: dict
):
    """Test endpoint to publish leaderboard updates"""
    await redis_streams.publish_leaderboard_update(event_id, update)
    return {"message": "Leaderboard update published", "event_id": event_id}


@router.post("/publish/activity/{event_id}")
async def publish_test_activity(
    event_id: str,
    activity: dict
):
    """Test endpoint to publish competition activities"""
    await redis_streams.publish_activity(event_id, activity)
    return {"message": "Activity published", "event_id": event_id}


@router.post("/publish/announcement/{event_id}")
async def publish_test_announcement(
    event_id: str,
    announcement: dict
):
    """Test endpoint to publish announcements"""
    await redis_streams.publish_announcement(event_id, announcement)
    return {"message": "Announcement published", "event_id": event_id}


@router.get("/stats/{event_id}")
async def get_websocket_stats(event_id: str):
    """Get WebSocket connection statistics for an event"""
    stats = await websocket_manager.get_connection_stats(event_id)
    return stats


@router.get("/test")
async def get_websocket_test_page():
    """Test page for WebSocket connections"""
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>PitchScoop WebSocket Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .messages { 
            border: 1px solid #ccc; 
            height: 400px; 
            overflow-y: scroll; 
            padding: 10px; 
            margin: 10px 0; 
            background: #f9f9f9;
        }
        .message { 
            margin: 5px 0; 
            padding: 5px;
            border-radius: 3px;
        }
        .leaderboard_update { background: #e8f5e8; }
        .competition_activity { background: #e8f0ff; }
        .judge_activity { background: #fff8e8; }
        .announcement { background: #ffe8e8; }
        .connection_established { background: #f0f0f0; }
        
        button { padding: 10px 15px; margin: 5px; }
        input, select { padding: 5px; margin: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 PitchScoop WebSocket Test</h1>
        
        <div>
            <label>Event ID:</label>
            <input type="text" id="eventId" value="mcp-hackathon-demo" />
            
            <label>User Type:</label>
            <select id="userType">
                <option value="viewer">Viewer</option>
                <option value="judge">Judge</option>
                <option value="organizer">Organizer</option>
            </select>
            
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        
        <div class="messages" id="messages"></div>
        
        <div>
            <h3>Test Publishers</h3>
            <button onclick="publishLeaderboard()">📊 Publish Leaderboard Update</button>
            <button onclick="publishActivity()">🎯 Publish Activity</button>
            <button onclick="publishAnnouncement()">📢 Publish Announcement</button>
        </div>
        
        <div>
            <button onclick="clearMessages()">Clear Messages</button>
            <button onclick="getStats()">Get Connection Stats</button>
        </div>
    </div>

    <script>
        let socket = null;
        let eventId = 'mcp-hackathon-demo';

        function addMessage(type, data) {
            const messages = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.innerHTML = `
                <strong>${type}:</strong> 
                <pre>${JSON.stringify(data, null, 2)}</pre>
                <small>${new Date().toLocaleTimeString()}</small>
            `;
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }

        function connect() {
            eventId = document.getElementById('eventId').value;
            const userType = document.getElementById('userType').value;
            
            if (socket) {
                socket.close();
            }

            const wsUrl = `ws://localhost:8000/ws/event/${eventId}?user_type=${userType}`;
            socket = new WebSocket(wsUrl);

            socket.onopen = function(event) {
                addMessage('connection', { status: 'Connected', eventId, userType });
            };

            socket.onmessage = function(event) {
                const message = JSON.parse(event.data);
                addMessage(message.type, message);
            };

            socket.onclose = function(event) {
                addMessage('connection', { status: 'Disconnected', code: event.code });
                socket = null;
            };

            socket.onerror = function(error) {
                addMessage('error', { error: 'WebSocket error', details: error });
            };
        }

        function disconnect() {
            if (socket) {
                socket.close();
                socket = null;
            }
        }

        async function publishLeaderboard() {
            const response = await fetch(`/ws/publish/leaderboard/${eventId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    team_name: 'Neural Ninjas',
                    score: Math.floor(Math.random() * 100),
                    rank: Math.floor(Math.random() * 10) + 1,
                    previous_rank: Math.floor(Math.random() * 10) + 1
                })
            });
            addMessage('publish_result', await response.json());
        }

        async function publishActivity() {
            const activities = [
                { type: 'team_registered', team_name: 'Quantum Commerce', message: 'Team registered for competition' },
                { type: 'recording_started', team_name: 'VectorDB Labs', session_id: 'session_123', message: 'Started pitch recording' },
                { type: 'scoring_completed', team_name: 'Redis Robotics', message: 'AI scoring completed' }
            ];
            
            const activity = activities[Math.floor(Math.random() * activities.length)];
            
            const response = await fetch(`/ws/publish/activity/${eventId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(activity)
            });
            addMessage('publish_result', await response.json());
        }

        async function publishAnnouncement() {
            const announcements = [
                { title: 'Competition Update', message: 'Next team will pitch in 5 minutes', priority: 'normal' },
                { title: 'Technical Issue', message: 'Brief audio delay - please standby', priority: 'high' },
                { title: 'Congratulations', message: 'Excellent pitch from the last team!', priority: 'low' }
            ];
            
            const announcement = announcements[Math.floor(Math.random() * announcements.length)];
            
            const response = await fetch(`/ws/publish/announcement/${eventId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(announcement)
            });
            addMessage('publish_result', await response.json());
        }

        async function getStats() {
            const response = await fetch(`/ws/stats/${eventId}`);
            const stats = await response.json();
            addMessage('stats', stats);
        }

        function clearMessages() {
            document.getElementById('messages').innerHTML = '';
        }

        // Auto-connect on page load
        window.onload = function() {
            connect();
        };
    </script>
</body>
</html>
    """
    return HTMLResponse(html)
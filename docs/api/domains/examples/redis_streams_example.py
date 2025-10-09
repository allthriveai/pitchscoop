#!/usr/bin/env python3
"""
Redis Streams Implementation Example for PitchScoop
Shows how to add real-time features to the competition platform
"""
import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
from typing import Dict, Any, List
import uuid

class PitchScoopStreams:
    """Redis Streams service for real-time competition features"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
    
    # 1. Live Transcription Streaming
    async def stream_transcript_segment(self, session_id: str, segment: Dict[str, Any]):
        """Stream real-time transcript segments"""
        stream_key = f"stream:session:{session_id}:transcript"
        
        await self.redis_client.xadd(stream_key, {
            "segment_id": segment["id"],
            "text": segment["text"],
            "start_time": segment["start_time"],
            "confidence": segment.get("confidence", 1.0),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Set expiration for stream cleanup
        await self.redis_client.expire(stream_key, 86400)  # 24 hours
        print(f"📝 Streamed transcript: {segment['text'][:50]}...")
    
    # 2. Live Leaderboard Updates
    async def stream_leaderboard_update(self, event_id: str, update: Dict[str, Any]):
        """Stream leaderboard changes"""
        stream_key = f"stream:event:{event_id}:leaderboard"
        
        await self.redis_client.xadd(stream_key, {
            "update_id": str(uuid.uuid4()),
            "team_name": update["team_name"],
            "new_score": update["score"],
            "new_rank": update["rank"],
            "previous_rank": update.get("previous_rank", 0),
            "action": "score_update",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        await self.redis_client.expire(stream_key, 86400 * 7)  # 1 week
        print(f"🏆 Streamed leaderboard: {update['team_name']} now rank #{update['rank']}")
    
    # 3. Competition Activity Stream
    async def stream_competition_event(self, event_id: str, activity: Dict[str, Any]):
        """Stream general competition activities"""
        stream_key = f"stream:event:{event_id}:activity"
        
        await self.redis_client.xadd(stream_key, {
            "activity_id": str(uuid.uuid4()),
            "event_type": activity["type"],
            "team_name": activity.get("team_name", ""),
            "session_id": activity.get("session_id", ""),
            "judge_id": activity.get("judge_id", ""),
            "message": activity.get("message", ""),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print(f"🎯 Competition activity: {activity['type']} - {activity.get('message', '')}")
    
    # 4. Judge Coordination Stream
    async def stream_judge_activity(self, event_id: str, judge_action: Dict[str, Any]):
        """Stream judge activities for coordination"""
        stream_key = f"stream:event:{event_id}:judges"
        
        await self.redis_client.xadd(stream_key, {
            "action_id": str(uuid.uuid4()),
            "judge_id": judge_action["judge_id"],
            "action": judge_action["action"],
            "session_id": judge_action.get("session_id", ""),
            "team_name": judge_action.get("team_name", ""),
            "status": judge_action.get("status", "active"),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print(f"👨‍⚖️ Judge {judge_action['judge_id']}: {judge_action['action']}")
    
    # 5. Real-time Stream Consumer
    async def consume_event_streams(self, event_id: str, callback_func):
        """Consumer that listens to all event streams"""
        streams = {
            f"stream:event:{event_id}:leaderboard": "$",
            f"stream:event:{event_id}:activity": "$", 
            f"stream:event:{event_id}:judges": "$"
        }
        
        print(f"🎧 Listening to streams for event {event_id}...")
        
        while True:
            try:
                # Read from multiple streams with blocking
                messages = await self.redis_client.xread(
                    streams, 
                    count=10, 
                    block=1000  # Block for 1 second
                )
                
                for stream, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        # Process each message
                        await callback_func(stream, message_id, fields)
                        
                        # Update stream position for next read
                        streams[stream] = message_id
                        
            except Exception as e:
                print(f"Stream consumer error: {e}")
                await asyncio.sleep(1)
    
    # 6. Session-specific transcript consumer
    async def consume_transcript_stream(self, session_id: str, callback_func):
        """Listen to real-time transcripts for a specific session"""
        stream_key = f"stream:session:{session_id}:transcript"
        
        # Start from the latest message
        last_id = "$"
        
        print(f"📻 Listening to transcript stream for session {session_id}...")
        
        while True:
            try:
                messages = await self.redis_client.xread(
                    {stream_key: last_id},
                    count=1,
                    block=2000  # Block for 2 seconds
                )
                
                for stream, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        await callback_func(fields)
                        last_id = message_id
                        
            except Exception as e:
                print(f"Transcript stream error: {e}")
                break

# Demo functions for testing
async def handle_competition_update(stream_name: str, message_id: str, fields: Dict[str, str]):
    """Handle incoming competition updates"""
    if "leaderboard" in stream_name:
        print(f"🏆 LEADERBOARD UPDATE: {fields.get('team_name')} → Rank #{fields.get('new_rank')}")
    elif "activity" in stream_name:
        print(f"📢 ACTIVITY: {fields.get('event_type')} - {fields.get('message')}")
    elif "judges" in stream_name:
        print(f"👨‍⚖️ JUDGE: {fields.get('judge_id')} {fields.get('action')}")

async def handle_transcript_update(fields: Dict[str, str]):
    """Handle real-time transcript updates"""
    print(f"📝 LIVE TRANSCRIPT: {fields.get('text')} (confidence: {fields.get('confidence')})")

async def demo_streams():
    """Demo the Redis Streams functionality"""
    streams = PitchScoopStreams()
    event_id = "mcp-hackathon-demo"
    
    print("🚀 Starting PitchScoop Redis Streams Demo\n")
    
    # Simulate some competition activities
    activities = [
        {
            "type": "team_registered",
            "team_name": "Neural Ninjas",
            "message": "Team Neural Ninjas joined the competition"
        },
        {
            "type": "recording_started", 
            "team_name": "Neural Ninjas",
            "session_id": "session_001",
            "message": "Neural Ninjas started their pitch"
        },
        {
            "type": "recording_completed",
            "team_name": "Neural Ninjas", 
            "session_id": "session_001",
            "message": "Neural Ninjas completed their 3-minute pitch"
        }
    ]
    
    # Stream the activities
    for activity in activities:
        await streams.stream_competition_event(event_id, activity)
        await asyncio.sleep(0.5)
    
    # Simulate leaderboard updates
    leaderboard_updates = [
        {"team_name": "Neural Ninjas", "score": 94.5, "rank": 1, "previous_rank": 0},
        {"team_name": "Quantum Commerce", "score": 92.1, "rank": 2, "previous_rank": 0},
        {"team_name": "VectorDB Labs", "score": 89.7, "rank": 3, "previous_rank": 0}
    ]
    
    for update in leaderboard_updates:
        await streams.stream_leaderboard_update(event_id, update)
        await asyncio.sleep(0.5)
    
    # Simulate judge activities
    judge_actions = [
        {"judge_id": "judge_001", "action": "started_scoring", "session_id": "session_001", "team_name": "Neural Ninjas"},
        {"judge_id": "judge_001", "action": "completed_scoring", "session_id": "session_001", "team_name": "Neural Ninjas"}
    ]
    
    for action in judge_actions:
        await streams.stream_judge_activity(event_id, action)
        await asyncio.sleep(0.5)
    
    # Simulate transcript updates
    transcript_segments = [
        {"id": "seg_001", "text": "Hi everyone, I'm excited to present Neural Ninjas.", "start_time": 0.0, "confidence": 0.95},
        {"id": "seg_002", "text": "We've built an AI agent that revolutionizes document processing.", "start_time": 3.2, "confidence": 0.92},
        {"id": "seg_003", "text": "Our solution integrates with Redis, OpenAI, and MinIO seamlessly.", "start_time": 7.1, "confidence": 0.88}
    ]
    
    session_id = "session_001"
    for segment in transcript_segments:
        await streams.stream_transcript_segment(session_id, segment)
        await asyncio.sleep(0.5)
    
    print("\n✅ Demo completed! In a real implementation:")
    print("   • Frontend would subscribe to these streams via WebSockets")
    print("   • Real-time UI updates would happen automatically")
    print("   • Multiple judges could coordinate through streams")
    print("   • Audience screens would show live competition updates")

async def demo_stream_consumer():
    """Demo consuming streams in real-time"""
    streams = PitchScoopStreams()
    event_id = "mcp-hackathon-demo"
    
    print("🎧 Starting stream consumer demo...")
    print("   This would run continuously to handle real-time updates")
    
    # In a real app, this would run as a background task
    # For demo, we'll just show the concept
    try:
        await asyncio.wait_for(
            streams.consume_event_streams(event_id, handle_competition_update),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        print("📻 Consumer demo completed (timeout reached)")

if __name__ == "__main__":
    async def main():
        print("🎮 Choose demo:")
        print("1. Stream producer demo")
        print("2. Stream consumer demo") 
        
        try:
            await demo_streams()
            print("\n" + "="*50)
            await demo_stream_consumer()
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            print("Make sure Redis is running: docker run -d -p 6379:6379 redis:latest")
    
    asyncio.run(main())
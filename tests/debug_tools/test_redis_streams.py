#!/usr/bin/env python3
"""
Test Redis Streams publishing for recording events.

This script can be used to:
1. Start a consumer that listens for recording events
2. Test that recording events are being published correctly
3. Debug Redis Streams integration

Usage:
    python test_redis_streams.py --mode consumer  # Listen for events
    python test_redis_streams.py --mode test      # Test recording with events monitoring
"""
import asyncio
import sys
import os
import json
import redis.asyncio as redis
from datetime import datetime, timezone
import argparse

# Setup dynamic imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tests.utils.path_utils import setup_imports
setup_imports()

from api.domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler


async def consume_recording_events(redis_client, stream_name="recording_events", consumer_group="test_group", consumer_name="test_consumer"):
    """
    Consume recording events from Redis Streams
    """
    print(f"🔄 Starting consumer for stream: {stream_name}")
    print(f"   Consumer group: {consumer_group}")
    print(f"   Consumer name: {consumer_name}")
    print("-" * 60)
    
    try:
        # Try to create the consumer group (will fail if it already exists, which is fine)
        try:
            await redis_client.xgroup_create(stream_name, consumer_group, id="0", mkstream=True)
            print(f"✅ Created consumer group: {consumer_group}")
        except redis.RedisError as e:
            if "BUSYGROUP" in str(e):
                print(f"ℹ️  Consumer group already exists: {consumer_group}")
            else:
                print(f"⚠️  Error creating consumer group: {e}")
        
        # Consume messages
        print(f"\n👂 Listening for recording events...")
        print("   Press Ctrl+C to stop\n")
        
        while True:
            try:
                # Read from stream with consumer group
                messages = await redis_client.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream_name: ">"},  # ">" means only new messages
                    count=1,
                    block=1000  # Block for 1 second
                )
                
                if messages:
                    for stream, msgs in messages:
                        for msg_id, fields in msgs:
                            # Parse the event
                            event = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v 
                                   for k, v in fields.items()}
                            
                            # Pretty print the event
                            event_type = event.get('event_type', 'unknown')
                            session_id = event.get('session_id', 'N/A')
                            team_name = event.get('team_name', 'N/A')
                            timestamp = event.get('timestamp', 'N/A')
                            
                            print(f"📨 {event_type.upper()}")
                            print(f"   🕒 {timestamp}")
                            print(f"   🆔 Session: {session_id[:8]}...")
                            print(f"   👥 Team: {team_name}")
                            
                            if event_type == 'recording_started':
                                print(f"   🎤 Pitch: {event.get('pitch_title', 'N/A')}")
                                print(f"   📅 Event: {event.get('event_id', 'N/A')}")
                            elif event_type == 'recording_completed':
                                print(f"   🎤 Pitch: {event.get('pitch_title', 'N/A')}")
                                print(f"   ⏱️  Duration: {event.get('duration_seconds', 'N/A')}s")
                                print(f"   📝 Has transcript: {event.get('has_transcript', False)}")
                                print(f"   🎵 Has audio: {event.get('has_audio', False)}")
                                print(f"   📊 Segments: {event.get('segments_count', 0)}")
                            
                            print(f"   🔗 Stream: {stream.decode()}")
                            print(f"   🏷️  Message ID: {msg_id.decode()}")
                            print("-" * 60)
                            
                            # Acknowledge the message
                            await redis_client.xack(stream_name, consumer_group, msg_id)
                            
            except redis.RedisError as e:
                print(f"❌ Redis error: {e}")
                await asyncio.sleep(1)
                continue
            except KeyboardInterrupt:
                print("\n👋 Stopping consumer...")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                await asyncio.sleep(1)
                continue
                
    except Exception as e:
        print(f"❌ Failed to start consumer: {e}")


async def test_recording_with_monitoring():
    """
    Test a recording session while monitoring Redis Streams
    """
    print("🧪 Testing recording with Redis Streams monitoring")
    print("=" * 60)
    
    # Start the consumer in the background
    redis_client = redis.from_url('redis://localhost:6379/0', decode_responses=True)
    
    # Start consumer task
    consumer_task = asyncio.create_task(
        consume_recording_events(redis_client, consumer_name="test_monitor")
    )
    
    # Wait a moment for consumer to start
    await asyncio.sleep(1)
    
    try:
        print("\n🎬 Starting recording test...")
        
        # Test the recording flow
        handler = GladiaMCPHandler()
        
        # Step 1: Start recording
        print("1️⃣ Starting recording session...")
        session = await handler.start_pitch_recording(
            team_name='Redis Streams Test Team',
            pitch_title='Testing Redis Streams Integration',
            event_id='redis-streams-test'
        )
        
        if 'error' in session:
            print(f'❌ Failed to start session: {session["error"]}')
            return
        
        session_id = session['session_id']
        print(f'✅ Session started: {session_id}')
        
        # Wait a moment to see the stream event
        await asyncio.sleep(2)
        
        # Step 2: Generate test audio and stop recording
        print("2️⃣ Generating test audio and stopping recording...")
        
        # Generate simple test audio
        import base64
        import struct
        import math
        
        def generate_test_audio(duration=2.0, sample_rate=16000):
            samples = []
            for i in range(int(sample_rate * duration)):
                t = i / sample_rate
                frequency = 440  # A4 note
                amplitude = 0.3
                sample = int(16383 * amplitude * math.sin(2 * math.pi * frequency * t))
                samples.append(struct.pack('<h', sample))
            return b''.join(samples)
        
        audio_data = generate_test_audio(3.0)  # 3 seconds
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Stop recording
        result = await handler.stop_pitch_recording(
            session_id=session_id,
            audio_data_base64=audio_b64
        )
        
        if 'error' in result:
            print(f'❌ Failed to stop session: {result["error"]}')
        else:
            print(f'✅ Recording completed: {result.get("status", "unknown")}')
            print(f'   Transcript segments: {result.get("transcript", {}).get("segments_count", 0)}')
            print(f'   Has audio: {result.get("audio", {}).get("has_audio", False)}')
        
        # Wait to see the completion event
        print("\n⏳ Waiting for completion event...")
        await asyncio.sleep(3)
        
        print("\n🎉 Test completed! Check the events above.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        # Cancel the consumer
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        
        await redis_client.close()


async def main():
    parser = argparse.ArgumentParser(description='Test Redis Streams for recording events')
    parser.add_argument('--mode', choices=['consumer', 'test'], default='test',
                       help='Mode: consumer (listen for events) or test (run recording test)')
    parser.add_argument('--stream', default='recording_events',
                       help='Stream name to consume from')
    parser.add_argument('--group', default='test_group',
                       help='Consumer group name')
    parser.add_argument('--consumer', default='test_consumer',
                       help='Consumer name')
    
    args = parser.parse_args()
    
    if args.mode == 'consumer':
        redis_client = redis.from_url('redis://localhost:6379/0', decode_responses=True)
        try:
            await consume_recording_events(
                redis_client, 
                stream_name=args.stream,
                consumer_group=args.group,
                consumer_name=args.consumer
            )
        finally:
            await redis_client.close()
    
    elif args.mode == 'test':
        await test_recording_with_monitoring()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
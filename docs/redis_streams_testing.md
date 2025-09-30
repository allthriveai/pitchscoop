# Redis Streams Testing Guide

## Overview

This guide shows how to test the Redis Streams implementation that publishes recording events in real-time.

## Fixed: No More Hardcoded Paths

**Problem**: Test files had hardcoded paths like `/Users/allierays/Sites/pitchscoop` which made them non-portable.

**Solution**: Created a dynamic path resolution system in `tests/utils/path_utils.py`.

### How to Use in Test Files

**Old way (❌ Don't do this):**
```python
sys.path.insert(0, '/Users/allierays/Sites/pitchscoop')
sys.path.insert(0, '/Users/allierays/Sites/pitchscoop/api')
```

**New way (✅ Portable):**
```python
import os
import sys

# Add project root to path dynamically
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tests.utils.path_utils import setup_imports
setup_imports()

# Now you can import from api
from api.domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler
```

## Redis Streams Testing

### 1. Test Redis Streams Basic Functionality

First, verify Redis Streams are working:

```bash
cd /path/to/pitchscoop
python tests/utils/test_path_utils.py
```

**Expected output:**
```
🧪 Testing Path Utilities
========================================
✅ Project root found: /path/to/pitchscoop
✅ Found expected file: docker-compose.yml
✅ Found expected file: README.md
✅ Import paths setup successfully
✅ Successfully imported from api module
✅ API directory contains expected files

🎉 All path utility tests passed!
```

### 2. Test Redis Streams Consumer

Start a consumer to listen for recording events:

```bash
python tests/debug_tools/test_redis_streams.py --mode consumer
```

**Expected output:**
```
🔄 Starting consumer for stream: recording_events
   Consumer group: test_group
   Consumer name: test_consumer
------------------------------------------------------------
✅ Created consumer group: test_group

👂 Listening for recording events...
   Press Ctrl+C to stop
```

### 3. Test Complete Recording Flow with Streams

In another terminal, test the recording workflow:

```bash
python tests/debug_tools/test_redis_streams.py --mode test
```

This will:
1. Start a background consumer
2. Create a recording session (publishes `recording_started` event)
3. Generate test audio and stop recording (publishes `recording_completed` event)
4. Show events in real-time

## Redis Streams Implementation Details

### Events Published

The implementation publishes two types of events:

#### 1. Recording Started
```json
{
  "event_type": "recording_started",
  "session_id": "uuid-string", 
  "event_id": "event-id",
  "team_name": "Team Name",
  "pitch_title": "Pitch Title",
  "timestamp": "2024-01-01T10:00:00Z",
  "status": "ready_to_record"
}
```

#### 2. Recording Completed  
```json
{
  "event_type": "recording_completed",
  "session_id": "uuid-string",
  "event_id": "event-id", 
  "team_name": "Team Name",
  "pitch_title": "Pitch Title",
  "timestamp": "2024-01-01T10:05:00Z",
  "status": "completed",
  "has_transcript": true,
  "has_audio": true,
  "duration_seconds": 180.5,
  "segments_count": 8
}
```

### Streams Used

1. **`recording_events`** - Global stream for all recording events
2. **`event:{event_id}:recording_events`** - Event-specific streams

### Code Integration

Events are published in the `gladia_mcp_handler.py`:

- **Start recording**: Lines ~250-270 in `start_pitch_recording()`
- **Stop recording**: Lines ~660-690 in `stop_pitch_recording()`

Both methods use:
```python
await redis_client.xadd("recording_events", stream_event)
await redis_client.xadd(f"event:{event_id}:recording_events", stream_event)
```

### Error Handling

- Stream publishing failures are logged as warnings
- Main recording operations continue even if streams fail
- This ensures robustness - recordings work even if streams are down

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're using the new path utilities
2. **Redis not running**: Start with `docker-compose up -d redis`
3. **No events showing**: Check Redis connection and stream names
4. **Path errors**: Use `tests/utils/path_utils.py` for dynamic paths

### Debug Commands

```bash
# Check Redis is running
docker-compose exec redis redis-cli ping

# List all streams
docker-compose exec redis redis-cli --scan --pattern "*recording_events*"

# View recent events
docker-compose exec redis redis-cli XREAD STREAMS recording_events 0-0

# Check consumer groups
docker-compose exec redis redis-cli XINFO GROUPS recording_events
```

## Benefits

### 1. Real-Time Monitoring
- Dashboard can show live recording activity
- Administrators can see who's recording when
- Analytics on recording patterns

### 2. Event-Driven Architecture
- Other services can react to recording events
- Automatic notifications when recordings complete
- Trigger downstream processing

### 3. Multi-Tenant Support
- Event-specific streams ensure data isolation
- Each competition gets its own event stream
- No cross-contamination between events

### 4. Scalable Processing
- Consumer groups enable horizontal scaling
- Multiple consumers can process events in parallel
- Built-in load balancing and acknowledgment

## Next Steps

1. **Implement Dashboard**: Create a web dashboard that consumes these streams
2. **Add More Events**: Consider adding progress events during recording
3. **Webhooks**: Convert stream events to webhook calls for external integration
4. **Analytics**: Use stream data for usage analytics and reporting
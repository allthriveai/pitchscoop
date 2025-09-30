# Redis Streams Implementation for PitchScoop

This document describes the Redis Streams implementation for real-time recording event streaming in PitchScoop.

## Overview

Redis Streams have been integrated into the recording workflow to provide real-time event notifications for:

- Recording session starts
- Recording session completions
- Event-specific activity monitoring
- Real-time analytics and dashboards

## Implementation Details

### Streams Used

1. **`recording_events`** - Global stream for all recording events
2. **`event:{event_id}:recording_events`** - Event-specific streams for multi-tenant isolation

### Event Types

#### `recording_started`
Published when a new recording session begins.

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

#### `recording_completed`
Published when a recording session finishes.

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

## Code Integration

### Publishing Events

Events are published in two key locations:

1. **Recording Start** - In `start_pitch_recording()` method
2. **Recording Completion** - In `stop_pitch_recording()` method

Both methods publish to:
- Global stream: `recording_events`
- Event-specific stream: `event:{event_id}:recording_events`

### Error Handling

- Stream publishing failures are logged as warnings but don't fail the main operations
- This ensures recording functionality remains robust even if streams are unavailable

## Testing

### Test Consumer

Use the provided test script to verify streams are working:

```bash
# Listen for all recording events
python tests/debug_tools/test_redis_streams.py --mode consumer

# Run a complete recording test with monitoring
python tests/debug_tools/test_redis_streams.py --mode test

# Listen to event-specific stream
python tests/debug_tools/test_redis_streams.py --mode consumer --stream "event:your-event-id:recording_events"
```

### Manual Testing

1. Start the consumer in one terminal:
```bash
python tests/debug_tools/test_redis_streams.py --mode consumer
```

2. Run a recording test in another terminal:
```bash
python tests/debug_tools/test_redis_streams.py --mode test
```

You should see events being published and consumed in real-time.

## Use Cases

### Real-Time Dashboard Updates
Consumer applications can listen to streams and update dashboards with:
- Active recording sessions
- Completion statistics
- Team activity monitoring

### Analytics and Monitoring
- Track recording patterns
- Monitor system health
- Generate usage statistics

### Event-Driven Architecture
- Trigger automatic scoring after recording completion
- Send notifications to team members
- Update leaderboards in real-time

### Multi-Tenant Support
Event-specific streams ensure proper data isolation:
- Each event gets its own stream
- Consumers can subscribe to specific events
- No data leakage between different events/organizations

## Redis Configuration

Ensure Redis is configured to handle streams:

```redis
# Optional: Set maximum stream length to prevent unbounded growth
XADD recording_events MAXLEN ~ 10000 * field value

# Consumer groups will be created automatically
```

## Performance Considerations

- Streams are lightweight and designed for high throughput
- Events are published asynchronously to avoid blocking recording operations
- Consider setting up stream trimming for production environments
- Monitor Redis memory usage in high-volume scenarios

## Future Enhancements

Potential future additions:
- Audio processing progress events
- Transcription quality events  
- System health events
- Integration with external webhooks
- Stream-based retry mechanisms

## Error Recovery

If Redis streams are temporarily unavailable:
- Recording operations continue normally
- Events are logged for debugging
- Manual event republishing could be implemented if needed
- No data loss in the main recording workflow
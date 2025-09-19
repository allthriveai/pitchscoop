# PitchScoop Storage Strategy

## 🎯 What We Need to Store

### 1. **Audio Files** 
- Raw recorded audio (potentially large, 1-10MB per pitch)
- Optional: processed/compressed versions
- Need: Fast upload, reliable storage, playback capability

### 2. **Transcripts**
- Raw transcript segments from Gladia
- Final transcript collections
- Need: Fast search, frequent access

### 3. **Session Metadata**
- STT session details, status, timestamps
- Team information, event data
- Need: Fast read/write, session management

### 4. **Scores & Feedback**
- Generated scores and feedback reports
- Need: Fast retrieval, structured queries

## 🏗️ Storage Options Analysis

### **Option 1: MinIO (Recommended for Audio)**
| Aspect | Details |
|--------|---------|
| **Best for** | Audio files, large binary data |
| **Pros** | ✅ S3-compatible, optimized for files<br/>✅ Built-in versioning<br/>✅ Presigned URLs for direct access<br/>✅ Perfect for audio playback<br/>✅ Handles large files efficiently |
| **Cons** | ❌ Not ideal for structured data<br/>❌ No built-in search<br/>❌ Requires separate service |
| **Use Case** | Store `.wav`, `.mp3` audio files |

### **Option 2: Redis (Recommended for Cache + Sessions)**
| Aspect | Details |
|--------|---------|
| **Best for** | Session data, real-time data, caching |
| **Pros** | ✅ Extremely fast read/write<br/>✅ Already running<br/>✅ Perfect for session management<br/>✅ TTL for cleanup<br/>✅ Pub/Sub for real-time updates |
| **Cons** | ❌ Memory-based (expensive for large data)<br/>❌ Not ideal for permanent storage<br/>❌ Size limitations |
| **Use Case** | Active sessions, temporary data, real-time status |

### **Option 3: PostgreSQL (Recommended for Structured Data)**
| Aspect | Details |
|--------|---------|
| **Best for** | Structured data, relationships, queries |
| **Pros** | ✅ ACID transactions<br/>✅ Complex queries<br/>✅ JSON support for flexible schemas<br/>✅ Full-text search<br/>✅ Reliable persistence |
| **Cons** | ❌ Requires setup<br/>❌ Not optimal for binary data<br/>❌ Slower than Redis |
| **Use Case** | Transcripts, scores, teams, events |

## 🎯 **Recommended Hybrid Approach**

### **Data Distribution Strategy:**

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    MinIO    │    │    Redis    │    │ PostgreSQL  │
│  (Files)    │    │  (Cache)    │    │ (Structured)│
└─────────────┘    └─────────────┘    └─────────────┘
      │                    │                    │
      ▼                    ▼                    ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Audio Files  │    │Live Sessions│    │Transcripts  │
│• .wav/.mp3  │    │• STT Status │    │• Final Text │
│• Recordings │    │• Real-time  │    │• Metadata   │
│• Playback   │    │• WebSocket  │    │• Search     │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 **Phase 1: Start Simple (Current Implementation)**

### **For MVP - Use Redis + Local Storage**
```python
# Store in Redis with TTL
session_data = {
    "session_id": "session_123",
    "status": "recording",
    "transcript_segments": [...],
    "audio_file_path": "/tmp/audio/session_123.wav",  # Local file
    "metadata": {...}
}

redis.setex(f"session:{session_id}", 3600, json.dumps(session_data))
```

**Benefits:**
- ✅ Simple to implement
- ✅ Fast development 
- ✅ Uses existing Redis
- ✅ Easy to test

**Limitations:**
- ❌ Audio files not persistent
- ❌ Memory usage for large transcripts
- ❌ No advanced querying

## 🔄 **Phase 2: Add MinIO for Audio Storage**

### **Enhanced Architecture**
```python
# Store audio in MinIO
audio_url = await minio_client.upload_audio(audio_data, f"{session_id}.wav")

# Store metadata in Redis
session_data = {
    "session_id": "session_123",
    "status": "completed",
    "audio_url": audio_url,  # MinIO URL
    "transcript_segments": [...],
    "metadata": {...}
}
```

**Benefits:**
- ✅ Persistent audio storage
- ✅ Direct audio playback URLs
- ✅ Scalable file handling

## 📊 **Specific Storage Decisions**

### **Audio Files → MinIO**
```python
# Upload after recording completes
audio_key = f"sessions/{session_id}/recording.wav"
minio_url = await minio_client.put_object(audio_key, audio_data)

# Generate presigned URL for playback
playback_url = minio_client.presigned_get_object(audio_key, expires_in=3600)
```

### **Transcripts → Redis (immediate) → PostgreSQL (permanent)**
```python
# Real-time: Store in Redis
await redis.lpush(f"transcript:{session_id}", transcript_segment)

# Final: Move to PostgreSQL
await db.execute(
    "INSERT INTO transcripts (session_id, segments, full_text) VALUES ($1, $2, $3)",
    session_id, segments_json, full_text
)
```

### **Session State → Redis**
```python
# Active session tracking
await redis.hset(f"session:{session_id}", {
    "status": "recording",
    "team_name": "Team Alpha", 
    "started_at": timestamp,
    "gladia_session_id": gladia_id
})
```

## 🎪 **For Competition Context**

### **What we need for Record → Score → Leaderboard → Feedback:**

1. **During Recording (Redis)**
   - Session status and metadata
   - Real-time transcript segments
   - WebSocket connection tracking

2. **After Recording (MinIO + Redis)**
   - Audio file stored in MinIO
   - Final transcript in Redis for fast access
   - Session marked as "ready for scoring"

3. **For Scoring (Redis)**
   - Fast transcript access for AI analysis
   - Score results cached for leaderboard

4. **For Playback (MinIO)**
   - Direct audio URLs for team pages
   - Presigned URLs for secure access

## 🚀 **Implementation Recommendation**

**For MVP (Phase 1):** Start with **Redis-only** approach
- Fast to implement
- Covers all basic functionality
- Easy to test
- Can always migrate data later

**When to add MinIO:** When you need:
- Audio playback functionality
- Persistent audio storage
- File size > 1MB consistently

**When to add PostgreSQL:** When you need:
- Complex queries across sessions
- Full-text search in transcripts
- Multi-event competition management

## 💡 **Immediate Decision**

For our current **Gladia MCP implementation**, I recommend:

**Start with Redis** for everything:
- Session metadata
- Transcript segments  
- Audio file paths (store locally in container)

This lets us build and test the complete MCP flow quickly, then optimize storage later.

Should we proceed with **Redis-first approach** for the Gladia MCP tools?
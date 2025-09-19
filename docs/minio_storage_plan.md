# MinIO + Redis Storage Architecture for PitchScoop

## 🎯 Storage Decision: MinIO + Redis from Day 1

Since we need **audio playback on the website**, let's implement the proper storage architecture immediately:

- **MinIO** → Audio files (`.wav`, `.mp3`) with direct playback URLs
- **Redis** → Session state, metadata, cached transcripts

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│      MinIO      │    │      Redis      │
│   (Audio Files) │    │  (Session Data) │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│• session_123.wav│    │session:123      │
│• session_124.mp3│    │• status         │
│• Direct URLs    │    │• metadata       │  
│• Presigned URLs │    │• transcript     │
└─────────────────┘    └─────────────────┘
```

## 🐳 Docker Compose Setup

Let's add MinIO to our docker-compose.yml:

```yaml
version: '3.8'

services:
  api:
    build: ./api
    ports:
      - "8000:8000"
    volumes:
      - ./api:/app
    environment:
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=pitchscoop
      - MINIO_SECRET_KEY=pitchscoop123
    depends_on:
      - redis
      - minio
    networks:
      - hackathon-net

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    networks:
      - hackathon-net

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"      # API
      - "9001:9001"      # Console
    environment:
      - MINIO_ACCESS_KEY=pitchscoop
      - MINIO_SECRET_KEY=pitchscoop123
    volumes:
      - minio-data:/data
    command: server /data --console-address ":9001"
    networks:
      - hackathon-net

volumes:
  redis-data:
  minio-data:

networks:
  hackathon-net:
    driver: bridge
```

## 📊 Data Storage Strategy

### **Audio Files → MinIO**
```python
# File paths in MinIO
"sessions/{session_id}/recording.wav"     # Original recording
"sessions/{session_id}/compressed.mp3"   # Compressed for web
"sessions/{team_name}/{timestamp}.wav"   # Organized by team
```

### **Session Data → Redis**
```python
# Redis keys
"session:{session_id}" = {
    "status": "completed",
    "team_name": "Team Alpha", 
    "audio_minio_key": "sessions/123/recording.wav",
    "audio_playback_url": "http://localhost:9000/pitchscoop/sessions/123/recording.wav",
    "transcript": {...},
    "metadata": {...}
}
```

## 🎵 Audio Playback Flow

### **1. Recording Complete**
```python
# Upload to MinIO
minio_key = f"sessions/{session_id}/recording.wav"
await minio_client.put_object("pitchscoop", minio_key, audio_data)

# Store reference in Redis
session_data = {
    "audio_minio_key": minio_key,
    "audio_size": len(audio_data),
    "has_audio": True
}
await redis.hset(f"session:{session_id}", session_data)
```

### **2. Website Playback**
```python
# MCP Tool: Get playback URL
@mcp_tool("pitches.get_playback_url")
async def get_playback_url(session_id: str) -> dict:
    # Generate presigned URL (secure, expires in 1 hour)
    playback_url = minio_client.presigned_get_object(
        bucket_name="pitchscoop",
        object_name=f"sessions/{session_id}/recording.wav",
        expires=timedelta(hours=1)
    )
    return {"playback_url": playback_url, "expires_in": 3600}
```

### **3. Frontend HTML5 Audio**
```html
<!-- Team page audio player -->
<audio controls>
    <source src="{presigned_url}" type="audio/wav">
    Your browser does not support audio playback.
</audio>
```

## 🔧 Implementation Steps

### **Step 1: Add MinIO to Docker Compose**
- Update docker-compose.yml
- Add MinIO service with persistent storage
- Add environment variables for API

### **Step 2: Add MinIO Client**
```bash
# Add to requirements.txt
minio==7.2.7
```

### **Step 3: Create MinIO Service**
```python
# app/domains/gladia/infrastructure/minio_client.py
class MinIOAudioStorage:
    async def upload_audio(self, session_id: str, audio_data: bytes) -> str
    async def get_playback_url(self, session_id: str) -> str
    async def delete_audio(self, session_id: str) -> bool
```

### **Step 4: Update Gladia MCP Tools**
- Store audio in MinIO after recording
- Return playback URLs in session data
- Add playback URL generation tool

## 🎪 MCP Tools with Audio Playback

### **Enhanced MCP Tools:**

```python
@mcp_tool("pitches.start_recording")
async def start_recording(team_name: str, pitch_title: str) -> dict:
    # Creates session, starts Gladia STT
    # Returns session_id and WebSocket info
    
@mcp_tool("pitches.stop_recording") 
async def stop_recording(session_id: str, audio_data: bytes) -> dict:
    # 1. Upload audio to MinIO
    # 2. Finalize transcript in Redis  
    # 3. Return session summary with audio URL
    
@mcp_tool("pitches.get_session_details")
async def get_session_details(session_id: str) -> dict:
    # Returns: transcript, metadata, AND audio playback URL
    
@mcp_tool("pitches.get_playback_url")
async def get_playback_url(session_id: str) -> dict:
    # Returns presigned MinIO URL for audio playback
```

## 📱 Website Integration

### **Team Pages**
- Show pitch transcript
- **Audio player with recorded pitch**
- Download option (if permitted)

### **Organizer Dashboard**
- List all sessions with audio indicators
- **Bulk audio playback for review**
- Export options

### **Leaderboard**
- Rankings with **"Listen"** buttons
- Audio previews of top performances

## 🚀 **Implementation Plan**

1. **Add MinIO to docker-compose** ✨
2. **Create MinIO client service** 
3. **Update Gladia MCP tools** with audio storage
4. **Test audio recording → storage → playback** flow
5. **Build other domains** (Score, Leaderboard, Feedback)

This gives us **full audio capability** from the start, making the website much more engaging for competition participants.

Should I proceed with adding MinIO to the docker-compose and implementing the audio storage?
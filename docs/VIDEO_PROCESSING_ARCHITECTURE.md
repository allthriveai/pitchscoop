# Video Processing Architecture: Hume AI Integration

## 🎬 Overview

PitchScoop now uses **Hume AI** for video-based emotion and expression analysis instead of audio-only processing. This provides richer insights into presentation delivery through facial expressions, emotional states, and engagement levels.

## 🏗️ Architecture Components

### **Core Integration Layer**
```
📁 api/domains/recordings/repositories/
├── hume_api_repository.py          # Hume AI API client
├── stt_provider_factory.py         # Updated for video processing
└── (removed: gladia_api_repository.py)
```

### **Data Flow**
```
🎥 Video Upload → 🤖 Hume AI Processing → 📊 Emotion Analysis → 🎯 Scoring
```

## 🔧 Technical Implementation

### **1. Hume API Repository**
- **Real Mode**: Actual API calls to Hume AI
- **Mock Mode**: Simulated responses for testing without API keys
- **Async Operations**: Non-blocking video processing
- **Error Handling**: Robust timeout and retry logic

### **2. Video Processing Workflow**
1. **Upload**: Video file sent to Hume AI via multipart form data
2. **Processing**: Hume analyzes facial expressions and emotions
3. **Polling**: Status checks until analysis completes
4. **Results**: Emotion data returned with confidence scores

### **3. Emotion Data Structure**
```json
{
  "expressions": [
    {
      "time": 1.0,
      "confidence": 0.88,
      "joy": 0.75,
      "surprise": 0.25,
      "fear": 0.08,
      "anger": 0.03,
      "sadness": 0.12,
      "disgust": 0.04,
      "contempt": 0.02
    }
  ]
}
```

## 🎯 Key Differences from Audio Processing

| Aspect | Audio (Gladia) | Video (Hume) |
|--------|----------------|--------------|
| **Input** | Audio files (WAV, MP3) | Video files (MP4, MOV) |
| **Analysis** | Speech transcription | Facial emotion analysis |
| **Real-time** | WebSocket streaming | Batch processing |
| **Data Size** | ~1-5MB audio | ~10-50MB video |
| **Processing Time** | 1-10 seconds | 30-120 seconds |
| **Insights** | Speech patterns, WPM | Emotions, engagement, confidence |

## 📈 Benefits for Pitch Analysis

### **Enhanced Coaching Metrics**
- **Emotional Engagement**: Joy, surprise, confidence levels
- **Presentation Anxiety**: Fear, nervousness detection
- **Authenticity**: Natural vs forced expressions
- **Audience Connection**: Emotional resonance scoring

### **Richer Scoring Algorithms**
- Combine transcript content with emotional delivery
- Weight presentation confidence in final scores
- Detect engagement patterns throughout pitch
- Identify improvement opportunities in delivery

## 🧪 Testing & Validation

### **Test Suite: `test_hume_integration.py`**
```bash
cd /Users/allierays/Sites/pitchscoop
python tests/integration/test_hume_integration.py
```

**Test Coverage:**
- ✅ Environment configuration
- ✅ API connectivity
- ✅ Video upload workflow  
- ✅ Complete analysis pipeline
- ✅ Mock mode (no API keys required)

## ⚙️ Configuration

### **Environment Variables**
```bash
# Required for real API calls
HUME_API_KEY=your_hume_api_key_here
HUME_SECRET_KEY=your_hume_secret_key_here

# Optional
VIDEO_PROCESSOR=hume
```

### **API Credentials**
1. Sign up at [https://hume.ai](https://hume.ai)
2. Get API key and secret key
3. Set environment variables
4. Run tests to verify connectivity

## 🚀 Usage Examples

### **Basic Video Analysis**
```python
from api.domains.recordings.repositories.hume_api_repository import get_hume_client

# Get client (real or mock based on environment)
client = get_hume_client()

# Test connectivity
health = await client.health_check()

# Analyze video file
with open('pitch_video.mp4', 'rb') as f:
    video_data = f.read()

result = await client.analyze_video_complete(video_data, 'pitch.mp4')

# Get emotion analysis
expressions = result.get('analysis_results', {}).get('expressions', [])
for expr in expressions:
    time = expr['time']
    joy = expr['joy'] 
    confidence = expr['confidence']
    print(f"Time {time}s: Joy={joy:.3f} (confidence={confidence:.3f})")
```

## 🔄 Migration Status

### ✅ **Completed**
- Hume API repository implementation
- Mock mode for testing without API keys
- Complete test suite
- Environment configuration
- Basic video processing workflow

### 🚧 **Next Steps**
- Integrate with existing MCP tools
- Update video storage in MinIO
- Create emotion-based scoring algorithms
- Build frontend video capture
- Add video intelligence value objects

## 📊 Performance Considerations

### **Video File Sizes**
- Recommended: 10-50MB per pitch (2-5 minutes)
- Maximum: 100MB per file
- Compression: H.264 codec recommended

### **Processing Times**
- Small videos (5MB): ~30 seconds
- Medium videos (20MB): ~60 seconds
- Large videos (50MB): ~120 seconds

### **Rate Limits**
- Monitor Hume API quotas
- Implement queuing for batch processing
- Cache results to avoid reprocessing

## 🎯 Future Enhancements

- **Real-time Analysis**: Explore streaming video analysis
- **Multi-modal**: Combine audio transcription + video emotions
- **Advanced Metrics**: Micro-expressions, engagement patterns
- **Comparative Analysis**: Judge vs presenter emotion correlation

---
*Architecture ready for production deployment with proper API credentials*
# Hume AI Integration Usage Guide

## 🎬 What is Hume AI?

**Hume AI** specializes in emotion detection and expression analysis from video content. For PitchScoop, this means analyzing facial expressions and emotional engagement during pitch presentations to provide deeper insights into presentation delivery.

## 🚀 Quick Start

### 1. **Test Without API Keys (Mock Mode)**
```bash
# Run integration test
python tests/integration/test_hume_integration.py

# Run demo in mock mode
python tests/demo/demo_hume_video_analysis.py --mock
```

### 2. **Get Hume API Credentials**
1. Visit [https://hume.ai](https://hume.ai)
2. Sign up for an account
3. Navigate to your API dashboard
4. Generate API Key and Secret Key

### 3. **Configure Environment**
```bash
# Add to your .env file
HUME_API_KEY=your_actual_api_key_here
HUME_SECRET_KEY=your_actual_secret_key_here
```

### 4. **Test with Real API**
```bash
# Test API connectivity
python tests/integration/test_hume_integration.py

# Analyze a real video file
python tests/demo/demo_hume_video_analysis.py path/to/your/video.mp4
```

## 🎯 How It Works

### **Video Processing Pipeline**
```
📹 Video File → 🔄 Upload to Hume → 🧠 AI Analysis → 📊 Emotion Data → 🎯 Insights
```

### **What Hume Analyzes**
- **Joy**: Happiness, enthusiasm, positive engagement
- **Surprise**: Excitement, curiosity, reaction to content  
- **Fear**: Nervousness, anxiety, uncertainty
- **Anger**: Frustration, intensity, assertiveness
- **Sadness**: Disappointment, low energy, concern
- **Disgust**: Disapproval, skepticism
- **Contempt**: Disdain, superiority

### **Confidence Scores**
Each emotion detection includes a confidence score (0.0 to 1.0) indicating how certain the AI is about the detected emotion.

## 📊 Sample Output

```
📊 Emotion Analysis Results (2 time points):
Time   1.0s: Joy=0.750 Surprise=0.250 Fear=0.080 (confidence=0.880)
Time   2.0s: Joy=0.680 Surprise=0.350 Fear=0.120 (confidence=0.820)

📈 Summary Statistics:
Average Confidence: 0.850
Average Joy: 0.715
Average Surprise: 0.300

💡 Quick Insights:
😊 High joy levels detected - appears to be a positive, engaging presentation
📈 High confidence in emotion detection - reliable results
```

## 🎥 Video Requirements

### **Supported Formats**
- **MP4** (recommended)
- **MOV**
- **AVI** 
- **WebM**

### **Quality Guidelines**
- **Resolution**: 720p or higher recommended
- **Duration**: 30 seconds to 10 minutes optimal
- **File Size**: Under 100MB for faster processing
- **Face Visibility**: Clear view of presenter's face
- **Lighting**: Well-lit environment for better detection

### **Processing Times**
- **Small videos (5MB)**: ~30 seconds
- **Medium videos (20MB)**: ~60 seconds  
- **Large videos (50MB)**: ~120 seconds

## 💻 Code Examples

### **Basic Usage**
```python
from api.domains.recordings.repositories.hume_api_repository import get_hume_client

# Get client (real or mock based on environment)
client = get_hume_client()

# Test API health
health = await client.health_check()
print(f"API Status: {health['status']}")

# Load video file
with open('pitch_video.mp4', 'rb') as f:
    video_data = f.read()

# Analyze video
result = await client.analyze_video_complete(video_data, 'pitch.mp4')

if result['success']:
    expressions = result['analysis_results']['expressions']
    for expr in expressions:
        time = expr['time']
        joy = expr['joy']
        confidence = expr['confidence']
        print(f"Time {time}s: Joy={joy:.3f} (confidence={confidence:.3f})")
```

### **Error Handling**
```python
try:
    result = await client.analyze_video_complete(video_data, filename)
    
    if result['success']:
        # Process results
        expressions = result['analysis_results']['expressions']
        print(f"Analysis complete: {len(expressions)} time points")
    else:
        print(f"Analysis failed: {result['error']}")
        
except Exception as e:
    print(f"Exception during analysis: {str(e)}")
finally:
    await client.close()
```

## 🧪 Testing & Development

### **Integration Tests**
```bash
# Full test suite
python tests/integration/test_hume_integration.py

# Expected output:
🎭 Hume AI Integration Test Suite
⚙️ Testing Environment Configuration
🔍 Testing Hume API Health Check  
🎬 Testing Hume Video Upload
🎯 Testing Complete Hume Video Analysis Workflow
📊 Test Summary
🎉 All tests passed! Hume integration is ready.
```

### **Mock vs Real Mode**
- **Mock Mode**: No API keys needed, simulated responses
- **Real Mode**: Requires valid API keys, actual Hume API calls
- **Automatic**: System chooses mode based on environment variables

### **Demo Script Features**
- File size validation
- Processing time estimation
- Detailed emotion analysis display
- Summary statistics and insights
- Error handling and recovery

## 🔧 Troubleshooting

### **Common Issues**

**❌ "Hume API credentials not configured"**
- Set `HUME_API_KEY` and `HUME_SECRET_KEY` environment variables
- Verify keys are valid and not placeholder values

**❌ "Video file not found"**
- Check file path is correct
- Ensure file exists and is readable
- Try absolute path instead of relative path

**❌ "Analysis timeout"**
- Large video files take longer to process
- Increase timeout for files over 50MB
- Check internet connection stability

**❌ "Upload failed: 413"**
- Video file too large (over 100MB)
- Compress video or reduce quality
- Split long videos into shorter segments

### **Performance Tips**
- Use H.264 encoded MP4 files for best compatibility
- Compress videos to reduce upload time
- Ensure stable internet connection for large files
- Monitor API usage limits and quotas

## 📈 Integration Benefits

### **For Pitch Analysis**
- **Emotion-Based Scoring**: Weight presentation confidence in scores
- **Engagement Detection**: Identify when audience would be most engaged
- **Anxiety Recognition**: Help presenters improve confidence
- **Authenticity Measurement**: Detect genuine vs forced enthusiasm

### **For Coaching**
- **Specific Feedback**: "Increase enthusiasm at 2:30 mark"
- **Confidence Building**: Show improvement over multiple presentations
- **Emotional Patterns**: Identify when presenter feels most/least confident
- **Targeted Practice**: Focus improvement on specific emotional aspects

## 🚧 Current Status

### ✅ **Ready**
- API client implementation
- Mock mode for testing
- Complete test suite
- Error handling and timeouts
- Documentation and examples

### 🚧 **In Development**  
- MCP tool integration
- Video storage in MinIO
- Emotion-based scoring algorithms
- Frontend video capture

---
*Ready to analyze your first pitch video? Start with mock mode and then get your Hume API keys!*
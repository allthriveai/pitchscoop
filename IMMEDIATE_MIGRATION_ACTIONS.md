# Immediate Migration Actions - Hume Integration

## 🚨 CRITICAL: Scoring Domain Must Be Fixed Immediately

The **scoring domain is broken** because it depends heavily on the deleted recordings domain. Here are the immediate actions needed:

## ⚡ **Phase 1: Emergency Fixes (TODAY)**

### 1. **Update Docker Configuration**
```bash
# Edit docker-compose.yml
# Remove these lines:
- STT_PROVIDER=${STT_PROVIDER}
- GLADIA_API_KEY=${GLADIA_API_KEY}
- GLADIA_API_URL=${GLADIA_API_URL}

# Add these lines:
- HUME_API_KEY=${HUME_API_KEY}
- HUME_SECRET_KEY=${HUME_SECRET_KEY}
```

### 2. **Delete Broken Audio Integration Files**
```bash
rm api/domains/scoring/mcp/scoring_mcp_handler_audio_integrated.py
rm api/domains/scoring/mcp/scoring_mcp_tools_audio_integrated.py
rm api/domains/scoring/services/recording_integration.py
```

### 3. **Fix Import Errors in Scoring Domain**
Update these files to remove recordings imports:
- `api/domains/scoring/mcp/scoring_mcp_handler.py`
- `api/domains/scoring/mcp/scoring_mcp_tools.py`

## 🔧 **Phase 2: Integration (THIS WEEK)**

### 1. **Connect Scoring to Pitches Domain**

Create new scoring integration with video intelligence:

```python
# NEW FILE: api/domains/scoring/services/video_intelligence_integration.py
from ...pitches.value_objects.video_intelligence import VideoIntelligence
from ...pitches.services.pitch_analysis_service import PitchAnalysisService

class VideoIntelligenceScorer:
    """Scores pitches using Hume video intelligence instead of transcript."""
    
    async def score_pitch_delivery(self, video_intelligence: VideoIntelligence) -> Dict[str, Any]:
        """Score presentation delivery using emotion analysis."""
        # Replace transcript WPM analysis with confidence scores
        # Replace audio intelligence with facial expression analysis
        # Generate coaching insights from emotional timeline
```

### 2. **Update Scoring MCP Tools**

Replace the broken `analysis.analyze_presentation_delivery` tool:

```python
# In scoring_mcp_tools.py, replace:
"analysis.analyze_presentation_delivery": {
    # OLD: Transcript + Gladia Audio Intelligence 
    # NEW: Video + Hume Emotion Analysis
    "description": "Analyze presentation delivery using Hume AI video analysis",
    # Update schema to expect video intelligence data
}
```

### 3. **Create Scoring Bridge Service**

```python
# NEW FILE: api/domains/scoring/services/pitch_scoring_bridge.py
class PitchScoringBridge:
    """Bridges pitches domain video analysis with scoring domain."""
    
    async def score_pitch_from_video_analysis(self, session_id: str) -> Dict[str, Any]:
        # Get video intelligence from pitches domain
        # Convert to scoring metrics
        # Return comprehensive score
```

## 📋 **Phase 3: Test Updates (NEXT WEEK)**

### 1. **Update MCP Integration Tests**
- Replace recording-based tests with video-based tests
- Update test data to use video intelligence mocks
- Fix broken test imports

### 2. **Update Scoring Tests**
- Replace transcript analysis tests with video analysis tests
- Update mock data structures
- Test new scoring algorithms

## 🎯 **Critical Files to Update Immediately:**

### **HIGH PRIORITY (BROKEN):**
1. `api/main.py` - ✅ **ALREADY FIXED**
2. `api/mcp_server.py` - ✅ **ALREADY FIXED** 
3. `docker-compose.yml` - ⚠️ **NEEDS UPDATE**
4. `api/domains/scoring/mcp/scoring_mcp_handler.py` - ⚠️ **BROKEN IMPORTS**
5. `api/domains/scoring/mcp/scoring_mcp_tools.py` - ⚠️ **BROKEN FUNCTIONALITY**

### **MEDIUM PRIORITY (DEGRADED):**
1. All scoring-related tests
2. MCP integration tests
3. End-to-end flow tests

## 💡 **Recommended Immediate Workflow:**

### **Day 1 (Emergency Stabilization):**
1. ✅ Update docker-compose.yml 
2. ✅ Delete audio integration files
3. ✅ Fix import errors in scoring domain
4. ✅ Create basic video intelligence scoring bridge

### **Day 2-3 (Core Integration):**
1. Implement video-based presentation delivery analysis
2. Update scoring MCP tools to use video intelligence
3. Create pitch-to-scoring integration service
4. Test basic video scoring workflow

### **Day 4-5 (Testing & Validation):**
1. Update critical MCP tests
2. Validate scoring accuracy with video intelligence
3. Test end-to-end pitch → video analysis → score flow
4. Performance testing

## 🚀 **Quick Win: Parallel Approach**

While scoring domain is being refactored, the **pitches domain works independently**:

✅ **Working Right Now:**
- Create pitch sessions
- Upload and analyze videos
- Get emotion analysis results
- Receive coaching insights

🔧 **Needs Integration:**
- Connect video insights to scoring algorithms
- Generate numerical scores from emotion data
- Integrate with leaderboard system

## 📈 **Success Metrics:**

### **Phase 1 Success:**
- Docker containers start without errors
- No broken imports in scoring domain
- Basic video analysis works end-to-end

### **Phase 2 Success:**
- Video intelligence data feeds into scoring
- Presentation delivery scores generated from emotion analysis
- MCP tools return valid scoring results

### **Phase 3 Success:**
- Full end-to-end video pitch scoring workflow
- Test suite passes with video-based tests
- Performance matches or exceeds audio-based system

---

**The migration from Gladia audio to Hume video is a major architectural change, but the modular domain design makes it manageable. The key is to stabilize the scoring domain quickly while building robust video intelligence integration.**
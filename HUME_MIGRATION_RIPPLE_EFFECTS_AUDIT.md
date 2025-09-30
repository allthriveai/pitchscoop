# Hume Migration Ripple Effects Audit

## Executive Summary

Moving from Gladia audio processing to Hume video analysis creates **significant ripple effects** throughout the codebase. This audit identifies all systems that need to be removed, replaced, or updated.

## 🔥 **CRITICAL IMPACT AREAS**

### 1. **SCORING DOMAIN - MAJOR REFACTOR REQUIRED**

The scoring domain is **heavily dependent** on audio/transcript data and requires complete restructuring:

#### **Files Requiring Major Changes:**
- `api/domains/scoring/mcp/scoring_mcp_handler_audio_integrated.py` - **DELETE**
- `api/domains/scoring/mcp/scoring_mcp_tools_audio_integrated.py` - **DELETE** 
- `api/domains/scoring/services/recording_integration.py` - **DELETE**
- `api/domains/scoring/mcp/scoring_mcp_tools.py` - **MAJOR UPDATES NEEDED**
- `api/domains/scoring/mcp/scoring_mcp_handler.py` - **MAJOR UPDATES NEEDED**

#### **Specific Functionality to Replace:**
1. **`analysis.analyze_presentation_delivery`** tool - Currently uses Gladia Audio Intelligence
2. **Transcript-based scoring** - All scoring relies on transcript content analysis
3. **Audio metrics integration** - WPM, filler words, confidence analysis from audio
4. **Recording integration hooks** - Background market intelligence tied to audio recordings

#### **New Video-Based Scoring Architecture Needed:**
```
OLD: Audio Recording → Transcript → AI Analysis → Score
NEW: Video Recording → Hume Emotion Analysis → Presentation Metrics → Score
```

### 2. **ENVIRONMENT & INFRASTRUCTURE**

#### **Docker Configuration Updates:**
- **docker-compose.yml**: Remove lines 23-25 (STT_PROVIDER, GLADIA_API_KEY, GLADIA_API_URL)
- **docker-compose.yml**: Add HUME_API_KEY and HUME_SECRET_KEY environment variables

#### **Environment Variables:**
- **.env.example**: Already updated with Hume configuration ✅
- Remove from production: `STT_PROVIDER`, `GLADIA_API_KEY`, `GLADIA_API_URL`
- Add to production: `HUME_API_KEY`, `HUME_SECRET_KEY`

### 3. **MAJOR DEPENDENCIES TO REMOVE**

#### **Import Dependencies (70+ files affected):**
```python
# REMOVE ALL THESE IMPORTS:
from ...recordings.* 
from domains.recordings.*
from api.domains.recordings.*
```

#### **Services & Handlers to Delete:**
- All Gladia MCP handlers and tools
- STT domain services 
- Audio intelligence value objects
- Recording progression services
- Transcript analysis utilities

## 📋 **DETAILED REMOVAL PLAN**

### **Phase 1: Delete Legacy Audio Files**
```bash
# Already completed - recordings domain deleted ✅
rm -rf api/domains/recordings/
```

### **Phase 2: Update Scoring Domain (HIGH PRIORITY)**

#### **Files to Delete:**
1. `api/domains/scoring/mcp/scoring_mcp_handler_audio_integrated.py`
2. `api/domains/scoring/mcp/scoring_mcp_tools_audio_integrated.py`
3. `api/domains/scoring/services/recording_integration.py`

#### **Files to Update:**

**`api/domains/scoring/mcp/scoring_mcp_tools.py`:**
- Remove `analysis.analyze_presentation_delivery` tool (lines 181-227)
- Replace with video-based presentation analysis
- Update all references to transcript/audio data

**`api/domains/scoring/mcp/scoring_mcp_handler.py`:**
- Remove all Gladia/audio intelligence imports
- Replace transcript analysis with video intelligence
- Update scoring algorithms to use emotion data instead of transcript data

### **Phase 3: Update Tests (90+ files affected)**

#### **Test Categories to Remove/Update:**
1. **Recording flow tests** (12 files) - DELETE or convert to video flow
2. **Audio processing tests** (25 files) - DELETE
3. **Transcript analysis tests** (18 files) - DELETE
4. **MCP integration tests** - UPDATE to use pitch tools
5. **Gladia integration tests** (8 files) - DELETE

#### **Test Files Requiring Updates:**
- `tests/mcp/test_mcp_integration.py` - Update to use pitches MCP tools
- `tests/unit/domains/scoring/` - All scoring tests need video data instead of transcript
- `tests/e2e/` - All end-to-end flows need video upload instead of audio recording

### **Phase 4: Documentation Updates (40+ files)**

#### **Documentation to Update:**
1. **Architecture docs** - Update all references to audio → video
2. **API documentation** - Replace recording endpoints with video upload
3. **MCP tool documentation** - Update tool descriptions and schemas
4. **Setup guides** - Replace Gladia setup with Hume setup
5. **Domain boundaries** - Update recordings → pitches domain mapping

### **Phase 5: Infrastructure & Configuration**

#### **Docker Updates:**
```yaml
# Remove from docker-compose.yml:
- STT_PROVIDER=${STT_PROVIDER}
- GLADIA_API_KEY=${GLADIA_API_KEY}  
- GLADIA_API_URL=${GLADIA_API_URL}

# Add to docker-compose.yml:
- HUME_API_KEY=${HUME_API_KEY}
- HUME_SECRET_KEY=${HUME_SECRET_KEY}
```

## 🔄 **REPLACEMENT STRATEGY**

### **1. Data Flow Transformation**

**OLD Audio-Based Flow:**
```
Microphone → Audio Recording → STT → Transcript → AI Analysis → Score
```

**NEW Video-Based Flow:**
```
Camera → Video Recording → Hume AI → Emotion Analysis → Presentation Score
```

### **2. Scoring Metric Replacement**

| **Old Audio Metrics** | **New Video Metrics** |
|----------------------|----------------------|
| Words Per Minute (WPM) | Confidence Level (0-1) |
| Filler Word Frequency | Emotional Consistency |
| Voice Quality | Authenticity Score |
| Pause Analysis | Energy Level |
| Transcript Content | Facial Expression Analysis |

### **3. MCP Tools Replacement**

| **Old Recording Tools** | **New Pitches Tools** |
|------------------------|---------------------|
| `recordings.start_recording` | `create_pitch_session` |
| `recordings.get_transcript` | `analyze_pitch_video` |
| `recordings.get_audio_intelligence` | `get_coaching_insights` |
| `recordings.health_check` | `pitch_health_check` |

## ⚠️ **BREAKING CHANGES**

### **API Endpoints**
- All `/api/recordings/*` endpoints removed
- Replaced with `/api/pitches/*` endpoints
- Different payload structures (video upload vs audio recording)

### **MCP Tool Schemas**
- Complete schema changes for all tools
- Different input/output formats
- New tool names and parameters

### **Database Schema**
- Session data structure changes
- Analysis results format changes  
- No more transcript storage, now emotion timeline data

## 📊 **IMPACT ASSESSMENT**

### **Files Affected by Category:**
- **🔴 HIGH IMPACT (DELETE)**: 45+ files
- **🟡 MEDIUM IMPACT (MAJOR UPDATES)**: 30+ files  
- **🟢 LOW IMPACT (MINOR UPDATES)**: 60+ files
- **📝 DOCUMENTATION**: 40+ files

### **Estimated Migration Effort:**
- **Scoring Domain Refactor**: 3-5 days
- **Test Suite Updates**: 2-3 days
- **Documentation Updates**: 1-2 days
- **Infrastructure Updates**: 1 day
- **Integration Testing**: 2-3 days

**Total Estimated Effort: 9-14 days**

## 🎯 **MIGRATION PRIORITIES**

### **Priority 1 (CRITICAL):**
1. Update scoring domain to use video intelligence instead of transcript analysis
2. Remove all Gladia-based scoring tools
3. Update Docker configuration

### **Priority 2 (HIGH):**
1. Update all MCP integration tests
2. Remove audio-based test files
3. Update main documentation

### **Priority 3 (MEDIUM):**
1. Clean up remaining test files
2. Update secondary documentation
3. Remove unused dependencies

### **Priority 4 (LOW):**
1. Archive old audio test data
2. Update minor documentation references
3. Clean up configuration comments

## 🔧 **IMMEDIATE ACTION ITEMS**

1. **Update docker-compose.yml** - Remove Gladia vars, add Hume vars
2. **Delete audio integration files** in scoring domain
3. **Create video-based scoring handlers** to replace audio-based ones
4. **Update scoring MCP tools** to use pitch analysis instead of transcript
5. **Migrate scoring tests** to use mock video intelligence data

## 💾 **DATA MIGRATION STRATEGY**

### **Existing Audio Data:**
- **Option 1**: Archive all existing audio recordings and transcripts
- **Option 2**: Delete all audio data (if no longer needed)
- **Option 3**: Convert existing sessions to "audio-only" legacy format

### **Recommended Approach:**
Keep existing audio sessions as "legacy" data but disable new audio recording functionality. All new sessions use video analysis.

## 🚨 **RISK MITIGATION**

1. **Backup Strategy**: Archive all deleted files in `legacy/` directory before deletion
2. **Feature Flag**: Implement feature flag to switch between audio/video modes during transition
3. **Rollback Plan**: Keep old audio handlers available but unused for emergency rollback
4. **Testing Strategy**: Comprehensive integration tests for new video flow before removing audio flow

---

**This audit reveals that the Hume migration is a major architectural change affecting 135+ files across the entire codebase. The scoring domain requires complete rebuilding, and extensive testing will be needed to ensure the new video-based analysis provides equivalent functionality to the previous audio-based system.**
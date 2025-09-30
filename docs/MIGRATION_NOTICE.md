# Migration Notice: Gladia → Hume

## 🚧 System Migration in Progress

PitchScoop is currently migrating from **Gladia (audio processing)** to **Hume AI (video processing)**.

### Current Status
- ❌ **Gladia integration**: Removed from codebase
- ⚠️ **Audio processing**: Temporarily disabled  
- 🔄 **Video processing**: Ready for Hume integration
- 📋 **MCP tools**: Disabled during migration

### What's Changed
1. **Environment Variables**: `GLADIA_API_KEY` removed, `HUME_API_KEY` + `HUME_SECRET_KEY` to be added
2. **Processing Type**: Moving from audio transcription to video emotion analysis
3. **Data Models**: Audio intelligence → Video emotion/expression analysis
4. **MCP Tools**: Temporarily disabled, will be replaced with video-focused tools

### Documentation Status
Many documentation files still reference Gladia. These will be updated once Hume integration is complete.

### For Developers
- **API endpoints**: Recording endpoints temporarily non-functional
- **Tests**: Gladia-specific tests removed
- **Integration**: Focus on video processing implementation

---
*Last updated: Migration Phase 1 Complete*
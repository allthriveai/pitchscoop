# 🦙 LlamaIndex Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Build and Start Services
```bash
cd /Users/allierays/Sites/pitchscoop

# Rebuild with LlamaIndex dependencies
docker-compose build api

# Start all services (now includes Qdrant)
docker-compose up -d
```

### 2. Verify Integration
```bash
# Test LlamaIndex connection
docker-compose exec api python test_llamaindex.py
```

Expected output:
```
🦙 Testing LlamaIndex Integration
==================================================

1. Testing health check...
✅ Indexing system is healthy!
   Qdrant collections: 0
   LLM model: gpt-4

2. Testing rubric indexing...
✅ Rubric indexed successfully!
   Event: test-event-123
   Criteria count: 4

3. Testing transcript indexing...
✅ Transcript indexed successfully!
   Team: AI Innovators
   Word count: 65

[... more tests ...]

🎉 LlamaIndex integration test completed!
```

## 📋 Available MCP Tools

### Indexing Tools
```python
# Index event rubric for context-aware scoring
await execute_mcp_tool("index.add_rubric", {
    "event_id": "hackathon-2024",
    "rubric_data": {
        "event_name": "AI Hackathon 2024",
        "criteria": ["Technical Innovation", "Presentation", "Impact"],
        "weights": {"Technical Innovation": 0.4, "Presentation": 0.3, "Impact": 0.3},
        "guidelines": "Score 1-10 based on clarity and innovation"
    }
})

# Index transcript after recording
await execute_mcp_tool("index.add_transcript", {
    "event_id": "hackathon-2024", 
    "session_id": "session-123",
    "transcript_data": {
        "team_name": "AI Innovators",
        "pitch_title": "Smart City Platform",
        "transcript_text": "Our AI solution...",
        "duration_seconds": 180,
        "word_count": 150
    }
})

# Index team profile for personalized feedback
await execute_mcp_tool("index.add_team_profile", {
    "event_id": "hackathon-2024",
    "team_data": {
        "team_name": "AI Innovators",
        "members": ["Alice", "Bob", "Carol"],
        "bio": "AI researchers focused on smart cities",
        "skills": ["Python", "ML", "Computer Vision"]
    }
})
```

### Query Tools
```python
# Check system health
await execute_mcp_tool("index.health_check", {})

# List all collections for an event
await execute_mcp_tool("index.list_collections", {
    "event_id": "hackathon-2024"
})
```

## 🔍 RAG Query Examples

```python
from domains.indexing.services.llamaindex_service import llamaindex_service

# Query rubric for scoring criteria
result = await llamaindex_service.query_index(
    event_id="hackathon-2024",
    document_type="rubrics",
    query="What are the technical innovation criteria?",
    top_k=3
)

# Search transcripts for specific content
result = await llamaindex_service.query_index(
    event_id="hackathon-2024", 
    document_type="transcripts",
    query="machine learning computer vision AI",
    top_k=5
)

# Query team profiles
result = await llamaindex_service.query_index(
    event_id="hackathon-2024",
    document_type="teams", 
    query="teams with Python and ML experience",
    top_k=3
)
```

## 🏗️ Integration with Existing Domains

### Auto-Index Transcripts After Recording
```python
# In domains/recordings/mcp/gladia_mcp_handler.py
async def stop_pitch_recording(self, ...):
    # ... existing code ...
    
    # After recording completion, auto-index transcript
    if transcript_data:
        from domains.indexing.mcp.indexing_tools import execute_indexing_tool
        await execute_indexing_tool("index.add_transcript", {
            "event_id": event_id,
            "session_id": session_id,
            "transcript_data": {
                "team_name": session_data["team_name"],
                "pitch_title": session_data["pitch_title"], 
                "transcript_text": final_transcript["total_text"],
                "duration_seconds": duration,
                "word_count": len(final_transcript["total_text"].split())
            }
        })
```

### Context-Aware Scoring
```python
# New scoring domain using RAG
from domains.indexing.services.llamaindex_service import llamaindex_service

async def score_with_context(event_id: str, session_id: str):
    # 1. Get rubric context
    rubric_context = await llamaindex_service.query_index(
        event_id=event_id,
        document_type="rubrics",
        query="scoring criteria weights guidelines"
    )
    
    # 2. Get transcript to score
    transcript_context = await llamaindex_service.query_index(
        event_id=event_id,
        document_type="transcripts", 
        query=f"session_id:{session_id}"
    )
    
    # 3. Use Azure OpenAI to score with full context
    prompt = f"""
    Based on this scoring rubric:
    {rubric_context['response']}
    
    Score this pitch transcript:
    {transcript_context['response']}
    
    Provide detailed scores for each criterion with reasoning.
    """
    
    # Use Settings.llm to get structured scores
    # ...
```

## 🎯 Next Steps for Hackathon

### Phase 1: Basic RAG (30 minutes)
1. ✅ LlamaIndex setup complete
2. ✅ Test basic indexing and querying
3. 🔧 Auto-index transcripts after recording

### Phase 2: Scoring Engine (1 hour)
1. Create `domains/scoring/` with RAG-powered scoring
2. Implement `scores.evaluate` MCP tool using context
3. Generate structured scores with reasoning

### Phase 3: Frontend Integration (1 hour)  
1. Display scores in browser interface
2. Show context sources used for scoring
3. Create leaderboard based on scores

## 🐛 Troubleshooting

### Common Issues

**"No module named 'llama_index'"**
```bash
# Rebuild Docker image
docker-compose build api
```

**"Connection refused" to Qdrant**
```bash
# Make sure Qdrant is running
docker-compose ps qdrant

# Restart if needed
docker-compose restart qdrant api
```

**"Azure OpenAI authentication failed"**
```bash
# Check environment variables
docker-compose exec api env | grep AZURE

# Make sure .env has:
# SYSTEM_LLM_AZURE_ENDPOINT=https://...
# SYSTEM_LLM_AZURE_API_KEY=...
# SYSTEM_LLM_AZURE_DEPLOYMENT=...
```

### Debug Commands
```bash
# Check Qdrant collections
curl http://localhost:6333/collections

# Test Azure OpenAI connection
docker-compose exec api python -c "
import os
print('Endpoint:', os.getenv('SYSTEM_LLM_AZURE_ENDPOINT'))
print('Deployment:', os.getenv('SYSTEM_LLM_AZURE_DEPLOYMENT'))
"

# Test LlamaIndex health
docker-compose exec api python -c "
from domains.indexing.services.llamaindex_service import llamaindex_service
import asyncio
print(asyncio.run(llamaindex_service.health_check()))
"
```

## 🚢 Ready to Ship!

LlamaIndex is now integrated and ready for RAG-powered scoring! Your next priorities:

1. **Build scoring engine** using RAG context
2. **Create frontend** to display intelligent scores  
3. **Demo the AI-powered** pitch evaluation system

The foundation is solid - now make it shine for the judges! 🏆
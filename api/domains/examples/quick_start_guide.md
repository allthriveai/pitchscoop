# Quick Start: RAG-Powered PitchScoop

## Your Setup Status ✅

**Good news!** Your PitchScoop environment is already mostly ready for RAG functionality:

- ✅ Redis Stack configured in `docker-compose.yml`
- ✅ Environment variables structured in `.env.example`
- ✅ Dependencies added to `requirements.txt`
- ✅ RAG code implemented and ready

## What You Need To Do

### 1. Set up your environment file

```bash
cd /Users/allierays/Sites/pitchscoop

# Copy the example environment file
cp .env.example .env

# Edit .env and add your Azure OpenAI credentials
nano .env  # or use your preferred editor
```

Add your real Azure OpenAI values:
```env
SYSTEM_LLM_AZURE_ENDPOINT=https://your-resource.openai.azure.com/
SYSTEM_LLM_AZURE_API_KEY=your_actual_api_key_here
SYSTEM_LLM_AZURE_DEPLOYMENT=your_deployment_name
SYSTEM_LLM_AZURE_API_VERSION=2024-02-15-preview
```

### 2. Install dependencies

```bash
cd /Users/allierays/Sites/pitchscoop/api
pip install -r requirements.txt
```

### 3. Start your services

```bash
cd /Users/allierays/Sites/pitchscoop
docker-compose up -d
```

### 4. Verify Redis Stack is working

```bash
# Check Redis Stack modules
docker-compose exec redis redis-cli MODULE LIST

# You should see "search" in the output
```

### 5. Test the RAG integration

```bash
cd /Users/allierays/Sites/pitchscoop/api
python -m domains.examples.rag_integration_example
```

## What the RAG System Provides

### For Judges/Users:
- **Smart Conversations**: Chat with AI about pitches using actual transcript data
- **Document Search**: Find specific information across all pitch materials
- **Comparative Analysis**: "How did Team A's technical approach compare to Team B?"
- **Context-Aware Scoring**: Enhanced scoring that references rubrics and other pitches

### For Developers:
- **Multi-tenant**: Each event's data is completely isolated
- **Source Attribution**: All AI responses cite their sources
- **Scalable**: Built on Redis Stack for performance
- **Fallback**: If RAG fails, falls back to existing LangChain scoring

## RAG-Powered Features

### 1. **Enhanced Scoring**
```python
# Existing scoring now includes RAG context
result = await execute_scoring_mcp_tool(
    tool_name="analysis.score_pitch",
    arguments={
        "session_id": "pitch_001",
        "event_id": "hackathon_2024",
        "judge_id": "judge_smith"
    }
)
# Now automatically uses rubrics and comparative context!
```

### 2. **Smart Chat**
```python
# Start a conversation about specific pitches
conversation = await execute_chat_mcp_tool(
    tool_name="chat.start_conversation", 
    arguments={
        "event_id": "hackathon_2024",
        "conversation_type": "pitch_analysis",
        "session_ids": ["pitch_001", "pitch_002"]
    }
)

# Ask questions with full context
response = await execute_chat_mcp_tool(
    tool_name="chat.send_message",
    arguments={
        "conversation_id": conversation["conversation_id"],
        "event_id": "hackathon_2024", 
        "message": "Which team had better technical implementation?"
    }
)
```

### 3. **Document Indexing**
```python
# Index pitch transcripts for RAG
from domains.indexing.services.document_indexing_service import document_indexing_service

result = await document_indexing_service.index_pitch_transcripts(
    event_id="hackathon_2024",
    session_data_list=session_data  # Your existing session data
)
```

## Integration Points

The RAG system integrates with your existing PitchScoop components:

### With Recording Domain:
- Automatically indexes completed transcripts
- Uses session metadata for context

### With Scoring Domain:  
- Enhances existing scoring with rubric context
- Provides comparative analysis across pitches
- Maintains backward compatibility

### With Your Frontend:
- Same API endpoints, enhanced responses
- New chat endpoints for conversational features
- Source attribution in UI components

## File Structure

The RAG functionality adds these new components to your existing structure:

```
api/domains/
├── chat/                    # NEW: RAG-powered chat
│   ├── entities/
│   ├── mcp/
│   └── services/
├── indexing/               # NEW: Document indexing
│   └── services/
├── scoring/               # ENHANCED: Now includes RAG
│   └── mcp/               # Enhanced with RAG context
└── examples/              # NEW: Examples and guides
    └── rag_integration_example.py
```

## Monitoring

### RedisInsight (Web UI)
- Access at: http://localhost:8001
- View vector indices
- Monitor search performance
- Debug queries

### Health Checks
```python
# Check system health
health = await execute_chat_mcp_tool(
    tool_name="chat.health_check",
    arguments={"detailed_check": True}
)
```

## Next Steps

1. **Set up .env file** with your Azure OpenAI credentials
2. **Start services**: `docker-compose up -d`
3. **Install dependencies**: `pip install -r requirements.txt` 
4. **Run test**: `python -m domains.examples.rag_integration_example`
5. **Index your existing data** to enable RAG features
6. **Integrate with your frontend** to expose chat features

## Need Help?

The RAG system is designed to work alongside your existing PitchScoop functionality without breaking anything. All existing features continue to work, with enhanced capabilities when RAG data is available.

**Common issues:**
- Make sure you're using Redis Stack, not regular Redis (already configured ✅)
- Add real Azure OpenAI credentials to .env
- Install the updated requirements.txt dependencies

Ready to give judges AI-powered insights into pitch competitions! 🚀
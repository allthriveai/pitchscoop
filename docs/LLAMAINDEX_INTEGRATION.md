# 🦙 LlamaIndex Integration for PitchScoop

## 🎯 Overview

LlamaIndex will power the RAG (Retrieval Augmented Generation) features in PitchScoop:
- **Scoring Engine**: Context-aware pitch evaluation using rubrics and examples
- **Chat Interface**: Q&A over event rules, team bios, and transcripts  
- **Feedback Generation**: Rich, contextual feedback based on best practices
- **Search**: Semantic search across all pitch content

## 🏗️ Architecture

### Vector Store Strategy
```
Qdrant Collections (per event for isolation):
├── event:{event_id}:rubrics     # Scoring criteria, examples
├── event:{event_id}:transcripts # All pitch transcripts  
├── event:{event_id}:teams       # Team bios and profiles
└── event:{event_id}:feedback    # Generated feedback examples
```

### Document Types
1. **Rubric Documents**: Scoring criteria, examples of good/bad pitches
2. **Transcript Documents**: Full pitch transcripts with metadata
3. **Team Documents**: Bios, previous performance, focus areas
4. **Feedback Documents**: Historical feedback for similar pitches

## 🔧 Implementation Structure

```
/domains/indexing/
├── __init__.py
├── entities/
│   ├── document.py           # Document entity
│   └── index_entry.py        # Index metadata
├── services/
│   ├── llamaindex_service.py # Core LlamaIndex integration
│   ├── document_processor.py # Document chunking/processing
│   └── embedding_service.py  # Embedding generation
├── infrastructure/
│   ├── qdrant_client.py      # Qdrant vector store
│   └── openai_client.py      # Azure OpenAI integration
├── mcp/
│   ├── indexing_tools.py     # MCP tools for indexing
│   └── search_tools.py       # MCP tools for search/chat
└── repositories/
    └── index_repository.py   # Index persistence
```

## 📋 MCP Tools to Implement

### Indexing Tools
```python
@mcp_tool("index.add_rubric")
async def add_rubric(event_id: str, rubric_data: dict) -> dict:
    """Index event rubric for scoring context"""

@mcp_tool("index.add_transcript") 
async def add_transcript(event_id: str, session_id: str, transcript: str) -> dict:
    """Index pitch transcript for search/analysis"""

@mcp_tool("index.add_team_profile")
async def add_team_profile(event_id: str, team_data: dict) -> dict:
    """Index team information for personalized feedback"""
```

### Search & Chat Tools
```python
@mcp_tool("search.semantic_search")
async def semantic_search(event_id: str, query: str) -> dict:
    """Search across all indexed content"""

@mcp_tool("chat.query_event")
async def query_event(event_id: str, question: str) -> dict:
    """RAG-powered Q&A over event data"""

@mcp_tool("scoring.context_aware_score")
async def context_aware_score(event_id: str, session_id: str) -> dict:
    """Score pitch using rubric + examples via RAG"""
```

## 🚀 Quick Start Implementation

### 1. LlamaIndex Service Core
```python
# domains/indexing/services/llamaindex_service.py
import os
from typing import List, Dict, Any
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

class LlamaIndexService:
    def __init__(self):
        # Configure LlamaIndex with Azure OpenAI
        Settings.embed_model = OpenAIEmbedding(
            api_key=os.getenv("SYSTEM_LLM_AZURE_API_KEY"),
            api_base=os.getenv("SYSTEM_LLM_AZURE_ENDPOINT"),
            api_type="azure",
            api_version=os.getenv("SYSTEM_LLM_AZURE_API_VERSION"),
            deployment_name="text-embedding-ada-002"
        )
        
        Settings.llm = OpenAI(
            api_key=os.getenv("SYSTEM_LLM_AZURE_API_KEY"),
            api_base=os.getenv("SYSTEM_LLM_AZURE_ENDPOINT"),
            api_type="azure", 
            api_version=os.getenv("SYSTEM_LLM_AZURE_API_VERSION"),
            deployment_name=os.getenv("SYSTEM_LLM_AZURE_DEPLOYMENT")
        )
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "qdrant"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
    
    async def create_event_index(self, event_id: str, document_type: str) -> VectorStoreIndex:
        """Create or get index for specific event and document type"""
        collection_name = f"event_{event_id}_{document_type}"
        
        vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=collection_name
        )
        
        return VectorStoreIndex.from_vector_store(vector_store)
    
    async def index_documents(self, event_id: str, document_type: str, documents: List[Document]):
        """Add documents to the event index"""
        index = await self.create_event_index(event_id, document_type)
        
        for doc in documents:
            index.insert(doc)
        
        return {"indexed_count": len(documents)}
    
    async def query_index(self, event_id: str, document_type: str, query: str, top_k: int = 5):
        """Query the event index"""
        index = await self.create_event_index(event_id, document_type)
        query_engine = index.as_query_engine(similarity_top_k=top_k)
        
        response = query_engine.query(query)
        return {
            "response": str(response),
            "source_nodes": [
                {
                    "content": node.text,
                    "score": node.score,
                    "metadata": node.metadata
                }
                for node in response.source_nodes
            ]
        }
```

### 2. Document Processing
```python
# domains/indexing/services/document_processor.py
from llama_index.core import Document
from typing import List, Dict, Any

class DocumentProcessor:
    @staticmethod
    def create_rubric_document(event_id: str, rubric_data: dict) -> Document:
        """Convert rubric to LlamaIndex document"""
        content = f"""
        Event Scoring Rubric for {event_id}:
        
        Criteria: {rubric_data.get('criteria', [])}
        Weights: {rubric_data.get('weights', {})}
        Examples: {rubric_data.get('examples', {})}
        Guidelines: {rubric_data.get('guidelines', '')}
        """
        
        return Document(
            text=content,
            metadata={
                "event_id": event_id,
                "document_type": "rubric",
                "criteria_count": len(rubric_data.get('criteria', []))
            }
        )
    
    @staticmethod  
    def create_transcript_document(event_id: str, session_id: str, transcript_data: dict) -> Document:
        """Convert transcript to LlamaIndex document"""
        content = f"""
        Pitch Transcript:
        Team: {transcript_data.get('team_name', 'Unknown')}
        Title: {transcript_data.get('pitch_title', 'Unknown')}
        
        Transcript: {transcript_data.get('transcript_text', '')}
        
        Metrics:
        - Duration: {transcript_data.get('duration_seconds', 0)} seconds
        - Word Count: {transcript_data.get('word_count', 0)}
        - Speaking Rate: {transcript_data.get('words_per_minute', 0)} WPM
        """
        
        return Document(
            text=content,
            metadata={
                "event_id": event_id,
                "session_id": session_id,
                "document_type": "transcript",
                "team_name": transcript_data.get('team_name'),
                "duration": transcript_data.get('duration_seconds', 0)
            }
        )
```

### 3. MCP Tools Implementation
```python
# domains/indexing/mcp/indexing_tools.py
from typing import Dict, Any
from ..services.llamaindex_service import LlamaIndexService
from ..services.document_processor import DocumentProcessor

llamaindex_service = LlamaIndexService()
doc_processor = DocumentProcessor()

async def add_rubric(event_id: str, rubric_data: Dict[str, Any]) -> Dict[str, Any]:
    """Index event rubric for context-aware scoring"""
    try:
        # Create rubric document
        doc = doc_processor.create_rubric_document(event_id, rubric_data)
        
        # Index the document
        result = await llamaindex_service.index_documents(
            event_id=event_id,
            document_type="rubrics", 
            documents=[doc]
        )
        
        return {
            "success": True,
            "event_id": event_id,
            "indexed_documents": result["indexed_count"],
            "message": "Rubric indexed successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "event_id": event_id
        }

async def add_transcript(event_id: str, session_id: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
    """Index pitch transcript for search and analysis"""
    try:
        # Create transcript document
        doc = doc_processor.create_transcript_document(event_id, session_id, transcript_data)
        
        # Index the document
        result = await llamaindex_service.index_documents(
            event_id=event_id,
            document_type="transcripts",
            documents=[doc]
        )
        
        return {
            "success": True,
            "event_id": event_id,
            "session_id": session_id,
            "indexed_documents": result["indexed_count"],
            "message": "Transcript indexed successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "event_id": event_id,
            "session_id": session_id
        }
```

### 4. Context-Aware Scoring
```python
# domains/scoring/services/llamaindex_scoring_service.py
class LlamaIndexScoringService:
    def __init__(self):
        self.llamaindex_service = LlamaIndexService()
    
    async def score_with_context(self, event_id: str, session_id: str) -> Dict[str, Any]:
        """Score pitch using RAG with rubric and examples"""
        
        # 1. Get transcript data
        transcript_query = f"session_id:{session_id}"
        transcript_results = await self.llamaindex_service.query_index(
            event_id=event_id,
            document_type="transcripts", 
            query=transcript_query
        )
        
        # 2. Get rubric context
        rubric_results = await self.llamaindex_service.query_index(
            event_id=event_id,
            document_type="rubrics",
            query="scoring criteria and examples"
        )
        
        # 3. Generate context-aware score using LLM
        scoring_prompt = f"""
        Based on the following rubric and examples:
        {rubric_results['response']}
        
        Score this pitch transcript:
        {transcript_results['response']}
        
        Provide scores for each criterion with explanations.
        Return as JSON with structure: {{"criterion": {{"score": 0-100, "reasoning": "..."}}}}
        """
        
        # Use LlamaIndex LLM to generate scores
        # Implementation depends on your LLM setup
        
        return {
            "session_id": session_id,
            "scores": {}, # Generated scores
            "context_used": {
                "rubric_sources": len(rubric_results['source_nodes']),
                "transcript_found": len(transcript_results['source_nodes']) > 0
            }
        }
```

## 🔌 Integration Points

### 1. Update Docker Compose
```yaml
# Add Qdrant service to docker-compose.yml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
    - "6334:6334"  
  volumes:
    - qdrant-data:/qdrant/storage
  networks:
    - hackathon-net

volumes:
  qdrant-data: # Add to volumes section
```

### 2. Environment Variables
```bash
# Add to docker-compose.yml environment
- QDRANT_HOST=qdrant
- QDRANT_PORT=6333

# Azure OpenAI already configured:
- SYSTEM_LLM_AZURE_ENDPOINT=${SYSTEM_LLM_AZURE_ENDPOINT}
- SYSTEM_LLM_AZURE_API_KEY=${SYSTEM_LLM_AZURE_API_KEY}
- SYSTEM_LLM_AZURE_DEPLOYMENT=${SYSTEM_LLM_AZURE_DEPLOYMENT}
```

### 3. Integration with Existing Domains
```python
# Update domains/recordings/mcp/gladia_mcp_handler.py
async def stop_pitch_recording(self, ...):
    # ... existing code ...
    
    # After recording is complete, index the transcript
    if transcript_data:
        from domains.indexing.mcp.indexing_tools import add_transcript
        await add_transcript(
            event_id=event_id,
            session_id=session_id, 
            transcript_data={
                "team_name": session_data["team_name"],
                "pitch_title": session_data["pitch_title"],
                "transcript_text": final_transcript["total_text"],
                "duration_seconds": duration,
                "word_count": len(final_transcript["total_text"].split())
            }
        )
```

## 🎯 Implementation Priority

### Phase 1: Basic RAG Setup (2-3 hours)
1. ✅ Add dependencies
2. ✅ Create LlamaIndex service
3. ✅ Set up Qdrant integration
4. ✅ Basic document indexing

### Phase 2: Scoring Integration (2 hours)
1. Context-aware scoring service
2. Rubric indexing from events
3. Transcript auto-indexing after recording
4. MCP tools for scoring

### Phase 3: Chat Interface (1-2 hours)
1. Query engine for event Q&A
2. Frontend chat component
3. Real-time search functionality

## 🚀 Quick Start Commands

```bash
# Rebuild with new dependencies
docker-compose build api

# Start with Qdrant
docker-compose up -d qdrant redis minio api

# Test LlamaIndex integration
docker-compose exec api python -c "
from domains.indexing.services.llamaindex_service import LlamaIndexService
service = LlamaIndexService()
print('✅ LlamaIndex initialized successfully')
"
```

This integration will make your scoring much more intelligent and enable powerful search/chat features that will wow the judges! 🦙✨
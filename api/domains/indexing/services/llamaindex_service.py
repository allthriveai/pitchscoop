"""
LlamaIndex Service - Core RAG functionality for PitchScoop

Handles document indexing, embedding generation, and query processing
using LlamaIndex with Azure OpenAI and Qdrant vector store.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)


class LlamaIndexService:
    """Core LlamaIndex service for RAG functionality."""
    
    def __init__(self):
        """Initialize LlamaIndex with Azure OpenAI and Qdrant."""
        self._configure_llamaindex()
        self._initialize_qdrant()
    
    def _configure_llamaindex(self):
        """Configure LlamaIndex global settings."""
        # Configure embeddings with Azure OpenAI
        Settings.embed_model = OpenAIEmbedding(
            api_key=os.getenv("SYSTEM_LLM_AZURE_API_KEY"),
            azure_endpoint=os.getenv("SYSTEM_LLM_AZURE_ENDPOINT"),
            api_type="azure",
            api_version=os.getenv("SYSTEM_LLM_AZURE_API_VERSION", "2024-02-01"),
            azure_deployment="text-embedding-ada-002"  # Standard embedding model
        )
        
        # Configure LLM with Azure OpenAI
        Settings.llm = OpenAI(
            api_key=os.getenv("SYSTEM_LLM_AZURE_API_KEY"),
            azure_endpoint=os.getenv("SYSTEM_LLM_AZURE_ENDPOINT"),
            api_type="azure",
            api_version=os.getenv("SYSTEM_LLM_AZURE_API_VERSION", "2024-02-01"),
            azure_deployment=os.getenv("SYSTEM_LLM_AZURE_DEPLOYMENT")
        )
        
        logger.info("LlamaIndex configured with Azure OpenAI")
    
    def _initialize_qdrant(self):
        """Initialize Qdrant client."""
        self.qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", 6333))
        )
        logger.info("Qdrant client initialized")
    
    def _get_collection_name(self, event_id: str, document_type: str) -> str:
        """Generate collection name for event and document type."""
        # Sanitize for Qdrant collection names (alphanumeric + underscore only)
        safe_event_id = "".join(c if c.isalnum() else "_" for c in event_id)
        return f"event_{safe_event_id}_{document_type}"
    
    async def ensure_collection_exists(self, event_id: str, document_type: str):
        """Ensure Qdrant collection exists for the event and document type."""
        collection_name = self._get_collection_name(event_id, document_type)
        
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            existing_names = [c.name for c in collections.collections]
            
            if collection_name not in existing_names:
                # Create collection with default vector configuration
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=1536,  # OpenAI ada-002 embedding size
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    async def create_event_index(self, event_id: str, document_type: str) -> VectorStoreIndex:
        """Create or get index for specific event and document type."""
        await self.ensure_collection_exists(event_id, document_type)
        
        collection_name = self._get_collection_name(event_id, document_type)
        
        vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=collection_name
        )
        
        return VectorStoreIndex.from_vector_store(vector_store)
    
    async def index_documents(self, event_id: str, document_type: str, documents: List[Document]) -> Dict[str, Any]:
        """Add documents to the event index."""
        try:
            index = await self.create_event_index(event_id, document_type)
            
            # Insert documents
            for doc in documents:
                index.insert(doc)
            
            logger.info(f"Indexed {len(documents)} documents for event {event_id}, type {document_type}")
            
            return {
                "success": True,
                "indexed_count": len(documents),
                "event_id": event_id,
                "document_type": document_type
            }
            
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return {
                "success": False,
                "error": str(e),
                "indexed_count": 0
            }
    
    async def query_index(self, event_id: str, document_type: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Query the event index."""
        try:
            index = await self.create_event_index(event_id, document_type)
            query_engine = index.as_query_engine(similarity_top_k=top_k)
            
            response = query_engine.query(query)
            
            result = {
                "success": True,
                "response": str(response),
                "source_nodes": [
                    {
                        "content": node.text,
                        "score": getattr(node, 'score', 0.0),
                        "metadata": node.metadata or {}
                    }
                    for node in (response.source_nodes or [])
                ],
                "query": query,
                "event_id": event_id,
                "document_type": document_type
            }
            
            logger.info(f"Queried index for event {event_id}, type {document_type}: {len(result['source_nodes'])} results")
            return result
            
        except Exception as e:
            logger.error(f"Error querying index: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "",
                "source_nodes": []
            }
    
    async def delete_event_index(self, event_id: str, document_type: str) -> Dict[str, Any]:
        """Delete all documents for an event and document type."""
        try:
            collection_name = self._get_collection_name(event_id, document_type)
            
            # Delete the entire collection
            self.qdrant_client.delete_collection(collection_name)
            
            logger.info(f"Deleted index for event {event_id}, type {document_type}")
            
            return {
                "success": True,
                "event_id": event_id,
                "document_type": document_type,
                "message": "Index deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of LlamaIndex service."""
        try:
            # Check Qdrant connection
            collections = self.qdrant_client.get_collections()
            
            return {
                "healthy": True,
                "qdrant_collections": len(collections.collections),
                "embedding_model": "text-embedding-ada-002",
                "llm_model": os.getenv("SYSTEM_LLM_AZURE_DEPLOYMENT", "unknown")
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }


# Global service instance
llamaindex_service = LlamaIndexService()
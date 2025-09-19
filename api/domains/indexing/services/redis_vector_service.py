"""
Redis Vector Service - Core RAG functionality for PitchScoop

Handles document indexing, embedding generation, and query processing
using LlamaIndex with Azure OpenAI and Redis Vector Search.
"""
import os
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
import numpy as np
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.redis import RedisVectorStore
import redis
from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

logger = logging.getLogger(__name__)


class RedisVectorService:
    """Core Redis Vector service for RAG functionality."""
    
    def __init__(self):
        """Initialize Redis Vector service with Azure OpenAI."""
        self._configure_llamaindex()
        self._initialize_redis()
    
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
    
    def _initialize_redis(self):
        """Initialize Redis client with vector search capabilities."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        logger.info("Redis client initialized with vector search capabilities")
    
    def _get_index_name(self, event_id: str, document_type: str) -> str:
        """Generate index name for event and document type."""
        # Sanitize for Redis index names
        safe_event_id = "".join(c if c.isalnum() else "_" for c in event_id)
        return f"idx:event_{safe_event_id}_{document_type}"
    
    def _get_key_prefix(self, event_id: str, document_type: str) -> str:
        """Generate key prefix for documents."""
        safe_event_id = "".join(c if c.isalnum() else "_" for c in event_id)
        return f"doc:event_{safe_event_id}_{document_type}"
    
    async def ensure_index_exists(self, event_id: str, document_type: str):
        """Ensure Redis vector index exists for the event and document type."""
        index_name = self._get_index_name(event_id, document_type)
        key_prefix = self._get_key_prefix(event_id, document_type)
        
        try:
            # Check if index exists
            try:
                self.redis_client.ft(index_name).info()
                logger.debug(f"Index {index_name} already exists")
                return
            except redis.ResponseError:
                # Index doesn't exist, create it
                pass
            
            # Create index with vector field
            schema = [
                VectorField(
                    "embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": 1536,  # OpenAI ada-002 embedding size
                        "DISTANCE_METRIC": "COSINE"
                    }
                ),
                TextField("content"),
                TextField("metadata"),
                TextField("event_id"),
                TextField("document_type"),
                NumericField("created_at")
            ]
            
            index_definition = IndexDefinition(
                prefix=[f"{key_prefix}:"],
                index_type=IndexType.HASH
            )
            
            self.redis_client.ft(index_name).create_index(
                schema, 
                definition=index_definition
            )
            
            logger.info(f"Created Redis vector index: {index_name}")
            
        except Exception as e:
            logger.error(f"Error ensuring index exists: {e}")
            raise
    
    async def create_event_index(self, event_id: str, document_type: str) -> VectorStoreIndex:
        """Create or get LlamaIndex using Redis vector store."""
        await self.ensure_index_exists(event_id, document_type)
        
        index_name = self._get_index_name(event_id, document_type)
        key_prefix = self._get_key_prefix(event_id, document_type)
        
        vector_store = RedisVectorStore(
            redis_client=self.redis_client,
            index_name=index_name,
            index_prefix=f"{key_prefix}:",
            vector_key="embedding",
            text_key="content",
            metadata_key="metadata"
        )
        
        return VectorStoreIndex.from_vector_store(vector_store)
    
    async def index_documents(self, event_id: str, document_type: str, documents: List[Document]) -> Dict[str, Any]:
        """Add documents to the event index."""
        try:
            index = await self.create_event_index(event_id, document_type)
            
            # Insert documents
            for doc in documents:
                # Ensure document has required metadata
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata.update({
                    "event_id": event_id,
                    "document_type": document_type
                })
                
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
            index_name = self._get_index_name(event_id, document_type)
            key_prefix = self._get_key_prefix(event_id, document_type)
            
            # Delete all documents with the prefix
            keys = self.redis_client.keys(f"{key_prefix}:*")
            if keys:
                self.redis_client.delete(*keys)
            
            # Delete the index
            try:
                self.redis_client.ft(index_name).dropindex(delete_documents=True)
            except redis.ResponseError:
                # Index might not exist
                pass
            
            logger.info(f"Deleted index for event {event_id}, type {document_type}")
            
            return {
                "success": True,
                "event_id": event_id,
                "document_type": document_type,
                "message": "Index deleted successfully",
                "deleted_documents": len(keys)
            }
            
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_event_indices(self, event_id: str) -> Dict[str, Any]:
        """List all indices for an event."""
        try:
            safe_event_id = "".join(c if c.isalnum() else "_" for c in event_id)
            pattern = f"idx:event_{safe_event_id}_*"
            
            # Get all indices that match the pattern
            all_indices = []
            try:
                # This is a bit hacky - Redis doesn't have a direct way to list indices by pattern
                # We'll try common document types and see which indices exist
                common_types = ["transcripts", "documents", "pitches", "submissions", "feedback"]
                
                for doc_type in common_types:
                    index_name = self._get_index_name(event_id, doc_type)
                    try:
                        info = self.redis_client.ft(index_name).info()
                        all_indices.append({
                            "index_name": index_name,
                            "document_type": doc_type,
                            "num_docs": info.get("num_docs", 0),
                            "num_terms": info.get("num_terms", 0)
                        })
                    except redis.ResponseError:
                        # Index doesn't exist
                        continue
            except Exception:
                pass
            
            return {
                "success": True,
                "event_id": event_id,
                "indices": all_indices
            }
            
        except Exception as e:
            logger.error(f"Error listing event indices: {e}")
            return {
                "success": False,
                "error": str(e),
                "indices": []
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of Redis Vector service."""
        try:
            # Check Redis connection
            self.redis_client.ping()
            
            # Check if Redis has vector search capabilities
            modules = self.redis_client.module_list()
            has_search = any(module[1] == b'search' for module in modules)
            
            return {
                "healthy": True,
                "redis_connected": True,
                "vector_search_available": has_search,
                "embedding_model": "text-embedding-ada-002",
                "llm_model": os.getenv("SYSTEM_LLM_AZURE_DEPLOYMENT", "unknown")
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "redis_connected": False,
                "vector_search_available": False
            }


# Global service instance
redis_vector_service = RedisVectorService()
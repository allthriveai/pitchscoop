"""
LlamaIndex Service - Core RAG functionality for PitchScoop

Handles document indexing, embedding generation, and query processing
using LlamaIndex with Azure OpenAI and Qdrant vector store.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.vector_stores.redis import RedisVectorStore
from redisvl.schema import IndexSchema
import redis

logger = logging.getLogger(__name__)


class LlamaIndexService:
    """Core LlamaIndex service for RAG functionality."""
    
    def __init__(self):
        """Initialize LlamaIndex with Azure OpenAI and RedisVL."""
        self._configure_llamaindex()
        self._initialize_redis()
    
    def _configure_llamaindex(self):
        """Configure LlamaIndex global settings."""
        # Configure embeddings with Azure OpenAI
        Settings.embed_model = AzureOpenAIEmbedding(
            api_key=os.getenv("SYSTEM_LLM_AZURE_API_KEY"),
            azure_endpoint=os.getenv("SYSTEM_LLM_AZURE_ENDPOINT"),
            api_version=os.getenv("SYSTEM_LLM_AZURE_API_VERSION", "2024-02-01"),
            azure_deployment=os.getenv("SYSTEM_LLM_AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        )
        
        # Configure LLM with Azure OpenAI
        Settings.llm = AzureOpenAI(
            api_key=os.getenv("SYSTEM_LLM_AZURE_API_KEY"),
            azure_endpoint=os.getenv("SYSTEM_LLM_AZURE_ENDPOINT"),
            api_version=os.getenv("SYSTEM_LLM_AZURE_API_VERSION", "2024-02-01"),
            azure_deployment=os.getenv("SYSTEM_LLM_AZURE_DEPLOYMENT")
        )
        
        logger.info("LlamaIndex configured with Azure OpenAI")
    
    def _initialize_redis(self):
        """Initialize Redis client for vector operations."""
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        logger.info("Redis client initialized for vector operations")
    
    def _get_index_name(self, event_id: str, document_type: str) -> str:
        """Generate index name for event and document type."""
        # Sanitize for Redis index names (alphanumeric + underscore only)
        safe_event_id = "".join(c if c.isalnum() else "_" for c in event_id)
        return f"idx_event_{safe_event_id}_{document_type}"
    
    async def ensure_index_exists(self, event_id: str, document_type: str):
        """Ensure Redis index exists for the event and document type."""
        index_name = self._get_index_name(event_id, document_type)
        
        try:
            # RedisVectorStore will handle index creation automatically
            # when documents are inserted, so this is mainly for validation
            logger.info(f"Redis index ready: {index_name}")
            
        except Exception as e:
            logger.error(f"Error ensuring index exists: {e}")
            raise
    
    async def create_event_index(self, event_id: str, document_type: str) -> VectorStoreIndex:
        """Create or get index for specific event and document type."""
        await self.ensure_index_exists(event_id, document_type)
        
        index_name = self._get_index_name(event_id, document_type)
        index_prefix = f"event_{event_id}_{document_type}_"
        
        # Create IndexSchema for RedisVL
        schema = IndexSchema.from_dict({
            "index": {
                "name": index_name,
                "prefix": index_prefix,
                "storage_type": "hash"
            },
            "fields": [
                {
                    "name": "id",
                    "type": "tag"
                },
                {
                    "name": "doc_id", 
                    "type": "tag"
                },
                {
                    "name": "text",
                    "type": "text"
                },
                {
                    "name": "vector",
                    "type": "vector",
                    "attrs": {
                        "dims": 1536,
                        "distance_metric": "COSINE",
                        "algorithm": "FLAT",
                        "type": "FLOAT32"
                    }
                }
            ]
        })
        
        vector_store = RedisVectorStore(
            schema=schema,
            redis_client=self.redis_client
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
            index_name = self._get_index_name(event_id, document_type)
            index_prefix = f"event_{event_id}_{document_type}_"
            
            # Delete all keys with the index prefix
            pattern = f"{index_prefix}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            # Try to drop the index itself (may not exist)
            try:
                self.redis_client.execute_command("FT.DROPINDEX", index_name, "DD")
            except Exception:
                pass  # Index might not exist, which is fine
            
            logger.info(f"Deleted index for event {event_id}, type {document_type}")
            
            return {
                "success": True,
                "event_id": event_id,
                "document_type": document_type,
                "message": "Index deleted successfully",
                "deleted_keys": len(keys) if keys else 0
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
            # Check Redis connection
            redis_info = self.redis_client.info()
            
            # Check for RedisSearch module
            modules = self.redis_client.execute_command("MODULE", "LIST")
            # modules is a list of lists, flatten and check for search module
            modules_flat = []
            for module in modules:
                if isinstance(module, (list, tuple)):
                    modules_flat.extend([str(item).lower() for item in module])
                else:
                    modules_flat.append(str(module).lower())
            has_search = any("search" in module_str for module_str in modules_flat)
            
            return {
                "healthy": True,
                "redis_connected": True,
                "redis_version": redis_info.get("redis_version", "unknown"),
                "redisearch_available": has_search,
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
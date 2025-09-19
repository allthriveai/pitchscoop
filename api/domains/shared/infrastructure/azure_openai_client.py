"""
Azure OpenAI Client - Infrastructure for LLM integration

Provides Azure OpenAI API integration using environment variables:
- SYSTEM_LLM_AZURE_ENDPOINT
- SYSTEM_LLM_AZURE_API_KEY  
- SYSTEM_LLM_AZURE_DEPLOYMENT
- SYSTEM_LLM_AZURE_API_VERSION

This client handles multi-tenant isolation using {event_id} and follows
DDD patterns for clean separation of infrastructure concerns.
"""
import os
import asyncio
from typing import Dict, Any, Optional, List, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import json

from openai import AsyncAzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from ...shared.value_objects.llm_request import LLMRequest, LLMResponse, LLMMessage


@dataclass
class AzureOpenAIConfig:
    """Configuration for Azure OpenAI client."""
    
    endpoint: str
    api_key: str
    deployment: str
    api_version: str
    
    @classmethod
    def from_environment(cls) -> "AzureOpenAIConfig":
        """Create configuration from environment variables."""
        endpoint = os.getenv("SYSTEM_LLM_AZURE_ENDPOINT")
        api_key = os.getenv("SYSTEM_LLM_AZURE_API_KEY")
        deployment = os.getenv("SYSTEM_LLM_AZURE_DEPLOYMENT")
        api_version = os.getenv("SYSTEM_LLM_AZURE_API_VERSION")
        
        if not all([endpoint, api_key, deployment, api_version]):
            missing = []
            if not endpoint: missing.append("SYSTEM_LLM_AZURE_ENDPOINT")
            if not api_key: missing.append("SYSTEM_LLM_AZURE_API_KEY") 
            if not deployment: missing.append("SYSTEM_LLM_AZURE_DEPLOYMENT")
            if not api_version: missing.append("SYSTEM_LLM_AZURE_API_VERSION")
            
            raise ValueError(f"Missing required Azure OpenAI environment variables: {missing}")
        
        return cls(
            endpoint=endpoint,
            api_key=api_key,
            deployment=deployment,
            api_version=api_version
        )


class AzureOpenAIClient:
    """Azure OpenAI client with multi-tenant support."""
    
    def __init__(self, config: Optional[AzureOpenAIConfig] = None):
        """Initialize the Azure OpenAI client."""
        self.config = config or AzureOpenAIConfig.from_environment()
        self._client: Optional[AsyncAzureOpenAI] = None
    
    async def get_client(self) -> AsyncAzureOpenAI:
        """Get or create Azure OpenAI client instance."""
        if self._client is None:
            self._client = AsyncAzureOpenAI(
                azure_endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version
            )
        return self._client
    
    async def chat_completion(
        self,
        request: LLMRequest,
        event_id: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate chat completion using Azure OpenAI.
        
        Args:
            request: LLM request with messages and parameters
            event_id: Event ID for multi-tenant isolation
            
        Returns:
            LLM response with generated content
        """
        try:
            client = await self.get_client()
            
            # Convert our domain messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ]
            
            # Store event_id for logging but don't pass to API
            # OpenAI API doesn't accept event_id as a parameter
            
            response = await client.chat.completions.create(
                model=self.config.deployment,
                messages=openai_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop=request.stop_sequences
            )
            
            # Extract response content
            choice = response.choices[0]
            content = choice.message.content or ""
            
            return LLMResponse(
                content=content,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                model=self.config.deployment,
                created_at=datetime.utcnow(),
                metadata={
                    "event_id": event_id,
                    "request_id": request.request_id
                }
            )
            
        except Exception as e:
            # Log error with event_id context
            error_msg = f"Azure OpenAI API error for event_id={event_id}: {str(e)}"
            print(f"ERROR: {error_msg}")
            
            return LLMResponse(
                content="",
                finish_reason="error",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                model=self.config.deployment,
                created_at=datetime.utcnow(),
                error=error_msg,
                metadata={
                    "event_id": event_id,
                    "request_id": request.request_id if request else None
                }
            )
    
    async def stream_chat_completion(
        self,
        request: LLMRequest,
        event_id: Optional[str] = None
    ) -> AsyncIterator[str]:
        """
        Generate streaming chat completion.
        
        Args:
            request: LLM request with messages and parameters
            event_id: Event ID for multi-tenant isolation
            
        Yields:
            Streaming content chunks
        """
        try:
            client = await self.get_client()
            
            # Convert our domain messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in request.messages
            ]
            
            # Store event_id for logging but don't pass to API
            # OpenAI API doesn't accept event_id as a parameter
            
            stream = await client.chat.completions.create(
                model=self.config.deployment,
                messages=openai_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                frequency_penalty=request.frequency_penalty,
                presence_penalty=request.presence_penalty,
                stop=request.stop_sequences,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            error_msg = f"Azure OpenAI streaming error for event_id={event_id}: {str(e)}"
            print(f"ERROR: {error_msg}")
            yield f"[ERROR: {error_msg}]"
    
    async def embeddings(
        self,
        texts: List[str],
        event_id: Optional[str] = None,
        model: str = "text-embedding-ada-002"
    ) -> List[List[float]]:
        """
        Generate embeddings for text analysis.
        
        Args:
            texts: List of texts to embed
            event_id: Event ID for multi-tenant isolation
            model: Embedding model to use
            
        Returns:
            List of embedding vectors
        """
        try:
            client = await self.get_client()
            
            response = await client.embeddings.create(
                model=model,
                input=texts
            )
            
            return [embedding.embedding for embedding in response.data]
            
        except Exception as e:
            error_msg = f"Azure OpenAI embeddings error for event_id={event_id}: {str(e)}"
            print(f"ERROR: {error_msg}")
            return [[0.0] * 1536 for _ in texts]  # Return zero embeddings on error
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Azure OpenAI service health.
        
        Returns:
            Health check status
        """
        try:
            # Simple completion to test connectivity
            test_request = LLMRequest(
                messages=[LLMMessage(role="user", content="Hello")],
                max_tokens=5,
                temperature=0.1
            )
            
            response = await self.chat_completion(test_request)
            
            return {
                "status": "healthy" if not response.error else "error",
                "endpoint": self.config.endpoint,
                "deployment": self.config.deployment,
                "api_version": self.config.api_version,
                "error": response.error,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "endpoint": self.config.endpoint,
                "deployment": self.config.deployment,
                "api_version": self.config.api_version,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global client instance
_azure_openai_client: Optional[AzureOpenAIClient] = None


async def get_azure_openai_client() -> AzureOpenAIClient:
    """Get global Azure OpenAI client instance."""
    global _azure_openai_client
    if _azure_openai_client is None:
        _azure_openai_client = AzureOpenAIClient()
    return _azure_openai_client


# For testing and development
async def test_azure_openai_connection():
    """Test Azure OpenAI connection with sample request."""
    print("Testing Azure OpenAI connection...")
    
    try:
        client = await get_azure_openai_client()
        health = await client.health_check()
        
        print(f"Health check result: {json.dumps(health, indent=2)}")
        
        if health["status"] == "healthy":
            print("✅ Azure OpenAI connection successful!")
        else:
            print("❌ Azure OpenAI connection failed!")
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")


if __name__ == "__main__":
    # Run connection test when executed directly
    asyncio.run(test_azure_openai_connection())
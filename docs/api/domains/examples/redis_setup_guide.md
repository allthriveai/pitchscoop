# Redis Setup Guide for RAG-Powered PitchScoop

This guide explains how to set up Redis with vector search capabilities (RedisVL) for the RAG-powered functionality in PitchScoop.

**Good News**: Your docker-compose.yml already has Redis Stack configured correctly!

## Prerequisites

- Docker and Docker Compose (recommended)
- Redis Stack or Redis with RedisSearch module
- Python dependencies from requirements.txt

## Your Current Setup ✅

Your `docker-compose.yml` already has Redis Stack configured correctly:

```yaml
redis:
  image: redis/redis-stack:7.2.0-v9
  ports:
    - "6379:6379"      # Redis
    - "8001:8001"      # RedisInsight (optional)
  volumes:
    - redis-data:/data
  environment:
    - REDIS_ARGS="--appendonly yes"
  networks:
    - hackathon-net
```

**This is perfect for RAG functionality!**

### Quick Setup Steps

1. **Start your services**:
   ```bash
   cd /Users/allierays/Sites/pitchscoop
   docker-compose up -d
   ```

2. **Verify Redis Stack is running**:
   ```bash
   # Check if Redis Stack is running with vector search
   docker-compose exec redis redis-cli MODULE LIST
   
   # You should see something like:
   # 1) 1) "name"
   #    2) "search"
   #    3) "ver" 
   #    4) "20604"
   ```

## Option 2: Local Redis Setup

### 1. Install Redis Stack

**macOS (using Homebrew):**
```bash
brew tap redis-stack/redis-stack
brew install redis-stack
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list
sudo apt-get update
sudo apt-get install redis-stack
```

### 2. Start Redis Stack

```bash
redis-stack-server --port 6379
```

## Configuration

### Environment Variables ✅

Your `.env.example` is already set up correctly! Just copy it and add your Azure OpenAI credentials:

```bash
cp .env.example .env
```

Then edit `.env` and add your Azure OpenAI details:

```env
# Redis Configuration (already correct)
REDIS_URL=redis://redis:6379/0

# Azure OpenAI Configuration - ADD YOUR REAL VALUES
SYSTEM_LLM_AZURE_ENDPOINT=https://your-resource.openai.azure.com/
SYSTEM_LLM_AZURE_API_KEY=your_actual_api_key_here
SYSTEM_LLM_AZURE_DEPLOYMENT=your_deployment_name
SYSTEM_LLM_AZURE_API_VERSION=2024-02-15-preview
```

### Redis Configuration for Production

For production deployments, consider these Redis configurations:

```redis
# redis.conf
# Memory optimization
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Vector search optimizations
module-load-configs /opt/redis-stack/lib/redisearch.so
```

## Testing the Setup

### 1. Install Python Dependencies

```bash
cd /Users/allierays/Sites/pitchscoop/api

# Install the updated requirements (includes RedisVL)
pip install -r requirements.txt
```

### 2. Run Health Check

```python
# Test script to verify Redis + vector search
import redis
import asyncio
from domains.indexing.services.llamaindex_service import llamaindex_service

async def test_redis_setup():
    try:
        # Test basic Redis connection
        r = redis.Redis(host='localhost', port=6379, decode_responses=False)
        r.ping()
        print("✓ Redis connection successful")
        
        # Test RedisSearch module
        modules = r.execute_command("MODULE", "LIST")
        has_search = any(b"search" in str(module).lower() for module in modules)
        print(f"✓ RedisSearch available: {has_search}")
        
        # Test LlamaIndex service
        health = await llamaindex_service.health_check()
        print(f"✓ LlamaIndex service healthy: {health['healthy']}")
        print(f"  - Redis version: {health.get('redis_version', 'unknown')}")
        print(f"  - RedisSearch available: {health.get('redisearch_available', False)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Setup test failed: {e}")
        return False

# Run the test
asyncio.run(test_redis_setup())
```

### 3. Run Full Integration Test

```bash
cd /Users/allierays/Sites/pitchscoop/api
python -m domains.examples.rag_integration_example
```

## Vector Index Management

### Understanding RedisVL Indices

RedisVL creates vector indices automatically when documents are indexed. Each event and document type gets its own index:

- Index name pattern: `idx_event_{event_id}_{document_type}`
- Key prefix pattern: `event_{event_id}_{document_type}_`

### Viewing Indices

```bash
# Connect to Redis
redis-cli

# List all indices
FT._LIST

# Get index info
FT.INFO idx_event_example_event_2024_01_15_transcript

# Search an index
FT.SEARCH idx_event_example_event_2024_01_15_transcript "medical AI"
```

### Index Management

```python
from domains.indexing.services.llamaindex_service import llamaindex_service

# Check indexing status
status = await document_indexing_service.get_indexing_status("event_2024_01_15")

# Clear all indices for an event
result = await document_indexing_service.clear_event_index("event_2024_01_15")
```

## Performance Optimization

### Memory Configuration

```redis
# Optimize for vector operations
maxmemory-policy volatile-lru

# Index-specific settings
FT.CONFIG SET MAXSEARCHRESULTS 10000
FT.CONFIG SET TIMEOUT 500
```

### Vector Search Performance

- **Embedding dimensions**: 1536 (OpenAI ada-002)
- **Distance metric**: Cosine similarity
- **Index algorithm**: FLAT (for smaller datasets) or HNSW (for larger datasets)

### Monitoring

Access RedisInsight web UI at http://localhost:8001 to:
- Monitor memory usage
- View indices and their statistics
- Debug vector search queries
- Analyze performance metrics

## Troubleshooting

### Common Issues

1. **RedisSearch module not loaded**:
   ```bash
   # Check if Redis Stack is being used instead of regular Redis
   docker logs canaryqa-redis
   ```

2. **Connection refused**:
   ```bash
   # Verify Redis is running
   docker ps | grep redis
   redis-cli ping
   ```

3. **Module command not found**:
   ```bash
   # Use Redis Stack, not regular Redis
   docker-compose down
   docker-compose up -d redis
   ```

4. **Vector search not working**:
   ```python
   # Verify RedisVL installation
   import redisvl
   print(redisvl.__version__)
   ```

### Performance Issues

1. **Slow vector search**:
   - Increase Redis memory allocation
   - Consider HNSW algorithm for large datasets
   - Optimize embedding dimensions if possible

2. **Memory usage**:
   - Monitor Redis memory with `INFO memory`
   - Set appropriate `maxmemory` limits
   - Use memory-efficient serialization

## Integration with CanaryQA

The RAG system will automatically:
1. Create vector indices for each event and document type
2. Index pitch transcripts, rubrics, and scoring data
3. Provide semantic search across all indexed content
4. Enable context-aware conversations and scoring
5. Maintain multi-tenant isolation using event IDs

## Security Considerations

- Use Redis AUTH in production: `requirepass your_password`
- Enable TLS for Redis connections in production
- Restrict Redis network access to application servers only
- Regularly backup Redis data containing vector indices

## Next Steps

1. Start Redis Stack using the Docker Compose configuration
2. Install the updated Python dependencies
3. Run the integration tests to verify setup
4. Begin indexing your pitch data for RAG functionality
5. Test the chat and scoring features with indexed content

For additional support, refer to:
- [Redis Stack Documentation](https://redis.io/docs/stack/)
- [RedisVL Documentation](https://github.com/RedisVentures/redisvl)
- [LlamaIndex Redis Integration](https://docs.llamaindex.ai/en/stable/examples/vector_stores/RedisIndexDemo/)
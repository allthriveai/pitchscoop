#!/usr/bin/env python3
"""
PitchScoop RAG Setup Test

Quick test to verify that your RAG setup is working correctly.
Run this after setting up your .env file and starting docker-compose.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the api directory to Python path
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

async def test_redis_connection():
    """Test basic Redis connection."""
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, decode_responses=False)
        r.ping()
        print("✅ Redis connection successful")
        
        # Test RedisSearch module
        modules = r.execute_command("MODULE", "LIST")
        # modules is a list of lists, flatten and check for search module
        modules_flat = []
        for module in modules:
            if isinstance(module, (list, tuple)):
                modules_flat.extend([str(item).lower() for item in module])
            else:
                modules_flat.append(str(module).lower())
        has_search = any("search" in module_str for module_str in modules_flat)
        print(f"✅ RedisSearch available: {has_search}")
        
        if not has_search:
            print("⚠️  RedisSearch module not found. Make sure you're using Redis Stack.")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Make sure docker-compose is running: docker-compose up -d")
        return False

async def test_llamaindex_service():
    """Test LlamaIndex service configuration."""
    try:
        from api.domains.indexing.services.llamaindex_service import llamaindex_service
        
        health = await llamaindex_service.health_check()
        print(f"✅ LlamaIndex service: {health['healthy']}")
        
        if health['healthy']:
            print(f"   - Redis version: {health.get('redis_version', 'unknown')}")
            print(f"   - RedisSearch: {health.get('redisearch_available', False)}")
            print(f"   - Embedding model: {health.get('embedding_model', 'unknown')}")
        else:
            print(f"   - Error: {health.get('error', 'Unknown error')}")
            
        return health['healthy']
        
    except Exception as e:
        print(f"❌ LlamaIndex service test failed: {e}")
        return False

async def test_azure_openai_config():
    """Test Azure OpenAI configuration."""
    try:
        endpoint = os.getenv("SYSTEM_LLM_AZURE_ENDPOINT")
        api_key = os.getenv("SYSTEM_LLM_AZURE_API_KEY") 
        deployment = os.getenv("SYSTEM_LLM_AZURE_DEPLOYMENT")
        
        if not endpoint:
            print("❌ SYSTEM_LLM_AZURE_ENDPOINT not set in .env")
            return False
        if not api_key:
            print("❌ SYSTEM_LLM_AZURE_API_KEY not set in .env") 
            return False
        if not deployment:
            print("❌ SYSTEM_LLM_AZURE_DEPLOYMENT not set in .env")
            return False
            
        print("✅ Azure OpenAI environment variables configured")
        print(f"   - Endpoint: {endpoint}")
        print(f"   - Deployment: {deployment}")
        print(f"   - API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else 'SET'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure OpenAI config test failed: {e}")
        return False

async def test_dependencies():
    """Test that required dependencies are installed."""
    try:
        import llama_index.core
        print("✅ llama-index: Core module available")
        
        import redisvl
        print(f"✅ redisvl: {redisvl.__version__}")
        
        from llama_index.vector_stores.redis import RedisVectorStore
        print("✅ RedisVectorStore available")
        
        from redisvl.schema import IndexSchema
        print("✅ IndexSchema available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Dependency test failed: {e}")
        return False

async def test_basic_indexing():
    """Test basic document indexing functionality."""
    try:
        from api.domains.indexing.services.document_indexing_service import document_indexing_service
        
        # Test with minimal data
        test_session = {
            "session_id": "test_session_001",
            "team_name": "Test Team",
            "pitch_title": "Test Pitch",
            "status": "completed",
            "final_transcript": {
                "total_text": "This is a test pitch transcript for RAG functionality testing. We use OpenAI for natural language processing and RedisVL for vector search capabilities in our PitchScoop application."
            }
        }
        
        # Try indexing
        result = await document_indexing_service.index_pitch_transcripts(
            event_id="test_event_001",
            session_data_list=[test_session]
        )
        
        if result['success']:
            print("✅ Basic document indexing works")
            print(f"   - Indexed {result['indexed_sessions']} sessions")
            
            # Clean up test data
            await document_indexing_service.clear_event_index("test_event_001")
            print("✅ Test data cleaned up")
            
            return True
        else:
            print(f"❌ Indexing failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Basic indexing test failed: {e}")
        return False

async def main():
    """Run all setup tests."""
    print("🧪 Testing PitchScoop RAG Setup")
    print("=" * 40)
    
    # Check environment
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Run: cp .env.example .env")
        print("   Then add your Azure OpenAI credentials")
        return
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Dependencies", test_dependencies),
        ("Azure OpenAI Config", test_azure_openai_config),
        ("LlamaIndex Service", test_llamaindex_service),
        ("Basic Indexing", test_basic_indexing),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 40)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your RAG setup is ready.")
        print("\nNext steps:")
        print("1. Run the full integration example:")
        print("   python -m domains.examples.rag_integration_example")
        print("2. Start using RAG features in your application")
        print("3. Check RedisInsight at http://localhost:8001")
    elif passed >= total * 0.7:
        print("\n⚠️  Most tests passed, but some issues need attention.")
        print("Check the failed tests above and fix any configuration issues.")
    else:
        print("\n❌ Several tests failed. Please check your setup:")
        print("1. Make sure docker-compose is running: docker-compose up -d")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Set up .env with Azure OpenAI credentials")

if __name__ == "__main__":
    asyncio.run(main())
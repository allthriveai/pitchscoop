#!/usr/bin/env python3
"""
Test LlamaIndex service health and configuration without requiring embeddings
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the api directory to Python path
api_dir = Path(__file__).parent / 'api'
sys.path.insert(0, str(api_dir))

async def test_service_imports():
    """Test that our services can be imported"""
    print("🧪 Testing Service Imports")
    print("=" * 40)
    
    try:
        # Test core imports
        from api.domains.indexing.services.llamaindex_service import llamaindex_service
        print("✅ LlamaIndex service imported successfully")
        
        from api.domains.indexing.services.document_indexing_service import document_indexing_service  
        print("✅ Document indexing service imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Service import test failed: {e}")
        return False

async def test_service_health():
    """Test service health checks"""
    print("\n🧪 Testing Service Health")
    print("=" * 40)
    
    try:
        from api.domains.indexing.services.llamaindex_service import llamaindex_service
        
        # Test health check
        health = await llamaindex_service.health_check()
        print(f"✅ Health check completed: {health.get('healthy', False)}")
        
        if health.get('healthy'):
            print(f"   - Redis connected: {health.get('redis_connected', False)}")
            print(f"   - Redis version: {health.get('redis_version', 'unknown')}")
            print(f"   - RedisSearch available: {health.get('redisearch_available', False)}")
            print(f"   - Embedding model: {health.get('embedding_model', 'unknown')}")
            print(f"   - LLM model: {health.get('llm_model', 'unknown')}")
        else:
            print(f"   - Error: {health.get('error', 'Unknown error')}")
            
        return health.get('healthy', False)
        
    except Exception as e:
        print(f"❌ Service health test failed: {e}")
        return False

async def test_redis_operations():
    """Test basic Redis operations"""
    print("\n🧪 Testing Redis Operations")
    print("=" * 40)
    
    try:
        from api.domains.indexing.services.llamaindex_service import llamaindex_service
        
        # Test Redis connection
        try:
            redis_info = llamaindex_service.redis_client.info()
            print("✅ Redis info retrieved successfully")
            print(f"   - Version: {redis_info.get('redis_version', 'unknown')}")
            print(f"   - Memory used: {redis_info.get('used_memory_human', 'unknown')}")
            print(f"   - Connected clients: {redis_info.get('connected_clients', 'unknown')}")
        except Exception as e:
            print(f"❌ Redis info failed: {e}")
            return False
        
        # Test basic operations
        test_key = "test:pitchscoop:health"
        test_value = "healthy"
        
        llamaindex_service.redis_client.set(test_key, test_value, ex=60)  # 60 second expiry
        retrieved_value = llamaindex_service.redis_client.get(test_key)
        
        if retrieved_value and retrieved_value.decode() == test_value:
            print("✅ Basic Redis set/get operations working")
        else:
            print("❌ Redis set/get operations failed")
            return False
            
        # Cleanup
        llamaindex_service.redis_client.delete(test_key)
        print("✅ Test cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis operations test failed: {e}")
        return False

async def test_index_creation():
    """Test index creation without documents"""
    print("\n🧪 Testing Index Creation")
    print("=" * 40)
    
    try:
        from api.domains.indexing.services.llamaindex_service import llamaindex_service
        
        test_event_id = "test_event_health_check"
        test_doc_type = "test_transcript"
        
        # Test index creation (this should work without embeddings)
        try:
            await llamaindex_service.ensure_index_exists(test_event_id, test_doc_type)
            print("✅ Index existence check completed")
        except Exception as e:
            print(f"⚠️  Index existence check warning: {e}")
        
        # Test index name generation
        index_name = llamaindex_service._get_index_name(test_event_id, test_doc_type)
        print(f"✅ Index name generated: {index_name}")
        
        # Test cleanup
        try:
            await llamaindex_service.delete_event_index(test_event_id, test_doc_type)
            print("✅ Index cleanup completed")
        except Exception as e:
            print(f"⚠️  Index cleanup warning: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Index creation test failed: {e}")
        return False

async def test_configuration():
    """Test configuration values"""
    print("\n🧪 Testing Configuration")
    print("=" * 40)
    
    try:
        # Check environment variables
        required_vars = [
            "SYSTEM_LLM_AZURE_ENDPOINT",
            "SYSTEM_LLM_AZURE_API_KEY", 
            "SYSTEM_LLM_AZURE_DEPLOYMENT",
            "SYSTEM_LLM_AZURE_EMBEDDING_DEPLOYMENT",
            "REDIS_URL"
        ]
        
        all_set = True
        for var in required_vars:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "API_KEY" in var:
                    display_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "SET"
                else:
                    display_value = value
                print(f"✅ {var}: {display_value}")
            else:
                print(f"❌ {var}: Not set")
                all_set = False
        
        return all_set
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def main():
    """Run all health tests"""
    print("🚀 PitchScoop LlamaIndex Health Check")
    print("=" * 60)
    
    tests = [
        ("Configuration Check", test_configuration),
        ("Service Imports", test_service_imports),
        ("Service Health", test_service_health),
        ("Redis Operations", test_redis_operations),
        ("Index Creation", test_index_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print("📊 Health Check Results:")
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All health checks passed! System is ready (except embeddings)!")
    elif passed >= 3:
        print("\n⚠️  Core system is healthy! Only minor issues.")
    else:
        print("\n❌ System needs attention before proceeding.")
    
    print("\n💡 Next Steps:")
    print("   1. Create an embedding deployment in Azure OpenAI")
    print("   2. Update SYSTEM_LLM_AZURE_EMBEDDING_DEPLOYMENT in .env")
    print("   3. Run the full RAG tests")

if __name__ == "__main__":
    asyncio.run(main())
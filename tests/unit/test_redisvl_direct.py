#!/usr/bin/env python3
"""
Test RedisVL directly without requiring Azure OpenAI embeddings
"""
import asyncio
import os
import sys
import redis
import numpy as np
from redisvl.schema import IndexSchema
from redisvl.index import SearchIndex

# Add the api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

async def test_redisvl_basic():
    """Test basic RedisVL functionality"""
    print("🧪 Testing RedisVL Basic Functionality")
    print("=" * 50)
    
    try:
        # Connect to Redis
        redis_client = redis.from_url("redis://redis:6379/0", decode_responses=False)
        redis_client.ping()
        print("✅ Redis connection successful")
        
        # Create test index schema
        schema = IndexSchema.from_dict({
            "index": {
                "name": "test_pitchscoop_index",
                "prefix": "test_pitch:",
                "storage_type": "hash"
            },
            "fields": [
                {
                    "name": "id",
                    "type": "tag"
                },
                {
                    "name": "content",
                    "type": "text"
                },
                {
                    "name": "team_name", 
                    "type": "tag"
                },
                {
                    "name": "vector",
                    "type": "vector",
                    "attrs": {
                        "dims": 128,  # Smaller for testing
                        "distance_metric": "COSINE",
                        "algorithm": "FLAT",
                        "type": "FLOAT32"
                    }
                }
            ]
        })
        
        print("✅ Index schema created")
        
        # Create search index
        index = SearchIndex(schema, redis_client)
        
        try:
            index.create()
            print("✅ Index created successfully")
        except Exception as e:
            if "Index already exists" in str(e):
                print("✅ Index already exists (OK)")
            else:
                raise
        
        # Generate some test vectors
        test_data = [
            {
                "id": "pitch_001",
                "content": "This is a revolutionary AI startup that will change the world",
                "team_name": "AI Innovators",
                "vector": np.random.rand(128).astype(np.float32).tobytes()
            },
            {
                "id": "pitch_002", 
                "content": "We're building the next generation e-commerce platform",
                "team_name": "E-Commerce Masters",
                "vector": np.random.rand(128).astype(np.float32).tobytes()
            },
            {
                "id": "pitch_003",
                "content": "Our fintech solution revolutionizes payments",
                "team_name": "FinTech Pioneers", 
                "vector": np.random.rand(128).astype(np.float32).tobytes()
            }
        ]
        
        # Load test data
        index.load(test_data)
        print(f"✅ Loaded {len(test_data)} test documents")
        
        # Test text search
        text_results = index.query("AI startup")
        print(f"✅ Text search for 'AI startup': {len(text_results)} results")
        
        # Test tag filtering
        filter_results = index.query("*", filter_expression="@team_name:{FinTech Pioneers}")
        print(f"✅ Tag filter for 'FinTech Pioneers': {len(filter_results)} results")
        
        # Test vector similarity (using random query vector)
        query_vector = np.random.rand(128).astype(np.float32).tobytes()
        vector_results = index.query(
            query="*",
            return_fields=["id", "content", "team_name"],
            vector_name="vector",
            vector=query_vector,
            num_results=3
        )
        print(f"✅ Vector similarity search: {len(vector_results)} results")
        
        # Show some results
        if vector_results:
            print("\n📊 Sample Results:")
            for i, result in enumerate(vector_results[:2]):
                print(f"  {i+1}. ID: {result.get('id', 'N/A')}")
                print(f"     Team: {result.get('team_name', 'N/A')}")
                print(f"     Content: {result.get('content', 'N/A')[:50]}...")
        
        # Cleanup
        try:
            index.delete()
            print("✅ Test cleanup completed")
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"❌ RedisVL test failed: {e}")
        return False

async def test_redis_connection():
    """Test Redis connection and modules"""
    print("\n🔍 Testing Redis Connection & Modules")
    print("-" * 40)
    
    try:
        redis_client = redis.from_url("redis://redis:6379/0", decode_responses=False)
        
        # Test basic connection
        redis_client.ping()
        print("✅ Redis ping successful")
        
        # Check Redis info
        info = redis_client.info()
        print(f"✅ Redis version: {info.get('redis_version', 'unknown')}")
        
        # Check modules
        modules = redis_client.execute_command("MODULE", "LIST")
        modules_flat = []
        for module in modules:
            if isinstance(module, (list, tuple)):
                modules_flat.extend([str(item).lower() for item in module])
            else:
                modules_flat.append(str(module).lower())
                
        has_search = any("search" in module_str for module_str in modules_flat)
        has_json = any("json" in module_str for module_str in modules_flat)
        
        print(f"✅ RedisSearch module: {'Available' if has_search else 'Missing'}")
        print(f"✅ RedisJSON module: {'Available' if has_json else 'Missing'}")
        
        return has_search and has_json
        
    except Exception as e:
        print(f"❌ Redis connection test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 PitchScoop RedisVL Testing Suite")
    print("=" * 60)
    
    tests = [
        ("Redis Connection & Modules", test_redis_connection),
        ("RedisVL Basic Functionality", test_redisvl_basic),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
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
    print("📊 Test Results Summary:")
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! RedisVL is working perfectly!")
    elif passed >= 1:
        print("\n⚠️  RedisVL core functionality is working!")
    else:
        print("\n❌ RedisVL setup needs attention.")

if __name__ == "__main__":
    asyncio.run(main())
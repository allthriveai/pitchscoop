#!/usr/bin/env python3
"""
Redis Vector Integration Test

Tests the complete Redis Vector integration to ensure it works
properly as a replacement for Qdrant.
"""
import asyncio
import sys
import os
import logging
from pathlib import Path

# Add the api directory to Python path
api_path = Path(__file__).parent / "api"
sys.path.insert(0, str(api_path))

from domains.indexing.services.redis_vector_service import redis_vector_service
from llama_index.core import Document

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_redis_vector_integration():
    """Test complete Redis Vector integration."""
    
    print("🧪 Redis Vector Integration Test")
    print("=" * 60)
    
    test_event_id = "test_event_redis_vector"
    test_results = {
        "health_check": False,
        "index_creation": False,
        "document_indexing": False,
        "document_querying": False,
        "index_listing": False,
        "index_cleanup": False
    }
    
    try:
        # Test 1: Health Check
        print("\n1️⃣ Testing Redis Vector health check...")
        health_result = await redis_vector_service.health_check()
        
        if health_result["healthy"]:
            print(f"✅ Redis Vector healthy: {health_result}")
            test_results["health_check"] = True
            
            if not health_result.get("vector_search_available", False):
                print("⚠️  Warning: Vector search module not detected in Redis")
                print("   Make sure you're using redis-stack image")
        else:
            print(f"❌ Redis Vector unhealthy: {health_result}")
            return test_results
        
        # Test 2: Index Creation
        print("\n2️⃣ Testing index creation...")
        try:
            await redis_vector_service.ensure_index_exists(test_event_id, "test_documents")
            print("✅ Index creation successful")
            test_results["index_creation"] = True
        except Exception as e:
            print(f"❌ Index creation failed: {e}")
            return test_results
        
        # Test 3: Document Indexing
        print("\n3️⃣ Testing document indexing...")
        test_documents = [
            Document(
                text="This is a test document about AI and machine learning applications in hackathons.",
                metadata={"type": "test", "topic": "AI"}
            ),
            Document(
                text="Here we discuss blockchain technology and its use in decentralized applications.",
                metadata={"type": "test", "topic": "blockchain"}
            ),
            Document(
                text="This document covers web development using React and Node.js for building scalable applications.",
                metadata={"type": "test", "topic": "web_dev"}
            )
        ]
        
        indexing_result = await redis_vector_service.index_documents(
            event_id=test_event_id,
            document_type="test_documents",
            documents=test_documents
        )
        
        if indexing_result["success"]:
            print(f"✅ Document indexing successful: {indexing_result['indexed_count']} documents")
            test_results["document_indexing"] = True
        else:
            print(f"❌ Document indexing failed: {indexing_result}")
            return test_results
        
        # Test 4: Document Querying
        print("\n4️⃣ Testing document querying...")
        query_result = await redis_vector_service.query_index(
            event_id=test_event_id,
            document_type="test_documents",
            query="Tell me about AI and machine learning",
            top_k=2
        )
        
        if query_result["success"]:
            print(f"✅ Document querying successful: {len(query_result['source_nodes'])} results")
            print(f"   Response: {query_result['response'][:100]}...")
            for i, node in enumerate(query_result["source_nodes"]):
                print(f"   Result {i+1}: Score {node['score']:.3f}, Topic: {node.get('metadata', {}).get('topic', 'unknown')}")
            test_results["document_querying"] = True
        else:
            print(f"❌ Document querying failed: {query_result}")
            return test_results
        
        # Test 5: Index Listing
        print("\n5️⃣ Testing index listing...")
        list_result = await redis_vector_service.list_event_indices(test_event_id)
        
        if list_result["success"]:
            print(f"✅ Index listing successful: {len(list_result['indices'])} indices found")
            for idx in list_result["indices"]:
                print(f"   Index: {idx['document_type']} -> {idx['index_name']}")
            test_results["index_listing"] = True
        else:
            print(f"❌ Index listing failed: {list_result}")
        
        # Test 6: Index Cleanup
        print("\n6️⃣ Testing index cleanup...")
        cleanup_result = await redis_vector_service.delete_event_index(
            event_id=test_event_id,
            document_type="test_documents"
        )
        
        if cleanup_result["success"]:
            print(f"✅ Index cleanup successful: {cleanup_result['deleted_documents']} documents deleted")
            test_results["index_cleanup"] = True
        else:
            print(f"❌ Index cleanup failed: {cleanup_result}")
        
    except Exception as e:
        print(f"❌ Integration test failed with exception: {e}")
        logger.exception("Test failure details:")
    
    # Summary
    print("\n📊 Test Results Summary")
    print("-" * 40)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All Redis Vector integration tests passed!")
        print("✅ Ready to replace Qdrant with Redis Vector Search")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed")
        print("❌ Redis Vector integration needs attention before replacing Qdrant")
    
    return test_results


async def main():
    """Run the integration test."""
    try:
        test_results = await test_redis_vector_integration()
        
        # Exit code based on results
        if all(test_results.values()):
            sys.exit(0)  # All tests passed
        else:
            sys.exit(1)  # Some tests failed
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
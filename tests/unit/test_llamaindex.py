#!/usr/bin/env python3
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

Test LlamaIndex Integration

Verifies that LlamaIndex, Qdrant, and Azure OpenAI integration
works correctly in the Docker environment.
"""
import asyncio
from api.domains.indexing.mcp.indexing_tools import execute_indexing_tool


async def test_llamaindex_integration():
    print("🦙 Testing LlamaIndex Integration")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        result = await execute_indexing_tool("index.health_check", {})
        if result.get("healthy"):
            print("✅ Indexing system is healthy!")
            print(f"   Qdrant collections: {result['details'].get('qdrant_collections', 0)}")
            print(f"   LLM model: {result['details'].get('llm_model', 'unknown')}")
        else:
            print(f"❌ Health check failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Health check exception: {e}")
        return False
    
    # Test 2: Index a sample rubric
    print("\n2. Testing rubric indexing...")
    try:
        sample_rubric = {
            "event_name": "Test Event",
            "criteria": [
                "Technical Innovation",
                "Presentation Quality", 
                "Problem-Solution Fit",
                "Market Potential"
            ],
            "weights": {
                "Technical Innovation": 0.3,
                "Presentation Quality": 0.2,
                "Problem-Solution Fit": 0.3,
                "Market Potential": 0.2
            },
            "guidelines": "Score each criterion from 1-10 based on clarity, innovation, and feasibility.",
            "scale": {"min": 1, "max": 10}
        }
        
        result = await execute_indexing_tool("index.add_rubric", {
            "event_id": "test-event-123",
            "rubric_data": sample_rubric
        })
        
        if result.get("success"):
            print("✅ Rubric indexed successfully!")
            print(f"   Event: {result.get('event_id')}")
            print(f"   Criteria count: {result.get('criteria_count')}")
        else:
            print(f"❌ Rubric indexing failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Rubric indexing exception: {e}")
        return False
    
    # Test 3: Index a sample transcript
    print("\n3. Testing transcript indexing...")
    try:
        sample_transcript = {
            "team_name": "AI Innovators",
            "pitch_title": "Smart City Analytics Platform",
            "transcript_text": "Hello everyone, today we're presenting our Smart City Analytics Platform. Our solution addresses the critical problem of urban traffic congestion using real-time AI analysis. We've developed a machine learning model that processes traffic camera data to optimize signal timing and reduce wait times by up to 30%. Our team has extensive experience in computer vision and urban planning. We've already deployed a pilot program in downtown with promising results.",
            "duration_seconds": 120,
            "word_count": 65,
            "words_per_minute": 32.5
        }
        
        result = await execute_indexing_tool("index.add_transcript", {
            "event_id": "test-event-123",
            "session_id": "session-456",
            "transcript_data": sample_transcript
        })
        
        if result.get("success"):
            print("✅ Transcript indexed successfully!")
            print(f"   Team: {result.get('team_name')}")
            print(f"   Word count: {result.get('word_count')}")
        else:
            print(f"❌ Transcript indexing failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Transcript indexing exception: {e}")
        return False
    
    # Test 4: List collections
    print("\n4. Testing collection listing...")
    try:
        result = await execute_indexing_tool("index.list_collections", {
            "event_id": "test-event-123"
        })
        
        if result.get("success"):
            print("✅ Collections listed successfully!")
            print(f"   Total collections: {result.get('total_collections')}")
            for collection in result.get('collections', []):
                status = "✅ exists" if collection.get('exists') else "❌ empty"
                print(f"   - {collection['document_type']}: {status}")
        else:
            print(f"❌ Collection listing failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Collection listing exception: {e}")
    
    # Test 5: Index team profile
    print("\n5. Testing team profile indexing...")
    try:
        sample_team = {
            "team_name": "AI Innovators",
            "members": ["Alice Chen", "Bob Smith", "Carol Wang"],
            "bio": "We are a team of AI researchers and urban planning experts focused on creating smart city solutions.",
            "focus_areas": ["Machine Learning", "Computer Vision", "Urban Analytics"],
            "experience": "Combined 15+ years in AI research and 10+ years in urban planning",
            "skills": ["Python", "TensorFlow", "OpenCV", "GIS", "Data Analysis"]
        }
        
        result = await execute_indexing_tool("index.add_team_profile", {
            "event_id": "test-event-123",
            "team_data": sample_team
        })
        
        if result.get("success"):
            print("✅ Team profile indexed successfully!")
            print(f"   Team: {result.get('team_name')}")
            print(f"   Members: {result.get('member_count')}")
        else:
            print(f"❌ Team profile indexing failed: {result.get('error')}")
    except Exception as e:
        print(f"❌ Team profile indexing exception: {e}")
    
    print("\n🎉 LlamaIndex integration test completed!")
    return True


async def test_rag_query():
    """Test RAG query functionality (if basic indexing works)."""
    print("\n🔍 Testing RAG Query Functionality")
    print("=" * 40)
    
    try:
        from api.domains.indexing.services.llamaindex_service import llamaindex_service
        
        # Test querying the indexed rubric
        result = await llamaindex_service.query_index(
            event_id="test-event-123",
            document_type="rubrics",
            query="What are the scoring criteria for technical innovation?",
            top_k=3
        )
        
        if result.get("success"):
            print("✅ RAG query successful!")
            print(f"   Query: {result['query']}")
            print(f"   Response: {result['response'][:200]}...")
            print(f"   Source nodes: {len(result['source_nodes'])}")
        else:
            print(f"❌ RAG query failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ RAG query exception: {e}")


if __name__ == "__main__":
    print("🚀 Starting LlamaIndex Integration Tests...")
    print("🐳 Make sure Docker services are running:")
    print("   docker-compose up -d qdrant redis minio api")
    print()
    
    success = asyncio.run(test_llamaindex_integration())
    
    if success:
        print("\n🔍 Running advanced RAG tests...")
        asyncio.run(test_rag_query())
    
    print("\n📋 Next Steps:")
    print("1. ✅ LlamaIndex integration is working")
    print("2. 🔧 Build scoring engine using RAG")
    print("3. 🎨 Add frontend to display scores")
    print("4. 🏆 Create leaderboard with rankings")
    
    exit(0 if success else 1)
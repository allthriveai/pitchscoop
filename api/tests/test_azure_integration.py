#!/usr/bin/env python3
"""
Azure OpenAI Integration Test Runner

This script tests the complete Azure OpenAI integration with your existing
pitch recording and scoring workflow. Run this to verify everything is working.

Usage:
    python test_azure_integration.py

Requirements:
    - Azure OpenAI environment variables set
    - Redis running (for session storage)
    - All dependencies installed: pip install -r requirements.txt
"""
import asyncio
import json
import os
import sys
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_environment_setup():
    """Test that all required environment variables are set."""
    print("🔧 Testing environment setup...")
    
    required_vars = [
        "SYSTEM_LLM_AZURE_ENDPOINT",
        "SYSTEM_LLM_AZURE_API_KEY", 
        "SYSTEM_LLM_AZURE_DEPLOYMENT",
        "SYSTEM_LLM_AZURE_API_VERSION"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set these in your .env file or environment")
        return False
    
    print("✅ All required environment variables are set")
    return True


async def test_azure_openai_client():
    """Test Azure OpenAI client connectivity."""
    print("\n🔗 Testing Azure OpenAI connectivity...")
    
    try:
        from domains.shared.infrastructure.azure_openai_client import get_azure_openai_client
        
        client = await get_azure_openai_client()
        health = await client.health_check()
        
        print(f"   Status: {health['status']}")
        print(f"   Endpoint: {health['endpoint']}")
        print(f"   Deployment: {health['deployment']}")
        
        if health['status'] == 'healthy':
            print("✅ Azure OpenAI client is working")
            return True
        else:
            print(f"❌ Azure OpenAI client error: {health.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Azure OpenAI client test failed: {str(e)}")
        return False


async def test_langchain_integration():
    """Test LangChain integration with Azure OpenAI."""
    print("\n⛓️  Testing LangChain integration...")
    
    try:
        from domains.shared.infrastructure.langchain_config import get_pitch_analysis_chains
        
        chains = get_pitch_analysis_chains()
        
        # Test with a sample transcript
        sample_transcript = """
        Hi, I'm presenting CanaryQA, our AI agent for document quality assurance.
        We've built a vertical-specific agent that uses advanced reasoning to analyze 
        technical documentation. Our agent integrates three sponsor tools: OpenAI for 
        language processing, Qdrant for vector search, and MinIO for document storage.
        The agent can automatically detect quality issues, suggest improvements, and 
        generate reports. Thank you.
        """
        
        result = await chains.score_pitch(sample_transcript, event_id="test-integration")
        
        if result['success']:
            print("✅ LangChain integration is working")
            analysis = result['analysis']
            print(f"   Sample analysis completed successfully")
            return True
        else:
            print(f"❌ LangChain integration failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ LangChain integration test failed: {str(e)}")
        return False


async def test_scoring_mcp_tools():
    """Test scoring MCP tools integration."""
    print("\n🎯 Testing scoring MCP tools...")
    
    try:
        from domains.scoring.mcp.scoring_mcp_tools import (
            list_scoring_tools,
            get_scoring_tools_summary,
            execute_scoring_mcp_tool
        )
        
        # Test tool registry
        tools = list_scoring_tools()
        print(f"   Available tools: {len(tools)}")
        for tool in tools:
            print(f"     - {tool}")
        
        # Test health check
        health_result = await execute_scoring_mcp_tool("analysis.health_check", {
            "event_id": "test-integration",
            "detailed_check": True
        })
        
        if health_result.get('status') == 'healthy':
            print("✅ Scoring MCP tools are working")
            return True
        else:
            print(f"❌ Scoring MCP tools health check failed: {health_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Scoring MCP tools test failed: {str(e)}")
        return False


async def test_complete_workflow():
    """Test the complete workflow with mock session data."""
    print("\n🔄 Testing complete pitch scoring workflow...")
    
    try:
        from domains.scoring.mcp.scoring_mcp_tools import execute_scoring_mcp_tool
        import redis.asyncio as redis
        
        # Create mock session data in Redis (simulating completed pitch recording)
        # Try Docker Redis first, fallback to localhost
        try:
            redis_client = redis.from_url("redis://redis:6379/0", decode_responses=True)
            await redis_client.ping()  # Test connection
        except:
            try:
                redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
                await redis_client.ping()  # Test connection
            except Exception as e:
                print(f"   ❌ Cannot connect to Redis: {e}")
                return False
        
        mock_session = {
            "session_id": "integration-test-123",
            "event_id": "test-event",
            "event_name": "Test Competition",
            "team_name": "Test Team",
            "pitch_title": "AI Integration Test",
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "final_transcript": {
                "segments_count": 3,
                "total_text": "Hi, I'm presenting our AI agent for document analysis. We use OpenAI, Qdrant, and MinIO. Our agent provides automated quality feedback for technical documents.",
                "segments": []
            }
        }
        
        # Store mock session
        await redis_client.setex(
            "event:test-event:session:integration-test-123",
            300,  # 5 minutes TTL
            json.dumps(mock_session)
        )
        
        print("   Mock session created in Redis")
        
        # Test scoring
        score_result = await execute_scoring_mcp_tool("analysis.score_pitch", {
            "session_id": "integration-test-123",
            "event_id": "test-event",  # Match the event_id used when creating session
            "judge_id": "integration-tester"
        })
        
        if score_result.get('success'):
            print("✅ Complete workflow test passed")
            scores = score_result.get('scores', {})
            print(f"   Total Score: {scores.get('total_score', 'N/A')}")
            return True
        else:
            print(f"❌ Complete workflow test failed: {score_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Complete workflow test failed: {str(e)}")
        return False
    finally:
        try:
            await redis_client.close()
        except:
            pass


async def main():
    """Run all integration tests."""
    print("🚀 Azure OpenAI Integration Test Suite")
    print("=" * 50)
    
    tests = [
        test_environment_setup,
        test_azure_openai_client, 
        test_langchain_integration,
        test_scoring_mcp_tools,
        test_complete_workflow
    ]
    
    results = []
    for test_func in tests:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    test_names = [
        "Environment Setup",
        "Azure OpenAI Client",
        "LangChain Integration", 
        "Scoring MCP Tools",
        "Complete Workflow"
    ]
    
    for i, (test_name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Azure OpenAI integration is ready to use.")
        print("\nNext steps:")
        print("1. Use MCP tools in AI assistants:")
        print("   - analysis.score_pitch - Score completed pitch recordings")
        print("   - analysis.analyze_tools - Analyze sponsor tool usage")
        print("   - analysis.compare_pitches - Compare multiple pitches") 
        print("2. Integration with recordings workflow is complete")
        print("3. Multi-tenant isolation with event_id is implemented")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix issues before using.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
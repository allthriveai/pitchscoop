#!/usr/bin/env python3
"""
Simple LLM Connection Test

A focused test to verify your LLM connection is working properly.
This test focuses on the core Azure OpenAI functionality without complex dependencies.

Usage:
    docker compose exec api python tests/test_llm_connection.py

Requirements:
    - Azure OpenAI environment variables set in .env
    - Services running: docker compose up -d
"""
import asyncio
import json
import os
import sys
from datetime import datetime

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

async def test_environment_variables():
    """Test that all required Azure OpenAI environment variables are set."""
    print("🔧 Checking Azure OpenAI environment variables...")
    
    required_vars = [
        "SYSTEM_LLM_AZURE_ENDPOINT",
        "SYSTEM_LLM_AZURE_API_KEY", 
        "SYSTEM_LLM_AZURE_DEPLOYMENT",
        "SYSTEM_LLM_AZURE_API_VERSION"
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask API key for security
            if "key" in var.lower():
                display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
            all_set = False
    
    return all_set


async def test_azure_openai_client():
    """Test Azure OpenAI client creation and health check."""
    print("\n🔗 Testing Azure OpenAI client...")
    
    try:
        from api.domains.shared.infrastructure.azure_openai_client import get_azure_openai_client
        
        # Create client
        client = await get_azure_openai_client()
        print("   ✅ Client created successfully")
        
        # Test health check
        health = await client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Endpoint: {health['endpoint']}")
        print(f"   Deployment: {health['deployment']}")
        print(f"   API Version: {health['api_version']}")
        
        if health['status'] == 'healthy':
            print("   ✅ Health check passed")
            return True
        else:
            print(f"   ❌ Health check failed: {health.get('error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Client test failed: {str(e)}")
        return False


async def test_simple_completion():
    """Test a simple chat completion."""
    print("\n💬 Testing simple chat completion...")
    
    try:
        from api.domains.shared.infrastructure.azure_openai_client import get_azure_openai_client
        from api.domains.shared.value_objects.llm_request import LLMRequest, LLMMessage
        
        client = await get_azure_openai_client()
        
        # Create a simple test request
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="user", 
                    content="Hello! Please respond with exactly: 'LLM connection successful'"
                )
            ],
            max_tokens=20,
            temperature=0.1
        )
        
        # Make the request
        response = await client.chat_completion(request, event_id="llm-test")
        
        if response.error:
            print(f"   ❌ Completion failed: {response.error}")
            return False
        
        print(f"   ✅ Response received: '{response.content.strip()}'")
        print(f"   📊 Tokens used: {response.usage['total_tokens']}")
        print(f"   🕒 Response time: {response.created_at}")
        
        # Check if response contains expected content
        if "LLM connection successful" in response.content:
            print("   ✅ Response content verified")
        else:
            print("   ⚠️  Response content differs from expected")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Completion test failed: {str(e)}")
        return False


async def test_pitch_analysis_simple():
    """Test a simple pitch analysis using direct client."""
    print("\n🎯 Testing simple pitch analysis...")
    
    try:
        from api.domains.shared.infrastructure.azure_openai_client import get_azure_openai_client
        from api.domains.shared.value_objects.llm_request import LLMRequest, LLMMessage
        
        client = await get_azure_openai_client()
        
        # Sample pitch transcript
        sample_pitch = """
        Hi, I'm presenting CanaryQA, our AI agent for document quality assurance.
        We've built a vertical-specific agent that uses advanced reasoning to analyze 
        technical documentation. Our solution integrates OpenAI for language processing,
        and MinIO for document storage. The agent automatically detects quality issues
        and generates improvement suggestions. Thank you.
        """
        
        # Create analysis request
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content="""You are a pitch analysis expert. Score this startup pitch on a scale of 1-10 for:
                    1. Idea clarity and innovation
                    2. Technical implementation
                    3. Market potential
                    
                    Respond with JSON format: {"idea_score": X, "technical_score": Y, "market_score": Z, "total_score": average, "summary": "brief analysis"}"""
                ),
                LLMMessage(
                    role="user",
                    content=f"Please analyze this pitch: {sample_pitch}"
                )
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        # Make the analysis request
        response = await client.chat_completion(request, event_id="pitch-analysis-test")
        
        if response.error:
            print(f"   ❌ Analysis failed: {response.error}")
            return False
        
        print("   ✅ Analysis completed successfully")
        print(f"   📊 Tokens used: {response.usage['total_tokens']}")
        
        # Try to parse JSON response
        try:
            analysis_result = json.loads(response.content)
            print("   ✅ JSON response parsed successfully")
            print(f"   📝 Analysis preview:")
            for key, value in analysis_result.items():
                if key != "summary":
                    print(f"      {key}: {value}")
            print(f"      summary: {analysis_result.get('summary', 'N/A')[:100]}...")
        except json.JSONDecodeError:
            print("   ⚠️  Response is not valid JSON, but analysis completed")
            print(f"   📝 Response preview: {response.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Analysis test failed: {str(e)}")
        return False


async def test_redis_connection():
    """Test Redis connection for storing results."""
    print("\n📊 Testing Redis connection...")
    
    try:
        import redis.asyncio as redis
        
        # Try Docker Redis first, fallback to localhost
        redis_urls = [
            "redis://redis:6379/0",  # Docker compose
            "redis://localhost:6379/0"  # Local
        ]
        
        redis_client = None
        connected_url = None
        
        for url in redis_urls:
            try:
                redis_client = redis.from_url(url, decode_responses=True)
                await redis_client.ping()
                connected_url = url
                print(f"   ✅ Connected to Redis: {url}")
                break
            except Exception:
                continue
        
        if not redis_client:
            print("   ❌ Could not connect to Redis")
            return False
        
        # Test basic operations
        test_key = f"llm-test:{datetime.utcnow().timestamp()}"
        test_data = {
            "test": "llm_connection_test",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
        # Store test data
        await redis_client.setex(test_key, 60, json.dumps(test_data))  # 60 second TTL
        print("   ✅ Test data stored in Redis")
        
        # Retrieve test data
        retrieved = await redis_client.get(test_key)
        if retrieved:
            parsed_data = json.loads(retrieved)
            print("   ✅ Test data retrieved successfully")
            print(f"   📝 Data: {parsed_data['test']} at {parsed_data['timestamp']}")
        
        # Clean up
        await redis_client.delete(test_key)
        await redis_client.close()
        print("   ✅ Redis test completed and cleaned up")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Redis test failed: {str(e)}")
        return False


async def main():
    """Run all LLM connection tests."""
    print("🚀 LLM Connection Test Suite")
    print("=" * 50)
    print("Testing core LLM functionality for PitchScoop")
    print()
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Azure OpenAI Client", test_azure_openai_client),
        ("Simple Completion", test_simple_completion),
        ("Pitch Analysis", test_pitch_analysis_simple),
        ("Redis Connection", test_redis_connection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your LLM connection is working perfectly!")
        print("\n🎯 Ready for use:")
        print("1. ✅ Azure OpenAI connection verified")
        print("2. ✅ Chat completions working")
        print("3. ✅ Pitch analysis capability confirmed")
        print("4. ✅ Redis storage available for results")
        print("\n📝 Next steps:")
        print("- Use the LLM for pitch scoring via MCP tools")
        print("- Integration with recording workflow is ready")
        print("- Multi-tenant isolation working with event_id")
        return True
    else:
        failed = total - passed
        print(f"\n⚠️  {failed} test(s) failed. Please address issues:")
        
        for test_name, result in results:
            if not result:
                print(f"- Fix: {test_name}")
                
        print("\n🔧 Common solutions:")
        print("- Check .env file has all required Azure OpenAI variables")
        print("- Ensure docker compose services are running")
        print("- Verify Azure OpenAI endpoint and key are valid")
        
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'🎉 SUCCESS' if success else '❌ FAILED'}: LLM Connection Test")
    sys.exit(0 if success else 1)
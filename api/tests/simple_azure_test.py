#!/usr/bin/env python3
"""
Simple Azure OpenAI Test

Quick test to verify Azure OpenAI integration is working.
"""
import asyncio
import os
import sys

# Add the parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_azure_connection():
    """Test basic Azure OpenAI connection."""
    print("🔧 Testing Azure OpenAI environment variables...")
    
    required_vars = [
        "SYSTEM_LLM_AZURE_ENDPOINT",
        "SYSTEM_LLM_AZURE_API_KEY", 
        "SYSTEM_LLM_AZURE_DEPLOYMENT",
        "SYSTEM_LLM_AZURE_API_VERSION"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Only show first/last few chars for security
            if "key" in var.lower():
                display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set")
    
    print("\n🔗 Testing Azure OpenAI client import...")
    try:
        from domains.shared.infrastructure.azure_openai_client import get_azure_openai_client
        print("✅ Azure OpenAI client imported successfully")
        
        client = await get_azure_openai_client()
        print("✅ Azure OpenAI client created successfully")
        
        health = await client.health_check()
        print(f"✅ Health check: {health['status']}")
        
        if health['status'] == 'healthy':
            print("🎉 Azure OpenAI integration is working!")
            return True
        else:
            print(f"❌ Health check failed: {health.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_azure_connection())
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
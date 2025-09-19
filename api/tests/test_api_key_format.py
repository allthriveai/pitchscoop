#!/usr/bin/env python3
"""
Test API Key Format and Validation
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler
from domains.recordings.value_objects.audio_configuration import AudioConfiguration


async def test_api_key_format():
    print("🔍 API Key Format Analysis")
    print("=" * 40)
    
    current_key = os.getenv('GLADIA_API_KEY')
    print(f"Current key: [{current_key}]")
    print(f"Length: {len(current_key)} characters")
    print(f"Expected UUID length: 36 characters")
    
    if current_key.startswith('y'):
        corrected_key = current_key[1:]  # Remove the 'y' prefix
        print(f"Corrected key: [{corrected_key}]")
        print(f"Corrected length: {len(corrected_key)} characters")
        
        # Test with corrected key
        print("\n🧪 Testing with corrected API key...")
        original_key = os.environ.get('GLADIA_API_KEY')
        
        try:
            # Temporarily use corrected key
            os.environ['GLADIA_API_KEY'] = corrected_key
            
            handler = GladiaMCPHandler()
            config = AudioConfiguration.create_default()
            
            response = await handler._create_gladia_session(config)
            if response:
                print("✅ Corrected API key works!")
                print(f"   Session ID: {response.get('id', 'N/A')}")
                print(f"   WebSocket URL: {response.get('url', 'N/A')[:50]}...")
                print(f"\n💡 To fix: Update your .env file to use: {corrected_key}")
            else:
                print("❌ Corrected key still doesn't work - may be invalid or expired")
                
        finally:
            # Restore original
            if original_key:
                os.environ['GLADIA_API_KEY'] = original_key
    else:
        print("Key format looks correct, issue might be elsewhere")


if __name__ == "__main__":
    asyncio.run(test_api_key_format())
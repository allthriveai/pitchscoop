#!/usr/bin/env python3
"""Test the new onboarding flow with event link check"""
import asyncio
import json

async def test_with_link():
    """Test flow when user provides an event link"""
    from domains.onboarding.mcp.onboarding_mcp_tools import execute_onboarding_mcp_tool
    
    print("\n" + "="*60)
    print("TEST: With Event Link")
    print("="*60 + "\n")
    
    # Step 1: Start
    result = await execute_onboarding_mcp_tool('onboarding.start', {
        'user_id': 'test_with_link',
        'role': 'organizer'
    })
    
    print(f"✅ Step 1: {result['current_step']['title']}")
    print(f"   Question: {result['current_step']['description']}\n")
    
    session_id = result['session_id']
    
    # Step 2: Provide link
    result = await execute_onboarding_mcp_tool('onboarding.submit_step', {
        'session_id': session_id,
        'step_data': {
            'event_link': 'https://devpost.com/test-hackathon'
        }
    })
    
    print(f"✅ Step 2: Submitted link")
    print(f"   Message: {result['message']}")
    print(f"   Next: {result['next_step']['title']}\n")
    
    return result

async def test_without_link():
    """Test flow when user doesn't provide an event link"""
    from domains.onboarding.mcp.onboarding_mcp_tools import execute_onboarding_mcp_tool
    
    print("\n" + "="*60)
    print("TEST: Without Event Link (Manual Entry)")
    print("="*60 + "\n")
    
    # Step 1: Start
    result = await execute_onboarding_mcp_tool('onboarding.start', {
        'user_id': 'test_no_link',
        'role': 'organizer'
    })
    
    print(f"✅ Step 1: {result['current_step']['title']}")
    print(f"   Question: {result['current_step']['description']}\n")
    
    session_id = result['session_id']
    
    # Step 2: Skip link (empty)
    result = await execute_onboarding_mcp_tool('onboarding.submit_step', {
        'session_id': session_id,
        'step_data': {}  # No link provided
    })
    
    print(f"✅ Step 2: Skipped link")
    print(f"   Message: {result['message']}")
    print(f"   Next: {result['next_step']['title']}\n")
    
    return result

async def main():
    print("\n🧪 Testing New Onboarding Flow")
    print("="*60)
    
    await test_with_link()
    await test_without_link()
    
    print("\n✅ Both flows tested successfully!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())

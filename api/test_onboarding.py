#!/usr/bin/env python3
"""
Test script for PitchScoop onboarding flow

Tests both organizer and participant onboarding flows end-to-end.
"""
import asyncio
import sys
import json
from datetime import datetime

sys.path.insert(0, '/Users/allierays/Sites/pitchscoop/api')

from domains.shared.infrastructure.database import AsyncSessionLocal
from domains.onboarding.services.onboarding_service import OnboardingService


async def test_organizer_onboarding():
    """Test complete organizer onboarding flow."""
    print("\n" + "="*60)
    print("🎯 Testing Organizer Onboarding Flow")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        # Step 1: Start onboarding
        print("📝 Step 1: Starting onboarding as organizer...")
        result = await service.start_onboarding(
            user_id="test_organizer_123",
            role="organizer"
        )
        print(f"✅ Session ID: {result['session_id']}")
        print(f"   Current step: {result['current_step']['title']}")
        print(f"   Message: {result.get('welcome_message', result.get('message'))}\n")
        
        session_id = result['session_id']
        
        # Step 2: Submit event details
        print("📝 Step 2: Submitting event details...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "event_name": "Test Hackathon 2024",
                "event_type": "hackathon",
                "event_description": "A test hackathon for our platform",
                "start_date": "2024-12-01",
                "end_date": "2024-12-02"
            }
        )
        print(f"✅ Next step: {result['next_step']['title']}")
        print(f"   Message: {result['message']}\n")
        
        # Step 3: Configure judging
        print("📝 Step 3: Configuring judging criteria...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "judging_mode": "default",
                "custom_categories": []
            }
        )
        print(f"✅ Next step: {result['next_step']['title']}")
        print(f"   Message: {result['message']}\n")
        
        # Step 4: Review and confirm
        print("📝 Step 4: Reviewing and confirming...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "confirm": True
            }
        )
        
        if result.get('completed'):
            print("🎉 ONBOARDING COMPLETE!")
            print(f"   Event ID: {result.get('event_id')}")
            print(f"   Summary: {json.dumps(result['summary'], indent=2)}")
            print(f"   Next actions: {result['next_actions']}")
            return True
        else:
            print(f"❌ Onboarding not completed: {result}")
            return False


async def test_participant_onboarding():
    """Test complete participant onboarding flow."""
    print("\n" + "="*60)
    print("👤 Testing Participant Onboarding Flow")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        # Step 1: Start onboarding
        print("📝 Step 1: Starting onboarding as participant...")
        result = await service.start_onboarding(
            user_id="test_participant_456",
            role="participant",
            event_id="test_event_789"  # Would be a real event ID
        )
        print(f"✅ Session ID: {result['session_id']}")
        print(f"   Current step: {result['current_step']['title']}")
        print(f"   Message: {result.get('welcome_message', result.get('message'))}\n")
        
        session_id = result['session_id']
        
        # Step 2: Submit team info
        print("📝 Step 2: Submitting team information...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "team_name": "Test Team Alpha",
                "team_size": 3,
                "team_members": ["Alice", "Bob", "Charlie"]
            }
        )
        print(f"✅ Next step: {result['next_step']['title']}")
        print(f"   Message: {result['message']}\n")
        
        # Step 3: Submit project info
        print("📝 Step 3: Submitting project information...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "project_name": "AI-Powered Test Tool",
                "project_description": "An innovative tool that uses AI to automate testing",
                "tech_stack": ["Python", "FastAPI", "OpenAI"]
            }
        )
        print(f"✅ Next step: {result['next_step']['title']}")
        print(f"   Message: {result['message']}\n")
        
        # Step 4: Review and confirm
        print("📝 Step 4: Reviewing and confirming...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "confirm": True
            }
        )
        
        if result.get('completed'):
            print("🎉 ONBOARDING COMPLETE!")
            print(f"   Summary: {json.dumps(result['summary'], indent=2)}")
            print(f"   Next actions: {result['next_actions']}")
            return True
        else:
            print(f"❌ Onboarding not completed: {result}")
            return False


async def test_validation_errors():
    """Test validation of required fields."""
    print("\n" + "="*60)
    print("🔍 Testing Validation Errors")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        # Start onboarding
        result = await service.start_onboarding(
            user_id="test_validation_999",
            role="organizer"
        )
        session_id = result['session_id']
        
        # Try to submit incomplete data
        print("📝 Submitting incomplete event details (missing event_name)...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "event_type": "hackathon",
                # Missing event_name!
                "start_date": "2024-12-01"
            }
        )
        
        if not result['success']:
            print(f"✅ Validation caught missing field!")
            print(f"   Errors: {result['errors']}")
            return True
        else:
            print("❌ Validation should have failed but didn't")
            return False


async def test_resume_onboarding():
    """Test resuming an existing onboarding session."""
    print("\n" + "="*60)
    print("🔄 Testing Resume Onboarding")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        user_id = "test_resume_777"
        
        # Start onboarding
        print("📝 Starting new onboarding session...")
        result1 = await service.start_onboarding(
            user_id=user_id,
            role="organizer"
        )
        print(f"✅ Created session: {result1['session_id']}")
        
        # Try to start again with same user
        print("\n📝 Attempting to start again with same user...")
        result2 = await service.start_onboarding(
            user_id=user_id,
            role="organizer"
        )
        
        if result2.get('resuming'):
            print(f"✅ Successfully resumed existing session!")
            print(f"   Session ID: {result2['session_id']}")
            print(f"   Current step: {result2['current_step']['title']}")
            return True
        else:
            print("❌ Should have resumed but created new session")
            return False


async def run_all_tests():
    """Run all onboarding tests."""
    print("\n" + "🚀 " + "="*56)
    print("🚀  PitchScoop Onboarding Test Suite")
    print("🚀 " + "="*56)
    
    tests = [
        ("Organizer Onboarding", test_organizer_onboarding),
        ("Participant Onboarding", test_participant_onboarding),
        ("Validation Errors", test_validation_errors),
        ("Resume Onboarding", test_resume_onboarding),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}  {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

"""
Test Onboarding Service

Simple test to verify the onboarding flow works correctly.
Tests both organizer and participant paths.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.domains.shared.infrastructure.database import AsyncSessionLocal, init_db
from api.domains.onboarding.services.onboarding_service import OnboardingService


async def test_organizer_flow():
    """Test event organizer onboarding flow"""
    print("\n=== Testing Event Organizer Flow ===\n")
    
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        # Step 1: Start onboarding
        print("Step 1: Starting onboarding as organizer...")
        result = await service.start_onboarding(
            user_id="test_organizer_1",
            role="organizer"
        )
        print(f"✅ Started: {result['welcome_message']}")
        print(f"   Session ID: {result['session_id']}")
        print(f"   Current Step: {result['current_step']['title']}\n")
        
        session_id = result['session_id']
        
        # Step 2: Submit event details
        print("Step 2: Submitting event details...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "event_name": "AI Innovation Challenge",
                "event_date": "2025-11-15",
                "event_type": "Hackathon",
                "event_link": "https://aiinnovation.com",
                "judging_rules": "Teams will be judged on innovation, technical implementation, and presentation"
            }
        )
        print(f"✅ Event details saved")
        print(f"   Message: {result['message']}")
        print(f"   Next Step: {result['next_step']['title']}\n")
        
        # Step 3: Configure judging with custom category
        print("Step 3: Configuring judging criteria with custom category...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "custom_category_name": "Sustainability Impact",
                "custom_category_description": "How environmentally friendly is the solution?",
                "custom_category_weight": 0.15
            }
        )
        print(f"✅ Onboarding complete!")
        print(f"   Message: {result['message']}")
        print(f"   Event ID: {result['event_id']}")
        print(f"   Event Name: {result['summary']['event_name']}")
        print(f"   Categories: {len(result['summary']['judging_categories'])} total\n")
        
        return result


async def test_participant_flow():
    """Test participant onboarding flow"""
    print("\n=== Testing Participant Flow ===\n")
    
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        # Step 1: Start onboarding
        print("Step 1: Starting onboarding as participant...")
        result = await service.start_onboarding(
            user_id="test_participant_1",
            role="participant"
        )
        print(f"✅ Started: {result['welcome_message']}")
        print(f"   Session ID: {result['session_id']}")
        print(f"   Current Step: {result['current_step']['title']}\n")
        
        session_id = result['session_id']
        
        # Step 2: Create profile
        print("Step 2: Creating profile...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "user_name": "Alex Chen",
                "team_name": "Team Rocket",
                "project_name": "EcoTracker",
                "project_description": "An AI-powered app that helps users track and reduce their carbon footprint through personalized recommendations",
                "github_repo": "https://github.com/alexchen/ecotracker"
            }
        )
        print(f"✅ Profile created")
        print(f"   Message: {result['message']}")
        print(f"   Next Step: {result['next_step']['title']}\n")
        
        # Step 3: Select participation option
        print("Step 3: Completing onboarding...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "selected_option": "join_existing"
            }
        )
        print(f"✅ Onboarding complete!")
        print(f"   Message: {result['message']}")
        print(f"   User: {result['summary']['user_name']}")
        print(f"   Team: {result['summary']['team_name']}")
        print(f"   Project: {result['summary']['project_name']}\n")
        
        return result


async def test_validation():
    """Test validation errors"""
    print("\n=== Testing Validation ===\n")
    
    async with AsyncSessionLocal() as db:
        service = OnboardingService(db)
        
        # Start onboarding
        result = await service.start_onboarding(
            user_id="test_validation_1",
            role="organizer"
        )
        session_id = result['session_id']
        
        # Try to submit incomplete data
        print("Submitting incomplete event details (missing required fields)...")
        result = await service.process_step(
            session_id=session_id,
            step_data={
                "event_name": "Test Event"
                # Missing: event_date, event_type, judging_rules
            }
        )
        
        if not result['success']:
            print(f"✅ Validation working correctly")
            print(f"   Errors: {', '.join(result['errors'])}\n")
        else:
            print(f"❌ Validation failed - should have caught errors\n")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("PitchScoop Onboarding Service Tests")
    print("="*60)
    
    try:
        # Initialize database tables
        print("\nInitializing database...")
        await init_db()
        print("✅ Database initialized\n")
        
        # Run tests
        await test_organizer_flow()
        await test_participant_flow()
        await test_validation()
        
        print("="*60)
        print("✅ All tests completed successfully!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

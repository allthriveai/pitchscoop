#!/usr/bin/env python3
"""
Test Hume AI Integration

This script tests the Hume API integration for video emotion analysis.
It can run in both mock mode (without API keys) and real mode (with valid API keys).
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv(str(Path(__file__).parent.parent.parent / '.env'))

from api.domains.recordings.repositories.hume_api_repository import get_hume_client, HumeAPIRepository, MockHumeAPIRepository

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_video_data() -> bytes:
    """
    Create minimal test video data for testing.
    
    In real usage, this would be actual video file bytes.
    For testing, we'll create a minimal MP4 header-like structure.
    """
    # This is a fake video data for testing - not a real video file
    # In practice, you'd read actual video file bytes
    test_data = b"fake_video_data_for_testing" * 100  # Make it somewhat larger
    logger.info(f"Created test video data: {len(test_data)} bytes")
    return test_data


async def test_hume_health_check():
    """Test Hume API health check."""
    print("\n🔍 Testing Hume API Health Check")
    print("=" * 50)
    
    client = get_hume_client()
    
    # Check what type of client we got
    is_mock = isinstance(client, MockHumeAPIRepository)
    client_type = "Mock" if is_mock else "Real"
    print(f"Using {client_type} Hume API client")
    
    try:
        health_result = await client.health_check()
        
        print(f"Health Check Result:")
        print(f"  Status: {health_result.get('status')}")
        print(f"  API Accessible: {health_result.get('api_accessible', False)}")
        
        if health_result.get('available_models'):
            print(f"  Available Models: {health_result['available_models']}")
        
        if health_result.get('error'):
            print(f"  Error: {health_result['error']}")
        
        if health_result.get('mock'):
            print("  Mode: Mock (no real API calls)")
        
        return health_result.get('status') == 'healthy'
        
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False
    finally:
        await client.close()


async def test_hume_video_upload():
    """Test video upload to Hume API."""
    print("\n🎬 Testing Hume Video Upload")
    print("=" * 50)
    
    client = get_hume_client()
    
    try:
        # Create test video data
        video_data = create_test_video_data()
        filename = "test_pitch_video.mp4"
        
        print(f"Uploading test video: {filename} ({len(video_data)} bytes)")
        
        # Upload video for analysis
        upload_result = await client.upload_video_for_analysis(video_data, filename)
        
        print(f"Upload Result:")
        print(f"  Success: {upload_result.get('success')}")
        
        if upload_result.get('success'):
            print(f"  Job ID: {upload_result.get('job_id')}")
            print(f"  Status: {upload_result.get('status')}")
            print(f"  Message: {upload_result.get('message')}")
            
            if upload_result.get('mock'):
                print("  Mode: Mock (no real upload)")
                
            return upload_result.get('job_id')
        else:
            print(f"  Error: {upload_result.get('error')}")
            print(f"  Details: {upload_result.get('details', 'None')}")
            return None
            
    except Exception as e:
        print(f"❌ Video upload failed: {str(e)}")
        return None
    finally:
        await client.close()


async def test_hume_complete_workflow():
    """Test complete video analysis workflow."""
    print("\n🎯 Testing Complete Hume Video Analysis Workflow")
    print("=" * 50)
    
    client = get_hume_client()
    
    try:
        # Create test video data
        video_data = create_test_video_data()
        filename = "complete_workflow_test.mp4"
        
        print(f"Starting complete analysis workflow: {filename}")
        print(f"Video size: {len(video_data)} bytes")
        
        # Run complete workflow with shorter timeout for testing
        max_wait = 30  # 30 seconds for testing
        analysis_result = await client.analyze_video_complete(video_data, filename, max_wait)
        
        print(f"\nWorkflow Result:")
        print(f"  Success: {analysis_result.get('success')}")
        
        if analysis_result.get('success'):
            print(f"  Job ID: {analysis_result.get('job_id')}")
            print(f"  Filename: {analysis_result.get('filename')}")
            print(f"  Processing Time: {analysis_result.get('processing_time', 'N/A')}s")
            
            # Show analysis results
            results = analysis_result.get('analysis_results', {})
            expressions = results.get('expressions', [])
            
            if expressions:
                print(f"\nExpression Analysis ({len(expressions)} time points):")
                for i, expr in enumerate(expressions[:3]):  # Show first 3 time points
                    time = expr.get('time', 0)
                    confidence = expr.get('confidence', 0)
                    joy = expr.get('joy', 0)
                    surprise = expr.get('surprise', 0)
                    print(f"  Time {time}s: Joy={joy:.3f}, Surprise={surprise:.3f} (confidence={confidence:.3f})")
                    
                if len(expressions) > 3:
                    print(f"  ... and {len(expressions) - 3} more time points")
            
            if analysis_result.get('mock'):
                print("  Mode: Mock (simulated analysis)")
                
            return True
        else:
            print(f"  Error: {analysis_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Complete workflow failed: {str(e)}")
        return False
    finally:
        await client.close()


async def test_environment_configuration():
    """Test environment configuration for Hume."""
    print("\n⚙️ Testing Environment Configuration")
    print("=" * 50)
    
    api_key = os.getenv('HUME_API_KEY')
    secret_key = os.getenv('HUME_SECRET_KEY')
    
    print(f"Environment Variables:")
    print(f"  HUME_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"  HUME_SECRET_KEY: {'✅ Set' if secret_key else '❌ Not set'}")
    
    if api_key and secret_key and api_key != 'your_hume_api_key_here':
        print(f"  Configuration: ✅ Ready for real API calls")
        return "real"
    else:
        print(f"  Configuration: ⚠️ Using mock mode (no valid API keys)")
        return "mock"


async def main():
    """Run all Hume integration tests."""
    print("🎭 Hume AI Integration Test Suite")
    print("=" * 60)
    
    # Test environment configuration
    config_status = await test_environment_configuration()
    
    # Test health check
    health_ok = await test_hume_health_check()
    
    if not health_ok:
        print("\n❌ Health check failed, skipping other tests")
        return False
    
    # Test video upload
    job_id = await test_hume_video_upload()
    
    # Test complete workflow
    workflow_ok = await test_hume_complete_workflow()
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    print(f"Configuration: {'✅' if config_status else '❌'} {config_status.upper()} mode")
    print(f"Health Check: {'✅' if health_ok else '❌'}")
    print(f"Video Upload: {'✅' if job_id else '❌'}")
    print(f"Complete Workflow: {'✅' if workflow_ok else '❌'}")
    
    if config_status == "mock":
        print(f"\n💡 To test with real Hume API:")
        print(f"   1. Get API keys from https://hume.ai")
        print(f"   2. Set HUME_API_KEY and HUME_SECRET_KEY environment variables")
        print(f"   3. Run this test again")
    
    success = health_ok and (job_id is not None) and workflow_ok
    
    if success:
        print(f"\n🎉 All tests passed! Hume integration is ready.")
    else:
        print(f"\n⚠️ Some tests failed. Check the errors above.")
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit_code = 0 if result else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {str(e)}")
        sys.exit(1)
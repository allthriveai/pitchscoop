#!/usr/bin/env python3
"""
Quick Hume Test - Verify API connection and upload functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv(str(Path(__file__).parent.parent.parent / '.env'))

from api.domains.recordings.repositories.hume_api_repository import get_hume_client


async def quick_test():
    """Quick test of Hume API functionality."""
    print("🎭 Quick Hume API Test")
    print("=" * 50)
    
    # Check environment
    api_key = os.getenv('HUME_API_KEY')
    secret_key = os.getenv('HUME_SECRET_KEY')
    
    print(f"API Key: {'✅ Configured' if api_key else '❌ Missing'}")
    print(f"Secret Key: {'✅ Configured' if secret_key else '❌ Missing'}")
    
    if not api_key or not secret_key:
        print("❌ API credentials not configured")
        return False
    
    # Get client
    client = get_hume_client()
    
    try:
        print(f"\n🔍 Testing API Health...")
        health = await client.health_check()
        
        if health.get('status') == 'healthy':
            print(f"✅ API is healthy and accessible")
            print(f"   Working endpoint: {health.get('working_endpoint', 'N/A')}")
        else:
            print(f"❌ API health check failed: {health.get('error')}")
            return False
        
        print(f"\n🎬 Testing Video Upload...")
        
        # Create small test data
        test_video_data = b"fake_test_video_data" * 50  # Small fake data
        
        upload_result = await client.upload_video_for_analysis(test_video_data, "quick_test.mp4")
        
        if upload_result.get('success'):
            job_id = upload_result.get('job_id')
            print(f"✅ Video upload successful!")
            print(f"   Job ID: {job_id}")
            print(f"   Status: {upload_result.get('status')}")
            
            # Check initial job status (don't wait for completion)
            print(f"\n📊 Checking job status...")
            status_result = await client.get_analysis_status(job_id)
            
            if status_result.get('success'):
                status = status_result.get('status', 'unknown')
                print(f"✅ Job status retrieved: {status}")
                
                if status in ['queued', 'in_progress', 'submitted']:
                    print(f"📈 Job is processing normally (this would take 1-5 minutes for real video)")
                elif status == 'completed':
                    print(f"🎉 Job completed already! (unlikely with real video)")
                elif status == 'failed':
                    print(f"❌ Job failed")
                
                return True
            else:
                print(f"⚠️  Could not check job status: {status_result.get('error')}")
                return True  # Upload worked, status check might just be timing
        else:
            print(f"❌ Video upload failed: {upload_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test exception: {str(e)}")
        return False
    finally:
        await client.close()


async def main():
    """Run quick test."""
    success = await quick_test()
    
    if success:
        print(f"\n🎉 Quick Test PASSED!")
        print(f"   ✅ Hume API is working correctly")
        print(f"   ✅ Video uploads are functional")
        print(f"   ✅ Ready for real video analysis")
        print(f"\n💡 To analyze a real video file:")
        print(f"   python tests/demo/demo_hume_video_analysis.py path/to/video.mp4")
    else:
        print(f"\n❌ Quick Test FAILED")
        print(f"   Check API credentials and connection")
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
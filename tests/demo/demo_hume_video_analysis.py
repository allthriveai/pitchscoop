#!/usr/bin/env python3
"""
Demo: Hume Video Analysis

This script demonstrates how to use Hume AI for video emotion analysis.
You can test it with actual video files or in mock mode.

Usage:
    # With real video file and API keys
    python demo_hume_video_analysis.py path/to/video.mp4
    
    # Mock mode (no API keys needed)  
    python demo_hume_video_analysis.py --mock
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv(str(Path(__file__).parent.parent.parent / '.env'))

from api.domains.recordings.repositories.hume_api_repository import get_hume_client, MockHumeAPIRepository


async def analyze_video_file(video_path: str):
    """Analyze a real video file with Hume AI."""
    print(f"\n🎬 Analyzing Video File: {video_path}")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    # Get file size
    file_size = os.path.getsize(video_path)
    print(f"📁 File: {os.path.basename(video_path)}")
    print(f"💾 Size: {file_size / (1024*1024):.1f} MB")
    
    if file_size > 100 * 1024 * 1024:  # 100MB limit
        print("⚠️  Warning: File is quite large, processing may take several minutes")
    
    # Read video data
    try:
        with open(video_path, 'rb') as f:
            video_data = f.read()
        print(f"✅ Video file loaded successfully")
    except Exception as e:
        print(f"❌ Failed to read video file: {str(e)}")
        return False
    
    # Get Hume client
    client = get_hume_client()
    is_mock = isinstance(client, MockHumeAPIRepository)
    
    if is_mock:
        print(f"⚠️  Using mock mode (no real API calls)")
    else:
        print(f"🚀 Using real Hume API")
    
    try:
        # Test API connectivity first
        print(f"\n🔍 Testing API connectivity...")
        health = await client.health_check()
        
        if health.get('status') != 'healthy':
            print(f"❌ API health check failed: {health.get('error', 'Unknown error')}")
            return False
        
        print(f"✅ API is healthy and ready")
        
        # Start video analysis
        print(f"\n🎭 Starting emotion analysis...")
        filename = os.path.basename(video_path)
        
        # Set timeout based on file size (rough estimate)
        timeout_minutes = max(5, int(file_size / (10 * 1024 * 1024)))  # 5 min minimum, +1 min per 10MB
        timeout_seconds = timeout_minutes * 60
        
        print(f"⏱️  Max processing time: {timeout_minutes} minutes")
        
        result = await client.analyze_video_complete(
            video_data, 
            filename, 
            max_wait_seconds=timeout_seconds
        )
        
        if result.get('success'):
            print(f"\n🎉 Analysis Complete!")
            print(f"🆔 Job ID: {result.get('job_id')}")
            print(f"⏱️  Processing time: {result.get('processing_time', 'N/A')}s")
            
            # Display emotion analysis results
            analysis_results = result.get('analysis_results', {})
            expressions = analysis_results.get('expressions', [])
            
            if expressions:
                print(f"\n📊 Emotion Analysis Results ({len(expressions)} time points):")
                print("-" * 80)
                
                # Show first few and last few time points
                display_count = min(5, len(expressions))
                
                for i in range(display_count):
                    expr = expressions[i]
                    time = expr.get('time', 0)
                    confidence = expr.get('confidence', 0)
                    
                    emotions = {
                        'Joy': expr.get('joy', 0),
                        'Surprise': expr.get('surprise', 0),
                        'Fear': expr.get('fear', 0),
                        'Anger': expr.get('anger', 0),
                        'Sadness': expr.get('sadness', 0),
                        'Disgust': expr.get('disgust', 0),
                        'Contempt': expr.get('contempt', 0)
                    }
                    
                    # Find top 3 emotions
                    top_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]
                    
                    print(f"Time {time:5.1f}s: ", end="")
                    for emotion, value in top_emotions:
                        print(f"{emotion}={value:.3f} ", end="")
                    print(f"(confidence={confidence:.3f})")
                
                if len(expressions) > display_count:
                    print(f"... and {len(expressions) - display_count} more time points")
                
                # Summary statistics
                avg_confidence = sum(e.get('confidence', 0) for e in expressions) / len(expressions)
                avg_joy = sum(e.get('joy', 0) for e in expressions) / len(expressions)
                avg_surprise = sum(e.get('surprise', 0) for e in expressions) / len(expressions)
                
                print(f"\n📈 Summary Statistics:")
                print(f"Average Confidence: {avg_confidence:.3f}")
                print(f"Average Joy: {avg_joy:.3f}")
                print(f"Average Surprise: {avg_surprise:.3f}")
                
                # Insights
                print(f"\n💡 Quick Insights:")
                if avg_joy > 0.5:
                    print("😊 High joy levels detected - appears to be a positive, engaging presentation")
                elif avg_joy < 0.2:
                    print("😐 Lower joy levels - might benefit from more enthusiasm")
                
                if avg_confidence > 0.8:
                    print("📈 High confidence in emotion detection - reliable results")
                elif avg_confidence < 0.5:
                    print("⚠️  Lower confidence - video quality might affect accuracy")
                
            else:
                print("⚠️  No expression data found in results")
                
            if result.get('mock'):
                print("\n🧪 Note: This was a mock analysis for demonstration purposes")
            
            return True
            
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis exception: {str(e)}")
        return False
    finally:
        await client.close()


async def demo_mock_mode():
    """Run demo in mock mode without real video files."""
    print(f"\n🧪 Mock Mode Demo")
    print("=" * 60)
    print("This demo shows how Hume integration works without requiring:")
    print("- Real API keys")
    print("- Actual video files")
    print("- Internet connection")
    
    # Create mock client
    client = MockHumeAPIRepository()
    
    try:
        print(f"\n1️⃣ Testing API health...")
        health = await client.health_check()
        print(f"   Status: {health.get('status')}")
        print(f"   Models: {health.get('available_models', [])}")
        
        print(f"\n2️⃣ Mock video upload...")
        fake_video_data = b"fake_video_data" * 1000
        upload_result = await client.upload_video_for_analysis(fake_video_data, "demo.mp4")
        print(f"   Upload success: {upload_result.get('success')}")
        print(f"   Job ID: {upload_result.get('job_id')}")
        
        print(f"\n3️⃣ Complete workflow simulation...")
        workflow_result = await client.analyze_video_complete(fake_video_data, "demo_workflow.mp4")
        
        if workflow_result.get('success'):
            expressions = workflow_result.get('analysis_results', {}).get('expressions', [])
            print(f"   ✅ Mock analysis complete")
            print(f"   📊 Generated {len(expressions)} emotion data points")
            
            if expressions:
                first_expr = expressions[0]
                print(f"   Sample: Joy={first_expr.get('joy', 0):.3f}, Confidence={first_expr.get('confidence', 0):.3f}")
        
        print(f"\n🎉 Mock demo complete! The system is ready for real video analysis.")
        return True
        
    except Exception as e:
        print(f"❌ Mock demo failed: {str(e)}")
        return False
    finally:
        await client.close()


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="Hume Video Analysis Demo")
    parser.add_argument("video_path", nargs="?", help="Path to video file to analyze")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode (no real API calls)")
    
    args = parser.parse_args()
    
    print("🎭 Hume AI Video Analysis Demo")
    print("=" * 70)
    
    # Check environment
    has_api_key = bool(os.getenv('HUME_API_KEY'))
    has_secret_key = bool(os.getenv('HUME_SECRET_KEY'))
    
    print(f"Environment Check:")
    print(f"  HUME_API_KEY: {'✅' if has_api_key else '❌'}")
    print(f"  HUME_SECRET_KEY: {'✅' if has_secret_key else '❌'}")
    
    if args.mock:
        # Run mock demo
        success = asyncio.run(demo_mock_mode())
    elif args.video_path:
        # Analyze provided video file
        success = asyncio.run(analyze_video_file(args.video_path))
    else:
        # Show usage info
        print(f"\n📖 Usage Options:")
        print(f"1. Mock Mode (no API keys needed):")
        print(f"   python {sys.argv[0]} --mock")
        print(f"\n2. Real Video Analysis (requires API keys):")
        print(f"   python {sys.argv[0]} path/to/video.mp4")
        print(f"\n3. Get Hume API Keys:")
        print(f"   Visit https://hume.ai to sign up and get API credentials")
        
        success = True
    
    if success:
        print(f"\n✨ Demo completed successfully!")
    else:
        print(f"\n❌ Demo encountered errors")
    
    return success


if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        sys.exit(1)
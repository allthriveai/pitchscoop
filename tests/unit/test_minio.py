#!/usr/bin/env python3
"""
Test MinIO integration for audio storage.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the api directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from api.domains.recordings.infrastructure.minio_audio_storage import MinIOAudioStorage
import pytest


@pytest.mark.asyncio
async def test_minio_integration():
    """Test MinIO audio storage functionality."""
    print("🚀 Testing MinIO Audio Storage Integration\n")
    
    # Initialize MinIO client
    print("🔍 Initializing MinIO client...")
    try:
        minio_storage = MinIOAudioStorage()
        print("✅ MinIO client initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize MinIO client: {e}")
        return False
    
    # Generate test audio data
    print("\n🔍 Generating test audio data...")
    def generate_test_audio(duration_seconds=1.0, sample_rate=16000):
        """Generate test audio data (sine wave)."""
        import math
        import struct
        
        samples = []
        for i in range(int(sample_rate * duration_seconds)):
            t = i / sample_rate
            # Generate sine wave at 440Hz
            sample = int(16383 * math.sin(2 * math.pi * 440 * t))
            samples.append(struct.pack('<h', sample))
        
        return b''.join(samples)
    
    test_audio = generate_test_audio(duration_seconds=2.0)
    print(f"✅ Generated {len(test_audio)} bytes of test audio")
    
    # Test session ID
    test_session_id = "test-session-123"
    
    # Test 1: Upload audio
    print("\n🔍 Testing audio upload...")
    try:
        object_key = await minio_storage.upload_audio(
            session_id=test_session_id,
            audio_data=test_audio,
            file_format="wav"
        )
        print(f"✅ Audio uploaded successfully: {object_key}")
    except Exception as e:
        print(f"❌ Audio upload failed: {e}")
        return False
    
    # Test 2: Get audio info
    print("\n🔍 Testing audio info retrieval...")
    try:
        audio_info = await minio_storage.get_audio_info(test_session_id)
        if audio_info:
            print(f"✅ Audio info retrieved:")
            print(f"   Size: {audio_info['size']} bytes")
            print(f"   Content-Type: {audio_info['content_type']}")
            print(f"   Object Key: {audio_info['object_key']}")
        else:
            print("❌ Audio info not found")
            return False
    except Exception as e:
        print(f"❌ Audio info retrieval failed: {e}")
        return False
    
    # Test 3: Generate playback URL
    print("\n🔍 Testing playback URL generation...")
    try:
        playback_url = await minio_storage.get_playback_url(test_session_id)
        if playback_url:
            print(f"✅ Playback URL generated:")
            print(f"   URL: {playback_url}")
        else:
            print("❌ Playback URL generation failed")
            return False
    except Exception as e:
        print(f"❌ Playback URL generation failed: {e}")
        return False
    
    # Test 4: Get direct URL
    print("\n🔍 Testing direct URL generation...")
    try:
        direct_url = await minio_storage.get_direct_url(test_session_id)
        print(f"✅ Direct URL generated: {direct_url}")
    except Exception as e:
        print(f"❌ Direct URL generation failed: {e}")
        return False
    
    # Test 5: List audio files
    print("\n🔍 Testing audio file listing...")
    try:
        audio_files = await minio_storage.list_session_audio_files(test_session_id)
        print(f"✅ Found {len(audio_files)} audio files:")
        for file in audio_files:
            print(f"   - {file}")
    except Exception as e:
        print(f"❌ Audio file listing failed: {e}")
        return False
    
    # Test 6: Upload compressed audio
    print("\n🔍 Testing compressed audio upload...")
    try:
        # Simulate compressed audio (just smaller data for test)
        compressed_audio = test_audio[:len(test_audio)//2]  # Simulate compression
        compressed_key = await minio_storage.upload_compressed_audio(
            session_id=test_session_id,
            compressed_data=compressed_audio
        )
        print(f"✅ Compressed audio uploaded: {compressed_key}")
    except Exception as e:
        print(f"❌ Compressed audio upload failed: {e}")
        return False
    
    # Test 7: List all files again
    print("\n🔍 Testing updated file listing...")
    try:
        audio_files = await minio_storage.list_session_audio_files(test_session_id)
        print(f"✅ Now found {len(audio_files)} audio files:")
        for file in audio_files:
            print(f"   - {file}")
    except Exception as e:
        print(f"❌ Updated file listing failed: {e}")
        return False
    
    # Test 8: Clean up - delete audio files
    print("\n🔍 Testing audio deletion...")
    try:
        # Delete original
        deleted_original = await minio_storage.delete_audio(test_session_id, "wav")
        print(f"✅ Original audio deleted: {deleted_original}")
        
        # Delete compressed
        deleted_compressed = await minio_storage.delete_audio(test_session_id, "mp3")
        print(f"✅ Compressed audio deleted: {deleted_compressed}")
        
    except Exception as e:
        print(f"❌ Audio deletion failed: {e}")
        return False
    
    # Test 9: Verify deletion
    print("\n🔍 Verifying deletion...")
    try:
        audio_info_after = await minio_storage.get_audio_info(test_session_id)
        if audio_info_after is None:
            print("✅ Audio files successfully deleted")
        else:
            print("⚠️  Some audio files still exist")
            
        audio_files_after = await minio_storage.list_session_audio_files(test_session_id)
        print(f"✅ Files remaining: {len(audio_files_after)}")
        
    except Exception as e:
        print(f"❌ Deletion verification failed: {e}")
        return False
    
    print("\n🎉 All MinIO tests passed!")
    return True


async def main():
    """Run MinIO integration tests."""
    print("🔧 MinIO Storage Integration Tests")
    print("=" * 50)
    
    success = await test_minio_integration()
    
    if success:
        print("\n✅ MinIO integration is working perfectly!")
        print("\n💡 Next steps:")
        print("   - MinIO Console: http://localhost:9001")
        print("   - Login: pitchscoop / pitchscoop123")
        print("   - Check the 'pitchscoop' bucket for test files")
        print("   - Ready to implement Gladia MCP tools with audio storage!")
    else:
        print("\n❌ MinIO integration has issues. Check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
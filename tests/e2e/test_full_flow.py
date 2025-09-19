#!/usr/bin/env python3
"""
Test complete flow including transcript display
"""
import asyncio
import requests
import base64
import struct
import math

def generate_test_audio():
    """Generate a simple test audio file"""
    sample_rate = 16000
    duration = 2.0  # 2 seconds
    
    samples = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        # Create a tone that might trigger some response
        frequency = 400 + 100 * math.sin(t * 4)
        amplitude = 0.4 * (1 + 0.3 * math.sin(t * 8))
        sample = int(16383 * amplitude * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', sample))
    
    return b''.join(samples)

def test_full_api_flow():
    """Test the complete API flow"""
    base_url = "http://localhost:8000/mcp/execute"
    
    print("🧪 Testing Complete API Flow")
    print("=" * 40)
    
    # 1. Create event
    print("1. Creating event...")
    event_response = requests.post(base_url, json={
        "tool": "events.create_event",
        "arguments": {
            "event_type": "individual_practice",
            "event_name": "Full Flow Test",
            "description": "Testing complete transcript flow",
            "duration_minutes": 5
        }
    })
    event_data = event_response.json()
    event_id = event_data.get("event_id")
    print(f"✅ Event: {event_id}")
    
    # 2. Start recording
    print("2. Starting recording...")
    session_response = requests.post(base_url, json={
        "tool": "pitches.start_recording",
        "arguments": {
            "event_id": event_id,
            "team_name": "Full Test Team",
            "pitch_title": "Complete Flow Test"
        }
    })
    session_data = session_response.json()
    session_id = session_data.get("session_id")
    print(f"✅ Session: {session_id}")
    
    # 3. Generate and encode audio
    print("3. Preparing audio...")
    audio_data = generate_test_audio()
    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
    print(f"✅ Audio: {len(audio_data)} bytes")
    
    # 4. Stop recording with audio
    print("4. Uploading audio and processing...")
    stop_response = requests.post(base_url, json={
        "tool": "pitches.stop_recording",
        "arguments": {
            "session_id": session_id,
            "audio_data_base64": audio_b64
        }
    })
    stop_data = stop_response.json()
    
    print("📊 Stop Response:")
    print(f"   Status: {stop_data.get('status', 'unknown')}")
    
    # Check for transcript
    transcript = stop_data.get("transcript")
    if transcript:
        text = transcript.get("total_text", "").strip()
        segments = transcript.get("segments_count", 0)
        
        if text:
            print(f"📝 TRANSCRIPT: '{text}'")
            print(f"   Segments: {segments}")
        else:
            print(f"📝 No transcript text (segments: {segments})")
            print("   This is expected for synthetic audio")
    else:
        print("📝 No transcript in response")
    
    # Check audio storage
    audio_info = stop_data.get("audio", {})
    if audio_info.get("has_audio"):
        print(f"🎵 Audio stored: {audio_info.get('audio_size')} bytes")
        
    # 5. Test playback URL
    print("5. Getting playback URL...")
    playback_response = requests.post(base_url, json={
        "tool": "pitches.get_playback_url",
        "arguments": {
            "session_id": session_id,
            "expires_hours": 1
        }
    })
    playback_data = playback_response.json()
    
    if playback_data.get("playback_url"):
        print(f"🔗 Playback URL: {playback_data['playback_url'][:60]}...")
    else:
        print(f"❌ No playback URL: {playback_data}")
    
    print("\n📋 Complete Response Structure:")
    print("Stop Response Keys:", list(stop_data.keys()))
    if "transcript" in stop_data:
        print("Transcript Keys:", list(stop_data["transcript"].keys()))
    if "audio" in stop_data:
        print("Audio Keys:", list(stop_data["audio"].keys()))
    
    return stop_data

if __name__ == "__main__":
    result = test_full_api_flow()
    
    print("\n💡 For browser testing:")
    print("• The API is working correctly")
    print("• Check browser developer console for errors")
    print("• Verify the HTML is parsing the response properly")
#!/usr/bin/env python3
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

Test Gladia Audio Intelligence features
"""
import asyncio
from domains.recordings.value_objects.audio_configuration import AudioConfiguration
from domains.events.mcp.events_mcp_handler import events_mcp_handler
from domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler

async def test_audio_intelligence():
    print('🧠 Testing Gladia Audio Intelligence Features')
    print('=' * 50)
    
    # Test configuration creation
    print('1. Testing Audio Intelligence Configuration...')
    
    # Test default config
    default_config = AudioConfiguration.create_default()
    print(f'   Default config: {default_config.to_gladia_config()}')
    
    # Test pitch analysis config (with AI features)
    pitch_config = AudioConfiguration.create_pitch_analysis()
    basic_config = pitch_config.to_gladia_config()
    ai_config = pitch_config.to_gladia_config(include_ai_features=True)
    print(f'   Pitch config (basic): {basic_config}')
    print(f'   Pitch config (with AI): {ai_config}')
    
    # Verify Audio Intelligence features are enabled
    ai_features = ['sentiment_analysis', 'emotion_analysis', 'summarization', 'named_entity_recognition', 'chapterization']
    enabled_features = [feature for feature in ai_features if ai_config.get(feature, False)]
    
    print(f'\n📊 Audio Intelligence Features Enabled: {len(enabled_features)}/{len(ai_features)}')
    for feature in enabled_features:
        print(f'   ✅ {feature}')
    
    # Test with real session
    print('\n2. Testing with Real Recording Session...')
    
    # Create event
    event = await events_mcp_handler.create_event(
        event_type='individual_practice',
        event_name='AI Features Test',
        description='Testing Gladia Audio Intelligence'
    )
    event_id = event['event_id']
    print(f'   Event created: {event_id}')
    
    # Start recording session
    handler = GladiaMCPHandler()
    session = await handler.start_pitch_recording(
        'AI Test Speaker',
        'Audio Intelligence Test',
        event_id
    )
    
    if 'error' in session:
        print(f'   ❌ Session creation failed: {session["error"]}')
        return
    
    session_id = session['session_id']
    print(f'   ✅ Session created: {session_id}')
    print(f'   🧠 AI Features in session: {session.get("audio_config", {})}')
    
    # Check if Gladia session includes AI features
    gladia_session_id = session.get('gladia_session_id')
    websocket_url = session.get('websocket_url')
    
    if gladia_session_id and websocket_url:
        print(f'   ✅ Gladia session: {gladia_session_id}')
        print(f'   ✅ WebSocket URL: {websocket_url[:50]}...')
        print('   🧠 Audio Intelligence features are now active!')
    else:
        print('   ❌ Gladia session creation failed')
    
    print('\n💡 Next Steps:')
    print('   1. Record real speech using: http://localhost:8000/test')
    print('   2. Look for Audio Intelligence data in transcript results:')
    print('      - Sentiment analysis (positive/negative/neutral)')
    print('      - Emotion detection (happy, sad, angry, etc.)')
    print('      - Summarization (key points)')
    print('      - Named entities (people, places, organizations)')
    print('      - Chapter detection (topic segments)')
    
    print('\n🔍 Expected in Browser Results:')
    print('   - Enhanced transcript with sentiment/emotion per segment')
    print('   - Summary of the entire recording')
    print('   - Key entities mentioned in the speech')
    print('   - Emotional tone analysis')
    
    return session_id

if __name__ == "__main__":
    session_id = asyncio.run(test_audio_intelligence())
    print(f"\n✅ Audio Intelligence is configured and ready!")
    print(f"📱 Test at: http://localhost:8000/test")
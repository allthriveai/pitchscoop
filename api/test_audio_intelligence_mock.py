#!/usr/bin/env python3
"""
Test audio intelligence value objects with mock data
"""
import asyncio
import json
import sys
import os
sys.path.append('/app')

def test_audio_intelligence_value_objects():
    """Test the audio intelligence value objects with mock data"""
    print("🧪 Testing Audio Intelligence Value Objects")
    print("=" * 60)
    
    try:
        from domains.recordings.value_objects.audio_intelligence import (
            SpeechMetrics, FillerAnalysis, AudioIntelligence, ConfidenceMetrics, EnergyLevel
        )
        
        # Create mock speech metrics
        print("📊 Creating mock speech metrics...")
        speech_metrics = SpeechMetrics(
            words_per_minute=150.5,
            total_duration_seconds=145.0,
            total_pause_duration_seconds=25.0,
            pause_count=12,
            speaking_duration_seconds=120.0
        )
        
        print("✅ Speech Metrics created:")
        print(f"   WPM: {speech_metrics.words_per_minute}")
        print(f"   Speaking Rate: {speech_metrics.get_speaking_rate_assessment()}")
        print(f"   Pause Effectiveness: {speech_metrics.get_pause_effectiveness_score():.2f}")
        print(f"   Pacing Consistency: {speech_metrics.get_pacing_consistency_score():.2f}")
        print()
        
        # Create mock filler word analysis
        print("🔤 Creating mock filler word analysis...")
        filler_analysis = FillerAnalysis(
            total_filler_count=8,
            filler_words_detected=["um", "uh", "like", "um", "uh", "um", "like", "um"],
            filler_percentage=6.7,  # 8 fillers per 120 words
            most_common_filler="um",
            filler_frequency_per_minute=4.0
        )
        
        print("✅ Filler Word Analysis created:")
        print(f"   Total Fillers: {filler_analysis.total_filler_count}")
        print(f"   Filler Percentage: {filler_analysis.filler_percentage:.1f}%")
        print(f"   Professionalism Score: {filler_analysis.get_professionalism_score():.2f}")
        print(f"   Delivery Grade: {filler_analysis.get_delivery_grade()}")
        print()
        
        # Create mock confidence metrics
        print("💪 Creating mock confidence metrics...")
        confidence_metrics = ConfidenceMetrics(
            confidence_score=0.85,
            energy_level=EnergyLevel.HIGH,
            vocal_stability=0.78,
            pace_consistency=0.72
        )
        
        # Create comprehensive audio intelligence
        print("🎯 Creating comprehensive audio intelligence...")
        audio_intelligence = AudioIntelligence(
            session_id="test-session-123",
            gladia_session_id="gladia-test-456",
            speech_metrics=speech_metrics,
            filler_analysis=filler_analysis,
            confidence_metrics=confidence_metrics,
            analysis_timestamp="2025-01-21T12:00:00Z"
        )
        
        print("✅ Audio Intelligence created:")
        print(f"   Delivery Score: {audio_intelligence.get_presentation_delivery_score():.1f}/25.0")
        print(f"   Confidence: {audio_intelligence.confidence_metrics.confidence_score:.2f}")
        print(f"   Energy Level: {audio_intelligence.confidence_metrics.energy_level}")
        print(f"   Vocal Stability: {audio_intelligence.confidence_metrics.vocal_stability:.2f}")
        print()
        
        print("🎓 Coaching Insights:")
        coaching_insights = audio_intelligence.get_coaching_insights()
        for insight in coaching_insights:
            print(f"   - {insight}")
        print()
        
        print("💪 Strengths:")
        strengths = audio_intelligence.get_strengths()
        for strength in strengths:
            print(f"   - {strength}")
        
        return audio_intelligence
        
    except Exception as e:
        print(f"❌ Error testing value objects: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_scoring_integration():
    """Test the scoring MCP handler integration with mock data"""
    print("\n" + "=" * 60)
    print("🎯 Testing Scoring MCP Handler Integration")
    print("=" * 60)
    
    try:
        # First test our value objects
        mock_intelligence = test_audio_intelligence_value_objects()
        if not mock_intelligence:
            return
        
        print("\n🔗 Testing integration with scoring analysis...")
        
        # Create a mock analysis that combines transcript and audio intelligence
        mock_analysis = {
            "session_id": "test-session-123",
            "presentation_delivery": {
                "audio_intelligence": {
                    "speech_metrics": {
                        "words_per_minute": mock_intelligence.speech_metrics.words_per_minute,
                        "speaking_rate_assessment": str(mock_intelligence.speech_metrics.get_speaking_rate_assessment().value),
                        "pause_effectiveness_score": mock_intelligence.speech_metrics.get_pause_effectiveness_score(),
                        "pacing_consistency_score": mock_intelligence.speech_metrics.get_pacing_consistency_score()
                    },
                    "filler_analysis": {
                        "total_filler_count": mock_intelligence.filler_analysis.total_filler_count,
                        "filler_percentage": mock_intelligence.filler_analysis.filler_percentage,
                        "professionalism_score": mock_intelligence.filler_analysis.get_professionalism_score(),
                        "delivery_grade": str(mock_intelligence.filler_analysis.get_delivery_grade().value)
                    },
                    "confidence_metrics": {
                        "confidence_score": mock_intelligence.confidence_metrics.confidence_score,
                        "energy_level": str(mock_intelligence.confidence_metrics.energy_level.value),
                        "presentation_readiness": mock_intelligence.confidence_metrics.get_presentation_readiness_score()
                    },
                    "delivery_score": mock_intelligence.get_presentation_delivery_score(),
                    "coaching_insights": mock_intelligence.get_coaching_insights(),
                    "strengths": mock_intelligence.get_strengths()
                }
            }
        }
        
        print("✅ Mock scoring analysis created:")
        print(json.dumps(mock_analysis, indent=2, default=str))
        
    except Exception as e:
        print(f"❌ Error testing scoring integration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_audio_intelligence_value_objects()
    asyncio.run(test_scoring_integration())
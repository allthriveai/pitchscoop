"""
Audio Intelligence Value Objects

Domain objects for representing Gladia Audio Intelligence analysis results.
These objects encapsulate speech metrics, delivery quality assessments,
and presentation flow analysis for pitch presentation evaluation.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class SpeakingRate(Enum):
    """Speaking rate classifications for pitch presentations."""
    TOO_SLOW = "too_slow"
    APPROPRIATE = "appropriate"  
    TOO_FAST = "too_fast"


class DeliveryGrade(Enum):
    """Delivery quality grades."""
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"


class EnergyLevel(Enum):
    """Energy level classifications."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class SpeechMetrics:
    """Speech timing and pace analysis from Gladia Audio Intelligence."""
    
    words_per_minute: float
    total_duration_seconds: float
    total_pause_duration_seconds: float
    pause_count: int
    speaking_duration_seconds: float
    
    def get_speaking_rate_assessment(self, target_wpm: int = 150) -> SpeakingRate:
        """
        Assess speaking pace for pitch presentations.
        
        Args:
            target_wpm: Target words per minute for comparison
            
        Returns:
            Speaking rate classification
        """
        variance_threshold = target_wpm * 0.2  # 20% variance allowed
        
        if self.words_per_minute < (target_wpm - variance_threshold):
            return SpeakingRate.TOO_SLOW
        elif self.words_per_minute > (target_wpm + variance_threshold):
            return SpeakingRate.TOO_FAST
        else:
            return SpeakingRate.APPROPRIATE
    
    def get_pause_effectiveness_score(self) -> float:
        """
        Calculate pause effectiveness score (0.0 - 1.0).
        
        Returns:
            Score based on pause frequency and duration
        """
        if self.total_duration_seconds == 0:
            return 0.0
            
        # Ideal: 10-20% pause time for emphasis and breathing
        pause_percentage = (self.total_pause_duration_seconds / self.total_duration_seconds) * 100
        
        if 10 <= pause_percentage <= 20:
            return 1.0
        elif 5 <= pause_percentage < 10 or 20 < pause_percentage <= 30:
            return 0.7
        else:
            return 0.4
    
    def get_pacing_consistency_score(self) -> float:
        """
        Calculate pacing consistency score.
        
        Returns:
            Score based on optimal speaking vs pause ratio
        """
        if self.total_duration_seconds == 0:
            return 0.0
            
        speaking_percentage = (self.speaking_duration_seconds / self.total_duration_seconds) * 100
        
        # Optimal: 75-85% speaking time
        if 75 <= speaking_percentage <= 85:
            return 1.0
        elif 65 <= speaking_percentage < 75 or 85 < speaking_percentage <= 90:
            return 0.8
        else:
            return 0.5


@dataclass(frozen=True)
class FillerAnalysis:
    """Filler word analysis from Gladia Audio Intelligence."""
    
    total_filler_count: int
    filler_words_detected: List[str]
    filler_percentage: float
    most_common_filler: Optional[str]
    filler_frequency_per_minute: float
    
    def get_professionalism_score(self) -> float:
        """
        Calculate professionalism score based on filler usage (0.0 - 1.0).
        
        Returns:
            Score where 1.0 is excellent, 0.0 is poor
        """
        if self.filler_percentage <= 1.0:
            return 1.0
        elif self.filler_percentage <= 2.5:
            return 0.8
        elif self.filler_percentage <= 5.0:
            return 0.6
        else:
            return 0.3
    
    def get_delivery_grade(self) -> DeliveryGrade:
        """Get overall delivery grade based on filler usage."""
        if self.filler_percentage <= 2.0:
            return DeliveryGrade.EXCELLENT
        elif self.filler_percentage <= 5.0:
            return DeliveryGrade.GOOD
        else:
            return DeliveryGrade.NEEDS_IMPROVEMENT


@dataclass(frozen=True)
class ConfidenceMetrics:
    """Confidence and energy analysis from audio intelligence."""
    
    confidence_score: float  # 0.0 - 1.0
    energy_level: EnergyLevel
    vocal_stability: float  # 0.0 - 1.0
    pace_consistency: float  # 0.0 - 1.0
    
    def get_overall_confidence_assessment(self) -> str:
        """Get human-readable confidence assessment."""
        if self.confidence_score >= 0.8:
            return "high"
        elif self.confidence_score >= 0.6:
            return "moderate"
        else:
            return "low"
    
    def get_presentation_readiness_score(self) -> float:
        """
        Calculate overall presentation readiness (0.0 - 1.0).
        
        Combines confidence, energy, and stability metrics.
        """
        energy_score = 1.0 if self.energy_level == EnergyLevel.HIGH else (
            0.7 if self.energy_level == EnergyLevel.MODERATE else 0.4
        )
        
        return (
            self.confidence_score * 0.4 +
            energy_score * 0.3 +
            self.vocal_stability * 0.2 +
            self.pace_consistency * 0.1
        )


@dataclass(frozen=True)
class AudioIntelligence:
    """Complete audio intelligence analysis from Gladia."""
    
    session_id: str
    gladia_session_id: str
    speech_metrics: SpeechMetrics
    filler_analysis: FillerAnalysis
    confidence_metrics: ConfidenceMetrics
    analysis_timestamp: str
    
    def get_presentation_delivery_score(self, max_score: float = 25.0) -> float:
        """
        Calculate presentation delivery score based on audio intelligence.
        
        Args:
            max_score: Maximum possible score
            
        Returns:
            Score out of max_score
        """
        # Weight different aspects of delivery
        pace_score = 1.0 if self.speech_metrics.get_speaking_rate_assessment() == SpeakingRate.APPROPRIATE else 0.7
        pause_score = self.speech_metrics.get_pause_effectiveness_score()
        filler_score = self.filler_analysis.get_professionalism_score()
        confidence_score = self.confidence_metrics.get_presentation_readiness_score()
        
        # Weighted average
        overall_score = (
            pace_score * 0.25 +           # Speaking pace
            pause_score * 0.20 +          # Pause effectiveness  
            filler_score * 0.30 +         # Professionalism (filler control)
            confidence_score * 0.25       # Confidence and energy
        )
        
        return round(overall_score * max_score, 1)
    
    def get_coaching_insights(self) -> List[str]:
        """Generate actionable coaching insights."""
        insights = []
        
        # Speaking pace insights
        rate_assessment = self.speech_metrics.get_speaking_rate_assessment()
        if rate_assessment == SpeakingRate.TOO_SLOW:
            insights.append(f"Increase speaking pace from {self.speech_metrics.words_per_minute:.0f} to 140-160 WPM for better engagement")
        elif rate_assessment == SpeakingRate.TOO_FAST:
            insights.append(f"Slow down from {self.speech_metrics.words_per_minute:.0f} to 140-160 WPM for better comprehension")
        
        # Filler word insights
        if self.filler_analysis.filler_percentage > 3.0:
            insights.append(f"Reduce filler words from {self.filler_analysis.filler_percentage:.1f}% to under 2% (practice with pauses instead)")
        
        # Confidence insights
        if self.confidence_metrics.confidence_score < 0.7:
            insights.append("Practice delivery to improve vocal confidence and stability")
        
        # Pause insights
        pause_score = self.speech_metrics.get_pause_effectiveness_score()
        if pause_score < 0.7:
            insights.append("Use more strategic pauses for emphasis and audience engagement")
        
        return insights
    
    def get_strengths(self) -> List[str]:
        """Identify delivery strengths based on audio analysis."""
        strengths = []
        
        if self.speech_metrics.get_speaking_rate_assessment() == SpeakingRate.APPROPRIATE:
            strengths.append(f"Excellent pacing at {self.speech_metrics.words_per_minute:.0f} WPM")
        
        if self.filler_analysis.filler_percentage <= 2.0:
            strengths.append(f"Professional delivery with only {self.filler_analysis.filler_percentage:.1f}% filler words")
        
        if self.confidence_metrics.confidence_score >= 0.8:
            strengths.append("High vocal confidence and presentation energy")
        
        if self.speech_metrics.get_pause_effectiveness_score() >= 0.8:
            strengths.append("Effective use of strategic pauses for emphasis")
        
        return strengths if strengths else ["Completed full presentation delivery"]


def create_audio_intelligence_from_gladia_response(
    session_id: str,
    gladia_session_id: str,
    gladia_response: Dict[str, Any],
    analysis_timestamp: str
) -> AudioIntelligence:
    """
    Create AudioIntelligence object from Gladia API response.
    
    Args:
        session_id: Internal session ID
        gladia_session_id: Gladia session ID
        gladia_response: Raw response from Gladia Audio Intelligence API
        analysis_timestamp: When the analysis was performed
        
    Returns:
        AudioIntelligence object with parsed data
    """
    # Extract speech metrics
    speech_data = gladia_response.get("speech", {})
    prosodic_data = gladia_response.get("prosodic", {})
    
    speech_metrics = SpeechMetrics(
        words_per_minute=float(speech_data.get("words_per_minute", 0)),
        total_duration_seconds=float(gladia_response.get("metadata", {}).get("duration", 0)),
        total_pause_duration_seconds=float(prosodic_data.get("total_pause_duration", 0)),
        pause_count=int(prosodic_data.get("pause_count", 0)),
        speaking_duration_seconds=float(speech_data.get("speaking_duration", 0))
    )
    
    # Extract filler analysis
    filler_data = gladia_response.get("filler_analysis", {})
    filler_analysis = FillerAnalysis(
        total_filler_count=int(filler_data.get("total_count", 0)),
        filler_words_detected=filler_data.get("detected_fillers", []),
        filler_percentage=float(filler_data.get("percentage", 0)),
        most_common_filler=filler_data.get("most_common"),
        filler_frequency_per_minute=float(filler_data.get("frequency_per_minute", 0))
    )
    
    # Extract confidence metrics
    sentiment_data = gladia_response.get("sentiment", {})
    confidence_metrics = ConfidenceMetrics(
        confidence_score=float(sentiment_data.get("confidence", 0.5)),
        energy_level=EnergyLevel(prosodic_data.get("energy_level", "moderate")),
        vocal_stability=float(prosodic_data.get("stability", 0.5)),
        pace_consistency=float(speech_data.get("pace_consistency", 0.5))
    )
    
    return AudioIntelligence(
        session_id=session_id,
        gladia_session_id=gladia_session_id,
        speech_metrics=speech_metrics,
        filler_analysis=filler_analysis,
        confidence_metrics=confidence_metrics,
        analysis_timestamp=analysis_timestamp
    )
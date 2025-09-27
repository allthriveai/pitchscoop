"""
Video Intelligence Value Objects

Domain objects for representing Hume AI video emotion analysis results.
These objects encapsulate facial expression analysis, emotion detection,
and presentation engagement analysis for pitch presentation evaluation.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class EmotionIntensity(Enum):
    """Emotion intensity classifications."""
    LOW = "low"
    MODERATE = "moderate" 
    HIGH = "high"


class EngagementLevel(Enum):
    """Engagement level classifications."""
    DISENGAGED = "disengaged"
    NEUTRAL = "neutral"
    ENGAGED = "engaged"
    HIGHLY_ENGAGED = "highly_engaged"


class PresentationConfidence(Enum):
    """Presentation confidence classifications."""
    NERVOUS = "nervous"
    UNCERTAIN = "uncertain"
    CONFIDENT = "confident"
    VERY_CONFIDENT = "very_confident"


@dataclass(frozen=True)
class EmotionSnapshot:
    """Emotion analysis at a specific point in time."""
    
    time_seconds: float
    confidence: float  # 0.0 - 1.0
    
    # Core Hume emotions (0.0 - 1.0)
    joy: float
    surprise: float
    fear: float
    anger: float
    sadness: float
    disgust: float
    contempt: float
    
    def get_dominant_emotion(self) -> tuple[str, float]:
        """Get the strongest emotion and its value."""
        emotions = {
            'joy': self.joy,
            'surprise': self.surprise,
            'fear': self.fear,
            'anger': self.anger,
            'sadness': self.sadness,
            'disgust': self.disgust,
            'contempt': self.contempt
        }
        dominant = max(emotions.items(), key=lambda x: x[1])
        return dominant
    
    def get_positive_emotions_score(self) -> float:
        """Calculate overall positive emotion score."""
        return (self.joy + self.surprise) / 2.0
    
    def get_negative_emotions_score(self) -> float:
        """Calculate overall negative emotion score."""
        return (self.fear + self.anger + self.sadness + self.disgust + self.contempt) / 5.0
    
    def get_emotion_balance(self) -> float:
        """Get emotion balance (-1.0 negative to +1.0 positive)."""
        positive = self.get_positive_emotions_score()
        negative = self.get_negative_emotions_score()
        return positive - negative
    
    def is_high_confidence(self) -> bool:
        """Check if this snapshot has high confidence."""
        return self.confidence >= 0.8


@dataclass(frozen=True)
class EmotionTimeline:
    """Collection of emotion snapshots over time."""
    
    snapshots: List[EmotionSnapshot]
    total_duration_seconds: float
    
    def get_average_confidence(self) -> float:
        """Calculate average confidence across all snapshots."""
        if not self.snapshots:
            return 0.0
        return sum(s.confidence for s in self.snapshots) / len(self.snapshots)
    
    def get_emotion_progression(self) -> Dict[str, List[float]]:
        """Get emotion values over time for trending analysis."""
        emotions = ['joy', 'surprise', 'fear', 'anger', 'sadness', 'disgust', 'contempt']
        progression = {emotion: [] for emotion in emotions}
        
        for snapshot in self.snapshots:
            progression['joy'].append(snapshot.joy)
            progression['surprise'].append(snapshot.surprise)
            progression['fear'].append(snapshot.fear)
            progression['anger'].append(snapshot.anger)
            progression['sadness'].append(snapshot.sadness)
            progression['disgust'].append(snapshot.disgust)
            progression['contempt'].append(snapshot.contempt)
        
        return progression
    
    def get_average_emotions(self) -> Dict[str, float]:
        """Calculate average emotion levels throughout the presentation."""
        if not self.snapshots:
            return {}
        
        return {
            'joy': sum(s.joy for s in self.snapshots) / len(self.snapshots),
            'surprise': sum(s.surprise for s in self.snapshots) / len(self.snapshots),
            'fear': sum(s.fear for s in self.snapshots) / len(self.snapshots),
            'anger': sum(s.anger for s in self.snapshots) / len(self.snapshots),
            'sadness': sum(s.sadness for s in self.snapshots) / len(self.snapshots),
            'disgust': sum(s.disgust for s in self.snapshots) / len(self.snapshots),
            'contempt': sum(s.contempt for s in self.snapshots) / len(self.snapshots),
        }
    
    def get_engagement_level(self) -> EngagementLevel:
        """Determine overall engagement level based on emotions."""
        avg_emotions = self.get_average_emotions()
        
        if not avg_emotions:
            return EngagementLevel.NEUTRAL
        
        # High joy + surprise = engaged
        positive_score = (avg_emotions.get('joy', 0) + avg_emotions.get('surprise', 0)) / 2
        # High negative emotions = disengaged  
        negative_score = (avg_emotions.get('fear', 0) + avg_emotions.get('sadness', 0)) / 2
        
        if positive_score >= 0.6:
            return EngagementLevel.HIGHLY_ENGAGED if positive_score >= 0.8 else EngagementLevel.ENGAGED
        elif negative_score >= 0.4:
            return EngagementLevel.DISENGAGED
        else:
            return EngagementLevel.NEUTRAL


@dataclass(frozen=True)
class PresentationDeliveryMetrics:
    """Metrics for presentation delivery quality based on video analysis."""
    
    confidence_level: PresentationConfidence
    engagement_consistency: float  # 0.0 - 1.0 (how consistent engagement was)
    emotional_range: float  # 0.0 - 1.0 (variety of emotions shown)
    authenticity_score: float  # 0.0 - 1.0 (natural vs forced expressions)
    energy_level: EmotionIntensity
    
    def get_overall_delivery_score(self, max_score: float = 25.0) -> float:
        """Calculate overall delivery score for presentation category."""
        # Convert confidence to numeric score
        confidence_score = {
            PresentationConfidence.NERVOUS: 0.3,
            PresentationConfidence.UNCERTAIN: 0.6,
            PresentationConfidence.CONFIDENT: 0.8,
            PresentationConfidence.VERY_CONFIDENT: 1.0
        }[self.confidence_level]
        
        # Convert energy to numeric score
        energy_score = {
            EmotionIntensity.LOW: 0.4,
            EmotionIntensity.MODERATE: 0.7,
            EmotionIntensity.HIGH: 1.0
        }[self.energy_level]
        
        # Weighted combination
        overall_score = (
            confidence_score * 0.35 +           # Confidence most important
            self.engagement_consistency * 0.25 + # Consistent engagement
            self.authenticity_score * 0.20 +     # Natural delivery
            energy_score * 0.15 +               # Energy level
            self.emotional_range * 0.05         # Expression variety
        )
        
        return round(overall_score * max_score, 1)
    
    def get_coaching_insights(self) -> List[str]:
        """Generate actionable coaching insights."""
        insights = []
        
        # Confidence insights
        if self.confidence_level == PresentationConfidence.NERVOUS:
            insights.append("Practice delivery to build confidence - consider rehearsing in front of mirrors or friends")
        elif self.confidence_level == PresentationConfidence.UNCERTAIN:
            insights.append("Work on projecting more confidence through posture and facial expressions")
        
        # Engagement insights
        if self.engagement_consistency < 0.6:
            insights.append("Maintain more consistent engagement throughout the presentation")
        
        # Energy insights
        if self.energy_level == EmotionIntensity.LOW:
            insights.append("Increase energy and enthusiasm to better engage your audience")
        elif self.energy_level == EmotionIntensity.HIGH:
            insights.append("Great energy! Make sure to pace yourself to avoid overwhelming the audience")
        
        # Authenticity insights
        if self.authenticity_score < 0.6:
            insights.append("Focus on natural, authentic expressions rather than forced enthusiasm")
        
        # Emotional range insights
        if self.emotional_range < 0.3:
            insights.append("Use more varied expressions to keep your presentation dynamic and interesting")
        
        return insights if insights else ["Strong overall delivery with good emotional presence"]
    
    def get_strengths(self) -> List[str]:
        """Identify delivery strengths."""
        strengths = []
        
        if self.confidence_level in [PresentationConfidence.CONFIDENT, PresentationConfidence.VERY_CONFIDENT]:
            strengths.append("Strong, confident presence throughout presentation")
        
        if self.engagement_consistency >= 0.8:
            strengths.append("Excellent engagement consistency from start to finish")
        
        if self.authenticity_score >= 0.8:
            strengths.append("Natural, authentic delivery style")
        
        if self.energy_level == EmotionIntensity.HIGH:
            strengths.append("High energy and enthusiasm")
        
        if self.emotional_range >= 0.6:
            strengths.append("Good emotional range and expression variety")
        
        return strengths if strengths else ["Completed video presentation delivery"]


@dataclass(frozen=True)
class VideoIntelligence:
    """Complete video intelligence analysis from Hume AI."""
    
    session_id: str
    hume_job_id: str
    emotion_timeline: EmotionTimeline
    delivery_metrics: PresentationDeliveryMetrics
    analysis_timestamp: str
    processing_time_seconds: float
    
    def get_presentation_score(self, max_score: float = 25.0) -> float:
        """Calculate presentation delivery score based on video intelligence."""
        return self.delivery_metrics.get_overall_delivery_score(max_score)
    
    def get_emotional_summary(self) -> Dict[str, Any]:
        """Get summary of emotional analysis."""
        avg_emotions = self.emotion_timeline.get_average_emotions()
        dominant_emotion, dominant_value = max(avg_emotions.items(), key=lambda x: x[1]) if avg_emotions else ("neutral", 0.0)
        
        return {
            "dominant_emotion": dominant_emotion,
            "dominant_emotion_strength": round(dominant_value, 3),
            "average_emotions": {k: round(v, 3) for k, v in avg_emotions.items()},
            "engagement_level": self.emotion_timeline.get_engagement_level().value,
            "confidence_level": self.delivery_metrics.confidence_level.value,
            "emotional_balance": round(sum(s.get_emotion_balance() for s in self.emotion_timeline.snapshots) / len(self.emotion_timeline.snapshots), 3) if self.emotion_timeline.snapshots else 0.0
        }
    
    def get_coaching_feedback(self) -> Dict[str, Any]:
        """Get comprehensive coaching feedback."""
        return {
            "strengths": self.delivery_metrics.get_strengths(),
            "improvement_areas": self.delivery_metrics.get_coaching_insights(),
            "emotional_summary": self.get_emotional_summary(),
            "delivery_score": self.get_presentation_score(),
            "processing_metadata": {
                "analysis_quality": "high" if self.emotion_timeline.get_average_confidence() >= 0.8 else "moderate",
                "snapshots_analyzed": len(self.emotion_timeline.snapshots),
                "total_duration": self.emotion_timeline.total_duration_seconds,
                "processing_time": self.processing_time_seconds
            }
        }


def create_video_intelligence_from_hume_response(
    session_id: str,
    hume_job_id: str,
    hume_response: Dict[str, Any],
    analysis_timestamp: str,
    processing_time_seconds: float
) -> VideoIntelligence:
    """
    Create VideoIntelligence object from Hume API response.
    
    Args:
        session_id: Internal session ID
        hume_job_id: Hume job ID
        hume_response: Raw response from Hume API
        analysis_timestamp: When the analysis was performed
        processing_time_seconds: How long processing took
        
    Returns:
        VideoIntelligence object with parsed data
    """
    # Extract emotion snapshots from Hume response
    snapshots = []
    expressions = hume_response.get("expressions", [])
    
    for expr in expressions:
        snapshot = EmotionSnapshot(
            time_seconds=float(expr.get("time", 0)),
            confidence=float(expr.get("confidence", 0)),
            joy=float(expr.get("joy", 0)),
            surprise=float(expr.get("surprise", 0)),
            fear=float(expr.get("fear", 0)),
            anger=float(expr.get("anger", 0)),
            sadness=float(expr.get("sadness", 0)),
            disgust=float(expr.get("disgust", 0)),
            contempt=float(expr.get("contempt", 0))
        )
        snapshots.append(snapshot)
    
    # Calculate total duration
    total_duration = max(s.time_seconds for s in snapshots) if snapshots else 0.0
    
    # Create emotion timeline
    emotion_timeline = EmotionTimeline(
        snapshots=snapshots,
        total_duration_seconds=total_duration
    )
    
    # Calculate delivery metrics
    avg_emotions = emotion_timeline.get_average_emotions()
    
    # Determine confidence level
    avg_confidence = emotion_timeline.get_average_confidence()
    if avg_confidence >= 0.9:
        confidence_level = PresentationConfidence.VERY_CONFIDENT
    elif avg_confidence >= 0.7:
        confidence_level = PresentationConfidence.CONFIDENT
    elif avg_confidence >= 0.5:
        confidence_level = PresentationConfidence.UNCERTAIN
    else:
        confidence_level = PresentationConfidence.NERVOUS
    
    # Calculate engagement consistency (how consistent emotions were)
    if snapshots:
        emotion_variances = []
        emotions = ['joy', 'surprise', 'fear', 'anger', 'sadness']
        for emotion in emotions:
            values = [getattr(s, emotion) for s in snapshots]
            if len(values) > 1:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                emotion_variances.append(variance)
        
        avg_variance = sum(emotion_variances) / len(emotion_variances) if emotion_variances else 0
        engagement_consistency = max(0.0, 1.0 - (avg_variance * 2))  # Lower variance = higher consistency
    else:
        engagement_consistency = 0.5
    
    # Calculate emotional range
    if avg_emotions:
        emotion_values = list(avg_emotions.values())
        emotional_range = (max(emotion_values) - min(emotion_values)) if emotion_values else 0.0
    else:
        emotional_range = 0.0
    
    # Calculate authenticity score (inverse of extreme values - natural expressions avoid extremes)
    if snapshots:
        extreme_count = sum(1 for s in snapshots 
                          for emotion in [s.joy, s.surprise, s.fear, s.anger, s.sadness, s.disgust, s.contempt]
                          if emotion > 0.9 or emotion < 0.1)
        total_measurements = len(snapshots) * 7  # 7 emotions per snapshot
        authenticity_score = max(0.0, 1.0 - (extreme_count / total_measurements) * 2)
    else:
        authenticity_score = 0.5
    
    # Determine energy level
    if avg_emotions:
        energy_score = (avg_emotions.get('joy', 0) + avg_emotions.get('surprise', 0)) / 2
        if energy_score >= 0.7:
            energy_level = EmotionIntensity.HIGH
        elif energy_score >= 0.4:
            energy_level = EmotionIntensity.MODERATE
        else:
            energy_level = EmotionIntensity.LOW
    else:
        energy_level = EmotionIntensity.MODERATE
    
    delivery_metrics = PresentationDeliveryMetrics(
        confidence_level=confidence_level,
        engagement_consistency=round(engagement_consistency, 3),
        emotional_range=round(emotional_range, 3),
        authenticity_score=round(authenticity_score, 3),
        energy_level=energy_level
    )
    
    return VideoIntelligence(
        session_id=session_id,
        hume_job_id=hume_job_id,
        emotion_timeline=emotion_timeline,
        delivery_metrics=delivery_metrics,
        analysis_timestamp=analysis_timestamp,
        processing_time_seconds=processing_time_seconds
    )
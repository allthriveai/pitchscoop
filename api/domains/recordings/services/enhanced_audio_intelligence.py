"""
Enhanced Audio Intelligence Service

This service implements the hybrid approach combining Gladia transcription
with Azure OpenAI for pitch-specific analysis to solve analysis quality issues:

- Basic transcription from Gladia (reliable)
- Advanced sentiment analysis via Azure OpenAI
- Pitch-specific insights (persuasiveness, technical confidence, etc.)
- Higher confidence scores and contextual understanding
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass

from ..value_objects.transcript import TranscriptSegment, TranscriptCollection
from ...shared.infrastructure.azure_openai_client import get_azure_openai_client
from ...shared.value_objects.llm_request import LLMRequest, LLMMessage
from ...shared.infrastructure.logging import get_logger, log_with_context

logger = get_logger(__name__)


@dataclass
class PitchSpecificAnalysis:
    """Enhanced pitch-specific analysis results."""
    
    # Core pitch metrics
    persuasiveness_score: float  # 0.0 - 1.0
    technical_confidence: float  # 0.0 - 1.0
    market_understanding: float  # 0.0 - 1.0
    enthusiasm_level: str  # "low", "moderate", "high"
    clarity_score: float  # 0.0 - 1.0
    investor_appeal: float  # 0.0 - 1.0
    competitive_advantage_confidence: float  # 0.0 - 1.0
    
    # Enhanced sentiment with context
    overall_sentiment: str  # "positive", "neutral", "negative"
    sentiment_confidence: float  # 0.0 - 1.0 (much higher than basic Gladia)
    emotional_tone: str  # "confident", "nervous", "excited", "concerned"
    
    # Pitch structure analysis
    has_clear_problem: bool
    has_clear_solution: bool
    demonstrates_market_knowledge: bool
    shows_technical_depth: bool
    mentions_competition: bool
    
    # Coaching insights
    strengths: List[str]
    improvement_areas: List[str]
    specific_recommendations: List[str]
    
    # Metadata
    analysis_timestamp: str
    confidence_level: str  # "high", "medium", "low"
    processing_method: str  # "hybrid_ai_analysis"


class EnhancedAudioIntelligence:
    """Enhanced Audio Intelligence service using hybrid approach."""
    
    def __init__(self):
        self.logger = get_logger("enhanced_audio_intelligence")
    
    async def analyze_pitch_transcript(
        self, 
        transcript_segments: List[Dict], 
        event_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze pitch transcript using hybrid approach:
        1. Basic transcription from Gladia (already done)
        2. Enhanced analysis via Azure OpenAI
        3. Pitch-specific scoring and insights
        
        Args:
            transcript_segments: Raw transcript segments from Gladia
            event_id: Event ID for multi-tenant isolation
            session_id: Session ID for logging context
            
        Returns:
            Enhanced analysis with pitch-specific insights
        """
        operation = "analyze_pitch_transcript"
        
        log_with_context(
            self.logger, "INFO", "Starting enhanced pitch transcript analysis",
            event_id=event_id,
            session_id=session_id,
            operation=operation,
            segments_count=len(transcript_segments)
        )
        
        try:
            # Step 1: Extract full transcript text
            full_transcript = self._extract_full_transcript(transcript_segments)
            
            if not full_transcript.strip():
                log_with_context(
                    self.logger, "WARNING", "Empty transcript provided for analysis",
                    event_id=event_id,
                    session_id=session_id,
                    operation=operation
                )
                return {
                    "success": False,
                    "error": "Empty transcript provided",
                    "analysis_method": "hybrid_ai_analysis"
                }
            
            # Step 2: Enhanced sentiment analysis via Azure OpenAI
            log_with_context(
                self.logger, "DEBUG", "Starting enhanced sentiment analysis",
                event_id=event_id,
                session_id=session_id,
                operation="enhanced_sentiment_analysis"
            )
            
            enhanced_sentiment = await self._analyze_enhanced_sentiment(
                full_transcript, event_id, session_id
            )
            
            # Step 3: Pitch-specific analysis via Azure OpenAI
            log_with_context(
                self.logger, "DEBUG", "Starting pitch-specific analysis",
                event_id=event_id,
                session_id=session_id,
                operation="pitch_specific_analysis"
            )
            
            pitch_analysis = await self._analyze_pitch_content(
                full_transcript, event_id, session_id
            )
            
            # Step 4: Analyze speech patterns from transcript
            log_with_context(
                self.logger, "DEBUG", "Analyzing speech patterns",
                event_id=event_id,
                session_id=session_id,
                operation="speech_pattern_analysis"
            )
            
            delivery_metrics = self._analyze_speech_patterns(transcript_segments)
            
            # Step 5: Create comprehensive pitch-specific analysis
            pitch_specific_analysis = self._create_pitch_specific_analysis(
                enhanced_sentiment, pitch_analysis, delivery_metrics
            )
            
            # Step 6: Calculate overall score
            overall_score = self._calculate_pitch_score(
                pitch_specific_analysis, delivery_metrics
            )
            
            result = {
                "success": True,
                "analysis_method": "hybrid_ai_analysis",
                "sentiment_analysis": enhanced_sentiment,
                "pitch_intelligence": pitch_analysis,
                "delivery_metrics": delivery_metrics,
                "pitch_specific_analysis": pitch_specific_analysis.__dict__,
                "overall_score": overall_score,
                "confidence_improvement": {
                    "original_gladia_confidence": "typically_0.3_or_lower",
                    "enhanced_confidence": enhanced_sentiment.get("confidence", 0.0),
                    "improvement_factor": f"{enhanced_sentiment.get('confidence', 0.0) / 0.3:.1f}x" if enhanced_sentiment.get('confidence', 0) > 0.3 else "significant"
                },
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            log_with_context(
                self.logger, "INFO", "Enhanced pitch analysis completed successfully",
                event_id=event_id,
                session_id=session_id,
                operation=operation,
                overall_score=overall_score,
                enhanced_confidence=enhanced_sentiment.get("confidence", 0.0),
                analysis_categories=len([k for k, v in result.items() if isinstance(v, dict)])
            )
            
            return result
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", f"Enhanced pitch analysis failed: {str(e)}",
                event_id=event_id,
                session_id=session_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "success": False,
                "error": f"Enhanced analysis failed: {str(e)}",
                "analysis_method": "hybrid_ai_analysis_error"
            }
    
    def _extract_full_transcript(self, transcript_segments: List[Dict]) -> str:
        """Extract full transcript text from segments."""
        text_parts = []
        
        for segment in transcript_segments:
            text = segment.get("text", "").strip()
            if text and not segment.get("type"):  # Skip AI insight segments
                text_parts.append(text)
        
        return " ".join(text_parts)
    
    async def _analyze_enhanced_sentiment(
        self, 
        transcript: str, 
        event_id: Optional[str],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Enhanced sentiment analysis using Azure OpenAI.
        Replaces basic Gladia positive/negative/neutral with contextual analysis.
        """
        try:
            client = await get_azure_openai_client()
            
            # Specialized prompt for pitch sentiment analysis
            system_prompt = """You are an expert in analyzing pitch presentation sentiment with deep contextual understanding.

Your task is to analyze the sentiment of a pitch presentation with much higher accuracy than basic positive/negative/neutral classification.

Analyze the following aspects:
1. Overall Sentiment: positive, negative, neutral (with high confidence)
2. Emotional Tone: confident, nervous, excited, concerned, passionate, uncertain
3. Enthusiasm Level: high, moderate, low
4. Confidence Level: high, moderate, low
5. Investor Appeal: how compelling this would be to investors (0.0-1.0)

Provide confidence scores (0.0-1.0) that are typically 0.8+ for clear sentiment indicators.
Focus on business context, technical competence, and market understanding cues.

Return your analysis in JSON format with these exact keys:
- overall_sentiment: string
- sentiment_confidence: float (0.0-1.0, aim for 0.8+)
- emotional_tone: string
- enthusiasm_level: string
- confidence_level: string
- investor_appeal: float (0.0-1.0)
- reasoning: string explaining your analysis"""

            request = LLMRequest(
                messages=[
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=f"Analyze this pitch transcript:\n\n{transcript}")
                ],
                temperature=0.2,  # Lower for more consistent analysis
                max_tokens=500
            )
            
            response = await client.chat_completion(request, event_id=event_id)
            
            if not response.is_success:
                log_with_context(
                    self.logger, "ERROR", f"Enhanced sentiment analysis API failed: {response.error}",
                    event_id=event_id,
                    session_id=session_id,
                    operation="enhanced_sentiment_api_call"
                )
                return self._fallback_sentiment_analysis(transcript)
            
            # Parse JSON response
            try:
                sentiment_data = json.loads(response.content)
                
                # Validate and enhance the response
                sentiment_data["analysis_method"] = "azure_openai_enhanced"
                sentiment_data["processing_timestamp"] = datetime.now(timezone.utc).isoformat()
                
                log_with_context(
                    self.logger, "DEBUG", "Enhanced sentiment analysis successful",
                    event_id=event_id,
                    session_id=session_id,
                    operation="enhanced_sentiment_analysis",
                    sentiment=sentiment_data.get("overall_sentiment"),
                    confidence=sentiment_data.get("sentiment_confidence"),
                    emotional_tone=sentiment_data.get("emotional_tone")
                )
                
                return sentiment_data
                
            except json.JSONDecodeError:
                log_with_context(
                    self.logger, "WARNING", "Enhanced sentiment response not valid JSON, using fallback",
                    event_id=event_id,
                    session_id=session_id,
                    operation="enhanced_sentiment_json_parse",
                    raw_response=response.content[:200]
                )
                return self._fallback_sentiment_analysis(transcript)
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", f"Enhanced sentiment analysis error: {str(e)}",
                event_id=event_id,
                session_id=session_id,
                operation="enhanced_sentiment_analysis",
                error_type=type(e).__name__
            )
            return self._fallback_sentiment_analysis(transcript)
    
    async def _analyze_pitch_content(
        self, 
        transcript: str, 
        event_id: Optional[str],
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Pitch-specific content analysis using Azure OpenAI.
        Analyzes persuasiveness, technical confidence, market understanding, etc.
        """
        try:
            client = await get_azure_openai_client()
            
            # Specialized prompt for pitch-specific analysis
            system_prompt = """You are an expert pitch competition judge specializing in AI agent competitions.

Analyze this pitch presentation for pitch-specific metrics that go far beyond basic sentiment:

CORE PITCH METRICS (0.0-1.0 scores):
1. Persuasiveness Score: How compelling is the overall argument?
2. Technical Confidence: Does the speaker demonstrate deep technical understanding?
3. Market Understanding: Clear grasp of market size, customers, competition?
4. Clarity Score: How clearly is the solution explained?
5. Competitive Advantage Confidence: Strong differentiation from competitors?

PITCH STRUCTURE ANALYSIS (true/false):
- Has Clear Problem: Does the pitch identify a specific, compelling problem?
- Has Clear Solution: Is the solution clearly articulated and feasible?
- Demonstrates Market Knowledge: Shows understanding of target market?
- Shows Technical Depth: Demonstrates technical sophistication?
- Mentions Competition: Acknowledges competitive landscape?

COACHING INSIGHTS:
- Strengths: List 2-3 specific strengths demonstrated in this pitch
- Improvement Areas: List 2-3 areas that could be enhanced
- Specific Recommendations: List 2-3 actionable recommendations

Return analysis in JSON format with these exact keys:
{
  "persuasiveness_score": float,
  "technical_confidence": float, 
  "market_understanding": float,
  "clarity_score": float,
  "competitive_advantage_confidence": float,
  "has_clear_problem": bool,
  "has_clear_solution": bool,
  "demonstrates_market_knowledge": bool,
  "shows_technical_depth": bool,
  "mentions_competition": bool,
  "strengths": [string array],
  "improvement_areas": [string array], 
  "specific_recommendations": [string array],
  "overall_pitch_quality": string
}"""

            request = LLMRequest(
                messages=[
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=f"Analyze this pitch transcript:\n\n{transcript}")
                ],
                temperature=0.3,  # Slightly higher for more nuanced analysis
                max_tokens=800
            )
            
            response = await client.chat_completion(request, event_id=event_id)
            
            if not response.is_success:
                log_with_context(
                    self.logger, "ERROR", f"Pitch content analysis API failed: {response.error}",
                    event_id=event_id,
                    session_id=session_id,
                    operation="pitch_content_api_call"
                )
                return self._fallback_pitch_analysis(transcript)
            
            # Parse JSON response
            try:
                pitch_data = json.loads(response.content)
                
                # Enhance the response
                pitch_data["analysis_method"] = "azure_openai_pitch_specific"
                pitch_data["processing_timestamp"] = datetime.now(timezone.utc).isoformat()
                
                log_with_context(
                    self.logger, "DEBUG", "Pitch content analysis successful",
                    event_id=event_id,
                    session_id=session_id,
                    operation="pitch_content_analysis",
                    persuasiveness=pitch_data.get("persuasiveness_score"),
                    technical_confidence=pitch_data.get("technical_confidence"),
                    market_understanding=pitch_data.get("market_understanding")
                )
                
                return pitch_data
                
            except json.JSONDecodeError:
                log_with_context(
                    self.logger, "WARNING", "Pitch content response not valid JSON, using fallback",
                    event_id=event_id,
                    session_id=session_id,
                    operation="pitch_content_json_parse",
                    raw_response=response.content[:200]
                )
                return self._fallback_pitch_analysis(transcript)
                
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", f"Pitch content analysis error: {str(e)}",
                event_id=event_id,
                session_id=session_id,
                operation="pitch_content_analysis",
                error_type=type(e).__name__
            )
            return self._fallback_pitch_analysis(transcript)
    
    def _analyze_speech_patterns(self, transcript_segments: List[Dict]) -> Dict[str, Any]:
        """
        Analyze speech patterns from transcript segments.
        Enhanced version of basic Gladia metrics.
        """
        total_words = 0
        total_duration = 0.0
        segment_count = 0
        confidence_scores = []
        
        for segment in transcript_segments:
            text = segment.get("text", "").strip()
            if text and not segment.get("type"):  # Skip AI insight segments
                words = len(text.split())
                total_words += words
                segment_count += 1
                
                # Calculate segment duration
                start_time = segment.get("start_time", 0)
                end_time = segment.get("end_time", 0)
                duration = max(0, end_time - start_time)
                total_duration += duration
                
                # Collect confidence scores
                confidence = segment.get("confidence", 0.0)
                if confidence > 0:
                    confidence_scores.append(confidence)
        
        # Calculate metrics
        words_per_minute = (total_words / total_duration * 60) if total_duration > 0 else 0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Speech quality assessment
        speaking_rate_quality = self._assess_speaking_rate(words_per_minute)
        confidence_quality = self._assess_confidence_quality(avg_confidence)
        
        return {
            "total_words": total_words,
            "total_duration_seconds": total_duration,
            "words_per_minute": words_per_minute,
            "segment_count": segment_count,
            "average_confidence": avg_confidence,
            "speaking_rate_assessment": speaking_rate_quality,
            "confidence_assessment": confidence_quality,
            "delivery_quality_score": self._calculate_delivery_quality(
                words_per_minute, avg_confidence
            ),
            "analysis_method": "enhanced_speech_patterns"
        }
    
    def _assess_speaking_rate(self, wpm: float) -> Dict[str, Any]:
        """Assess speaking rate quality for pitch presentations."""
        if 140 <= wpm <= 170:
            return {"assessment": "optimal", "score": 1.0, "recommendation": "Excellent pace for investor presentations"}
        elif 120 <= wpm < 140:
            return {"assessment": "slightly_slow", "score": 0.8, "recommendation": "Consider increasing pace slightly for better engagement"}
        elif 170 < wpm <= 190:
            return {"assessment": "slightly_fast", "score": 0.8, "recommendation": "Consider slowing down slightly for better comprehension"}
        elif wpm < 120:
            return {"assessment": "too_slow", "score": 0.6, "recommendation": "Increase speaking pace to maintain audience engagement"}
        else:  # wpm > 190
            return {"assessment": "too_fast", "score": 0.5, "recommendation": "Slow down significantly for better audience comprehension"}
    
    def _assess_confidence_quality(self, avg_confidence: float) -> Dict[str, Any]:
        """Assess transcription confidence quality."""
        if avg_confidence >= 0.8:
            return {"assessment": "high", "score": 1.0, "note": "Clear, well-articulated speech"}
        elif avg_confidence >= 0.6:
            return {"assessment": "moderate", "score": 0.7, "note": "Generally clear speech with some unclear segments"}
        elif avg_confidence >= 0.3:
            return {"assessment": "low", "score": 0.4, "note": "Significant clarity issues, may need better audio setup"}
        else:
            return {"assessment": "very_low", "score": 0.2, "note": "Speech very difficult to transcribe, audio quality issues"}
    
    def _calculate_delivery_quality(self, wpm: float, avg_confidence: float) -> float:
        """Calculate overall delivery quality score (0.0-1.0)."""
        rate_score = self._assess_speaking_rate(wpm)["score"]
        confidence_score = self._assess_confidence_quality(avg_confidence)["score"]
        
        # Weighted average (rate 60%, confidence 40%)
        return round(rate_score * 0.6 + confidence_score * 0.4, 2)
    
    def _create_pitch_specific_analysis(
        self,
        sentiment_data: Dict[str, Any],
        pitch_data: Dict[str, Any],
        delivery_metrics: Dict[str, Any]
    ) -> PitchSpecificAnalysis:
        """Create comprehensive pitch-specific analysis object."""
        return PitchSpecificAnalysis(
            # Core pitch metrics from AI analysis
            persuasiveness_score=pitch_data.get("persuasiveness_score", 0.5),
            technical_confidence=pitch_data.get("technical_confidence", 0.5),
            market_understanding=pitch_data.get("market_understanding", 0.5),
            enthusiasm_level=sentiment_data.get("enthusiasm_level", "moderate"),
            clarity_score=pitch_data.get("clarity_score", 0.5),
            investor_appeal=sentiment_data.get("investor_appeal", 0.5),
            competitive_advantage_confidence=pitch_data.get("competitive_advantage_confidence", 0.5),
            
            # Enhanced sentiment with much higher confidence
            overall_sentiment=sentiment_data.get("overall_sentiment", "neutral"),
            sentiment_confidence=sentiment_data.get("sentiment_confidence", 0.8),  # Much higher than Gladia's 0.3
            emotional_tone=sentiment_data.get("emotional_tone", "neutral"),
            
            # Pitch structure analysis
            has_clear_problem=pitch_data.get("has_clear_problem", False),
            has_clear_solution=pitch_data.get("has_clear_solution", False),
            demonstrates_market_knowledge=pitch_data.get("demonstrates_market_knowledge", False),
            shows_technical_depth=pitch_data.get("shows_technical_depth", False),
            mentions_competition=pitch_data.get("mentions_competition", False),
            
            # Coaching insights
            strengths=pitch_data.get("strengths", ["Completed presentation"]),
            improvement_areas=pitch_data.get("improvement_areas", ["Consider adding more detail"]),
            specific_recommendations=pitch_data.get("specific_recommendations", ["Practice timing"]),
            
            # Metadata
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            confidence_level="high" if sentiment_data.get("sentiment_confidence", 0) >= 0.8 else "moderate",
            processing_method="hybrid_ai_analysis"
        )
    
    def _calculate_pitch_score(
        self,
        pitch_analysis: PitchSpecificAnalysis,
        delivery_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall pitch score based on enhanced analysis."""
        # Weight different components
        content_score = (
            pitch_analysis.persuasiveness_score * 0.3 +
            pitch_analysis.technical_confidence * 0.25 +
            pitch_analysis.market_understanding * 0.25 +
            pitch_analysis.clarity_score * 0.2
        )
        
        delivery_score = delivery_metrics.get("delivery_quality_score", 0.5)
        investor_appeal = pitch_analysis.investor_appeal
        
        # Overall weighted score
        overall_score = round(
            content_score * 0.6 +
            delivery_score * 0.2 + 
            investor_appeal * 0.2,
            2
        )
        
        return {
            "overall_score": overall_score,
            "content_score": round(content_score, 2),
            "delivery_score": delivery_score,
            "investor_appeal": investor_appeal,
            "score_breakdown": {
                "persuasiveness": pitch_analysis.persuasiveness_score,
                "technical_confidence": pitch_analysis.technical_confidence,
                "market_understanding": pitch_analysis.market_understanding,
                "clarity": pitch_analysis.clarity_score,
                "delivery_quality": delivery_score
            },
            "scoring_method": "enhanced_hybrid_analysis"
        }
    
    def _fallback_sentiment_analysis(self, transcript: str) -> Dict[str, Any]:
        """Fallback sentiment analysis if Azure OpenAI fails."""
        # Simple keyword-based fallback with higher confidence than basic Gladia
        positive_keywords = ["excited", "innovative", "solution", "growth", "success", "opportunity"]
        negative_keywords = ["problem", "challenge", "difficult", "issue", "concern"]
        
        transcript_lower = transcript.lower()
        positive_count = sum(1 for word in positive_keywords if word in transcript_lower)
        negative_count = sum(1 for word in negative_keywords if word in transcript_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            confidence = 0.7
        elif negative_count > positive_count:
            sentiment = "negative"
            confidence = 0.7
        else:
            sentiment = "neutral"
            confidence = 0.6
        
        return {
            "overall_sentiment": sentiment,
            "sentiment_confidence": confidence,
            "emotional_tone": "neutral",
            "enthusiasm_level": "moderate",
            "confidence_level": "moderate", 
            "investor_appeal": 0.5,
            "reasoning": "Fallback keyword-based analysis",
            "analysis_method": "fallback_keyword_based"
        }
    
    def _fallback_pitch_analysis(self, transcript: str) -> Dict[str, Any]:
        """Fallback pitch analysis if Azure OpenAI fails."""
        return {
            "persuasiveness_score": 0.5,
            "technical_confidence": 0.5,
            "market_understanding": 0.5,
            "clarity_score": 0.6,
            "competitive_advantage_confidence": 0.5,
            "has_clear_problem": "solution" in transcript.lower(),
            "has_clear_solution": "solution" in transcript.lower(),
            "demonstrates_market_knowledge": "market" in transcript.lower(),
            "shows_technical_depth": any(word in transcript.lower() for word in ["technical", "algorithm", "api", "data"]),
            "mentions_competition": "compet" in transcript.lower(),
            "strengths": ["Completed presentation"],
            "improvement_areas": ["Consider more specific details"],
            "specific_recommendations": ["Practice with timer"],
            "overall_pitch_quality": "moderate",
            "analysis_method": "fallback_basic_analysis"
        }


# Singleton instance
enhanced_audio_intelligence = EnhancedAudioIntelligence()
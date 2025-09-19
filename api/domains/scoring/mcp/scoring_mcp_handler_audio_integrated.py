"""
Enhanced Scoring MCP Handler with Audio Intelligence Integration

This handler integrates Gladia Audio Intelligence with presentation delivery scoring.
It combines transcript analysis with objective audio metrics for comprehensive evaluation.
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis.asyncio as redis
import traceback

# Import the existing Gladia MCP handler for audio intelligence
from ...recordings.mcp.gladia_mcp_handler import gladia_mcp_handler
from ...recordings.value_objects.audio_intelligence import AudioIntelligence

# Note: Removed llamaindex_service dependency to avoid import errors
# from ...indexing.services.llamaindex_service import llamaindex_service


class AudioIntegratedScoringMCPHandler:
    """Enhanced MCP handler with audio intelligence integration."""
    
    def __init__(self):
        """Initialize the enhanced scoring MCP handler."""
        self.redis_client: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis client connection."""
        if self.redis_client is None:
            redis_url = "redis://redis:6379/0"  # Docker internal network
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client
    
    async def analyze_presentation_delivery(
        self,
        session_id: str,
        event_id: str,
        include_audio_metrics: bool = True,
        benchmark_wpm: int = 150
    ) -> Dict[str, Any]:
        """
        Analyze presentation delivery using both transcript and audio intelligence.
        
        Args:
            session_id: Session identifier from pitch recording
            event_id: Event ID for multi-tenant isolation
            include_audio_metrics: Whether to include Gladia Audio Intelligence
            benchmark_wpm: Target words per minute for comparison
            
        Returns:
            Comprehensive presentation delivery analysis
        """
        analysis_start = datetime.utcnow()
        
        try:
            print(f"🎯 Starting presentation delivery analysis for session: {session_id}")
            
            # STEP 1: Get session data and transcript
            session_data = await self._get_session_data(session_id, event_id)
            if "error" in session_data:
                return session_data
            
            transcript_text = session_data.get("final_transcript", {}).get("total_text", "")
            if not transcript_text:
                return {
                    "error": "No transcript available for presentation analysis",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "missing_transcript"
                }
            
            print(f"📜 Retrieved transcript: {len(transcript_text)} characters")
            
            # STEP 2: Get audio intelligence if requested
            audio_intelligence = None
            if include_audio_metrics:
                print("🎵 Fetching audio intelligence from Gladia...")
                try:
                    ai_result = await gladia_mcp_handler.get_audio_intelligence(session_id)
                    
                    if "error" not in ai_result:
                        # Convert to AudioIntelligence object if we have valid data
                        if isinstance(ai_result, dict) and "speech_metrics" in ai_result:
                            audio_intelligence = ai_result
                            print("✅ Audio intelligence data retrieved successfully")
                        else:
                            print(f"⚠️ Audio intelligence format unexpected: {type(ai_result)}")
                    else:
                        print(f"⚠️ Audio intelligence error: {ai_result.get('error')}")
                        # Continue without audio intelligence
                        
                except Exception as e:
                    print(f"⚠️ Audio intelligence fetch failed: {e}")
                    # Continue without audio intelligence
            
            # STEP 3: Analyze transcript content
            transcript_analysis = await self._analyze_transcript_content(
                transcript_text, session_data, benchmark_wpm
            )
            
            # STEP 4: Combine analyses
            combined_analysis = await self._combine_transcript_and_audio_analysis(
                transcript_analysis=transcript_analysis,
                audio_intelligence=audio_intelligence,
                session_data=session_data,
                benchmark_wpm=benchmark_wpm
            )
            
            # Add metadata
            analysis_duration = (datetime.utcnow() - analysis_start).total_seconds()
            combined_analysis.update({
                "_analysis_metadata": {
                    "session_id": session_id,
                    "event_id": event_id,
                    "analysis_type": "presentation_delivery",
                    "included_audio_intelligence": bool(audio_intelligence),
                    "benchmark_wpm": benchmark_wpm,
                    "analysis_duration_seconds": round(analysis_duration, 2),
                    "completed_at": datetime.utcnow().isoformat()
                }
            })
            
            print(f"🎉 Analysis complete in {analysis_duration:.2f}s")
            return combined_analysis
            
        except Exception as e:
            error_msg = f"Presentation delivery analysis failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg,
                "session_id": session_id,
                "event_id": event_id,
                "error_type": "analysis_failure",
                "traceback": traceback.format_exc()
            }
    
    async def _get_session_data(self, session_id: str, event_id: str) -> Dict[str, Any]:
        """Get session data from Redis."""
        try:
            redis_client = await self.get_redis()
            session_key = f"event:{event_id}:session:{session_id}"
            session_json = await redis_client.get(session_key)
            
            if not session_json:
                return {
                    "error": f"Session {session_id} not found in event {event_id}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "session_not_found"
                }
            
            session_data = json.loads(session_json)
            return session_data
            
        except Exception as e:
            return {
                "error": f"Failed to retrieve session data: {str(e)}",
                "session_id": session_id,
                "event_id": event_id,
                "error_type": "database_error"
            }
    
    async def _analyze_transcript_content(
        self, 
        transcript_text: str, 
        session_data: Dict[str, Any],
        benchmark_wpm: int
    ) -> Dict[str, Any]:
        """Analyze transcript content for presentation quality."""
        
        # Calculate basic metrics
        word_count = len(transcript_text.split())
        char_count = len(transcript_text)
        sentence_count = len([s for s in transcript_text.split('.') if s.strip()])
        
        # Calculate estimated duration and WPM
        estimated_wpm = 0
        duration_score = 0.5  # Default neutral score
        
        if word_count > 0:
            # Estimate duration based on word count and average speaking rate
            estimated_duration_minutes = word_count / 150  # Assume 150 WPM average
            estimated_wpm = word_count / estimated_duration_minutes if estimated_duration_minutes > 0 else 0
            
            # Score based on 3-minute target
            if 2.5 <= estimated_duration_minutes <= 3.5:
                duration_score = 1.0  # Perfect timing
            elif 2.0 <= estimated_duration_minutes < 2.5 or 3.5 < estimated_duration_minutes <= 4.0:
                duration_score = 0.8  # Good timing
            elif 1.5 <= estimated_duration_minutes < 2.0 or 4.0 < estimated_duration_minutes <= 4.5:
                duration_score = 0.6  # Acceptable timing
            else:
                duration_score = 0.3  # Poor timing
        
        # Analyze content structure
        has_introduction = any(word in transcript_text.lower() for word in ['hello', 'hi', 'welcome', 'today', 'presenting'])
        has_problem_statement = any(word in transcript_text.lower() for word in ['problem', 'challenge', 'issue', 'pain'])
        has_solution = any(word in transcript_text.lower() for word in ['solution', 'solve', 'address', 'approach'])
        has_demo = any(word in transcript_text.lower() for word in ['demo', 'demonstration', 'show', 'example'])
        has_conclusion = any(word in transcript_text.lower() for word in ['conclusion', 'summary', 'thank', 'questions'])
        
        structure_score = sum([has_introduction, has_problem_statement, has_solution, has_demo, has_conclusion]) / 5.0
        
        # Analyze clarity metrics
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        clarity_score = min(1.0, max(0.3, 1.0 - abs(avg_sentence_length - 15) / 20))  # Optimal ~15 words/sentence
        
        return {
            "transcript_metrics": {
                "word_count": word_count,
                "character_count": char_count,
                "sentence_count": sentence_count,
                "estimated_duration_minutes": round(estimated_duration_minutes, 1) if 'estimated_duration_minutes' in locals() else None,
                "estimated_wpm": round(estimated_wpm, 1) if estimated_wpm > 0 else None,
                "average_sentence_length": round(avg_sentence_length, 1)
            },
            "content_structure": {
                "has_introduction": has_introduction,
                "has_problem_statement": has_problem_statement,
                "has_solution": has_solution,
                "has_demo": has_demo,
                "has_conclusion": has_conclusion,
                "structure_completeness_score": round(structure_score, 2)
            },
            "scoring": {
                "duration_score": round(duration_score, 2),
                "structure_score": round(structure_score, 2),
                "clarity_score": round(clarity_score, 2)
            }
        }
    
    async def _combine_transcript_and_audio_analysis(
        self,
        transcript_analysis: Dict[str, Any],
        audio_intelligence: Optional[Dict[str, Any]],
        session_data: Dict[str, Any],
        benchmark_wpm: int
    ) -> Dict[str, Any]:
        """Combine transcript and audio intelligence analyses."""
        
        # Start with transcript analysis
        result = {
            "session_id": session_data.get("session_id"),
            "team_name": session_data.get("team_name"),
            "pitch_title": session_data.get("pitch_title"),
            "transcript_analysis": transcript_analysis
        }
        
        # Add audio intelligence if available
        if audio_intelligence and "error" not in audio_intelligence:
            result["audio_intelligence"] = audio_intelligence
            
            # Create combined scoring
            transcript_score = (
                transcript_analysis["scoring"]["duration_score"] * 0.3 +
                transcript_analysis["scoring"]["structure_score"] * 0.4 +
                transcript_analysis["scoring"]["clarity_score"] * 0.3
            )
            
            # If we have audio intelligence with delivery score, use it
            if isinstance(audio_intelligence, dict) and "delivery_score" in audio_intelligence:
                audio_score = audio_intelligence["delivery_score"] / 25.0  # Normalize to 0-1
                combined_score = (transcript_score * 0.4 + audio_score * 0.6)  # Weight audio more heavily
            else:
                combined_score = transcript_score
                
            result["combined_scoring"] = {
                "transcript_score": round(transcript_score, 2),
                "audio_score": round(audio_score, 2) if 'audio_score' in locals() else None,
                "overall_presentation_score": round(combined_score * 25, 1),  # Out of 25 points
                "grade": self._get_presentation_grade(combined_score)
            }
            
            # Generate comprehensive coaching insights
            coaching_insights = []
            
            # From transcript analysis
            if transcript_analysis["scoring"]["duration_score"] < 0.8:
                coaching_insights.append("Focus on timing - aim for 2.5-3.5 minutes for optimal impact")
            
            if transcript_analysis["scoring"]["structure_score"] < 0.8:
                coaching_insights.append("Improve structure - ensure clear intro, problem, solution, demo, and conclusion")
            
            # From audio intelligence if available
            if isinstance(audio_intelligence, dict) and "coaching_insights" in audio_intelligence:
                coaching_insights.extend(audio_intelligence["coaching_insights"])
                
            result["coaching_insights"] = coaching_insights
            
        else:
            # Only transcript analysis available
            transcript_score = (
                transcript_analysis["scoring"]["duration_score"] * 0.3 +
                transcript_analysis["scoring"]["structure_score"] * 0.4 +
                transcript_analysis["scoring"]["clarity_score"] * 0.3
            )
            
            result["combined_scoring"] = {
                "transcript_score": round(transcript_score, 2),
                "audio_score": None,
                "overall_presentation_score": round(transcript_score * 25, 1),  # Out of 25 points
                "grade": self._get_presentation_grade(transcript_score)
            }
            
            result["audio_intelligence"] = {
                "available": False,
                "reason": "Audio intelligence data not available for this session"
            }
            
            # Basic coaching from transcript only
            coaching_insights = []
            if transcript_analysis["scoring"]["duration_score"] < 0.8:
                coaching_insights.append("Focus on timing - aim for 2.5-3.5 minutes for optimal impact")
            if transcript_analysis["scoring"]["structure_score"] < 0.8:
                coaching_insights.append("Improve structure - ensure clear intro, problem, solution, demo, and conclusion")
            if transcript_analysis["scoring"]["clarity_score"] < 0.8:
                coaching_insights.append("Improve clarity - use shorter sentences and clearer language")
                
            result["coaching_insights"] = coaching_insights
        
        return result
    
    def _get_presentation_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return "A+"
        elif score >= 0.85:
            return "A"
        elif score >= 0.8:
            return "A-"
        elif score >= 0.75:
            return "B+"
        elif score >= 0.7:
            return "B"
        elif score >= 0.65:
            return "B-"
        elif score >= 0.6:
            return "C+"
        elif score >= 0.55:
            return "C"
        elif score >= 0.5:
            return "C-"
        else:
            return "D"


# Create singleton instance
audio_integrated_scoring_mcp_handler = AudioIntegratedScoringMCPHandler()
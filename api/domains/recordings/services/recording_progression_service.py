#!/usr/bin/env python3
"""
Recording Progression Analysis Domain Service

Domain service for analyzing how teams' pitch recordings evolve over time.
Uses LlamaIndex for semantic analysis and vector storage for progression tracking.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..entities.recording_version import RecordingVersion
from ..value_objects.team_id import TeamId
from ..value_objects.recording_version_id import RecordingVersionId
from ..repositories.recording_version_repository import RecordingVersionRepository
from ...shared.infrastructure.azure_openai_client import get_azure_openai_client
from ...shared.value_objects.llm_request import LLMRequest, LLMMessage


class RecordingProgressionService:
    """Domain service for analyzing recording progression over time."""
    
    def __init__(self, repository: RecordingVersionRepository):
        self.repository = repository
    
    async def add_recording_version(
        self,
        team_id: TeamId,
        team_name: str,
        recording_title: str,
        stt_session: 'STTSession',
        event_id: Optional[str] = None,
        scores: Optional['RecordingScores'] = None,
        audio_intelligence: Optional['AudioIntelligence'] = None
    ) -> RecordingVersion:
        """Add a new recording version for a team."""
        
        # Get next version number for this team
        existing_versions = await self.repository.get_versions_by_team(team_id)
        next_version_number = len(existing_versions) + 1
        
        # Create the recording version
        recording_version = RecordingVersion.from_stt_session(
            stt_session=stt_session,
            team_id=team_id,
            team_name=team_name,
            recording_title=recording_title,
            version_number=next_version_number,
            scores=scores,
            audio_intelligence=audio_intelligence
        )
        
        # Store the version
        await self.repository.save(recording_version)
        
        return recording_version
    
    async def get_team_progression(self, team_id: TeamId) -> List[RecordingVersion]:
        """Get all recording versions for a team, sorted by version number."""
        versions = await self.repository.get_versions_by_team(team_id)
        return sorted(versions, key=lambda v: v.version_number)
    
    async def analyze_team_progression(self, team_id: TeamId) -> Dict[str, Any]:
        """Analyze how a team's recordings have evolved over time."""
        versions = await self.get_team_progression(team_id)
        
        if len(versions) < 2:
            return {
                "error": "Need at least 2 recording versions to analyze progression",
                "team_id": str(team_id),
                "version_count": len(versions)
            }
        
        # Calculate metrics
        metrics = self._calculate_progression_metrics(versions)
        
        # Get LLM analysis
        llm_analysis = await self._analyze_with_llm(versions)
        
        return {
            "team_id": str(team_id),
            "team_name": versions[0].team_name,
            "version_count": len(versions),
            "first_version": self._version_summary(versions[0]),
            "latest_version": self._version_summary(versions[-1]),
            "progression_metrics": metrics,
            "llm_analysis": llm_analysis,
            "timeline": [self._version_summary(v) for v in versions],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def compare_versions(
        self,
        version_1_id: RecordingVersionId,
        version_2_id: RecordingVersionId
    ) -> Dict[str, Any]:
        """Compare two specific recording versions."""
        
        version_1 = await self.repository.get_by_id(version_1_id)
        version_2 = await self.repository.get_by_id(version_2_id)
        
        if not version_1 or not version_2:
            return {"error": "One or both versions not found"}
        
        # Compare scores if both have them
        score_comparison = None
        if version_1.has_scores and version_2.has_scores:
            score_comparison = version_2.scores.compare_with(version_1.scores)
        
        # Get LLM comparison
        llm_comparison = await self._compare_versions_with_llm(version_1, version_2)
        
        return {
            "version_1": self._version_summary(version_1),
            "version_2": self._version_summary(version_2),
            "score_comparison": score_comparison,
            "llm_comparison": llm_comparison,
            "comparison_timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_progression_insights(self, team_id: TeamId) -> Dict[str, Any]:
        """Get AI-powered insights about a team's recording progression."""
        versions = await self.get_team_progression(team_id)
        
        if len(versions) < 2:
            return {"error": "Need at least 2 versions for insights"}
        
        # Generate comprehensive insights using LLM
        insights = await self._generate_progression_insights(versions)
        
        return {
            "team_id": str(team_id),
            "team_name": versions[0].team_name,
            "insights": insights,
            "version_count": len(versions),
            "time_span_days": (versions[-1].created_at - versions[0].created_at).days,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def _calculate_progression_metrics(self, versions: List[RecordingVersion]) -> Dict[str, Any]:
        """Calculate quantitative progression metrics."""
        if len(versions) < 2:
            return {}
        
        first = versions[0]
        latest = versions[-1]
        
        metrics = {
            "time_span_days": (latest.created_at - first.created_at).days,
            "version_count": len(versions),
            "word_count_change": latest.word_count - first.word_count,
            "duration_change_seconds": latest.duration_seconds - first.duration_seconds,
            "title_changes": sum(
                1 for i in range(1, len(versions))
                if versions[i].recording_title != versions[i-1].recording_title
            )
        }
        
        # Score progression analysis
        if first.has_scores and latest.has_scores:
            score_changes = latest.scores.compare_with(first.scores)
            metrics["score_changes"] = score_changes
            
            # Calculate average score improvement per version
            if len(versions) > 2:
                total_score_change = score_changes["total_change"]
                metrics["avg_score_improvement_per_version"] = total_score_change / (len(versions) - 1)
        
        # Audio intelligence progression
        if first.has_audio_intelligence and latest.has_audio_intelligence:
            ai_first = first.audio_intelligence
            ai_latest = latest.audio_intelligence
            
            metrics["audio_intelligence_changes"] = {
                "confidence_change": (
                    ai_latest.confidence_metrics.confidence_score - 
                    ai_first.confidence_metrics.confidence_score
                ),
                "filler_percentage_change": (
                    ai_latest.filler_analysis.filler_percentage - 
                    ai_first.filler_analysis.filler_percentage
                ),
                "words_per_minute_change": (
                    ai_latest.speech_metrics.words_per_minute - 
                    ai_first.speech_metrics.words_per_minute
                )
            }
        
        return metrics
    
    def _version_summary(self, version: RecordingVersion) -> Dict[str, Any]:
        """Create a summary representation of a recording version."""
        summary = {
            "version_id": str(version.version_id),
            "version_number": version.version_number,
            "recording_title": version.recording_title,
            "created_at": version.created_at.isoformat(),
            "word_count": version.word_count,
            "duration_seconds": version.duration_seconds
        }
        
        if version.has_scores:
            summary["scores"] = {
                "total": version.get_total_score(),
                "idea": version.get_score_by_category("idea"),
                "technical": version.get_score_by_category("technical"),
                "presentation": version.get_score_by_category("presentation"),
                "tool_use": version.get_score_by_category("tool_use"),
                "ranking_tier": version.scores.ranking_tier
            }
        
        if version.has_audio_intelligence:
            ai = version.audio_intelligence
            summary["audio_intelligence"] = {
                "confidence_score": ai.confidence_metrics.confidence_score,
                "filler_percentage": ai.filler_analysis.filler_percentage,
                "words_per_minute": ai.speech_metrics.words_per_minute,
                "energy_level": ai.confidence_metrics.energy_level.value
            }
        
        return summary
    
    async def _analyze_with_llm(self, versions: List[RecordingVersion]) -> Dict[str, Any]:
        """Use Azure OpenAI to analyze recording progression."""
        client = await get_azure_openai_client()
        
        # Prepare context with all versions
        context = f"RECORDING PROGRESSION ANALYSIS for {versions[0].team_name}\n\n"
        for version in versions:
            context += f"VERSION {version.version_number} ({version.created_at.date()}):\n"
            context += f"Title: {version.recording_title}\n"
            context += f"Duration: {version.duration_seconds:.1f}s, Words: {version.word_count}\n"
            context += f"Transcript: {version.final_transcript_text}\n"
            
            if version.has_scores:
                context += f"Scores: Total {version.get_total_score()}/100 "
                context += f"(Idea: {version.get_score_by_category('idea')}, "
                context += f"Tech: {version.get_score_by_category('technical')}, "
                context += f"Presentation: {version.get_score_by_category('presentation')}, "
                context += f"Tools: {version.get_score_by_category('tool_use')})\n"
            
            if version.has_audio_intelligence:
                ai = version.audio_intelligence
                context += f"Audio Intelligence: Confidence {ai.confidence_metrics.confidence_score:.2f}, "
                context += f"Fillers {ai.filler_analysis.filler_percentage:.1f}%, "
                context += f"WPM {ai.speech_metrics.words_per_minute:.0f}\n"
            
            context += "\n" + "="*80 + "\n\n"
        
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content="""You are an expert pitch coach analyzing how a team's recordings have evolved over time.

Analyze the progression and provide:
1. **Key Improvements**: What got significantly better between versions
2. **Areas of Concern**: What might have gotten worse or stagnated
3. **Content Evolution**: How the core message and structure changed
4. **Delivery Progress**: Changes in presentation delivery and confidence
5. **Strategic Recommendations**: Specific, actionable advice for the next version

Be specific about version numbers and cite exact changes. Focus on actionable insights."""
                ),
                LLMMessage(
                    role="user",
                    content=context
                )
            ],
            max_tokens=800,
            temperature=0.4
        )
        
        response = await client.chat_completion(request)
        
        return {
            "analysis": response.content,
            "token_usage": response.usage,
            "error": response.error
        }
    
    async def _compare_versions_with_llm(
        self,
        version_1: RecordingVersion,
        version_2: RecordingVersion
    ) -> Dict[str, Any]:
        """Compare two specific versions using LLM."""
        client = await get_azure_openai_client()
        
        comparison_context = f"""
COMPARE RECORDING VERSIONS:

VERSION {version_1.version_number} ({version_1.created_at.date()}):
Title: {version_1.recording_title}
Duration: {version_1.duration_seconds:.1f}s, Words: {version_1.word_count}
Transcript: {version_1.final_transcript_text}
"""
        
        if version_1.has_scores:
            comparison_context += f"Scores: {version_1.get_total_score()}/100\n"
        
        comparison_context += f"""

VERSION {version_2.version_number} ({version_2.created_at.date()}):
Title: {version_2.recording_title}
Duration: {version_2.duration_seconds:.1f}s, Words: {version_2.word_count}
Transcript: {version_2.final_transcript_text}
"""
        
        if version_2.has_scores:
            comparison_context += f"Scores: {version_2.get_total_score()}/100\n"
        
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content="You are a pitch coach comparing two versions of the same team's recording. Identify specific differences, improvements, and regressions between versions."
                ),
                LLMMessage(
                    role="user",
                    content=comparison_context.strip()
                )
            ],
            max_tokens=600,
            temperature=0.4
        )
        
        response = await client.chat_completion(request)
        
        return {
            "comparison_analysis": response.content,
            "token_usage": response.usage
        }
    
    async def _generate_progression_insights(self, versions: List[RecordingVersion]) -> str:
        """Generate comprehensive progression insights using LLM."""
        client = await get_azure_openai_client()
        
        # Create a concise summary for insights generation
        context = f"RECORDING PROGRESSION INSIGHTS for {versions[0].team_name}:\n\n"
        context += f"Team has {len(versions)} recording versions spanning "
        context += f"{(versions[-1].created_at - versions[0].created_at).days} days.\n\n"
        
        for version in versions:
            context += f"V{version.version_number} ({version.created_at.date()}): "
            context += f"{version.recording_title}\n"
            context += f"  • {version.word_count} words, {version.duration_seconds:.1f}s\n"
            
            if version.has_scores:
                context += f"  • Score: {version.get_total_score()}/100\n"
            
            context += f"  • Key content: {version.final_transcript_text[:150]}...\n\n"
        
        request = LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content="""Provide strategic insights about this team's recording progression. Focus on:

1. Overall trajectory and improvement patterns
2. Strengths that are developing consistently
3. Persistent weaknesses that need attention
4. Specific recommendations for the next version
5. Competitive positioning insights

Be concise but actionable."""
                ),
                LLMMessage(
                    role="user",
                    content=context
                )
            ],
            max_tokens=500,
            temperature=0.5
        )
        
        response = await client.chat_completion(request)
        
        return response.content
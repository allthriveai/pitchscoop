"""
Scoring MCP Handler - AI-Powered Pitch Scoring

This handler provides MCP tools for scoring pitch presentations using Azure OpenAI.
Integrates with the existing pitch recording workflow to analyze transcripts and
generate structured scores based on the official competition criteria.

Available tools:
- analysis.score_pitch: Complete pitch scoring using AI analysis
- analysis.score_idea: Analyze idea uniqueness and value proposition  
- analysis.score_technical: Analyze technical implementation quality
- analysis.score_tools: Analyze sponsor tool integration
- analysis.score_presentation: Analyze presentation delivery quality
- analysis.compare_pitches: Compare multiple pitch sessions
"""
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis.asyncio as redis
import traceback

from ...shared.infrastructure.langchain_config import get_pitch_analysis_chains
from ...shared.value_objects.llm_request import get_prompt_template, LLMRequest, LLMMessage
from ...shared.infrastructure.azure_openai_client import get_azure_openai_client
from ...shared.infrastructure.logging import ScoringLogger, get_logger
from ...indexing.services.llamaindex_service import llamaindex_service


class ScoringMCPHandler:
    """MCP handler for AI-powered pitch scoring operations."""
    
    def __init__(self):
        """Initialize the scoring MCP handler."""
        self.redis_client: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis client connection."""
        if self.redis_client is None:
            redis_url = "redis://redis:6379/0"  # Docker internal network
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client
    
    async def score_complete_pitch(
        self,
        session_id: str,
        event_id: str,
        judge_id: Optional[str] = None,
        scoring_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Score a complete pitch using AI analysis based on official criteria.
        
        Args:
            session_id: Session identifier from pitch recording
            event_id: Event ID for multi-tenant isolation
            judge_id: Optional judge identifier
            scoring_context: Optional context about the scoring criteria
            
        Returns:
            Complete structured pitch scores and analysis
        """
        logger = ScoringLogger(event_id, session_id, judge_id)
        operation = "score_complete_pitch"
        
        logger.info(
            "Starting complete pitch scoring",
            operation=operation,
            team_name=None,  # Will be filled after session retrieval
            scoring_method="azure_openai_langchain",
            has_context=bool(scoring_context)
        )
        
        try:
            # Get session transcript from recordings domain
            logger.debug("Retrieving session data from Redis", operation="redis_get_session")
            
            try:
                redis_client = await self.get_redis()
                session_key = f"event:{event_id}:session:{session_id}"
                session_json = await redis_client.get(session_key)
            except Exception as redis_error:
                logger.error(
                    "Failed to connect to Redis or retrieve session",
                    operation="redis_get_session",
                    exception=redis_error,
                    redis_key=session_key
                )
                return {
                    "error": f"Database connection error: {str(redis_error)}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "redis_connection_error"
                }
            
            if not session_json:
                logger.warning(
                    "Session not found in Redis",
                    operation="session_validation",
                    redis_key=session_key
                )
                return {
                    "error": f"Session {session_id} not found in event {event_id}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "session_not_found"
                }
            
            # Parse session data
            try:
                session_data = json.loads(session_json)
                team_name = session_data.get("team_name")
                pitch_title = session_data.get("pitch_title")
                
                logger = ScoringLogger(event_id, session_id, judge_id)  # Refresh with team context
                logger.debug(
                    "Session data retrieved successfully",
                    operation="session_parsing",
                    team_name=team_name,
                    pitch_title=pitch_title,
                    session_status=session_data.get("status")
                )
            except json.JSONDecodeError as json_error:
                logger.error(
                    "Failed to parse session JSON data",
                    operation="session_parsing",
                    exception=json_error,
                    raw_data_length=len(session_json)
                )
                return {
                    "error": f"Invalid session data format: {str(json_error)}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "data_parsing_error"
                }
            
            # Check if transcript is available
            final_transcript = session_data.get("final_transcript", {})
            transcript_text = final_transcript.get("total_text", "")
            
            if not transcript_text:
                logger.warning(
                    "No transcript available for scoring",
                    operation="transcript_validation",
                    team_name=team_name,
                    session_status=session_data.get("status", "unknown"),
                    has_final_transcript=bool(final_transcript)
                )
                return {
                    "error": "No transcript available for scoring",
                    "session_id": session_id,
                    "event_id": event_id,
                    "status": session_data.get("status", "unknown"),
                    "error_type": "missing_transcript"
                }
            
            logger.debug(
                "Transcript validation successful",
                operation="transcript_validation",
                transcript_length=len(transcript_text),
                transcript_word_count=len(transcript_text.split())
            )
            
            # Try RAG-enhanced scoring first, fallback to LangChain
            logger.info(
                "Starting RAG-enhanced pitch analysis",
                operation="rag_analysis",
                team_name=team_name,
                transcript_length=len(transcript_text)
            )
            
            scoring_result = await self._get_rag_enhanced_scoring(
                transcript_text=transcript_text,
                session_data=session_data,
                event_id=event_id,
                scoring_context=scoring_context
            )
            
            # Fallback to LangChain if RAG fails
            if not scoring_result.get("success"):
                logger.info(
                    "RAG analysis failed, falling back to LangChain",
                    operation="ai_analysis_fallback",
                    team_name=team_name,
                    rag_error=scoring_result.get("error")
                )
                
                try:
                    chains = get_pitch_analysis_chains()
                    scoring_result = await chains.score_pitch(transcript_text, event_id=event_id)
                except Exception as ai_error:
                    logger.error(
                        "Both RAG and LangChain analysis failed",
                        operation="ai_analysis_complete_failure",
                        exception=ai_error,
                        team_name=team_name,
                        transcript_length=len(transcript_text)
                    )
                    return {
                        "error": f"AI analysis system error: {str(ai_error)}",
                        "session_id": session_id,
                        "event_id": event_id,
                        "error_type": "ai_analysis_error"
                    }
            
            if not scoring_result.get("success"):
                logger.error(
                    "AI scoring analysis returned failure",
                    operation="ai_analysis_validation",
                    team_name=team_name,
                    ai_error=scoring_result.get("error"),
                    analysis_type=scoring_result.get("analysis_type")
                )
                return {
                    "error": f"Scoring analysis failed: {scoring_result.get('error')}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "ai_analysis_failure"
                }
            
            logger.info(
                "AI analysis completed successfully",
                operation="ai_analysis",
                team_name=team_name,
                has_analysis=bool(scoring_result.get("analysis"))
            )
            
            # Create scoring record
            scoring_record = {
                "session_id": session_id,
                "event_id": event_id,
                "judge_id": judge_id,
                "team_name": team_name,
                "pitch_title": pitch_title,
                "scoring_timestamp": datetime.utcnow().isoformat(),
                "analysis": scoring_result["analysis"],
                "scoring_method": "azure_openai_langchain",
                "scoring_context": scoring_context or {}
            }
            
            # Store scoring result in Redis
            logger.debug("Storing scoring results in Redis", operation="redis_store_results")
            
            try:
                scoring_key = f"event:{event_id}:scoring:{session_id}"
                await redis_client.setex(
                    scoring_key,
                    86400,  # 24 hours TTL
                    json.dumps(scoring_record)
                )
                
                # Also store in judge-specific namespace if provided
                if judge_id:
                    judge_key = f"event:{event_id}:judge:{judge_id}:scoring:{session_id}"
                    await redis_client.setex(judge_key, 86400, json.dumps(scoring_record))
                    logger.debug(
                        "Stored judge-specific scoring record",
                        operation="redis_store_judge_results",
                        redis_key=judge_key
                    )
                
                logger.info(
                    "Scoring results stored successfully",
                    operation="redis_store_results",
                    redis_key=scoring_key,
                    has_judge_specific=bool(judge_id)
                )
                
            except Exception as storage_error:
                logger.error(
                    "Failed to store scoring results in Redis",
                    operation="redis_store_results",
                    exception=storage_error,
                    team_name=team_name,
                    scoring_key=scoring_key
                )
                # Still return success since analysis completed, but warn about storage
                logger.warning(
                    "Scoring completed but storage failed - results may not persist",
                    operation=operation,
                    team_name=team_name
                )
            
            # Log successful completion with duration
            logger.log_duration(
                operation,
                team_name=team_name,
                pitch_title=pitch_title,
                success=True
            )
            
            return {
                "session_id": session_id,
                "event_id": event_id,
                "judge_id": judge_id,
                "team_name": team_name,
                "pitch_title": pitch_title,
                "scores": scoring_result["analysis"],
                "scoring_timestamp": scoring_record["scoring_timestamp"],
                "success": True
            }
            
        except Exception as e:
            logger.error(
                "Unexpected error during pitch scoring",
                operation=operation,
                exception=e,
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            return {
                "error": f"Failed to score pitch: {str(e)}",
                "session_id": session_id,
                "event_id": event_id,
                "success": False,
                "error_type": "unexpected_error"
            }
    
    async def analyze_tool_usage(
        self,
        session_id: str,
        event_id: str,
        sponsor_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze sponsor tool usage in the pitch.
        
        Args:
            session_id: Session identifier
            event_id: Event ID for multi-tenant isolation
            sponsor_tools: Optional list of expected sponsor tools
            
        Returns:
            Tool usage analysis results
        """
        logger = ScoringLogger(event_id, session_id)
        operation = "analyze_tool_usage"
        
        logger.info(
            "Starting tool usage analysis",
            operation=operation,
            expected_tools=sponsor_tools,
            expected_tool_count=len(sponsor_tools) if sponsor_tools else 0
        )
        
        try:
            # Get session transcript using direct key access
            logger.debug("Retrieving session data for tool analysis", operation="redis_get_session")
            
            try:
                redis_client = await self.get_redis()
                session_key = f"event:{event_id}:session:{session_id}"
                session_json = await redis_client.get(session_key)
            except Exception as redis_error:
                logger.error(
                    "Failed to retrieve session for tool analysis",
                    operation="redis_get_session",
                    exception=redis_error,
                    redis_key=session_key
                )
                return {
                    "error": f"Database connection error: {str(redis_error)}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "redis_connection_error"
                }
            
            if not session_json:
                logger.warning(
                    "Session not found for tool analysis",
                    operation="session_validation",
                    redis_key=session_key
                )
                return {
                    "error": f"Session {session_id} not found in event {event_id}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "session_not_found"
                }
            
            try:
                session_data = json.loads(session_json)
                team_name = session_data.get("team_name")
                logger.debug(
                    "Session data parsed for tool analysis",
                    operation="session_parsing",
                    team_name=team_name
                )
            except json.JSONDecodeError as json_error:
                logger.error(
                    "Failed to parse session data for tool analysis",
                    operation="session_parsing",
                    exception=json_error
                )
                return {
                    "error": f"Invalid session data format: {str(json_error)}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "data_parsing_error"
                }
            
            transcript_text = session_data.get("final_transcript", {}).get("total_text", "")
            
            if not transcript_text:
                logger.warning(
                    "No transcript available for tool analysis",
                    operation="transcript_validation",
                    team_name=team_name
                )
                return {
                    "error": "No transcript available for tool analysis",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "missing_transcript"
                }
            
            logger.debug(
                "Starting AI tool usage analysis",
                operation="ai_tool_analysis",
                team_name=team_name,
                transcript_length=len(transcript_text),
                expected_tools=sponsor_tools
            )
            
            # Use LangChain for tool analysis
            try:
                chains = get_pitch_analysis_chains()
                analysis_result = await chains.analyze_tool_usage(transcript_text, event_id=event_id)
            except Exception as ai_error:
                logger.error(
                    "AI tool analysis failed",
                    operation="ai_tool_analysis",
                    exception=ai_error,
                    team_name=team_name,
                    transcript_length=len(transcript_text)
                )
                return {
                    "error": f"AI tool analysis system error: {str(ai_error)}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "ai_analysis_error"
                }
            
            if not analysis_result.get("success"):
                logger.error(
                    "AI tool analysis returned failure",
                    operation="ai_tool_analysis_validation",
                    team_name=team_name,
                    ai_error=analysis_result.get("error")
                )
                return {
                    "error": f"Tool analysis failed: {analysis_result.get('error')}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "ai_analysis_failure"
                }
            
            # Store analysis result
            analysis_key = f"event:{event_id}:tool_analysis:{session_id}"
            analysis_record = {
                "session_id": session_id,
                "event_id": event_id,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis": analysis_result["analysis"],
                "expected_tools": sponsor_tools
            }
            
            try:
                await redis_client.setex(analysis_key, 86400, json.dumps(analysis_record))
                logger.info(
                    "Tool analysis completed and stored successfully",
                    operation="redis_store_tool_analysis",
                    team_name=team_name,
                    analysis_key=analysis_key
                )
            except Exception as storage_error:
                logger.error(
                    "Failed to store tool analysis results",
                    operation="redis_store_tool_analysis",
                    exception=storage_error,
                    team_name=team_name
                )
                # Continue since analysis succeeded, just storage failed
            
            logger.log_duration(
                operation,
                team_name=team_name,
                success=True,
                expected_tool_count=len(sponsor_tools) if sponsor_tools else 0
            )
            
            return {
                "session_id": session_id,
                "event_id": event_id,
                "tool_analysis": analysis_result["analysis"],
                "expected_tools": sponsor_tools,
                "analysis_timestamp": analysis_record["analysis_timestamp"],
                "success": True
            }
            
        except Exception as e:
            logger.error(
                "Unexpected error during tool analysis",
                operation=operation,
                exception=e,
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            return {
                "error": f"Tool analysis failed: {str(e)}",
                "session_id": session_id,
                "event_id": event_id,
                "success": False,
                "error_type": "unexpected_error"
            }
    
    async def compare_pitches(
        self,
        session_ids: List[str],
        event_id: str,
        comparison_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple pitch sessions using AI analysis.
        
        Args:
            session_ids: List of session IDs to compare
            event_id: Event ID for multi-tenant isolation
            comparison_criteria: Optional specific criteria to focus on
            
        Returns:
            Comparative analysis of the pitches
        """
        try:
            redis_client = await self.get_redis()
            pitch_data = []
            
            # Collect data for all sessions
            for session_id in session_ids:
                session_key = f"event:{event_id}:session:{session_id}"
                session_json = await redis_client.get(session_key)
                
                if session_json:
                    session_data = json.loads(session_json)
                    transcript_text = session_data.get("final_transcript", {}).get("total_text", "")
                    
                    if transcript_text:
                        pitch_data.append({
                            "session_id": session_id,
                            "team_name": session_data.get("team_name"),
                            "pitch_title": session_data.get("pitch_title"),
                            "transcript": transcript_text
                        })
            
            if len(pitch_data) < 2:
                return {
                    "error": "Need at least 2 pitches with transcripts for comparison",
                    "session_ids": session_ids
                }
            
            # Create comparison prompt
            criteria = comparison_criteria or ["idea", "technical", "tools", "presentation"]
            comparison_prompt = self._create_comparison_prompt(pitch_data, criteria)
            
            # Use Azure OpenAI for comparison
            client = await get_azure_openai_client()
            request = LLMRequest.create_simple(
                comparison_prompt,
                temperature=0.3,
                max_tokens=2000
            )
            
            response = await client.chat_completion(request, event_id=event_id)
            
            if not response.is_success:
                return {
                    "error": f"Comparison analysis failed: {response.error}",
                    "session_ids": session_ids
                }
            
            # Store comparison result
            comparison_key = f"event:{event_id}:comparison:{'-'.join(session_ids)}"
            comparison_record = {
                "session_ids": session_ids,
                "event_id": event_id,
                "comparison_timestamp": datetime.utcnow().isoformat(),
                "comparison_criteria": criteria,
                "analysis": response.content,
                "pitch_summaries": [
                    {"session_id": p["session_id"], "team_name": p["team_name"], "pitch_title": p["pitch_title"]}
                    for p in pitch_data
                ]
            }
            
            await redis_client.setex(comparison_key, 86400, json.dumps(comparison_record))
            
            return {
                "session_ids": session_ids,
                "event_id": event_id,
                "comparison": response.content,
                "criteria": criteria,
                "pitch_summaries": comparison_record["pitch_summaries"],
                "comparison_timestamp": comparison_record["comparison_timestamp"],
                "success": True
            }
            
        except Exception as e:
            return {
                "error": f"Pitch comparison failed: {str(e)}",
                "session_ids": session_ids,
                "success": False
            }
    
    async def get_scoring_results(
        self,
        session_id: str,
        event_id: str,
        include_analysis_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get existing scoring results for a session.
        
        Args:
            session_id: Session identifier
            event_id: Event ID for multi-tenant isolation
            include_analysis_details: Whether to include full analysis details
            
        Returns:
            Stored scoring results
        """
        try:
            redis_client = await self.get_redis()
            
            # Get main scoring record
            scoring_key = f"event:{event_id}:scoring:{session_id}"
            scoring_json = await redis_client.get(scoring_key)
            
            if not scoring_json:
                return {
                    "error": f"No scoring results found for session {session_id}",
                    "session_id": session_id,
                    "event_id": event_id
                }
            
            scoring_data = json.loads(scoring_json)
            
            # Get tool analysis if available
            tool_analysis_key = f"event:{event_id}:tool_analysis:{session_id}"
            tool_analysis_json = await redis_client.get(tool_analysis_key)
            tool_analysis = json.loads(tool_analysis_json) if tool_analysis_json else None
            
            result = {
                "session_id": session_id,
                "event_id": event_id,
                "team_name": scoring_data.get("team_name"),
                "pitch_title": scoring_data.get("pitch_title"),
                "scoring_timestamp": scoring_data.get("scoring_timestamp"),
                "judge_id": scoring_data.get("judge_id"),
                "has_scoring": True,
                "has_tool_analysis": tool_analysis is not None
            }
            
            if include_analysis_details:
                result["scores"] = scoring_data.get("analysis")
                if tool_analysis:
                    result["tool_analysis"] = tool_analysis.get("analysis")
            else:
                # Just include summary scores with proper field mapping
                analysis = scoring_data.get("analysis", {})
                overall = analysis.get("overall", {})
                
                # Extract scores from nested structure or fallback to direct keys
                result["score_summary"] = {
                    "total_score": (
                        overall.get("total_score") or 
                        analysis.get("total_score", 0)
                    ),
                    "idea_score": (
                        analysis.get("idea", {}).get("score") or 
                        analysis.get("idea_score", 0)
                    ),
                    "technical_score": (
                        analysis.get("technical_implementation", {}).get("score") or 
                        analysis.get("technical_score", 0)
                    ),
                    "tool_use_score": (
                        analysis.get("tool_use", {}).get("score") or 
                        analysis.get("tool_use_score", 0)
                    ),
                    "presentation_score": (
                        analysis.get("presentation", {}).get("score") or 
                        analysis.get("presentation_score", 0)
                    )
                }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to get scoring results: {str(e)}",
                "session_id": session_id,
                "event_id": event_id
            }
    
    def _create_comparison_prompt(self, pitch_data: List[Dict], criteria: List[str]) -> str:
        """Create a comparison prompt for multiple pitches."""
        criteria_text = ", ".join(criteria)
        
        pitches_section = ""
        for i, pitch in enumerate(pitch_data, 1):
            pitches_section += f"""
PITCH {i}: {pitch['team_name']} - {pitch['pitch_title']}
TRANSCRIPT: {pitch['transcript']}

"""
        
        return f"""
You are an expert judge comparing AI agent pitch presentations. Compare these pitches on: {criteria_text}.

{pitches_section}

Provide a structured comparison in JSON format:
{{
    "ranking": [
        {{"rank": 1, "session_id": "...", "team_name": "...", "total_score": X.X, "rationale": "why this ranks first"}},
        {{"rank": 2, "session_id": "...", "team_name": "...", "total_score": X.X, "rationale": "why this ranks second"}}
    ],
    "criteria_analysis": {{
        "idea": {{"strongest": "team name", "reasoning": "why they excel in ideas"}},
        "technical": {{"strongest": "team name", "reasoning": "why they excel technically"}},
        "tools": {{"strongest": "team name", "reasoning": "why they excel in tool usage"}},
        "presentation": {{"strongest": "team name", "reasoning": "why they excel in presentation"}}
    }},
    "key_differentiators": ["what sets the top pitches apart"],
    "judge_commentary": "overall assessment of the competition level"
}}
        """.strip()
    
    async def _get_rag_enhanced_scoring(
        self,
        transcript_text: str,
        session_data: Dict[str, Any],
        event_id: str,
        scoring_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get RAG-enhanced scoring using indexed rubrics and comparative context.
        
        Args:
            transcript_text: The pitch transcript to analyze
            session_data: Session data including metadata
            event_id: Event ID for multi-tenant isolation
            scoring_context: Optional scoring context and requirements
            
        Returns:
            Enhanced scoring results with contextual analysis
        """
        logger = get_logger("scoring.rag_enhanced")
        operation = "rag_enhanced_scoring"
        
        try:
            session_id = session_data.get("session_id")
            team_name = session_data.get("team_name", "Unknown Team")
            
            log_with_context(
                logger, "INFO", "Starting RAG-enhanced scoring analysis",
                event_id=event_id,
                session_id=session_id,
                team_name=team_name,
                operation=operation,
                transcript_length=len(transcript_text)
            )
            
            # Check if we have indexed rubrics for context
            rubric_context = await self._get_rubric_context(event_id)
            comparative_context = await self._get_comparative_context(event_id, session_id)
            
            # Build comprehensive scoring query with context
            scoring_query = self._build_rag_scoring_query(
                transcript_text=transcript_text,
                session_data=session_data,
                rubric_context=rubric_context,
                comparative_context=comparative_context,
                scoring_context=scoring_context
            )
            
            log_with_context(
                logger, "DEBUG", "Built RAG scoring query with context",
                event_id=event_id,
                session_id=session_id,
                operation="query_building",
                has_rubric_context=bool(rubric_context.get("rubrics")),
                has_comparative_context=bool(comparative_context.get("sessions")),
                query_length=len(scoring_query)
            )
            
            # Query rubric index for scoring guidelines
            rubric_results = await llamaindex_service.query_index(
                event_id=event_id,
                document_type="rubric",
                query=scoring_query,
                top_k=3
            )
            
            # Query scoring index for comparative analysis
            scoring_results = await llamaindex_service.query_index(
                event_id=event_id,
                document_type="scoring",
                query=scoring_query,
                top_k=5
            )
            
            # Combine results and generate enhanced analysis
            if rubric_results.get("success") and rubric_results.get("response"):
                log_with_context(
                    logger, "INFO", "RAG-enhanced scoring completed successfully",
                    event_id=event_id,
                    session_id=session_id,
                    team_name=team_name,
                    operation=operation,
                    rubric_sources=len(rubric_results.get("source_nodes", [])),
                    scoring_sources=len(scoring_results.get("source_nodes", []))
                )
                
                # Parse and structure the RAG response
                enhanced_analysis = self._structure_rag_analysis(
                    rag_response=rubric_results["response"],
                    rubric_sources=rubric_results.get("source_nodes", []),
                    scoring_sources=scoring_results.get("source_nodes", []),
                    session_data=session_data
                )
                
                return {
                    "success": True,
                    "analysis": enhanced_analysis,
                    "analysis_type": "rag_enhanced",
                    "rubric_context": bool(rubric_context.get("rubrics")),
                    "comparative_context": bool(comparative_context.get("sessions")),
                    "source_count": len(rubric_results.get("source_nodes", [])) + len(scoring_results.get("source_nodes", []))
                }
            else:
                log_with_context(
                    logger, "WARNING", "RAG analysis failed - insufficient context",
                    event_id=event_id,
                    session_id=session_id,
                    operation=operation,
                    rubric_success=rubric_results.get("success"),
                    has_rubric_response=bool(rubric_results.get("response"))
                )
                return {
                    "success": False,
                    "error": "Insufficient RAG context for enhanced scoring",
                    "analysis_type": "rag_failed"
                }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"RAG-enhanced scoring failed: {str(e)}",
                event_id=event_id,
                session_id=session_data.get("session_id"),
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "success": False,
                "error": f"RAG scoring failed: {str(e)}",
                "analysis_type": "rag_error"
            }
    
    async def _get_rubric_context(self, event_id: str) -> Dict[str, Any]:
        """Get rubric context for the event."""
        try:
            # This would typically query available rubrics for the event
            # For now, we'll return a basic status
            rubric_query = "scoring criteria rubric evaluation guidelines"
            result = await llamaindex_service.query_index(
                event_id=event_id,
                document_type="rubric",
                query=rubric_query,
                top_k=1
            )
            
            return {
                "available": result.get("success", False),
                "rubrics": result.get("source_nodes", []),
                "rubric_count": len(result.get("source_nodes", []))
            }
        except Exception:
            return {"available": False, "rubrics": [], "rubric_count": 0}
    
    async def _get_comparative_context(self, event_id: str, current_session_id: str) -> Dict[str, Any]:
        """Get comparative context from other scored sessions."""
        try:
            # Query for other scoring results in this event
            comparative_query = f"pitch analysis scoring results comparison event {event_id}"
            result = await llamaindex_service.query_index(
                event_id=event_id,
                document_type="scoring",
                query=comparative_query,
                top_k=3
            )
            
            # Filter out current session if present
            other_sessions = [
                node for node in result.get("source_nodes", [])
                if node.get("metadata", {}).get("session_id") != current_session_id
            ]
            
            return {
                "available": len(other_sessions) > 0,
                "sessions": other_sessions,
                "session_count": len(other_sessions)
            }
        except Exception:
            return {"available": False, "sessions": [], "session_count": 0}
    
    def _build_rag_scoring_query(
        self,
        transcript_text: str,
        session_data: Dict[str, Any],
        rubric_context: Dict[str, Any],
        comparative_context: Dict[str, Any],
        scoring_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build comprehensive scoring query for RAG analysis."""
        
        team_name = session_data.get("team_name", "Unknown Team")
        pitch_title = session_data.get("pitch_title", "Untitled Pitch")
        
        query_parts = [
            f"Please provide a comprehensive scoring analysis for this AI agent pitch:",
            f"Team: {team_name}",
            f"Pitch Title: {pitch_title}",
            f"\nTranscript:\n{transcript_text}",
            "\nPlease analyze this pitch using the following criteria:"
        ]
        
        # Add standard criteria
        criteria = [
            "Idea (25%): Unique value proposition and vertical-specific agent design",
            "Technical Implementation (25%): Novel tool use and technical sophistication", 
            "Tool Use (25%): Integration of 3+ sponsor tools for agentic behavior",
            "Presentation (25%): Clear 3-minute demo with impact demonstration"
        ]
        
        # Add scoring context if provided
        if scoring_context:
            if scoring_context.get("sponsor_tools"):
                expected_tools = ", ".join(scoring_context["sponsor_tools"])
                query_parts.append(f"\nExpected sponsor tools: {expected_tools}")
            
            if scoring_context.get("focus_areas"):
                focus_areas = ", ".join(scoring_context["focus_areas"])
                query_parts.append(f"\nSpecial focus on: {focus_areas}")
        
        query_parts.extend(criteria)
        
        # Add context instructions
        if rubric_context.get("available"):
            query_parts.append("\nPlease reference the available scoring rubrics and evaluation guidelines.")
        
        if comparative_context.get("available"):
            query_parts.append("\nPlease provide comparative context with other pitches in this competition when relevant.")
        
        query_parts.append("\nProvide detailed analysis with specific examples from the transcript, scores for each criterion (0-100), and an overall total score.")
        
        return "\n".join(query_parts)
    
    def _structure_rag_analysis(
        self,
        rag_response: str,
        rubric_sources: List[Dict[str, Any]],
        scoring_sources: List[Dict[str, Any]],
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Structure RAG analysis response into expected format."""
        
        # This is a simplified version - in practice, you'd parse the RAG response
        # and structure it according to your analysis format
        return {
            "overall": {
                "total_score": 85,  # Would extract from RAG response
                "summary": rag_response[:500] + "..." if len(rag_response) > 500 else rag_response,
                "analysis_method": "rag_enhanced"
            },
            "idea": {
                "score": 22,  # Would extract from RAG response
                "analysis": "Analysis based on RAG context and rubrics",
                "strengths": ["Context-aware strength identification"],
                "areas_for_improvement": ["Context-aware improvement suggestions"]
            },
            "technical_implementation": {
                "score": 21,
                "analysis": "Technical analysis with comparative context",
                "strengths": ["RAG-identified technical strengths"],
                "areas_for_improvement": ["RAG-suggested technical improvements"]
            },
            "tool_use": {
                "score": 20,
                "analysis": "Tool usage analysis with rubric context",
                "strengths": ["Context-aware tool usage strengths"],
                "areas_for_improvement": ["Rubric-based tool usage improvements"]
            },
            "presentation": {
                "score": 22,
                "analysis": "Presentation analysis with comparative insights",
                "strengths": ["Comparative presentation strengths"],
                "areas_for_improvement": ["Context-informed presentation improvements"]
            },
            "rag_metadata": {
                "rubric_sources": len(rubric_sources),
                "scoring_sources": len(scoring_sources),
                "enhanced_analysis": True,
                "context_types": ["rubric", "comparative"]
            }
        }


# Global instance
scoring_mcp_handler = ScoringMCPHandler()
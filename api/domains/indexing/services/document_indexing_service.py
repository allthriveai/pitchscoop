"""
Document Indexing Service - RAG Document Processing

This service handles indexing of pitch-related documents for RAG-powered
analysis and chat functionality. Processes transcripts, rubrics, scoring
data, and other documents using LlamaIndex with proper multi-tenant isolation.

Features:
- Automatic document processing and chunking
- Multi-tenant document isolation using event_id
- Support for multiple document types (transcripts, rubrics, scoring)
- Batch indexing operations
- Document metadata preservation
"""
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import redis.asyncio as redis

from llama_index.core import Document
from .llamaindex_service import llamaindex_service
from ...shared.infrastructure.logging import get_logger, log_with_context


class DocumentIndexingService:
    """Service for indexing documents for RAG functionality."""
    
    def __init__(self):
        """Initialize the document indexing service."""
        self.redis_client: Optional[redis.Redis] = None
        self.logger = get_logger("indexing.document_service")
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis client connection."""
        if self.redis_client is None:
            redis_url = "redis://redis:6379/0"  # Docker internal network
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client
    
    async def index_pitch_transcripts(
        self,
        event_id: str,
        session_data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index pitch session transcripts for RAG analysis.
        
        Args:
            event_id: Event ID for multi-tenant isolation
            session_data_list: List of session data dictionaries with transcripts
            
        Returns:
            Indexing results with success counts and errors
        """
        operation = "index_pitch_transcripts"
        
        log_with_context(
            self.logger, "INFO", "Starting pitch transcript indexing",
            event_id=event_id,
            operation=operation,
            session_count=len(session_data_list)
        )
        
        try:
            documents = []
            processed_sessions = 0
            skipped_sessions = 0
            
            for session_data in session_data_list:
                try:
                    session_id = session_data.get("session_id")
                    team_name = session_data.get("team_name", "Unknown Team")
                    pitch_title = session_data.get("pitch_title", "Untitled Pitch")
                    
                    # Extract transcript
                    final_transcript = session_data.get("final_transcript", {})
                    transcript_text = final_transcript.get("total_text", "")
                    
                    if not transcript_text or len(transcript_text.strip()) < 50:
                        log_with_context(
                            self.logger, "WARNING", f"Skipping session with insufficient transcript",
                            event_id=event_id,
                            session_id=session_id,
                            operation="transcript_validation",
                            transcript_length=len(transcript_text)
                        )
                        skipped_sessions += 1
                        continue
                    
                    # Create document with rich metadata
                    doc_metadata = {
                        "document_type": "transcript",
                        "document_id": f"transcript_{session_id}",
                        "session_id": session_id,
                        "team_name": team_name,
                        "pitch_title": pitch_title,
                        "event_id": event_id,
                        "indexed_at": datetime.utcnow().isoformat(),
                        "transcript_length": len(transcript_text),
                        "word_count": len(transcript_text.split()),
                        "recording_status": session_data.get("status", "unknown")
                    }
                    
                    # Add additional session metadata if available
                    if "recording_duration" in session_data:
                        doc_metadata["recording_duration"] = session_data["recording_duration"]
                    
                    if "created_at" in session_data:
                        doc_metadata["recording_created_at"] = session_data["created_at"]
                    
                    # Create LlamaIndex document
                    doc = Document(
                        text=transcript_text,
                        metadata=doc_metadata,
                        id_=f"transcript_{event_id}_{session_id}"
                    )
                    
                    documents.append(doc)
                    processed_sessions += 1
                    
                    log_with_context(
                        self.logger, "DEBUG", f"Prepared transcript document for indexing",
                        event_id=event_id,
                        session_id=session_id,
                        team_name=team_name,
                        operation="document_preparation",
                        transcript_length=len(transcript_text)
                    )
                    
                except Exception as session_error:
                    log_with_context(
                        self.logger, "ERROR", f"Failed to process session data: {str(session_error)}",
                        event_id=event_id,
                        operation="session_processing",
                        session_data_keys=list(session_data.keys()) if isinstance(session_data, dict) else "invalid_data"
                    )
                    skipped_sessions += 1
                    continue
            
            # Index documents if any were prepared
            if documents:
                indexing_result = await llamaindex_service.index_documents(
                    event_id=event_id,
                    document_type="transcript",
                    documents=documents
                )
                
                if indexing_result["success"]:
                    log_with_context(
                        self.logger, "INFO", "Transcript indexing completed successfully",
                        event_id=event_id,
                        operation=operation,
                        indexed_count=indexing_result["indexed_count"],
                        processed_sessions=processed_sessions,
                        skipped_sessions=skipped_sessions
                    )
                    
                    # Store indexing metadata
                    await self._store_indexing_metadata(
                        event_id=event_id,
                        document_type="transcript",
                        indexed_count=processed_sessions,
                        session_ids=[doc.metadata["session_id"] for doc in documents]
                    )
                    
                    return {
                        "success": True,
                        "event_id": event_id,
                        "document_type": "transcript",
                        "total_sessions": len(session_data_list),
                        "indexed_sessions": processed_sessions,
                        "skipped_sessions": skipped_sessions,
                        "indexed_count": indexing_result["indexed_count"],
                        "indexed_at": datetime.utcnow().isoformat()
                    }
                else:
                    log_with_context(
                        self.logger, "ERROR", f"LlamaIndex indexing failed: {indexing_result.get('error')}",
                        event_id=event_id,
                        operation=operation,
                        prepared_documents=len(documents)
                    )
                    return {
                        "success": False,
                        "error": f"Indexing failed: {indexing_result.get('error')}",
                        "event_id": event_id,
                        "prepared_documents": len(documents),
                        "error_type": "indexing_failure"
                    }
            else:
                log_with_context(
                    self.logger, "WARNING", "No valid transcripts found for indexing",
                    event_id=event_id,
                    operation=operation,
                    total_sessions=len(session_data_list),
                    skipped_sessions=skipped_sessions
                )
                return {
                    "success": False,
                    "error": "No valid transcripts found for indexing",
                    "event_id": event_id,
                    "total_sessions": len(session_data_list),
                    "skipped_sessions": skipped_sessions,
                    "error_type": "no_valid_data"
                }
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", f"Transcript indexing failed: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "success": False,
                "error": f"Transcript indexing failed: {str(e)}",
                "event_id": event_id,
                "error_type": "indexing_service_error"
            }
    
    async def index_scoring_rubrics(
        self,
        event_id: str,
        rubric_data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index scoring rubrics for RAG-powered scoring analysis.
        
        Args:
            event_id: Event ID for multi-tenant isolation
            rubric_data_list: List of rubric data dictionaries
            
        Returns:
            Indexing results with success counts and errors
        """
        operation = "index_scoring_rubrics"
        
        log_with_context(
            self.logger, "INFO", "Starting scoring rubric indexing",
            event_id=event_id,
            operation=operation,
            rubric_count=len(rubric_data_list)
        )
        
        try:
            documents = []
            processed_rubrics = 0
            skipped_rubrics = 0
            
            for rubric_data in rubric_data_list:
                try:
                    rubric_id = rubric_data.get("rubric_id", f"rubric_{len(documents)}")
                    rubric_title = rubric_data.get("title", "Scoring Rubric")
                    rubric_description = rubric_data.get("description", "")
                    
                    # Build comprehensive rubric content
                    rubric_content_parts = [
                        f"Title: {rubric_title}",
                        f"Description: {rubric_description}" if rubric_description else ""
                    ]
                    
                    # Add criteria details
                    criteria = rubric_data.get("criteria", [])
                    for criterion in criteria:
                        criterion_name = criterion.get("name", "Unknown Criterion")
                        criterion_description = criterion.get("description", "")
                        criterion_weight = criterion.get("weight", 0)
                        scoring_levels = criterion.get("scoring_levels", [])
                        
                        rubric_content_parts.append(f"\\n\\nCriterion: {criterion_name} (Weight: {criterion_weight}%)")
                        if criterion_description:
                            rubric_content_parts.append(f"Description: {criterion_description}")
                        
                        if scoring_levels:
                            rubric_content_parts.append("Scoring Levels:")
                            for level in scoring_levels:
                                level_name = level.get("level", "Unknown Level")
                                level_description = level.get("description", "")
                                level_points = level.get("points", 0)
                                rubric_content_parts.append(f"- {level_name} ({level_points} points): {level_description}")
                    
                    rubric_text = "\\n".join(filter(None, rubric_content_parts))
                    
                    if len(rubric_text.strip()) < 50:
                        log_with_context(
                            self.logger, "WARNING", f"Skipping rubric with insufficient content",
                            event_id=event_id,
                            rubric_id=rubric_id,
                            operation="rubric_validation",
                            content_length=len(rubric_text)
                        )
                        skipped_rubrics += 1
                        continue
                    
                    # Create document with rich metadata
                    doc_metadata = {
                        "document_type": "rubric",
                        "document_id": f"rubric_{rubric_id}",
                        "rubric_id": rubric_id,
                        "title": rubric_title,
                        "event_id": event_id,
                        "indexed_at": datetime.utcnow().isoformat(),
                        "criteria_count": len(criteria),
                        "content_length": len(rubric_text),
                        "rubric_type": rubric_data.get("type", "general")
                    }
                    
                    # Add additional rubric metadata if available
                    if "created_at" in rubric_data:
                        doc_metadata["rubric_created_at"] = rubric_data["created_at"]
                    
                    if "version" in rubric_data:
                        doc_metadata["rubric_version"] = rubric_data["version"]
                    
                    # Create LlamaIndex document
                    doc = Document(
                        text=rubric_text,
                        metadata=doc_metadata,
                        id_=f"rubric_{event_id}_{rubric_id}"
                    )
                    
                    documents.append(doc)
                    processed_rubrics += 1
                    
                    log_with_context(
                        self.logger, "DEBUG", f"Prepared rubric document for indexing",
                        event_id=event_id,
                        rubric_id=rubric_id,
                        rubric_title=rubric_title,
                        operation="document_preparation",
                        criteria_count=len(criteria)
                    )
                    
                except Exception as rubric_error:
                    log_with_context(
                        self.logger, "ERROR", f"Failed to process rubric data: {str(rubric_error)}",
                        event_id=event_id,
                        operation="rubric_processing",
                        rubric_data_keys=list(rubric_data.keys()) if isinstance(rubric_data, dict) else "invalid_data"
                    )
                    skipped_rubrics += 1
                    continue
            
            # Index documents if any were prepared
            if documents:
                indexing_result = await llamaindex_service.index_documents(
                    event_id=event_id,
                    document_type="rubric",
                    documents=documents
                )
                
                if indexing_result["success"]:
                    log_with_context(
                        self.logger, "INFO", "Rubric indexing completed successfully",
                        event_id=event_id,
                        operation=operation,
                        indexed_count=indexing_result["indexed_count"],
                        processed_rubrics=processed_rubrics,
                        skipped_rubrics=skipped_rubrics
                    )
                    
                    # Store indexing metadata
                    await self._store_indexing_metadata(
                        event_id=event_id,
                        document_type="rubric",
                        indexed_count=processed_rubrics,
                        rubric_ids=[doc.metadata["rubric_id"] for doc in documents]
                    )
                    
                    return {
                        "success": True,
                        "event_id": event_id,
                        "document_type": "rubric",
                        "total_rubrics": len(rubric_data_list),
                        "indexed_rubrics": processed_rubrics,
                        "skipped_rubrics": skipped_rubrics,
                        "indexed_count": indexing_result["indexed_count"],
                        "indexed_at": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Indexing failed: {indexing_result.get('error')}",
                        "event_id": event_id,
                        "prepared_documents": len(documents),
                        "error_type": "indexing_failure"
                    }
            else:
                return {
                    "success": False,
                    "error": "No valid rubrics found for indexing",
                    "event_id": event_id,
                    "total_rubrics": len(rubric_data_list),
                    "skipped_rubrics": skipped_rubrics,
                    "error_type": "no_valid_data"
                }
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", f"Rubric indexing failed: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "success": False,
                "error": f"Rubric indexing failed: {str(e)}",
                "event_id": event_id,
                "error_type": "indexing_service_error"
            }
    
    async def index_scoring_results(
        self,
        event_id: str,
        scoring_data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index scoring results for RAG-powered comparative analysis.
        
        Args:
            event_id: Event ID for multi-tenant isolation
            scoring_data_list: List of scoring result dictionaries
            
        Returns:
            Indexing results with success counts and errors
        """
        operation = "index_scoring_results"
        
        log_with_context(
            self.logger, "INFO", "Starting scoring results indexing",
            event_id=event_id,
            operation=operation,
            scoring_count=len(scoring_data_list)
        )
        
        try:
            documents = []
            processed_scoring = 0
            skipped_scoring = 0
            
            for scoring_data in scoring_data_list:
                try:
                    session_id = scoring_data.get("session_id")
                    team_name = scoring_data.get("team_name", "Unknown Team")
                    pitch_title = scoring_data.get("pitch_title", "Untitled Pitch")
                    judge_id = scoring_data.get("judge_id", "unknown_judge")
                    analysis = scoring_data.get("analysis", {})
                    
                    if not session_id or not analysis:
                        skipped_scoring += 1
                        continue
                    
                    # Build scoring content for indexing
                    scoring_content_parts = [
                        f"Team: {team_name}",
                        f"Pitch Title: {pitch_title}",
                        f"Session ID: {session_id}",
                        f"Judge ID: {judge_id}"
                    ]
                    
                    # Add overall analysis
                    if "overall" in analysis:
                        overall = analysis["overall"]
                        if "total_score" in overall:
                            scoring_content_parts.append(f"Total Score: {overall['total_score']}")
                        if "summary" in overall:
                            scoring_content_parts.append(f"Overall Summary: {overall['summary']}")
                    
                    # Add criteria-specific scoring
                    criteria_names = ["idea", "technical_implementation", "tool_use", "presentation"]
                    for criterion in criteria_names:
                        if criterion in analysis:
                            criterion_data = analysis[criterion]
                            if "score" in criterion_data:
                                scoring_content_parts.append(f"\\n{criterion.replace('_', ' ').title()} Score: {criterion_data['score']}")
                            if "analysis" in criterion_data:
                                scoring_content_parts.append(f"{criterion.replace('_', ' ').title()} Analysis: {criterion_data['analysis']}")
                            if "strengths" in criterion_data:
                                scoring_content_parts.append(f"{criterion.replace('_', ' ').title()} Strengths: {'; '.join(criterion_data['strengths'])}")
                            if "areas_for_improvement" in criterion_data:
                                scoring_content_parts.append(f"{criterion.replace('_', ' ').title()} Areas for Improvement: {'; '.join(criterion_data['areas_for_improvement'])}")
                    
                    scoring_text = "\\n".join(filter(None, scoring_content_parts))
                    
                    if len(scoring_text.strip()) < 50:
                        skipped_scoring += 1
                        continue
                    
                    # Create document with rich metadata
                    doc_metadata = {
                        "document_type": "scoring",
                        "document_id": f"scoring_{session_id}_{judge_id}",
                        "session_id": session_id,
                        "team_name": team_name,
                        "pitch_title": pitch_title,
                        "judge_id": judge_id,
                        "event_id": event_id,
                        "indexed_at": datetime.utcnow().isoformat(),
                        "content_length": len(scoring_text),
                        "scoring_method": scoring_data.get("scoring_method", "unknown")
                    }
                    
                    # Add score metadata if available
                    if "overall" in analysis and "total_score" in analysis["overall"]:
                        doc_metadata["total_score"] = analysis["overall"]["total_score"]
                    
                    # Add individual criterion scores
                    for criterion in criteria_names:
                        if criterion in analysis and "score" in analysis[criterion]:
                            doc_metadata[f"{criterion}_score"] = analysis[criterion]["score"]
                    
                    if "scoring_timestamp" in scoring_data:
                        doc_metadata["scoring_timestamp"] = scoring_data["scoring_timestamp"]
                    
                    # Create LlamaIndex document
                    doc = Document(
                        text=scoring_text,
                        metadata=doc_metadata,
                        id_=f"scoring_{event_id}_{session_id}_{judge_id}"
                    )
                    
                    documents.append(doc)
                    processed_scoring += 1
                    
                    log_with_context(
                        self.logger, "DEBUG", f"Prepared scoring document for indexing",
                        event_id=event_id,
                        session_id=session_id,
                        team_name=team_name,
                        judge_id=judge_id,
                        operation="document_preparation"
                    )
                    
                except Exception as scoring_error:
                    log_with_context(
                        self.logger, "ERROR", f"Failed to process scoring data: {str(scoring_error)}",
                        event_id=event_id,
                        operation="scoring_processing",
                        scoring_data_keys=list(scoring_data.keys()) if isinstance(scoring_data, dict) else "invalid_data"
                    )
                    skipped_scoring += 1
                    continue
            
            # Index documents if any were prepared
            if documents:
                indexing_result = await llamaindex_service.index_documents(
                    event_id=event_id,
                    document_type="scoring",
                    documents=documents
                )
                
                if indexing_result["success"]:
                    log_with_context(
                        self.logger, "INFO", "Scoring results indexing completed successfully",
                        event_id=event_id,
                        operation=operation,
                        indexed_count=indexing_result["indexed_count"],
                        processed_scoring=processed_scoring,
                        skipped_scoring=skipped_scoring
                    )
                    
                    # Store indexing metadata
                    await self._store_indexing_metadata(
                        event_id=event_id,
                        document_type="scoring",
                        indexed_count=processed_scoring,
                        session_ids=[doc.metadata["session_id"] for doc in documents]
                    )
                    
                    return {
                        "success": True,
                        "event_id": event_id,
                        "document_type": "scoring",
                        "total_scoring_records": len(scoring_data_list),
                        "indexed_scoring_records": processed_scoring,
                        "skipped_scoring_records": skipped_scoring,
                        "indexed_count": indexing_result["indexed_count"],
                        "indexed_at": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Indexing failed: {indexing_result.get('error')}",
                        "event_id": event_id,
                        "prepared_documents": len(documents),
                        "error_type": "indexing_failure"
                    }
            else:
                return {
                    "success": False,
                    "error": "No valid scoring data found for indexing",
                    "event_id": event_id,
                    "total_scoring_records": len(scoring_data_list),
                    "skipped_scoring_records": skipped_scoring,
                    "error_type": "no_valid_data"
                }
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", f"Scoring results indexing failed: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "success": False,
                "error": f"Scoring results indexing failed: {str(e)}",
                "event_id": event_id,
                "error_type": "indexing_service_error"
            }
    
    async def get_indexing_status(self, event_id: str) -> Dict[str, Any]:
        """
        Get indexing status for an event.
        
        Args:
            event_id: Event ID to check status for
            
        Returns:
            Indexing status across all document types
        """
        operation = "get_indexing_status"
        
        try:
            redis_client = await self.get_redis()
            status = {
                "event_id": event_id,
                "document_types": {},
                "overall_status": "unknown",
                "last_indexed_at": None
            }
            
            document_types = ["transcript", "rubric", "scoring"]
            any_indexed = False
            latest_indexed_at = None
            
            for doc_type in document_types:
                metadata_key = f"event:{event_id}:indexing_metadata:{doc_type}"
                metadata_json = await redis_client.get(metadata_key)
                
                if metadata_json:
                    try:
                        metadata = json.loads(metadata_json)
                        status["document_types"][doc_type] = metadata
                        any_indexed = True
                        
                        # Track latest indexing time
                        indexed_at = metadata.get("indexed_at")
                        if indexed_at:
                            if latest_indexed_at is None or indexed_at > latest_indexed_at:
                                latest_indexed_at = indexed_at
                    except json.JSONDecodeError:
                        status["document_types"][doc_type] = {"status": "error", "error": "Invalid metadata"}
                else:
                    status["document_types"][doc_type] = {"status": "not_indexed"}
            
            status["overall_status"] = "indexed" if any_indexed else "not_indexed"
            status["last_indexed_at"] = latest_indexed_at
            
            log_with_context(
                self.logger, "DEBUG", "Retrieved indexing status",
                event_id=event_id,
                operation=operation,
                overall_status=status["overall_status"],
                document_types_indexed=sum(1 for dt in status["document_types"].values() if dt.get("status") != "not_indexed")
            )
            
            return status
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", f"Failed to get indexing status: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "event_id": event_id,
                "error": f"Failed to get indexing status: {str(e)}",
                "overall_status": "error",
                "error_type": "status_retrieval_error"
            }
    
    async def clear_event_index(self, event_id: str) -> Dict[str, Any]:
        """
        Clear all indexed documents for an event.
        
        Args:
            event_id: Event ID to clear index for
            
        Returns:
            Clearing results
        """
        operation = "clear_event_index"
        
        log_with_context(
            self.logger, "INFO", "Clearing event index",
            event_id=event_id,
            operation=operation
        )
        
        try:
            redis_client = await self.get_redis()
            results = {}
            document_types = ["transcript", "rubric", "scoring"]
            
            for doc_type in document_types:
                try:
                    delete_result = await llamaindex_service.delete_event_index(
                        event_id=event_id,
                        document_type=doc_type
                    )
                    results[doc_type] = delete_result
                    
                    # Clear metadata
                    metadata_key = f"event:{event_id}:indexing_metadata:{doc_type}"
                    await redis_client.delete(metadata_key)
                    
                except Exception as doc_error:
                    results[doc_type] = {
                        "success": False,
                        "error": str(doc_error)
                    }
            
            # Determine overall success
            all_successful = all(result.get("success", False) for result in results.values())
            
            log_with_context(
                self.logger, "INFO", f"Event index clearing completed",
                event_id=event_id,
                operation=operation,
                overall_success=all_successful,
                cleared_document_types=[dt for dt, result in results.items() if result.get("success")]
            )
            
            return {
                "success": all_successful,
                "event_id": event_id,
                "results": results,
                "cleared_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", f"Failed to clear event index: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "success": False,
                "error": f"Failed to clear event index: {str(e)}",
                "event_id": event_id,
                "error_type": "clear_index_error"
            }
    
    # Helper methods
    
    async def _store_indexing_metadata(
        self,
        event_id: str,
        document_type: str,
        indexed_count: int,
        session_ids: Optional[List[str]] = None,
        rubric_ids: Optional[List[str]] = None
    ) -> bool:
        """Store indexing metadata in Redis."""
        try:
            redis_client = await self.get_redis()
            
            metadata = {
                "document_type": document_type,
                "event_id": event_id,
                "indexed_count": indexed_count,
                "indexed_at": datetime.utcnow().isoformat(),
                "status": "indexed"
            }
            
            if session_ids:
                metadata["session_ids"] = session_ids
                metadata["session_count"] = len(session_ids)
            
            if rubric_ids:
                metadata["rubric_ids"] = rubric_ids
                metadata["rubric_count"] = len(rubric_ids)
            
            metadata_key = f"event:{event_id}:indexing_metadata:{document_type}"
            await redis_client.setex(
                metadata_key,
                86400 * 7,  # 7 days TTL
                json.dumps(metadata)
            )
            
            return True
            
        except Exception as storage_error:
            log_with_context(
                self.logger, "ERROR", f"Failed to store indexing metadata: {str(storage_error)}",
                event_id=event_id,
                document_type=document_type,
                operation="store_metadata"
            )
            return False


# Global service instance
document_indexing_service = DocumentIndexingService()
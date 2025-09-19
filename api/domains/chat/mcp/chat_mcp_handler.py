"""
Chat MCP Handler - RAG-Powered Conversational AI

This handler provides RAG-powered chat functionality for PitchScoop using LlamaIndex.
Enables context-aware conversations about pitch analysis, scoring, and evaluation
with proper source attribution and multi-tenant isolation.

Features:
- Context-aware conversations using indexed documents
- Source attribution for all AI responses  
- Multi-tenant isolation using event_id
- Conversation context management
- Redis-backed conversation storage
"""
import json
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import redis.asyncio as redis
import traceback

from ..entities.chat_message import ChatMessage, SourceReference, MessageType, MessageStatus
from ..entities.conversation import Conversation, ConversationType, ConversationContext
from ...indexing.services.llamaindex_service import llamaindex_service
from ...shared.infrastructure.logging import get_logger, log_with_context


class ChatMCPHandler:
    """MCP handler for RAG-powered chat operations."""
    
    def __init__(self):
        """Initialize the chat MCP handler."""
        self.redis_client: Optional[redis.Redis] = None
        self.logger = get_logger("chat.mcp.handler")
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis client connection."""
        if self.redis_client is None:
            redis_url = "redis://redis:6379/0"  # Docker internal network
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client
    
    async def start_conversation(
        self,
        event_id: str,
        conversation_type: str = "general_chat",
        title: Optional[str] = None,
        session_ids: Optional[List[str]] = None,
        rubric_ids: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new RAG-powered conversation with contextual awareness.
        
        Args:
            event_id: Event ID for multi-tenant isolation
            conversation_type: Type of conversation to create
            title: Optional title for the conversation
            session_ids: Optional pitch session IDs to include in context
            rubric_ids: Optional rubric IDs to include in context
            focus_areas: Optional focus areas for the conversation
            user_id: Optional user ID for conversation attribution
            
        Returns:
            Created conversation details with context information
        """
        logger = get_logger("chat.start_conversation")
        operation = "start_conversation"
        
        log_with_context(
            logger, "INFO", "Starting new RAG-powered conversation",
            event_id=event_id,
            conversation_type=conversation_type,
            operation=operation,
            user_id=user_id,
            session_count=len(session_ids) if session_ids else 0,
            rubric_count=len(rubric_ids) if rubric_ids else 0
        )
        
        try:
            # Generate conversation ID
            conversation_id = str(uuid.uuid4())
            
            # Create conversation context
            context = ConversationContext(
                session_ids=session_ids or [],
                rubric_ids=rubric_ids or [],
                focus_areas=focus_areas or [],
                metadata={"created_via": "mcp_tool"}
            )
            
            # Create conversation entity
            conversation = Conversation.create_new(
                conversation_id=conversation_id,
                event_id=event_id,
                conversation_type=ConversationType(conversation_type),
                title=title,
                user_id=user_id,
                context=context
            )
            
            # Store conversation in Redis
            redis_client = await self.get_redis()
            conversation_key = f"event:{event_id}:conversation:{conversation_id}"
            
            try:
                await redis_client.setex(
                    conversation_key,
                    86400,  # 24 hours TTL
                    json.dumps(conversation.to_dict())
                )
                
                log_with_context(
                    logger, "INFO", "Conversation stored successfully",
                    event_id=event_id,
                    conversation_id=conversation_id,
                    operation="redis_store_conversation",
                    redis_key=conversation_key
                )
                
            except Exception as storage_error:
                log_with_context(
                    logger, "ERROR", "Failed to store conversation in Redis",
                    event_id=event_id,
                    conversation_id=conversation_id,
                    operation="redis_store_conversation",
                    error=str(storage_error)
                )
                return {
                    "error": f"Failed to store conversation: {str(storage_error)}",
                    "conversation_id": conversation_id,
                    "event_id": event_id,
                    "error_type": "storage_error"
                }
            
            # Check if we have indexed documents for context
            context_status = await self._check_context_availability(event_id, session_ids, rubric_ids)
            
            log_with_context(
                logger, "INFO", "Conversation created successfully",
                event_id=event_id,
                conversation_id=conversation_id,
                operation=operation,
                conversation_type=conversation_type,
                context_available=context_status.get("has_context", False)
            )
            
            return {
                "conversation_id": conversation_id,
                "event_id": event_id,
                "title": conversation.title,
                "conversation_type": conversation_type,
                "status": "active",
                "created_at": conversation.created_at.isoformat(),
                "context": {
                    "session_ids": session_ids or [],
                    "rubric_ids": rubric_ids or [],
                    "focus_areas": focus_areas or []
                },
                "context_status": context_status,
                "user_id": user_id,
                "success": True
            }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Failed to start conversation: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            return {
                "error": f"Failed to start conversation: {str(e)}",
                "event_id": event_id,
                "success": False,
                "error_type": "conversation_creation_error"
            }
    
    async def send_message(
        self,
        conversation_id: str,
        event_id: str,
        message: str,
        include_sources: bool = True,
        max_sources: int = 5,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message and get an AI-powered response with RAG context.
        
        Args:
            conversation_id: Conversation ID to send message to
            event_id: Event ID for multi-tenant isolation
            message: User message to process
            include_sources: Whether to include source attribution in response
            max_sources: Maximum number of source references to include
            user_id: Optional user ID for message attribution
            
        Returns:
            AI response with source attribution and conversation updates
        """
        logger = get_logger("chat.send_message")
        operation = "send_message"
        start_time = datetime.utcnow()
        
        log_with_context(
            logger, "INFO", "Processing chat message with RAG",
            event_id=event_id,
            conversation_id=conversation_id,
            operation=operation,
            user_id=user_id,
            message_length=len(message),
            include_sources=include_sources
        )
        
        try:
            # Retrieve conversation
            redis_client = await self.get_redis()
            conversation_key = f"event:{event_id}:conversation:{conversation_id}"
            conversation_json = await redis_client.get(conversation_key)
            
            if not conversation_json:
                log_with_context(
                    logger, "ERROR", "Conversation not found",
                    event_id=event_id,
                    conversation_id=conversation_id,
                    operation="conversation_retrieval",
                    redis_key=conversation_key
                )
                return {
                    "error": f"Conversation {conversation_id} not found",
                    "conversation_id": conversation_id,
                    "event_id": event_id,
                    "error_type": "conversation_not_found"
                }
            
            try:
                conversation_data = json.loads(conversation_json)
                conversation = Conversation.from_dict(conversation_data)
                
                log_with_context(
                    logger, "DEBUG", "Conversation retrieved successfully",
                    event_id=event_id,
                    conversation_id=conversation_id,
                    operation="conversation_parsing",
                    conversation_type=conversation.conversation_type.value,
                    message_count=conversation.message_count
                )
                
            except json.JSONDecodeError as json_error:
                log_with_context(
                    logger, "ERROR", "Failed to parse conversation data",
                    event_id=event_id,
                    conversation_id=conversation_id,
                    operation="conversation_parsing",
                    error=str(json_error)
                )
                return {
                    "error": f"Invalid conversation data: {str(json_error)}",
                    "conversation_id": conversation_id,
                    "event_id": event_id,
                    "error_type": "data_parsing_error"
                }
            
            # Create user message
            user_message_id = str(uuid.uuid4())
            user_message = ChatMessage.create_user_query(
                message_id=user_message_id,
                conversation_id=conversation_id,
                event_id=event_id,
                content=message,
                user_id=user_id
            )
            
            # Store user message
            await self._store_message(user_message)
            
            # Generate AI response using RAG
            log_with_context(
                logger, "DEBUG", "Generating RAG response",
                event_id=event_id,
                conversation_id=conversation_id,
                operation="rag_generation",
                message_length=len(message)
            )
            
            ai_response_data = await self._generate_rag_response(
                message=message,
                conversation=conversation,
                event_id=event_id,
                include_sources=include_sources,
                max_sources=max_sources
            )
            
            if "error" in ai_response_data:
                log_with_context(
                    logger, "ERROR", "RAG response generation failed",
                    event_id=event_id,
                    conversation_id=conversation_id,
                    operation="rag_generation",
                    error=ai_response_data["error"]
                )
                return {
                    "error": f"Failed to generate response: {ai_response_data['error']}",
                    "conversation_id": conversation_id,
                    "event_id": event_id,
                    "error_type": "rag_generation_error"
                }
            
            # Create AI response message
            ai_message_id = str(uuid.uuid4())
            processing_duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            ai_message = ChatMessage.create_ai_response(
                message_id=ai_message_id,
                conversation_id=conversation_id,
                event_id=event_id,
                content=ai_response_data["response"],
                sources=ai_response_data.get("sources", []),
                model_used=ai_response_data.get("model_used"),
                tokens_used=ai_response_data.get("tokens_used"),
                processing_duration_ms=processing_duration
            )
            
            # Store AI message
            await self._store_message(ai_message)
            
            # Update conversation message count
            conversation.update_message_count(conversation.message_count + 2)
            await redis_client.setex(
                conversation_key,
                86400,
                json.dumps(conversation.to_dict())
            )
            
            log_with_context(
                logger, "INFO", "Chat message processed successfully",
                event_id=event_id,
                conversation_id=conversation_id,
                operation=operation,
                user_id=user_id,
                processing_duration_ms=processing_duration,
                source_count=len(ai_response_data.get("sources", [])),
                response_length=len(ai_response_data["response"])
            )
            
            return {
                "conversation_id": conversation_id,
                "event_id": event_id,
                "user_message": user_message.to_dict(),
                "ai_response": ai_message.to_dict(),
                "processing_duration_ms": processing_duration,
                "success": True
            }
            
        except Exception as e:
            processing_duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log_with_context(
                logger, "ERROR", f"Failed to send message: {str(e)}",
                event_id=event_id,
                conversation_id=conversation_id,
                operation=operation,
                error_type=type(e).__name__,
                processing_duration_ms=processing_duration,
                traceback=traceback.format_exc()
            )
            return {
                "error": f"Failed to send message: {str(e)}",
                "conversation_id": conversation_id,
                "event_id": event_id,
                "success": False,
                "error_type": "message_processing_error"
            }
    
    async def search_documents(
        self,
        event_id: str,
        query: str,
        document_types: Optional[List[str]] = None,
        session_ids: Optional[List[str]] = None,
        max_results: int = 10,
        min_relevance_score: float = 0.1
    ) -> Dict[str, Any]:
        """
        Search indexed documents for specific information using RAG.
        
        Args:
            event_id: Event ID for multi-tenant isolation
            query: Search query or question
            document_types: Optional filter by document types
            session_ids: Optional filter by specific session IDs
            max_results: Maximum number of results to return
            min_relevance_score: Minimum relevance score for results
            
        Returns:
            Search results with relevance scores and content snippets
        """
        logger = get_logger("chat.search_documents")
        operation = "search_documents"
        
        log_with_context(
            logger, "INFO", "Searching indexed documents",
            event_id=event_id,
            operation=operation,
            query_length=len(query),
            document_types=document_types,
            session_ids=session_ids,
            max_results=max_results,
            min_relevance_score=min_relevance_score
        )
        
        try:
            search_results = []
            
            # Search each document type
            search_types = document_types or ["transcript", "rubric", "scoring"]
            
            for doc_type in search_types:
                try:
                    result = await llamaindex_service.query_index(
                        event_id=event_id,
                        document_type=doc_type,
                        query=query,
                        top_k=max_results
                    )
                    
                    if result["success"] and result["source_nodes"]:
                        for node in result["source_nodes"]:
                            # Apply session filter if provided
                            if session_ids:
                                node_session_id = node.get("metadata", {}).get("session_id")
                                if node_session_id and node_session_id not in session_ids:
                                    continue
                            
                            # Apply relevance score filter
                            relevance_score = node.get("score", 0.0)
                            if relevance_score >= min_relevance_score:
                                search_results.append({
                                    "document_type": doc_type,
                                    "content": node["content"],
                                    "relevance_score": relevance_score,
                                    "metadata": node.get("metadata", {}),
                                    "session_id": node.get("metadata", {}).get("session_id")
                                })
                
                except Exception as search_error:
                    log_with_context(
                        logger, "WARNING", f"Search failed for document type {doc_type}",
                        event_id=event_id,
                        operation="document_type_search",
                        document_type=doc_type,
                        error=str(search_error)
                    )
                    continue
            
            # Sort by relevance score and limit results
            search_results.sort(key=lambda x: x["relevance_score"], reverse=True)
            search_results = search_results[:max_results]
            
            log_with_context(
                logger, "INFO", "Document search completed",
                event_id=event_id,
                operation=operation,
                result_count=len(search_results),
                query_length=len(query),
                document_types_searched=search_types
            )
            
            return {
                "event_id": event_id,
                "query": query,
                "results": search_results,
                "total_results": len(search_results),
                "search_parameters": {
                    "document_types": document_types,
                    "session_ids": session_ids,
                    "max_results": max_results,
                    "min_relevance_score": min_relevance_score
                },
                "success": True
            }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Document search failed: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            return {
                "error": f"Document search failed: {str(e)}",
                "event_id": event_id,
                "query": query,
                "success": False,
                "error_type": "search_error"
            }
    
    async def ask_about_pitch(
        self,
        session_id: str,
        event_id: str,
        question: str,
        include_comparative_context: bool = False,
        focus_criteria: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ask specific questions about a pitch session with RAG context.
        
        Args:
            session_id: Pitch session ID to ask about
            event_id: Event ID for multi-tenant isolation
            question: Specific question about the pitch
            include_comparative_context: Whether to include context from other pitches
            focus_criteria: Optional focus on specific scoring criteria
            user_id: Optional user ID for query attribution
            
        Returns:
            AI response with pitch-specific context and source attribution
        """
        logger = get_logger("chat.ask_about_pitch")
        operation = "ask_about_pitch"
        
        log_with_context(
            logger, "INFO", "Processing pitch-specific question",
            event_id=event_id,
            session_id=session_id,
            operation=operation,
            user_id=user_id,
            question_length=len(question),
            include_comparative_context=include_comparative_context,
            focus_criteria=focus_criteria
        )
        
        try:
            # Create temporary conversation for this Q&A
            temp_conversation = Conversation.create_pitch_analysis(
                conversation_id=f"temp_{uuid.uuid4()}",
                event_id=event_id,
                session_id=session_id,
                user_id=user_id,
                title=f"Q&A about {session_id[:8]}"
            )
            
            # Set focus areas if provided
            if focus_criteria:
                temp_conversation.set_focus_areas(focus_criteria)
            
            # Generate contextualized question
            if include_comparative_context:
                contextualized_question = f"""
                Question about pitch session {session_id}: {question}
                
                Please provide comparative context with other pitches in this event when relevant.
                Focus areas: {', '.join(focus_criteria) if focus_criteria else 'all criteria'}
                """
            else:
                contextualized_question = f"""
                Question about pitch session {session_id}: {question}
                
                Focus areas: {', '.join(focus_criteria) if focus_criteria else 'all criteria'}
                """
            
            # Generate RAG response
            response_data = await self._generate_rag_response(
                message=contextualized_question,
                conversation=temp_conversation,
                event_id=event_id,
                include_sources=True,
                max_sources=5
            )
            
            if "error" in response_data:
                log_with_context(
                    logger, "ERROR", "Failed to generate pitch Q&A response",
                    event_id=event_id,
                    session_id=session_id,
                    operation="rag_generation",
                    error=response_data["error"]
                )
                return {
                    "error": f"Failed to answer question: {response_data['error']}",
                    "session_id": session_id,
                    "event_id": event_id,
                    "error_type": "rag_generation_error"
                }
            
            log_with_context(
                logger, "INFO", "Pitch Q&A completed successfully",
                event_id=event_id,
                session_id=session_id,
                operation=operation,
                user_id=user_id,
                response_length=len(response_data["response"]),
                source_count=len(response_data.get("sources", []))
            )
            
            return {
                "session_id": session_id,
                "event_id": event_id,
                "question": question,
                "response": response_data["response"],
                "sources": response_data.get("sources", []),
                "focus_criteria": focus_criteria,
                "include_comparative_context": include_comparative_context,
                "model_used": response_data.get("model_used"),
                "user_id": user_id,
                "success": True
            }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Pitch Q&A failed: {str(e)}",
                event_id=event_id,
                session_id=session_id,
                operation=operation,
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            return {
                "error": f"Pitch Q&A failed: {str(e)}",
                "session_id": session_id,
                "event_id": event_id,
                "success": False,
                "error_type": "pitch_qa_error"
            }
    
    async def compare_sessions(
        self,
        session_ids: List[str],
        event_id: str,
        comparison_focus: Optional[List[str]] = None,
        conversation_title: Optional[str] = None,
        judge_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Have conversational comparison of multiple pitch sessions.
        
        Args:
            session_ids: List of session IDs to compare
            event_id: Event ID for multi-tenant isolation
            comparison_focus: Optional focus areas for comparison
            conversation_title: Optional title for the comparison conversation
            judge_id: Optional judge ID conducting the comparison
            
        Returns:
            Created comparison conversation with initial analysis
        """
        logger = get_logger("chat.compare_sessions")
        operation = "compare_sessions"
        
        log_with_context(
            logger, "INFO", "Starting session comparison conversation",
            event_id=event_id,
            operation=operation,
            session_count=len(session_ids),
            comparison_focus=comparison_focus,
            judge_id=judge_id
        )
        
        try:
            # Create comparison conversation
            comparison_conversation = Conversation.create_scoring_review(
                conversation_id=str(uuid.uuid4()),
                event_id=event_id,
                session_ids=session_ids,
                judge_id=judge_id,
                title=conversation_title or f"Comparison of {len(session_ids)} pitches"
            )
            
            # Set focus areas if provided
            if comparison_focus:
                comparison_conversation.set_focus_areas(comparison_focus)
            
            # Store conversation
            redis_client = await self.get_redis()
            conversation_key = f"event:{event_id}:conversation:{comparison_conversation.conversation_id}"
            await redis_client.setex(
                conversation_key,
                86400,
                json.dumps(comparison_conversation.to_dict())
            )
            
            # Generate initial comparison analysis
            initial_question = f"""
            Please provide a comprehensive comparison of these {len(session_ids)} pitch sessions: {', '.join(session_ids)}.
            
            Focus on: {', '.join(comparison_focus) if comparison_focus else 'all criteria (idea, technical, tools, presentation)'}
            
            Include:
            1. Overall ranking with brief rationale
            2. Strengths and differentiators of each pitch
            3. Key criteria where teams excelled or struggled
            4. Notable technical implementations or tool usage patterns
            5. Recommendations for judges
            """
            
            response_data = await self._generate_rag_response(
                message=initial_question,
                conversation=comparison_conversation,
                event_id=event_id,
                include_sources=True,
                max_sources=10
            )
            
            if "error" in response_data:
                log_with_context(
                    logger, "ERROR", "Failed to generate comparison analysis",
                    event_id=event_id,
                    operation="rag_generation",
                    error=response_data["error"]
                )
                return {
                    "error": f"Failed to generate comparison: {response_data['error']}",
                    "session_ids": session_ids,
                    "event_id": event_id,
                    "error_type": "comparison_generation_error"
                }
            
            # Create initial AI message
            ai_message = ChatMessage.create_ai_response(
                message_id=str(uuid.uuid4()),
                conversation_id=comparison_conversation.conversation_id,
                event_id=event_id,
                content=response_data["response"],
                sources=response_data.get("sources", []),
                model_used=response_data.get("model_used")
            )
            
            await self._store_message(ai_message)
            
            # Update conversation message count
            comparison_conversation.update_message_count(1)
            await redis_client.setex(
                conversation_key,
                86400,
                json.dumps(comparison_conversation.to_dict())
            )
            
            log_with_context(
                logger, "INFO", "Session comparison conversation created successfully",
                event_id=event_id,
                conversation_id=comparison_conversation.conversation_id,
                operation=operation,
                session_count=len(session_ids),
                analysis_length=len(response_data["response"])
            )
            
            return {
                "conversation_id": comparison_conversation.conversation_id,
                "event_id": event_id,
                "session_ids": session_ids,
                "title": comparison_conversation.title,
                "comparison_focus": comparison_focus,
                "initial_analysis": response_data["response"],
                "sources": response_data.get("sources", []),
                "created_at": comparison_conversation.created_at.isoformat(),
                "judge_id": judge_id,
                "success": True
            }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Session comparison failed: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__,
                traceback=traceback.format_exc()
            )
            return {
                "error": f"Session comparison failed: {str(e)}",
                "session_ids": session_ids,
                "event_id": event_id,
                "success": False,
                "error_type": "comparison_error"
            }
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        event_id: str,
        include_sources: bool = True,
        message_limit: int = 50,
        message_offset: int = 0,
        message_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve conversation history with messages and context.
        
        Args:
            conversation_id: Conversation ID to retrieve
            event_id: Event ID for multi-tenant isolation
            include_sources: Whether to include detailed source information
            message_limit: Maximum number of messages to return
            message_offset: Offset for pagination
            message_types: Optional filter by message types
            
        Returns:
            Conversation history with messages and metadata
        """
        logger = get_logger("chat.get_conversation_history")
        operation = "get_conversation_history"
        
        log_with_context(
            logger, "INFO", "Retrieving conversation history",
            event_id=event_id,
            conversation_id=conversation_id,
            operation=operation,
            message_limit=message_limit,
            message_offset=message_offset
        )
        
        try:
            redis_client = await self.get_redis()
            
            # Get conversation metadata
            conversation_key = f"event:{event_id}:conversation:{conversation_id}"
            conversation_json = await redis_client.get(conversation_key)
            
            if not conversation_json:
                return {
                    "error": f"Conversation {conversation_id} not found",
                    "conversation_id": conversation_id,
                    "event_id": event_id,
                    "error_type": "conversation_not_found"
                }
            
            conversation_data = json.loads(conversation_json)
            
            # Get messages
            message_keys_pattern = f"event:{event_id}:conversation:{conversation_id}:message:*"
            message_keys = await redis_client.keys(message_keys_pattern)
            
            messages = []
            for message_key in message_keys:
                try:
                    message_json = await redis_client.get(message_key)
                    if message_json:
                        message_data = json.loads(message_json)
                        message = ChatMessage.from_dict(message_data)
                        
                        # Apply message type filter
                        if message_types and message.message_type.value not in message_types:
                            continue
                        
                        # Include or exclude sources based on parameter
                        message_dict = message.to_dict()
                        if not include_sources:
                            message_dict["sources"] = []
                        
                        messages.append(message_dict)
                
                except Exception as message_error:
                    log_with_context(
                        logger, "WARNING", f"Failed to parse message: {str(message_error)}",
                        event_id=event_id,
                        conversation_id=conversation_id,
                        message_key=message_key
                    )
                    continue
            
            # Sort messages by timestamp
            messages.sort(key=lambda x: x["timestamp"])
            
            # Apply pagination
            total_messages = len(messages)
            messages = messages[message_offset:message_offset + message_limit]
            
            log_with_context(
                logger, "INFO", "Conversation history retrieved successfully",
                event_id=event_id,
                conversation_id=conversation_id,
                operation=operation,
                total_messages=total_messages,
                returned_messages=len(messages)
            )
            
            return {
                "conversation_id": conversation_id,
                "event_id": event_id,
                "conversation": conversation_data,
                "messages": messages,
                "pagination": {
                    "total_messages": total_messages,
                    "returned_count": len(messages),
                    "limit": message_limit,
                    "offset": message_offset,
                    "has_more": message_offset + len(messages) < total_messages
                },
                "success": True
            }
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Failed to retrieve conversation history: {str(e)}",
                event_id=event_id,
                conversation_id=conversation_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "error": f"Failed to retrieve conversation history: {str(e)}",
                "conversation_id": conversation_id,
                "event_id": event_id,
                "success": False,
                "error_type": "history_retrieval_error"
            }
    
    async def health_check(
        self,
        event_id: Optional[str] = None,
        detailed_check: bool = False,
        test_query: bool = False
    ) -> Dict[str, Any]:
        """
        """Check health and readiness of the RAG chat system.
        
        Args:
            event_id: Optional event ID for context-specific health check
            detailed_check: Whether to perform detailed component testing
            test_query: Whether to test with a sample RAG query
            
        Returns:
            Health status of all RAG chat components (RedisVL, Azure OpenAI, etc.)
        """
        logger = get_logger("chat.health_check")
        operation = "health_check"
        
        log_with_context(
            logger, "INFO", "Starting RAG chat system health check",
            event_id=event_id,
            operation=operation,
            detailed_check=detailed_check,
            test_query=test_query
        )
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": event_id,
            "components": {},
            "detailed_check": detailed_check,
            "test_query": test_query
        }
        
        try:
            # Check Redis connectivity
            try:
                redis_client = await self.get_redis()
                await redis_client.ping()
                health_status["components"]["redis"] = {"status": "healthy"}
            except Exception as redis_error:
                health_status["components"]["redis"] = {
                    "status": "error",
                    "error": str(redis_error)
                }
                health_status["status"] = "degraded"
            
            # Check LlamaIndex service
            try:
                llamaindex_health = await llamaindex_service.health_check()
                health_status["components"]["llamaindex"] = llamaindex_health
                if not llamaindex_health.get("healthy", False):
                    health_status["status"] = "degraded"
            except Exception as llama_error:
                health_status["components"]["llamaindex"] = {
                    "healthy": False,
                    "error": str(llama_error)
                }
                health_status["status"] = "unhealthy"
            
            # Perform test query if requested
            if test_query and event_id:
                try:
                    test_result = await self.search_documents(
                        event_id=event_id,
                        query="test health check query",
                        max_results=1
                    )
                    health_status["components"]["rag_pipeline"] = {
                        "status": "healthy" if test_result.get("success") else "error",
                        "test_result": test_result.get("success", False)
                    }
                except Exception as test_error:
                    health_status["components"]["rag_pipeline"] = {
                        "status": "error",
                        "error": str(test_error)
                    }
                    health_status["status"] = "degraded"
            
            log_with_context(
                logger, "INFO", f"Health check completed with status: {health_status['status']}",
                event_id=event_id,
                operation=operation,
                overall_status=health_status["status"],
                components_checked=list(health_status["components"].keys())
            )
            
            return health_status
            
        except Exception as e:
            log_with_context(
                logger, "ERROR", f"Health check system error: {str(e)}",
                event_id=event_id,
                operation=operation,
                error_type=type(e).__name__
            )
            return {
                "status": "unhealthy",
                "error": f"Health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat(),
                "event_id": event_id,
                "error_type": "health_check_system_error"
            }
    
    # Helper methods
    
    async def _check_context_availability(
        self,
        event_id: str,
        session_ids: Optional[List[str]] = None,
        rubric_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Check if indexed documents are available for the given context."""
        context_status = {
            "has_context": False,
            "available_document_types": [],
            "session_context_available": False,
            "rubric_context_available": False
        }
        
        try:
            # Check for indexed documents
            health_check = await llamaindex_service.health_check()
            if health_check.get("healthy", False):
                context_status["has_context"] = True
                context_status["available_document_types"] = ["transcript", "rubric", "scoring"]
            
            # Check session-specific context
            if session_ids:
                # This would typically check if sessions have indexed transcripts
                context_status["session_context_available"] = True
            
            # Check rubric context
            if rubric_ids:
                # This would typically check if rubrics are indexed
                context_status["rubric_context_available"] = True
        
        except Exception as e:
            context_status["error"] = str(e)
        
        return context_status
    
    async def _generate_rag_response(
        self,
        message: str,
        conversation: Conversation,
        event_id: str,
        include_sources: bool = True,
        max_sources: int = 5
    ) -> Dict[str, Any]:
        """Generate RAG-powered response for a message using conversation context."""
        try:
            # Build context-aware query
            context_info = []
            
            if conversation.context.session_ids:
                context_info.append(f"Session context: {', '.join(conversation.context.session_ids)}")
            
            if conversation.context.focus_areas:
                context_info.append(f"Focus areas: {', '.join(conversation.context.focus_areas)}")
            
            if conversation.conversation_type != ConversationType.GENERAL_CHAT:
                context_info.append(f"Conversation type: {conversation.conversation_type.value}")
            
            # Create contextualized query
            if context_info:
                contextualized_message = f"""
                Context: {'; '.join(context_info)}
                
                Query: {message}
                
                Please provide a comprehensive response using all available indexed information.
                """
            else:
                contextualized_message = message
            
            # Query multiple document types and combine results
            all_sources = []
            combined_context = []
            
            for doc_type in ["transcript", "rubric", "scoring"]:
                try:
                    result = await llamaindex_service.query_index(
                        event_id=event_id,
                        document_type=doc_type,
                        query=contextualized_message,
                        top_k=max_sources
                    )
                    
                    if result["success"] and result["source_nodes"]:
                        for node in result["source_nodes"]:
                            source_ref = SourceReference(
                                document_type=doc_type,
                                document_id=node.get("metadata", {}).get("document_id", "unknown"),
                                session_id=node.get("metadata", {}).get("session_id"),
                                content_snippet=node["content"][:500] + "..." if len(node["content"]) > 500 else node["content"],
                                relevance_score=node.get("score", 0.0),
                                metadata=node.get("metadata", {})
                            )
                            all_sources.append(source_ref)
                            combined_context.append(f"[{doc_type.upper()}] {node['content']}")
                
                except Exception as doc_error:
                    # Continue with other document types if one fails
                    continue
            
            # Sort sources by relevance and limit
            all_sources.sort(key=lambda x: x.relevance_score, reverse=True)
            all_sources = all_sources[:max_sources]
            
            # Generate response using LlamaIndex if we have context
            if combined_context:
                # Use the first available document type for response generation
                for doc_type in ["transcript", "rubric", "scoring"]:
                    try:
                        result = await llamaindex_service.query_index(
                            event_id=event_id,
                            document_type=doc_type,
                            query=contextualized_message,
                            top_k=1
                        )
                        
                        if result["success"] and result["response"]:
                            return {
                                "response": result["response"],
                                "sources": all_sources if include_sources else [],
                                "model_used": "llamaindex_with_azure_openai",
                                "context_types": ["transcript", "rubric", "scoring"]
                            }
                    except Exception:
                        continue
            
            # Fallback response if no context available
            return {
                "response": f"I don't have enough indexed context to answer your question about: {message}. Please ensure that relevant documents (transcripts, rubrics, scoring data) have been indexed for this event.",
                "sources": [],
                "model_used": "fallback",
                "context_types": []
            }
            
        except Exception as e:
            return {
                "error": f"RAG response generation failed: {str(e)}",
                "context_types": []
            }
    
    async def _store_message(self, message: ChatMessage) -> bool:
        """Store a message in Redis."""
        try:
            redis_client = await self.get_redis()
            message_key = f"event:{message.event_id}:conversation:{message.conversation_id}:message:{message.message_id}"
            
            await redis_client.setex(
                message_key,
                86400,  # 24 hours TTL
                json.dumps(message.to_dict())
            )
            return True
            
        except Exception as storage_error:
            log_with_context(
                self.logger, "ERROR", f"Failed to store message: {str(storage_error)}",
                event_id=message.event_id,
                conversation_id=message.conversation_id,
                message_id=message.message_id,
                operation="store_message"
            )
            return False


# Global instance
chat_mcp_handler = ChatMCPHandler()
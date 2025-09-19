"""
RAG Integration Example - LlamaIndex-Powered PitchScoop

This example demonstrates how to integrate and use the RAG-powered functionality
in PitchScoop, including document indexing, chat, and enhanced scoring.

Usage Examples:
1. Index documents for RAG functionality
2. Create RAG-powered conversations
3. Use enhanced scoring with context
4. Search indexed documents
5. Ask specific questions about pitches
"""
import asyncio
import json
from typing import Dict, Any, List

# Import the new RAG-powered services
from ..indexing.services.document_indexing_service import document_indexing_service
from ..indexing.services.llamaindex_service import llamaindex_service
from ..chat.mcp.chat_mcp_tools import execute_chat_mcp_tool
from ..scoring.mcp.scoring_mcp_tools import execute_scoring_mcp_tool


class RAGIntegrationExample:
    """Example usage of RAG-powered functionality in PitchScoop."""
    
    def __init__(self, event_id: str):
        """Initialize with event ID for multi-tenant isolation."""
        self.event_id = event_id
    
    async def example_1_index_documents(self):
        """
        Example 1: Index documents for RAG functionality.
        
        This example shows how to index pitch transcripts, rubrics,
        and scoring results to enable RAG-powered features.
        """
        print("\\n=== Example 1: Document Indexing ===")
        
        # Example session data with transcripts
        session_data_list = [
            {
                "session_id": "session_001",
                "team_name": "AI Innovators",
                "pitch_title": "HealthBot - AI-Powered Medical Assistant",
                "status": "completed",
                "final_transcript": {
                    "total_text": "Hello judges, I'm presenting HealthBot, an AI-powered medical assistant that integrates OpenAI for natural language processing, RedisVL for medical knowledge storage, and MinIO for secure patient data management. Our solution addresses the critical need for 24/7 medical support in underserved areas. The technical implementation uses advanced RAG architecture to provide accurate medical advice by retrieving relevant information from our comprehensive medical knowledge base stored in RedisVL. We demonstrate seamless integration of three sponsor tools: OpenAI's GPT-4 for conversational AI, RedisVL for vector similarity search of medical conditions, and MinIO for HIPAA-compliant storage of patient interactions. Our presentation showcases a live demo where HealthBot successfully diagnoses common conditions, provides treatment recommendations, and escalates complex cases to human physicians. The impact is significant - reducing wait times from hours to seconds while maintaining medical accuracy through our AI-agent architecture."
                },
                "created_at": "2024-01-15T10:00:00Z",
                "recording_duration": 180
            },
            {
                "session_id": "session_002", 
                "team_name": "DevOps Heroes",
                "pitch_title": "CloudAgent - Intelligent Infrastructure Management",
                "status": "completed",
                "final_transcript": {
                    "total_text": "Introducing CloudAgent, the intelligent infrastructure management system that revolutionizes DevOps workflows. Our AI agent integrates OpenAI for intelligent decision-making, RedisVL for storing and querying infrastructure patterns, and MinIO for artifact and configuration management. CloudAgent addresses the growing complexity of cloud infrastructure by providing autonomous monitoring, predictive scaling, and intelligent troubleshooting. The technical architecture implements sophisticated agent behavior using OpenAI's models to analyze system metrics, RedisVL to find similar historical incidents for pattern matching, and MinIO to store deployment artifacts and rollback configurations. Our tool integration demonstrates advanced agentic behavior - the system can automatically detect anomalies, predict resource needs, and execute remediation actions without human intervention. The presentation shows CloudAgent reducing incident response time by 75% and preventing 90% of potential outages through proactive monitoring and AI-driven insights."
                },
                "created_at": "2024-01-15T10:30:00Z", 
                "recording_duration": 175
            }
        ]
        
        # Index transcripts
        print("Indexing pitch transcripts...")
        transcript_result = await document_indexing_service.index_pitch_transcripts(
            event_id=self.event_id,
            session_data_list=session_data_list
        )
        print(f"Transcript indexing: {transcript_result['success']}")
        if transcript_result['success']:
            print(f"  - Indexed {transcript_result['indexed_sessions']} sessions")
            print(f"  - Skipped {transcript_result['skipped_sessions']} sessions")
        
        # Example rubric data
        rubric_data_list = [
            {
                "rubric_id": "main_rubric_2024",
                "title": "AI Agent Competition Scoring Rubric 2024",
                "description": "Official scoring criteria for AI agent pitch competition",
                "type": "competition",
                "criteria": [
                    {
                        "name": "Idea",
                        "description": "Unique value proposition and vertical-specific agent design",
                        "weight": 25,
                        "scoring_levels": [
                            {
                                "level": "Excellent",
                                "points": 90,
                                "description": "Highly innovative solution addressing clear market need with unique AI agent approach"
                            },
                            {
                                "level": "Good", 
                                "points": 70,
                                "description": "Solid solution with some innovative elements and clear agent use case"
                            },
                            {
                                "level": "Fair",
                                "points": 50,
                                "description": "Basic solution with limited innovation or unclear agent benefits"
                            }
                        ]
                    },
                    {
                        "name": "Technical Implementation",
                        "description": "Novel tool use and technical sophistication",
                        "weight": 25,
                        "scoring_levels": [
                            {
                                "level": "Excellent",
                                "points": 90,
                                "description": "Sophisticated technical architecture with novel integration patterns"
                            },
                            {
                                "level": "Good",
                                "points": 70, 
                                "description": "Solid technical implementation with good integration practices"
                            },
                            {
                                "level": "Fair",
                                "points": 50,
                                "description": "Basic technical implementation with standard integration"
                            }
                        ]
                    }
                ]
            }
        ]
        
        # Index rubrics
        print("\\nIndexing scoring rubrics...")
        rubric_result = await document_indexing_service.index_scoring_rubrics(
            event_id=self.event_id,
            rubric_data_list=rubric_data_list
        )
        print(f"Rubric indexing: {rubric_result['success']}")
        if rubric_result['success']:
            print(f"  - Indexed {rubric_result['indexed_rubrics']} rubrics")
        
        return transcript_result['success'] and rubric_result['success']
    
    async def example_2_create_rag_conversation(self):
        """
        Example 2: Create RAG-powered conversation.
        
        Shows how to start a context-aware conversation that can
        reference indexed documents.
        """
        print("\\n=== Example 2: RAG-Powered Conversation ===")
        
        # Start a conversation focused on pitch analysis
        conversation_result = await execute_chat_mcp_tool(
            tool_name="chat.start_conversation",
            arguments={
                "event_id": self.event_id,
                "conversation_type": "pitch_analysis",
                "title": "Analysis of Health and DevOps Pitches",
                "session_ids": ["session_001", "session_002"],
                "focus_areas": ["technical", "tools"],
                "user_id": "judge_001"
            }
        )
        
        if not conversation_result.get("success"):
            print(f"Failed to start conversation: {conversation_result.get('error')}")
            return None
        
        conversation_id = conversation_result["conversation_id"]
        print(f"Created conversation: {conversation_id}")
        print(f"Context available: {conversation_result.get('context_status', {}).get('has_context', False)}")
        
        # Send a message to the conversation
        print("\\nSending message to RAG-powered conversation...")
        message_result = await execute_chat_mcp_tool(
            tool_name="chat.send_message",
            arguments={
                "conversation_id": conversation_id,
                "event_id": self.event_id,
                "message": "Compare the technical implementations of HealthBot and CloudAgent. Which team showed better integration of sponsor tools?",
                "include_sources": True,
                "max_sources": 3,
                "user_id": "judge_001"
            }
        )
        
        if message_result.get("success"):
            ai_response = message_result["ai_response"]
            print(f"AI Response: {ai_response['content'][:200]}...")
            print(f"Sources: {len(ai_response.get('sources', []))} documents referenced")
            print(f"Processing time: {message_result['processing_duration_ms']}ms")
        else:
            print(f"Failed to send message: {message_result.get('error')}")
        
        return conversation_id
    
    async def example_3_enhanced_scoring(self):
        """
        Example 3: RAG-enhanced scoring.
        
        Demonstrates how the scoring system can use indexed rubrics
        and comparative context for more accurate evaluation.
        """
        print("\\n=== Example 3: RAG-Enhanced Scoring ===")
        
        # Score a pitch with RAG enhancement
        scoring_result = await execute_scoring_mcp_tool(
            tool_name="analysis.score_pitch",
            arguments={
                "session_id": "session_001",
                "event_id": self.event_id,
                "judge_id": "judge_001",
                "scoring_context": {
                    "event_type": "ai_agent_competition",
                    "sponsor_tools": ["OpenAI", "RedisVL", "MinIO"],
                    "focus_areas": ["technical", "tools"]
                }
            }
        )
        
        if scoring_result.get("success"):
            scores = scoring_result["scores"]
            print(f"Team: {scoring_result['team_name']}")
            print(f"Overall Score: {scores.get('overall', {}).get('total_score', 'N/A')}")
            
            # Check if RAG enhancement was used
            if "rag_metadata" in scores:
                print("\\nRAG Enhancement Details:")
                rag_meta = scores["rag_metadata"]
                print(f"  - Enhanced analysis: {rag_meta.get('enhanced_analysis', False)}")
                print(f"  - Rubric sources: {rag_meta.get('rubric_sources', 0)}")
                print(f"  - Scoring sources: {rag_meta.get('scoring_sources', 0)}")
                print(f"  - Context types: {', '.join(rag_meta.get('context_types', []))}")
            
            # Show criteria scores
            print("\\nCriteria Breakdown:")
            for criterion in ["idea", "technical_implementation", "tool_use", "presentation"]:
                if criterion in scores:
                    score = scores[criterion].get("score", "N/A")
                    print(f"  - {criterion.replace('_', ' ').title()}: {score}")
        else:
            print(f"Scoring failed: {scoring_result.get('error')}")
        
        return scoring_result.get("success", False)
    
    async def example_4_document_search(self):
        """
        Example 4: Search indexed documents.
        
        Shows how to perform semantic search across all indexed
        documents to find specific information.
        """
        print("\\n=== Example 4: Document Search ===")
        
        # Search for information about sponsor tool integration
        search_result = await execute_chat_mcp_tool(
            tool_name="chat.search_documents",
            arguments={
                "event_id": self.event_id,
                "query": "How did teams integrate OpenAI, RedisVL, and MinIO in their solutions?",
                "document_types": ["transcript", "rubric"],
                "max_results": 5,
                "min_relevance_score": 0.2
            }
        )
        
        if search_result.get("success"):
            results = search_result["results"]
            print(f"Found {len(results)} relevant documents")
            
            for i, result in enumerate(results, 1):
                print(f"\\nResult {i}:")
                print(f"  - Type: {result['document_type']}")
                print(f"  - Relevance: {result['relevance_score']:.3f}")
                print(f"  - Content: {result['content'][:150]}...")
                if result.get('session_id'):
                    print(f"  - Session: {result['session_id']}")
        else:
            print(f"Search failed: {search_result.get('error')}")
        
        return search_result.get("success", False)
    
    async def example_5_pitch_qa(self):
        """
        Example 5: Ask specific questions about pitches.
        
        Demonstrates targeted Q&A functionality for specific
        pitch sessions with comparative context.
        """
        print("\\n=== Example 5: Pitch-Specific Q&A ===")
        
        # Ask specific question about a pitch
        qa_result = await execute_chat_mcp_tool(
            tool_name="chat.ask_about_pitch",
            arguments={
                "session_id": "session_001",
                "event_id": self.event_id,
                "question": "What specific technical innovations did HealthBot demonstrate, and how do they compare to industry standards?",
                "include_comparative_context": True,
                "focus_criteria": ["technical", "tools"],
                "user_id": "judge_001"
            }
        )
        
        if qa_result.get("success"):
            print(f"Question: {qa_result['question']}")
            print(f"Answer: {qa_result['response'][:300]}...")
            print(f"Sources referenced: {len(qa_result.get('sources', []))}")
            print(f"Comparative context included: {qa_result['include_comparative_context']}")
        else:
            print(f"Q&A failed: {qa_result.get('error')}")
        
        return qa_result.get("success", False)
    
    async def example_6_session_comparison(self):
        """
        Example 6: Conversational comparison of multiple sessions.
        
        Creates a comparison conversation that judges can use to
        understand competitive dynamics and create rankings.
        """
        print("\\n=== Example 6: Session Comparison ===")
        
        # Start comparison conversation
        comparison_result = await execute_chat_mcp_tool(
            tool_name="chat.compare_sessions",
            arguments={
                "session_ids": ["session_001", "session_002"],
                "event_id": self.event_id,
                "comparison_focus": ["technical", "tools", "presentation"],
                "conversation_title": "HealthBot vs CloudAgent Comparison",
                "judge_id": "judge_001"
            }
        )
        
        if comparison_result.get("success"):
            print(f"Comparison conversation created: {comparison_result['conversation_id']}")
            print(f"Initial analysis: {comparison_result['initial_analysis'][:250]}...")
            print(f"Sources used: {len(comparison_result.get('sources', []))}")
            
            # You can now continue the conversation with follow-up questions
            print("\\n(Conversation created - judges can now ask follow-up questions)")
        else:
            print(f"Comparison failed: {comparison_result.get('error')}")
        
        return comparison_result.get("success", False)
    
    async def example_7_health_checks(self):
        """
        Example 7: System health checks.
        
        Shows how to verify that all RAG components are working
        properly before important competitions.
        """
        print("\\n=== Example 7: System Health Checks ===")
        
        # Check scoring system health (includes RAG components)
        scoring_health = await execute_scoring_mcp_tool(
            tool_name="analysis.health_check",
            arguments={
                "event_id": self.event_id,
                "detailed_check": True
            }
        )
        
        if scoring_health.get("status") == "healthy":
            print("✓ Scoring system healthy")
            components = scoring_health.get("components", {})
            for component, status in components.items():
                health_status = status.get("status", "unknown")
                print(f"  - {component}: {health_status}")
        else:
            print("✗ Scoring system issues detected")
            print(f"  Error: {scoring_health.get('error', 'Unknown error')}")
        
        # Check chat system health
        chat_health = await execute_chat_mcp_tool(
            tool_name="chat.health_check",
            arguments={
                "event_id": self.event_id,
                "detailed_check": True,
                "test_query": True
            }
        )
        
        if chat_health.get("status") == "healthy":
            print("✓ Chat system healthy")
            components = chat_health.get("components", {})
            for component, status in components.items():
                if isinstance(status, dict):
                    health_status = status.get("status", status.get("healthy", "unknown"))
                else:
                    health_status = status
                print(f"  - {component}: {health_status}")
        else:
            print("✗ Chat system issues detected")
            print(f"  Error: {chat_health.get('error', 'Unknown error')}")
        
        return (
            scoring_health.get("status") == "healthy" and 
            chat_health.get("status") == "healthy"
        )
    
    async def run_all_examples(self):
        """Run all RAG integration examples in sequence."""
        print("🚀 RAG Integration Examples for PitchScoop")
        print(f"Event ID: {self.event_id}")
        
        try:
            # Example 1: Index documents
            indexed = await self.example_1_index_documents()
            if not indexed:
                print("⚠️  Document indexing failed - some examples may not work fully")
            
            # Example 2: RAG conversation
            conversation_id = await self.example_2_create_rag_conversation()
            
            # Example 3: Enhanced scoring
            scoring_success = await self.example_3_enhanced_scoring()
            
            # Example 4: Document search
            search_success = await self.example_4_document_search()
            
            # Example 5: Pitch Q&A
            qa_success = await self.example_5_pitch_qa()
            
            # Example 6: Session comparison
            comparison_success = await self.example_6_session_comparison()
            
            # Example 7: Health checks
            health_success = await self.example_7_health_checks()
            
            # Summary
            print("\\n" + "="*50)
            print("📊 Example Results Summary:")
            print(f"  - Document Indexing: {'✓' if indexed else '✗'}")
            print(f"  - RAG Conversation: {'✓' if conversation_id else '✗'}")
            print(f"  - Enhanced Scoring: {'✓' if scoring_success else '✗'}")
            print(f"  - Document Search: {'✓' if search_success else '✗'}")
            print(f"  - Pitch Q&A: {'✓' if qa_success else '✗'}")
            print(f"  - Session Comparison: {'✓' if comparison_success else '✗'}")
            print(f"  - Health Checks: {'✓' if health_success else '✗'}")
            
            success_count = sum([
                indexed, bool(conversation_id), scoring_success,
                search_success, qa_success, comparison_success, health_success
            ])
            
            print(f"\\n🎯 Overall Success Rate: {success_count}/7 ({success_count/7*100:.1f}%)")
            
            if success_count >= 5:
                print("\n🎉 RAG integration is working well!")
                print("Ready for production use in PitchScoop competitions.")
            elif success_count >= 3:
                print("\\n⚠️  RAG integration partially working.")
                print("Some components may need attention before production use.")
            else:
                print("\\n❌ RAG integration needs troubleshooting.")
                print("Please check system configuration and dependencies.")
                
        except Exception as e:
            print(f"\\n💥 Example execution failed: {str(e)}")
            print("Please check system configuration and try again.")


async def main():
    """Main function to run RAG integration examples."""
    # Use a sample event ID (in practice, this would come from your application)
    event_id = "example_event_2024_01_15"
    
    # Create and run examples
    examples = RAGIntegrationExample(event_id=event_id)
    await examples.run_all_examples()


if __name__ == "__main__":
    asyncio.run(main())
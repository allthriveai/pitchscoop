"""
Test suite for Azure OpenAI Scoring MCP Tools

Tests the complete AI-powered scoring functionality including:
- Session transcript analysis and scoring
- Azure OpenAI integration with multi-tenant isolation
- LangChain structured output parsing
- Tool usage analysis and comparison features
- Error handling and edge cases
- Integration with existing pitch recording workflow

This test suite validates that AI assistants can successfully use the
MCP tools to analyze and score pitch presentations using Azure OpenAI.
"""
import pytest
import asyncio
import json
import base64
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from api.domains.scoring.mcp.scoring_mcp_handler import ScoringMCPHandler
from api.domains.scoring.mcp.scoring_mcp_tools import (
    execute_scoring_mcp_tool,
    get_scoring_tool_schema,
    list_scoring_tools,
    get_scoring_tools_summary,
    SCORING_MCP_TOOLS
)


class TestScoringMCPToolsRegistry:
    """Test scoring MCP tools registry and metadata."""
    
    def test_all_scoring_tools_registered(self):
        """Test that all expected scoring tools are registered."""
        expected_tools = [
            "analysis.score_pitch",
            "analysis.analyze_tools",
            "analysis.compare_pitches",
            "analysis.get_scores",
            "analysis.health_check"
        ]
        
        available_tools = list_scoring_tools()
        
        for tool in expected_tools:
            assert tool in available_tools, f"Tool {tool} not found in registry"
        
        assert len(available_tools) == len(expected_tools)
    
    def test_scoring_tool_schemas_valid(self):
        """Test that all scoring tools have valid schema definitions."""
        for tool_name in SCORING_MCP_TOOLS:
            schema = get_scoring_tool_schema(tool_name)
            
            assert schema is not None, f"No schema for {tool_name}"
            assert "name" in schema
            assert "description" in schema
            assert "inputSchema" in schema
            assert "handler" in schema
            
            # Validate input schema structure
            input_schema = schema["inputSchema"]
            assert "type" in input_schema
            assert input_schema["type"] == "object"
            assert "properties" in input_schema
            assert "required" in input_schema
            
            # Validate event_id is required for most tools
            if tool_name != "analysis.health_check":
                assert "event_id" in schema["inputSchema"]["required"], f"{tool_name} should require event_id"
    
    def test_scoring_tools_summary(self):
        """Test scoring tools summary generation."""
        summary = get_scoring_tools_summary()
        
        assert len(summary) == len(SCORING_MCP_TOOLS)
        
        for tool_name, info in summary.items():
            assert "description" in info
            assert "required_params" in info
            assert "optional_params" in info
            assert isinstance(info["required_params"], list)
            assert isinstance(info["optional_params"], list)


class TestScoringMCPToolExecution:
    """Test scoring MCP tool execution functionality."""
    
    @pytest.fixture
    def mock_scoring_handler(self):
        """Create a mock scoring handler for testing."""
        with patch('domains.scoring.mcp.scoring_mcp_tools.scoring_mcp_handler') as mock:
            # Configure methods to return async-compatible values
            mock.score_complete_pitch = AsyncMock()
            mock.analyze_tool_usage = AsyncMock()
            mock.compare_pitches = AsyncMock()
            mock.get_scoring_results = AsyncMock()
            yield mock
    
    @pytest.fixture
    def sample_session_data(self):
        """Sample session data with transcript for testing."""
        return {
            "session_id": "test-session-123",
            "event_id": "hackathon-2024",
            "team_name": "AI Innovators", 
            "pitch_title": "Revolutionary ML Agent",
            "status": "completed",
            "created_at": "2024-01-01T10:00:00",
            "completed_at": "2024-01-01T10:03:30",
            "final_transcript": {
                "segments_count": 5,
                "total_text": "Hi, I'm presenting our AI agent for document analysis. We use OpenAI for language processing, Qdrant for vector search, and MinIO for storage. Our agent can automatically analyze technical documents and provide quality feedback.",
                "segments": [
                    {"text": "Hi, I'm presenting our AI agent", "timestamp": "00:00"},
                    {"text": "for document analysis", "timestamp": "00:05"},
                    {"text": "We use OpenAI for language processing", "timestamp": "00:10"},
                    {"text": "Qdrant for vector search, and MinIO for storage", "timestamp": "00:15"},
                    {"text": "Our agent provides quality feedback", "timestamp": "00:20"}
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_unknown_scoring_tool_error(self):
        """Test error handling for unknown scoring tools."""
        result = await execute_scoring_mcp_tool("analysis.unknown_tool", {})
        
        assert "error" in result
        assert "Unknown scoring tool" in result["error"]
        assert "available_tools" in result
    
    @pytest.mark.asyncio
    async def test_score_pitch_success(self, mock_scoring_handler):
        """Test successful pitch scoring."""
        # Mock handler response
        mock_scoring_handler.score_complete_pitch.return_value = {
            "session_id": "test-session-123",
            "event_id": "test-org",
            "team_name": "AI Innovators",
            "pitch_title": "Revolutionary ML Agent",
            "scores": {
                "idea_score": 22.5,
                "technical_score": 20.0,
                "tool_use_score": 24.0,
                "presentation_score": 18.5,
                "total_score": 85.0
            },
            "success": True
        }
        
        result = await execute_scoring_mcp_tool("analysis.score_pitch", {
            "session_id": "test-session-123",
            "event_id": "test-org",
            "judge_id": "ai-judge-001"
        })
        
        assert "error" not in result
        assert result["session_id"] == "test-session-123"
        assert result["success"] is True
        assert "scores" in result
        assert result["scores"]["total_score"] == 85.0
        assert "_mcp_metadata" in result
        assert result["_mcp_metadata"]["tool"] == "analysis.score_pitch"
        
        # Verify handler was called with correct arguments
        mock_scoring_handler.score_complete_pitch.assert_called_once_with(
            session_id="test-session-123",
            event_id="test-org",
            judge_id="ai-judge-001"
        )
    
    @pytest.mark.asyncio
    async def test_score_pitch_no_transcript(self, mock_scoring_handler):
        """Test scoring when no transcript is available."""
        mock_scoring_handler.score_complete_pitch.return_value = {
            "error": "No transcript available for scoring",
            "session_id": "test-session-123",
            "event_id": "test-org",
            "status": "recording"
        }
        
        result = await execute_scoring_mcp_tool("analysis.score_pitch", {
            "session_id": "test-session-123",
            "event_id": "test-org"
        })
        
        assert "error" in result
        assert "No transcript available" in result["error"]
        assert result["session_id"] == "test-session-123"
    
    @pytest.mark.asyncio
    async def test_analyze_tools_success(self, mock_scoring_handler):
        """Test successful tool usage analysis."""
        mock_scoring_handler.analyze_tool_usage.return_value = {
            "session_id": "test-session-123",
            "event_id": "test-org",
            "tool_analysis": {
                "tools_identified": ["OpenAI", "Qdrant", "MinIO"],
                "tool_count": 3,
                "meets_requirement": True,
                "agentic_behaviors": ["document analysis", "quality feedback", "vector search"],
                "innovation_level": "high"
            },
            "success": True
        }
        
        result = await execute_scoring_mcp_tool("analysis.analyze_tools", {
            "session_id": "test-session-123",
            "event_id": "test-org",
            "sponsor_tools": ["OpenAI", "Qdrant", "MinIO"]
        })
        
        assert "error" not in result
        assert result["success"] is True
        assert result["tool_analysis"]["tool_count"] == 3
        assert result["tool_analysis"]["meets_requirement"] is True
        assert "_mcp_metadata" in result
        
        # Verify handler was called with correct arguments
        mock_scoring_handler.analyze_tool_usage.assert_called_once_with(
            session_id="test-session-123",
            event_id="test-org",
            sponsor_tools=["OpenAI", "Qdrant", "MinIO"]
        )
    
    @pytest.mark.asyncio
    async def test_compare_pitches_success(self, mock_scoring_handler):
        """Test successful pitch comparison."""
        mock_scoring_handler.compare_pitches.return_value = {
            "session_ids": ["session-1", "session-2"],
            "event_id": "test-org",
            "comparison": {
                "ranking": [
                    {"rank": 1, "session_id": "session-1", "team_name": "Team A", "total_score": 90.0},
                    {"rank": 2, "session_id": "session-2", "team_name": "Team B", "total_score": 85.0}
                ]
            },
            "success": True
        }
        
        result = await execute_scoring_mcp_tool("analysis.compare_pitches", {
            "session_ids": ["session-1", "session-2"],
            "event_id": "test-org"
        })
        
        assert "error" not in result
        assert result["success"] is True
        assert len(result["session_ids"]) == 2
        assert "comparison" in result
        assert "_mcp_metadata" in result
        
        # Verify handler was called with correct arguments
        mock_scoring_handler.compare_pitches.assert_called_once_with(
            session_ids=["session-1", "session-2"],
            event_id="test-org"
        )
    
    @pytest.mark.asyncio
    async def test_get_scores_success(self, mock_scoring_handler):
        """Test successful retrieval of scoring results."""
        mock_scoring_handler.get_scoring_results.return_value = {
            "session_id": "test-session-123",
            "event_id": "test-org",
            "team_name": "AI Innovators",
            "scores": {
                "total_score": 85.0,
                "idea_score": 22.5,
                "technical_score": 20.0
            },
            "has_scoring": True
        }
        
        result = await execute_scoring_mcp_tool("analysis.get_scores", {
            "session_id": "test-session-123",
            "event_id": "test-org",
            "include_details": True
        })
        
        assert "error" not in result
        assert result["session_id"] == "test-session-123"
        assert result["has_scoring"] is True
        assert "scores" in result
        assert "_mcp_metadata" in result
        
        # Verify handler was called with correct arguments
        mock_scoring_handler.get_scoring_results.assert_called_once_with(
            session_id="test-session-123",
            event_id="test-org",
            include_details=True
        )
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        with patch('domains.scoring.mcp.scoring_mcp_tools.get_azure_openai_client') as mock_client_fn:
            mock_client = AsyncMock()
            mock_client.health_check.return_value = {
                "status": "healthy",
                "endpoint": "https://test.openai.azure.com/",
                "deployment": "gpt-4"
            }
            mock_client_fn.return_value = mock_client
            
            result = await execute_scoring_mcp_tool("analysis.health_check", {
                "event_id": "test-org"
            })
            
            assert "error" not in result
            assert result["status"] in ["healthy", "degraded"]
            assert "timestamp" in result
            assert "components" in result
    
    @pytest.mark.asyncio
    async def test_missing_required_params(self):
        """Test error handling for missing required parameters."""
        result = await execute_scoring_mcp_tool("analysis.score_pitch", {
            "event_id": "test-org"
            # Missing session_id
        })
        
        assert "error" in result
        assert "Invalid arguments" in result["error"]
        assert "expected_schema" in result
    
    @pytest.mark.asyncio
    async def test_handler_exception_handling(self, mock_scoring_handler):
        """Test error handling when handler raises exceptions."""
        mock_scoring_handler.score_complete_pitch.side_effect = Exception("Azure OpenAI error")
        
        result = await execute_scoring_mcp_tool("analysis.score_pitch", {
            "session_id": "test-session-123",
            "event_id": "test-org"
        })
        
        assert "error" in result
        assert "Scoring tool execution failed" in result["error"]
        assert "Azure OpenAI error" in result["error"]
        assert result["success"] is False


class TestScoringMCPHandlerIntegration:
    """Integration tests for the scoring MCP handler."""
    
    @pytest.fixture
    def scoring_handler(self):
        """Create a scoring handler instance for testing."""
        return ScoringMCPHandler()
    
    @pytest.fixture
    def mock_redis_with_session(self, sample_session_data):
        """Mock Redis with sample session data."""
        mock_redis = AsyncMock()
        mock_redis.scan_iter.return_value = AsyncIterator([f"event:hackathon-2024:session:{sample_session_data['session_id']}"])
        mock_redis.get.return_value = json.dumps(sample_session_data)
        mock_redis.setex = AsyncMock()
        return mock_redis
    
    @pytest.fixture
    def sample_session_data(self):
        """Sample session data with transcript for testing."""
        return {
            "session_id": "test-session-123",
            "event_id": "hackathon-2024",
            "team_name": "AI Innovators", 
            "pitch_title": "Revolutionary ML Agent",
            "status": "completed",
            "created_at": "2024-01-01T10:00:00",
            "completed_at": "2024-01-01T10:03:30",
            "final_transcript": {
                "segments_count": 5,
                "total_text": "Hi, I'm presenting our AI agent for document analysis. We use OpenAI for language processing, Qdrant for vector search, and MinIO for storage. Our agent can automatically analyze technical documents and provide quality feedback.",
                "segments": []
            }
        }
    
    @pytest.mark.asyncio
    async def test_scoring_handler_redis_connection(self, scoring_handler):
        """Test Redis connection handling in scoring handler."""
        mock_redis_module = MagicMock()
        mock_client = MagicMock()
        mock_redis_module.from_url.return_value = mock_client
        
        with patch('domains.scoring.mcp.scoring_mcp_handler.redis', mock_redis_module):
            redis_client = await scoring_handler.get_redis()
            
            assert redis_client == mock_client
            mock_redis_module.from_url.assert_called_once_with(
                "redis://redis:6379/0",
                decode_responses=True
            )
    
    @pytest.mark.asyncio
    async def test_score_pitch_integration(self, scoring_handler, sample_session_data):
        """Test complete pitch scoring integration."""
        with patch.object(scoring_handler, 'get_redis') as mock_get_redis:
            # Mock Redis operations
            mock_redis = AsyncMock()
            
            # Create an async iterator for scan_iter
            async def mock_scan_iter(match):
                yield f"event:hackathon-2024:session:{sample_session_data['session_id']}"
            
            mock_redis.scan_iter = mock_scan_iter
            mock_redis.get.return_value = json.dumps(sample_session_data)
            mock_redis.setex = AsyncMock()
            mock_get_redis.return_value = mock_redis
            
            # Mock LangChain analysis
            with patch('domains.scoring.mcp.scoring_mcp_handler.get_pitch_analysis_chains') as mock_chains:
                mock_analysis_chains = AsyncMock()
                mock_analysis_chains.score_pitch.return_value = {
                    "success": True,
                    "analysis": {
                        "idea_score": 22.5,
                        "technical_score": 20.0,
                        "tool_use_score": 24.0,
                        "presentation_score": 18.5,
                        "total_score": 85.0
                    }
                }
                mock_chains.return_value = mock_analysis_chains
                
                result = await scoring_handler.score_complete_pitch(
                    session_id="test-session-123",
                    event_id="test-org"
                )
                
                assert result["success"] is True
                assert result["session_id"] == "test-session-123"
                assert result["scores"]["total_score"] == 85.0
                assert result["team_name"] == "AI Innovators"
                
                # Verify Redis storage was called
                mock_redis.setex.assert_called()


class TestScoringWorkflowIntegration:
    """End-to-end workflow tests for scoring integration."""
    
    @pytest.mark.asyncio
    async def test_complete_scoring_workflow(self):
        """Test complete scoring workflow from recording to analysis."""
        with patch('domains.scoring.mcp.scoring_mcp_tools.scoring_mcp_handler') as mock_handler:
            # Configure async mock methods for complete workflow
            mock_handler.score_complete_pitch = AsyncMock(return_value={
                "session_id": "workflow-test-123",
                "event_id": "test-org",
                "success": True,
                "scores": {
                    "total_score": 87.5,
                    "idea_score": 23.0,
                    "technical_score": 21.5,
                    "tool_use_score": 24.0,
                    "presentation_score": 19.0
                }
            })
            
            mock_handler.analyze_tool_usage = AsyncMock(return_value={
                "session_id": "workflow-test-123",
                "success": True,
                "tool_analysis": {
                    "tools_identified": ["OpenAI", "Qdrant", "MinIO"],
                    "tool_count": 3,
                    "meets_requirement": True
                }
            })
            
            mock_handler.get_scoring_results = AsyncMock(return_value={
                "session_id": "workflow-test-123",
                "has_scoring": True,
                "scores": {"total_score": 87.5}
            })
            
            # 1. Score the pitch
            score_result = await execute_scoring_mcp_tool("analysis.score_pitch", {
                "session_id": "workflow-test-123",
                "event_id": "test-org",
                "judge_id": "ai-judge-001"
            })
            
            assert "error" not in score_result
            assert score_result["success"] is True
            session_id = score_result["session_id"]
            
            # 2. Analyze tool usage
            tool_result = await execute_scoring_mcp_tool("analysis.analyze_tools", {
                "session_id": session_id,
                "event_id": "test-org"
            })
            
            assert "error" not in tool_result
            assert tool_result["success"] is True
            assert tool_result["tool_analysis"]["meets_requirement"] is True
            
            # 3. Get complete results
            results = await execute_scoring_mcp_tool("analysis.get_scores", {
                "session_id": session_id,
                "event_id": "test-org",
                "include_details": True
            })
            
            assert "error" not in results
            assert results["has_scoring"] is True
            
            # Verify all handlers were called
            mock_handler.score_complete_pitch.assert_called_once()
            mock_handler.analyze_tool_usage.assert_called_once()
            mock_handler.get_scoring_results.assert_called_once()


# Helper class for async iteration in mocks
class AsyncIterator:
    def __init__(self, items):
        self.items = iter(items)
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        try:
            return next(self.items)
        except StopIteration:
            raise StopAsyncIteration


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
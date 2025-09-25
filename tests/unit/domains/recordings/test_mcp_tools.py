"""
Test suite for Gladia MCP Tools

Tests the complete MCP tool functionality including:
- Session lifecycle (start/stop recording)
- Redis caching and session management
- MinIO audio storage integration
- Playback URL generation
- Error handling and edge cases

This test suite validates that AI assistants can successfully use the
MCP tools to manage pitch recording sessions.
"""
import pytest
import asyncio
import json
import base64
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from api.domains.recordings.mcp.mcp_tools import (
    execute_mcp_tool, 
    get_tool_schema,
    list_available_tools,
    get_tools_summary,
    MCP_TOOLS
)
from api.domains.recordings.mcp.gladia_mcp_handler import GladiaMCPHandler


class TestMCPToolsRegistry:
    """Test MCP tools registry and metadata."""
    
    def test_all_tools_registered(self):
        """Test that all expected tools are registered."""
        expected_tools = [
            "pitches.start_recording",
            "pitches.stop_recording", 
            "pitches.get_session",
            "pitches.get_playback_url",
            "pitches.list_sessions",
            "pitches.delete_session",
            "pitches.get_audio_intelligence"
        ]
        
        available_tools = list_available_tools()
        
        for tool in expected_tools:
            assert tool in available_tools, f"Tool {tool} not found in registry"
        
        assert len(available_tools) == len(expected_tools)
    
    def test_tool_schemas_valid(self):
        """Test that all tools have valid schema definitions."""
        for tool_name in MCP_TOOLS:
            schema = get_tool_schema(tool_name)
            
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
    
    def test_tools_summary(self):
        """Test tools summary generation."""
        summary = get_tools_summary()
        
        assert len(summary) == len(MCP_TOOLS)
        
        for tool_name, info in summary.items():
            assert "description" in info
            assert "required_params" in info
            assert "optional_params" in info
            assert isinstance(info["required_params"], list)
            assert isinstance(info["optional_params"], list)


class TestMCPToolExecution:
    """Test MCP tool execution functionality."""
    
    @pytest.fixture
    def mock_handler(self):
        """Create a mock handler for testing."""
        with patch('domains.recordings.mcp.mcp_tools.gladia_mcp_handler') as mock:
            # Configure methods to return async-compatible values
            mock.start_pitch_recording = AsyncMock()
            mock.stop_pitch_recording = AsyncMock()
            mock.get_session_details = AsyncMock()
            mock.get_playback_url = AsyncMock()
            mock.list_sessions = AsyncMock()
            mock.delete_session = AsyncMock()
            yield mock
    
    @pytest.mark.asyncio
    async def test_unknown_tool_error(self):
        """Test error handling for unknown tools."""
        result = await execute_mcp_tool("unknown.tool", {})
        
        assert "error" in result
        assert "Unknown tool" in result["error"]
        assert "available_tools" in result
    
    @pytest.mark.asyncio
    async def test_start_recording_success(self, mock_handler):
        """Test successful recording start."""
        # Mock handler response
        mock_handler.start_pitch_recording.return_value = {
            "session_id": "test-session-123",
            "team_name": "Test Team",
            "pitch_title": "Test Pitch",
            "status": "ready_to_record",
            "websocket_url": "wss://api.gladia.io/v2/live/test",
            "gladia_session_id": "gladia-123"
        }
        
        result = await execute_mcp_tool("pitches.start_recording", {
            "team_name": "Test Team",
            "pitch_title": "Test Pitch"
        })
        
        assert "error" not in result
        assert result["session_id"] == "test-session-123"
        assert result["status"] == "ready_to_record"
        assert "websocket_url" in result
        assert "_mcp_metadata" in result
        assert result["_mcp_metadata"]["tool"] == "pitches.start_recording"
        
        # Verify handler was called with correct arguments
        mock_handler.start_pitch_recording.assert_called_once_with(
            team_name="Test Team",
            pitch_title="Test Pitch"
        )
    
    @pytest.mark.asyncio
    async def test_start_recording_missing_required_param(self):
        """Test error handling for missing required parameters."""
        with patch('domains.recordings.mcp.mcp_tools.gladia_mcp_handler') as mock_handler:
            mock_handler.start_pitch_recording.side_effect = TypeError("missing required argument")
            
            result = await execute_mcp_tool("pitches.start_recording", {
                "team_name": "Test Team"
                # Missing pitch_title
            })
            
            assert "error" in result
            assert "Invalid arguments" in result["error"]
            assert "expected_schema" in result
    
    @pytest.mark.asyncio
    async def test_stop_recording_success(self, mock_handler):
        """Test successful recording stop."""
        mock_handler.stop_pitch_recording.return_value = {
            "session_id": "test-session-123",
            "status": "completed",
            "transcript": {"segments_count": 5, "total_text": "Test transcript"},
            "audio": {"has_audio": True, "playback_url": "https://minio/test.wav"}
        }
        
        result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": "test-session-123"
        })
        
        assert "error" not in result
        assert result["session_id"] == "test-session-123"
        assert result["status"] == "completed"
        assert "transcript" in result
        assert "_mcp_metadata" in result
    
    @pytest.mark.asyncio
    async def test_stop_recording_with_audio_data(self, mock_handler):
        """Test stop recording with base64 audio data."""
        mock_handler.stop_pitch_recording.return_value = {
            "session_id": "test-session-123",
            "status": "completed"
        }
        
        # Create test audio data
        test_audio = b"fake audio data"
        audio_b64 = base64.b64encode(test_audio).decode('utf-8')
        
        result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": "test-session-123",
            "audio_data_base64": audio_b64
        })
        
        assert "error" not in result
        
        # Verify handler was called with decoded audio data
        mock_handler.stop_pitch_recording.assert_called_once_with(
            session_id="test-session-123",
            audio_data=test_audio
        )
    
    @pytest.mark.asyncio
    async def test_stop_recording_invalid_base64(self, mock_handler):
        """Test error handling for invalid base64 audio data."""
        result = await execute_mcp_tool("pitches.stop_recording", {
            "session_id": "test-session-123",
            "audio_data_base64": "invalid-base64!@#"
        })
        
        assert "error" in result
        assert "Invalid base64 audio data" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, mock_handler):
        """Test successful session retrieval."""
        mock_handler.get_session_details.return_value = {
            "session_id": "test-session-123",
            "team_name": "Test Team",
            "pitch_title": "Test Pitch",
            "status": "completed",
            "has_audio": True,
            "current_playback_url": "https://minio/test.wav"
        }
        
        result = await execute_mcp_tool("pitches.get_session", {
            "session_id": "test-session-123"
        })
        
        assert "error" not in result
        assert result["session_id"] == "test-session-123"
        assert "current_playback_url" in result
    
    @pytest.mark.asyncio
    async def test_get_playback_url_success(self, mock_handler):
        """Test successful playback URL generation."""
        mock_handler.get_playback_url.return_value = {
            "session_id": "test-session-123",
            "playback_url": "https://minio/test.wav?expires=3600",
            "expires_in_seconds": 3600
        }
        
        result = await execute_mcp_tool("pitches.get_playback_url", {
            "session_id": "test-session-123",
            "expires_hours": 1
        })
        
        assert "error" not in result
        assert "playback_url" in result
        assert result["expires_in_seconds"] == 3600
    
    @pytest.mark.asyncio
    async def test_list_sessions_success(self, mock_handler):
        """Test successful session listing."""
        mock_handler.list_sessions.return_value = {
            "sessions": [
                {
                    "session_id": "session-1",
                    "team_name": "Team A",
                    "status": "completed"
                },
                {
                    "session_id": "session-2", 
                    "team_name": "Team B",
                    "status": "ready_to_record"
                }
            ],
            "total_count": 2
        }
        
        result = await execute_mcp_tool("pitches.list_sessions", {})
        
        assert "error" not in result
        assert "sessions" in result
        assert result["total_count"] == 2
        assert len(result["sessions"]) == 2
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_filters(self, mock_handler):
        """Test session listing with filters."""
        mock_handler.list_sessions.return_value = {
            "sessions": [{"session_id": "session-1", "team_name": "Team A"}],
            "total_count": 1
        }
        
        result = await execute_mcp_tool("pitches.list_sessions", {
            "team_name": "Team A",
            "status": "completed"
        })
        
        assert "error" not in result
        
        # Verify filters were passed to handler
        mock_handler.list_sessions.assert_called_once_with(
            team_name="Team A",
            status="completed"
        )
    
    @pytest.mark.asyncio
    async def test_delete_session_success(self, mock_handler):
        """Test successful session deletion."""
        mock_handler.delete_session.return_value = {
            "session_id": "test-session-123",
            "deleted": True,
            "redis_deleted": True,
            "audio_deleted": True
        }
        
        result = await execute_mcp_tool("pitches.delete_session", {
            "session_id": "test-session-123"
        })
        
        assert "error" not in result
        assert result["deleted"] is True
    
    @pytest.mark.asyncio
    async def test_handler_exception_handling(self, mock_handler):
        """Test error handling when handler raises exceptions."""
        mock_handler.start_pitch_recording.side_effect = Exception("Handler error")
        
        result = await execute_mcp_tool("pitches.start_recording", {
            "team_name": "Test Team",
            "pitch_title": "Test Pitch"
        })
        
        assert "error" in result
        assert "Tool execution failed" in result["error"]
        assert "Handler error" in result["error"]
        assert result["success"] is False


class TestMCPHandlerIntegration:
    """Integration tests for the MCP handler."""
    
    @pytest.fixture
    def handler(self):
        """Create a handler instance for testing."""
        return GladiaMCPHandler()
    
    @pytest.mark.asyncio
    async def test_handler_redis_connection(self, handler):
        """Test Redis connection handling."""
        # The module imports redis.asyncio as redis, so we need to mock the whole module
        mock_redis_module = MagicMock()
        mock_client = MagicMock()  # Regular mock, not AsyncMock since Redis client operations are async but creation is not
        mock_redis_module.from_url.return_value = mock_client
        
        with patch('domains.recordings.mcp.gladia_mcp_handler.redis', mock_redis_module):
            with patch('domains.recordings.mcp.gladia_mcp_handler.os.getenv') as mock_getenv:
                # Mock the environment to return test Redis URL
                mock_getenv.return_value = "redis://test:6379/0"
                
                redis_client = await handler.get_redis()
                
                assert redis_client == mock_client
                mock_redis_module.from_url.assert_called_once_with(
                    "redis://test:6379/0",
                    decode_responses=True
                )
            
            # Test client reuse
            redis_client2 = await handler.get_redis()
            assert redis_client2 == redis_client
            assert mock_redis_module.from_url.call_count == 1  # Should not create new client
    
    @pytest.mark.asyncio
    async def test_session_duration_calculation(self, handler):
        """Test session duration calculation."""
        # Test completed session
        session_data = {
            "created_at": "2024-01-01T10:00:00",
            "completed_at": "2024-01-01T10:05:30"
        }
        
        duration = handler._calculate_session_duration(session_data)
        assert duration == 330.0  # 5 minutes 30 seconds
        
        # Test with recording ended but not completed
        session_data = {
            "created_at": "2024-01-01T10:00:00",
            "recording_ended_at": "2024-01-01T10:03:15"
        }
        
        duration = handler._calculate_session_duration(session_data)
        assert duration == 195.0  # 3 minutes 15 seconds
        
        # Test invalid data
        session_data = {"created_at": "invalid-date"}
        duration = handler._calculate_session_duration(session_data)
        assert duration is None


class TestMCPWorkflowIntegration:
    """End-to-end workflow tests."""
    
    @pytest.mark.asyncio
    async def test_complete_recording_workflow(self):
        """Test complete recording workflow from start to finish."""
        with patch('domains.recordings.mcp.mcp_tools.gladia_mcp_handler') as mock_handler:
            # Configure async mock methods
            mock_handler.start_pitch_recording = AsyncMock(return_value={
                "session_id": "workflow-test-123",
                "status": "ready_to_record",
                "websocket_url": "wss://test.com"
            })
            
            mock_handler.stop_pitch_recording = AsyncMock(return_value={
                "session_id": "workflow-test-123",
                "status": "completed",
                "transcript": {"segments_count": 3}
            })
            
            mock_handler.get_session_details = AsyncMock(return_value={
                "session_id": "workflow-test-123",
                "status": "completed",
                "has_audio": True
            })
            
            mock_handler.get_playback_url = AsyncMock(return_value={
                "session_id": "workflow-test-123",
                "playback_url": "https://test.wav"
            })
            
            # 1. Start recording
            start_result = await execute_mcp_tool("pitches.start_recording", {
                "team_name": "Workflow Test Team",
                "pitch_title": "Integration Test Pitch"
            })
            
            assert "error" not in start_result
            session_id = start_result["session_id"]
            
            # 2. Stop recording
            stop_result = await execute_mcp_tool("pitches.stop_recording", {
                "session_id": session_id
            })
            
            assert "error" not in stop_result
            assert stop_result["status"] == "completed"
            
            # 3. Get session details
            details_result = await execute_mcp_tool("pitches.get_session", {
                "session_id": session_id
            })
            
            assert "error" not in details_result
            assert details_result["has_audio"] is True
            
            # 4. Get playback URL
            url_result = await execute_mcp_tool("pitches.get_playback_url", {
                "session_id": session_id
            })
            
            assert "error" not in url_result
            assert "playback_url" in url_result
            
            # Verify all handlers were called
            mock_handler.start_pitch_recording.assert_called_once()
            mock_handler.stop_pitch_recording.assert_called_once()
            mock_handler.get_session_details.assert_called_once()
            mock_handler.get_playback_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_with_error_recovery(self):
        """Test workflow error handling and recovery."""
        with patch('domains.recordings.mcp.mcp_tools.gladia_mcp_handler') as mock_handler:
            # Configure async mock methods
            mock_handler.start_pitch_recording = AsyncMock(return_value={
                "session_id": "error-test-123",
                "status": "ready_to_record"
            })
            
            # Mock stop to fail
            mock_handler.stop_pitch_recording = AsyncMock(return_value={
                "error": "Failed to stop recording",
                "session_id": "error-test-123"
            })
            
            # Start recording successfully
            start_result = await execute_mcp_tool("pitches.start_recording", {
                "team_name": "Error Test Team", 
                "pitch_title": "Error Test Pitch"
            })
            
            assert "error" not in start_result
            session_id = start_result["session_id"]
            
            # Stop recording fails
            stop_result = await execute_mcp_tool("pitches.stop_recording", {
                "session_id": session_id
            })
            
            assert "error" in stop_result
            assert stop_result["session_id"] == session_id
            
            # Can still attempt to get session details
            mock_handler.get_session_details = AsyncMock(return_value={
                "session_id": session_id,
                "status": "error",
                "error": "Recording failed to stop properly"
            })
            
            details_result = await execute_mcp_tool("pitches.get_session", {
                "session_id": session_id
            })
            
            # The tool executed successfully, but the session itself has an error status
            # This is different from a tool execution error
            assert details_result["status"] == "error"
            assert "error" in details_result  # The session data contains error info
            assert details_result["error"] == "Recording failed to stop properly"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
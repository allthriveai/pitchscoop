#!/usr/bin/env python3
"""
MCP Tools for Recording Progression Analysis

Provides MCP tools for tracking and analyzing recording progression over time
using Domain-Driven Design principles within the recordings domain.
"""
import asyncio
import json
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent

from ..services.recording_progression_service import RecordingProgressionService
from ..infrastructure.redis_recording_version_repository import RedisRecordingVersionRepository
from ..value_objects.team_id import TeamId
from ..value_objects.recording_version_id import RecordingVersionId
from ...shared.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RecordingProgressionMCPTools:
    """MCP tools for recording progression analysis."""
    
    def __init__(self, server: Server, event_id: str = ""):
        self.server = server
        self.event_id = event_id
        self.service: Optional[RecordingProgressionService] = None
        logger.info(f"📊 Initializing Recording Progression MCP Tools for event {event_id}")
    
    async def initialize(self):
        """Initialize the progression service and dependencies."""
        try:
            # Create repository and service
            repository = RedisRecordingVersionRepository()
            await repository.initialize()
            
            self.service = RecordingProgressionService(repository)
            logger.info("✅ Recording progression service initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize recording progression service: {str(e)}")
            raise
    
    def register_tools(self):
        """Register all recording progression tools with the MCP server."""
        logger.info("🔧 Registering recording progression tools...")
        
        @self.server.list_tools()
        async def handle_list_tools():
            return [
                Tool(
                    name="add_recording_version",
                    description="Add a new recording version for a team to track progression",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "team_id": {
                                "type": "string",
                                "description": "Unique identifier for the team"
                            },
                            "team_name": {
                                "type": "string", 
                                "description": "Display name of the team"
                            },
                            "recording_title": {
                                "type": "string",
                                "description": "Title of the recording"
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Session identifier for this recording"
                            },
                            "transcript_text": {
                                "type": "string",
                                "description": "Final transcript text of the recording"
                            },
                            "duration_seconds": {
                                "type": "number",
                                "description": "Duration of the recording in seconds"
                            },
                            "scores": {
                                "type": "object",
                                "description": "Optional scoring data for this version",
                                "properties": {
                                    "idea_score": {"type": "number"},
                                    "technical_score": {"type": "number"},
                                    "presentation_score": {"type": "number"},
                                    "tool_use_score": {"type": "number"},
                                    "total_score": {"type": "number"}
                                }
                            }
                        },
                        "required": ["team_id", "team_name", "recording_title", "session_id", "transcript_text"]
                    }
                ),
                Tool(
                    name="analyze_team_progression",
                    description="Analyze how a team's recordings have evolved over time",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "team_id": {
                                "type": "string",
                                "description": "Team identifier to analyze"
                            }
                        },
                        "required": ["team_id"]
                    }
                ),
                Tool(
                    name="get_progression_insights",
                    description="Get AI-powered insights about a team's recording progression",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "team_id": {
                                "type": "string",
                                "description": "Team identifier to get insights for"
                            }
                        },
                        "required": ["team_id"]
                    }
                ),
                Tool(
                    name="compare_recording_versions",
                    description="Compare two specific recording versions in detail",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "version_1_id": {
                                "type": "string",
                                "description": "First version ID to compare"
                            },
                            "version_2_id": {
                                "type": "string", 
                                "description": "Second version ID to compare"
                            }
                        },
                        "required": ["version_1_id", "version_2_id"]
                    }
                ),
                Tool(
                    name="get_team_recordings",
                    description="Get all recording versions for a team",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "team_id": {
                                "type": "string",
                                "description": "Team identifier to get recordings for"
                            }
                        },
                        "required": ["team_id"]
                    }
                ),
                Tool(
                    name="semantic_search_recordings",
                    description="Search recordings using semantic similarity",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for semantic similarity"
                            },
                            "team_id": {
                                "type": "string",
                                "description": "Optional team ID to filter results"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 10)",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            """Handle tool calls."""
            if not self.service:
                await self.initialize()
            
            try:
                logger.info(f"🔧 Processing tool: {name} with event_id: {self.event_id}")
                
                if name == "add_recording_version":
                    return await self._handle_add_recording_version(arguments)
                elif name == "analyze_team_progression":
                    return await self._handle_analyze_team_progression(arguments)
                elif name == "get_progression_insights":
                    return await self._handle_get_progression_insights(arguments)
                elif name == "compare_recording_versions":
                    return await self._handle_compare_recording_versions(arguments)
                elif name == "get_team_recordings":
                    return await self._handle_get_team_recordings(arguments)
                elif name == "semantic_search_recordings":
                    return await self._handle_semantic_search_recordings(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Unknown tool: {name}",
                            "available_tools": ["add_recording_version", "analyze_team_progression", 
                                              "get_progression_insights", "compare_recording_versions",
                                              "get_team_recordings", "semantic_search_recordings"]
                        }, indent=2)
                    )]
            
            except Exception as e:
                error_msg = f"Error processing tool {name}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                logger.error(traceback.format_exc())
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": error_msg,
                        "tool": name,
                        "event_id": self.event_id,
                        "traceback": traceback.format_exc()
                    }, indent=2)
                )]
    
    async def _handle_add_recording_version(self, arguments: dict) -> List[TextContent]:
        """Handle adding a new recording version."""
        logger.info(f"📝 Adding recording version for team {arguments.get('team_id')}")
        
        try:
            # For this simplified version, we'll create a minimal recording version
            # In a full implementation, this would integrate with STTSession
            
            result = {
                "success": True,
                "message": "Recording version functionality ready - integration with STTSession needed",
                "team_id": arguments["team_id"],
                "team_name": arguments["team_name"],
                "recording_title": arguments["recording_title"],
                "transcript_length": len(arguments.get("transcript_text", "")),
                "event_id": self.event_id,
                "note": "This is a stub implementation - full integration requires STTSession entity"
            }
            
            logger.info(f"✅ Recording version stub created for {arguments['team_name']}")
            
            return [TextContent(
                type="text", 
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"❌ Failed to add recording version: {str(e)}")
            raise
    
    async def _handle_analyze_team_progression(self, arguments: dict) -> List[TextContent]:
        """Handle analyzing team progression."""
        team_id = TeamId.from_string(arguments["team_id"])
        logger.info(f"📊 Analyzing progression for team {team_id}")
        
        try:
            analysis = await self.service.analyze_team_progression(team_id)
            
            # Add event context
            analysis["event_id"] = self.event_id
            analysis["analysis_timestamp"] = datetime.utcnow().isoformat()
            
            logger.info(f"✅ Completed progression analysis for team {team_id}")
            
            return [TextContent(
                type="text",
                text=json.dumps(analysis, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze team progression: {str(e)}")
            raise
    
    async def _handle_get_progression_insights(self, arguments: dict) -> List[TextContent]:
        """Handle getting progression insights."""
        team_id = TeamId.from_string(arguments["team_id"])
        logger.info(f"💡 Getting progression insights for team {team_id}")
        
        try:
            insights = await self.service.get_progression_insights(team_id)
            
            # Add event context
            insights["event_id"] = self.event_id
            
            logger.info(f"✅ Generated progression insights for team {team_id}")
            
            return [TextContent(
                type="text",
                text=json.dumps(insights, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"❌ Failed to get progression insights: {str(e)}")
            raise
    
    async def _handle_compare_recording_versions(self, arguments: dict) -> List[TextContent]:
        """Handle comparing recording versions."""
        version_1_id = RecordingVersionId.from_string(arguments["version_1_id"])
        version_2_id = RecordingVersionId.from_string(arguments["version_2_id"])
        logger.info(f"🔍 Comparing versions {version_1_id} vs {version_2_id}")
        
        try:
            comparison = await self.service.compare_versions(version_1_id, version_2_id)
            
            # Add event context
            comparison["event_id"] = self.event_id
            comparison["comparison_timestamp"] = datetime.utcnow().isoformat()
            
            logger.info(f"✅ Completed version comparison")
            
            return [TextContent(
                type="text",
                text=json.dumps(comparison, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"❌ Failed to compare versions: {str(e)}")
            raise
    
    async def _handle_get_team_recordings(self, arguments: dict) -> List[TextContent]:
        """Handle getting all recordings for a team."""
        team_id = TeamId.from_string(arguments["team_id"])
        logger.info(f"📋 Getting all recordings for team {team_id}")
        
        try:
            versions = await self.service.get_team_progression(team_id)
            
            result = {
                "team_id": str(team_id),
                "version_count": len(versions),
                "event_id": self.event_id,
                "versions": [
                    {
                        "version_id": str(v.version_id),
                        "version_number": v.version_number,
                        "recording_title": v.recording_title,
                        "created_at": v.created_at.isoformat(),
                        "word_count": v.word_count,
                        "duration_seconds": v.duration_seconds,
                        "has_scores": v.has_scores,
                        "has_audio_intelligence": v.has_audio_intelligence
                    }
                    for v in versions
                ]
            }
            
            if versions:
                result["team_name"] = versions[0].team_name
            
            logger.info(f"✅ Retrieved {len(versions)} recordings for team {team_id}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"❌ Failed to get team recordings: {str(e)}")
            raise
    
    async def _handle_semantic_search_recordings(self, arguments: dict) -> List[TextContent]:
        """Handle semantic search of recordings."""
        query = arguments["query"]
        team_id = TeamId.from_string(arguments["team_id"]) if arguments.get("team_id") else None
        limit = arguments.get("limit", 10)
        
        logger.info(f"🔍 Semantic search: '{query}' (team: {team_id}, limit: {limit})")
        
        try:
            # Get repository from service to perform semantic search
            versions = await self.service.repository.semantic_search(query, team_id, limit)
            
            result = {
                "query": query,
                "team_id": str(team_id) if team_id else None,
                "results_count": len(versions),
                "event_id": self.event_id,
                "results": [
                    {
                        "version_id": str(v.version_id),
                        "team_name": v.team_name,
                        "recording_title": v.recording_title,
                        "version_number": v.version_number,
                        "created_at": v.created_at.isoformat(),
                        "word_count": v.word_count,
                        "transcript_preview": v.final_transcript_text[:200] + "..." if len(v.final_transcript_text) > 200 else v.final_transcript_text
                    }
                    for v in versions
                ]
            }
            
            logger.info(f"✅ Semantic search returned {len(versions)} results")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"❌ Failed semantic search: {str(e)}")
            raise
    
    async def cleanup(self):
        """Clean up resources."""
        if self.service and hasattr(self.service, 'repository'):
            await self.service.repository.cleanup()


# Factory function for creating MCP tools
async def create_recording_progression_mcp_tools(server: Server, event_id: str = "") -> RecordingProgressionMCPTools:
    """Create and initialize recording progression MCP tools."""
    tools = RecordingProgressionMCPTools(server, event_id)
    await tools.initialize()
    tools.register_tools()
    return tools
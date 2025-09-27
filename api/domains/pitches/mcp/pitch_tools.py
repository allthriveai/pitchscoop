"""
MCP Tools for Pitch Video Analysis

Clean MCP tools implementation for pitch presentation analysis using Hume AI.
Provides video analysis, coaching feedback, and scoring capabilities.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
import base64
import json

from ..services.pitch_analysis_service import PitchAnalysisService
from ..entities.pitch_session import PitchSession

logger = logging.getLogger(__name__)


class PitchMCPTools:
    """MCP tools for pitch video analysis."""
    
    def __init__(self):
        """Initialize pitch MCP tools."""
        self.analysis_service = PitchAnalysisService()
        self.active_sessions: Dict[str, PitchSession] = {}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of pitch analysis system.
        
        Returns:
            Health status of pitch analysis services
        """
        try:
            service_health = await self.analysis_service.health_check()
            
            return {
                "tool": "pitch_health_check",
                "status": "success",
                "system_health": service_health,
                "active_sessions": len(self.active_sessions),
                "capabilities": [
                    "video_emotion_analysis",
                    "presentation_scoring", 
                    "coaching_feedback",
                    "pitch_category_insights"
                ]
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "tool": "pitch_health_check",
                "status": "error",
                "error": str(e)
            }
    
    async def create_pitch_session(
        self,
        user_id: str,
        title: str,
        pitch_category: Optional[str] = None,
        target_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new pitch presentation session.
        
        Args:
            user_id: ID of the user creating the pitch
            title: Title of the pitch presentation
            pitch_category: Category (investor_pitch, sales_pitch, elevator_pitch)
            target_duration: Expected duration in seconds
            
        Returns:
            Created pitch session details
        """
        try:
            # Validate pitch category
            valid_categories = ["investor_pitch", "sales_pitch", "elevator_pitch"]
            if pitch_category and pitch_category not in valid_categories:
                return {
                    "tool": "create_pitch_session",
                    "status": "error",
                    "error": f"Invalid pitch category. Must be one of: {valid_categories}"
                }
            
            # Create pitch session
            pitch_session = await self.analysis_service.create_pitch_session(
                user_id=user_id,
                title=title,
                pitch_category=pitch_category,
                target_duration_seconds=target_duration
            )
            
            # Store in active sessions
            self.active_sessions[pitch_session.session_id] = pitch_session
            
            logger.info(f"Created pitch session {pitch_session.session_id}")
            
            return {
                "tool": "create_pitch_session",
                "status": "success",
                "session": pitch_session.to_dict(),
                "message": f"Created pitch session: {title}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create pitch session: {str(e)}")
            return {
                "tool": "create_pitch_session",
                "status": "error",
                "error": str(e)
            }
    
    async def analyze_pitch_video(
        self,
        session_id: str,
        video_data_b64: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a pitch video using Hume AI emotion detection.
        
        Args:
            session_id: ID of the pitch session
            video_data_b64: Base64 encoded video file data
            filename: Optional filename for the video
            
        Returns:
            Video analysis results with coaching feedback
        """
        try:
            # Get pitch session
            if session_id not in self.active_sessions:
                return {
                    "tool": "analyze_pitch_video",
                    "status": "error", 
                    "error": f"Pitch session not found: {session_id}"
                }
            
            pitch_session = self.active_sessions[session_id]
            
            # Decode video data
            try:
                video_data = base64.b64decode(video_data_b64)
            except Exception as e:
                return {
                    "tool": "analyze_pitch_video",
                    "status": "error",
                    "error": f"Invalid base64 video data: {str(e)}"
                }
            
            logger.info(f"Starting video analysis for session {session_id}")
            
            # Analyze video
            updated_session = await self.analysis_service.analyze_pitch_video(
                pitch_session=pitch_session,
                video_data=video_data,
                filename=filename
            )
            
            # Update stored session
            self.active_sessions[session_id] = updated_session
            
            if updated_session.analysis_status == "failed":
                return {
                    "tool": "analyze_pitch_video", 
                    "status": "error",
                    "error": "Video analysis failed",
                    "session_id": session_id
                }
            
            # Get results
            result = {
                "tool": "analyze_pitch_video",
                "status": "success",
                "session_id": session_id,
                "analysis_status": updated_session.analysis_status,
                "presentation_score": updated_session.get_presentation_score(),
            }
            
            # Include detailed results if analysis is complete
            if updated_session.is_analysis_complete():
                result["emotional_summary"] = updated_session.get_emotional_summary()
                result["coaching_feedback"] = updated_session.get_coaching_feedback()
                
                logger.info(f"Completed video analysis for session {session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze video for session {session_id}: {str(e)}")
            return {
                "tool": "analyze_pitch_video",
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    async def get_coaching_insights(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed coaching insights for a pitch session.
        
        Args:
            session_id: ID of the analyzed pitch session
            
        Returns:
            Detailed coaching insights and recommendations
        """
        try:
            if session_id not in self.active_sessions:
                return {
                    "tool": "get_coaching_insights",
                    "status": "error",
                    "error": f"Pitch session not found: {session_id}"
                }
            
            pitch_session = self.active_sessions[session_id]
            
            if not pitch_session.is_analysis_complete():
                return {
                    "tool": "get_coaching_insights", 
                    "status": "error",
                    "error": "Analysis not complete for this session",
                    "session_id": session_id,
                    "current_status": pitch_session.analysis_status
                }
            
            # Get coaching insights
            insights = await self.analysis_service.get_coaching_insights(pitch_session)
            score_breakdown = await self.analysis_service.get_pitch_score_breakdown(pitch_session)
            
            return {
                "tool": "get_coaching_insights",
                "status": "success",
                "session_id": session_id,
                "insights": insights,
                "score_breakdown": score_breakdown,
                "session_info": {
                    "title": pitch_session.title,
                    "category": pitch_session.pitch_category,
                    "duration": pitch_session.actual_duration_seconds
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get coaching insights for {session_id}: {str(e)}")
            return {
                "tool": "get_coaching_insights",
                "status": "error", 
                "error": str(e),
                "session_id": session_id
            }
    
    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get status and basic info for a pitch session.
        
        Args:
            session_id: ID of the pitch session
            
        Returns:
            Session status and basic information
        """
        try:
            if session_id not in self.active_sessions:
                return {
                    "tool": "get_session_status",
                    "status": "error",
                    "error": f"Pitch session not found: {session_id}"
                }
            
            pitch_session = self.active_sessions[session_id]
            
            return {
                "tool": "get_session_status",
                "status": "success",
                "session": pitch_session.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to get session status for {session_id}: {str(e)}")
            return {
                "tool": "get_session_status",
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    async def list_active_sessions(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List active pitch sessions, optionally filtered by user.
        
        Args:
            user_id: Optional user ID to filter sessions
            
        Returns:
            List of active pitch sessions
        """
        try:
            sessions = []
            
            for session_id, pitch_session in self.active_sessions.items():
                # Filter by user if specified
                if user_id and pitch_session.user_id != user_id:
                    continue
                
                # Add basic session info
                sessions.append({
                    "session_id": session_id,
                    "title": pitch_session.title,
                    "user_id": pitch_session.user_id,
                    "status": pitch_session.analysis_status,
                    "category": pitch_session.pitch_category,
                    "score": pitch_session.get_presentation_score(),
                    "created_at": pitch_session.created_at.isoformat() if pitch_session.created_at else None
                })
            
            return {
                "tool": "list_active_sessions",
                "status": "success", 
                "sessions": sessions,
                "total_count": len(sessions),
                "filter_user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Failed to list active sessions: {str(e)}")
            return {
                "tool": "list_active_sessions",
                "status": "error",
                "error": str(e)
            }
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get MCP tool definitions for pitch analysis."""
        return [
            {
                "name": "pitch_health_check",
                "description": "Check health status of pitch analysis system",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "create_pitch_session",
                "description": "Create a new pitch presentation session for analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID creating the pitch session"
                        },
                        "title": {
                            "type": "string", 
                            "description": "Title of the pitch presentation"
                        },
                        "pitch_category": {
                            "type": "string",
                            "description": "Category of pitch (investor_pitch, sales_pitch, elevator_pitch)",
                            "enum": ["investor_pitch", "sales_pitch", "elevator_pitch"]
                        },
                        "target_duration": {
                            "type": "integer",
                            "description": "Expected duration in seconds"
                        }
                    },
                    "required": ["user_id", "title"]
                }
            },
            {
                "name": "analyze_pitch_video",
                "description": "Analyze pitch video using Hume AI emotion detection",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "ID of the pitch session"
                        },
                        "video_data_b64": {
                            "type": "string",
                            "description": "Base64 encoded video file data"
                        },
                        "filename": {
                            "type": "string",
                            "description": "Optional filename for the video"
                        }
                    },
                    "required": ["session_id", "video_data_b64"]
                }
            },
            {
                "name": "get_coaching_insights",
                "description": "Get detailed coaching insights for a pitch session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "ID of the analyzed pitch session"
                        }
                    },
                    "required": ["session_id"]
                }
            },
            {
                "name": "get_session_status",
                "description": "Get status and info for a pitch session",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "ID of the pitch session"
                        }
                    },
                    "required": ["session_id"]
                }
            },
            {
                "name": "list_active_sessions",
                "description": "List active pitch sessions, optionally filtered by user",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "Optional user ID to filter sessions"
                        }
                    },
                    "required": []
                }
            }
        ]


# Global instance for MCP integration
pitch_tools = PitchMCPTools()


async def handle_pitch_mcp_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle MCP tool calls for pitch analysis.
    
    Args:
        tool_name: Name of the MCP tool to call
        arguments: Tool arguments
        
    Returns:
        Tool execution result
    """
    try:
        if tool_name == "pitch_health_check":
            return await pitch_tools.health_check()
        
        elif tool_name == "create_pitch_session":
            return await pitch_tools.create_pitch_session(
                user_id=arguments["user_id"],
                title=arguments["title"],
                pitch_category=arguments.get("pitch_category"),
                target_duration=arguments.get("target_duration")
            )
        
        elif tool_name == "analyze_pitch_video":
            return await pitch_tools.analyze_pitch_video(
                session_id=arguments["session_id"],
                video_data_b64=arguments["video_data_b64"],
                filename=arguments.get("filename")
            )
        
        elif tool_name == "get_coaching_insights":
            return await pitch_tools.get_coaching_insights(
                session_id=arguments["session_id"]
            )
        
        elif tool_name == "get_session_status":
            return await pitch_tools.get_session_status(
                session_id=arguments["session_id"]
            )
        
        elif tool_name == "list_active_sessions":
            return await pitch_tools.list_active_sessions(
                user_id=arguments.get("user_id")
            )
        
        else:
            return {
                "status": "error",
                "error": f"Unknown pitch tool: {tool_name}"
            }
    
    except Exception as e:
        logger.error(f"MCP tool call failed for {tool_name}: {str(e)}")
        return {
            "tool": tool_name,
            "status": "error",
            "error": str(e)
        }
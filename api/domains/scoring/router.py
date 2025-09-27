"""
Scoring/Analysis domain REST API router
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from datetime import datetime

# Import MCP handlers
from .mcp.scoring_mcp_tools import SCORING_MCP_TOOLS, execute_scoring_mcp_tool
from .mcp.scoring_mcp_tools_audio_integrated import execute_audio_integrated_scoring_mcp_tool

router = APIRouter(prefix="/api/analysis", tags=["scoring", "analysis"])


# ============= Models =============

class ScoringRequest(BaseModel):
    """Request for pitch scoring"""
    session_id: str = Field(..., description="Session ID to score")
    event_id: str = Field(..., description="Event ID for context")
    scoring_criteria: Optional[Dict[str, float]] = Field(None, description="Custom scoring weights")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_neural_ninjas_001",
                "event_id": "hackathon-2024",
                "scoring_criteria": {
                    "innovation": 0.3,
                    "technical": 0.3,
                    "presentation": 0.2,
                    "business_value": 0.2
                }
            }
        }


class ScoringResponse(BaseModel):
    """Scoring result response"""
    session_id: str
    event_id: str
    total_score: float
    category_scores: Dict[str, float]
    ai_feedback: str
    strengths: List[str]
    improvements: List[str]
    recommendation: str
    scored_at: datetime
    

class PresentationDeliveryRequest(BaseModel):
    """Request for presentation delivery analysis"""
    session_id: str = Field(..., description="Session ID to analyze")
    event_id: str = Field(..., description="Event ID for context")
    include_audio_metrics: bool = Field(True, description="Include audio analysis")
    benchmark_wpm: int = Field(150, description="Words per minute benchmark")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_neural_ninjas_001",
                "event_id": "hackathon-2024",
                "include_audio_metrics": True,
                "benchmark_wpm": 150
            }
        }


class PresentationDeliveryResponse(BaseModel):
    """Presentation delivery analysis response"""
    session_id: str
    delivery_score: float
    pace_rating: str
    clarity_score: float
    confidence_score: float
    engagement_score: float
    audio_metrics: Optional[Dict[str, Any]]
    recommendations: List[str]
    strengths: List[str]


class BatchScoringRequest(BaseModel):
    """Request for batch scoring multiple sessions"""
    event_id: str = Field(..., description="Event ID to score all sessions for")
    session_ids: Optional[List[str]] = Field(None, description="Specific sessions to score")
    force_rescore: bool = Field(False, description="Force rescoring of already scored sessions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "hackathon-2024",
                "session_ids": ["session_001", "session_002"],
                "force_rescore": False
            }
        }


class JudgeFeedbackRequest(BaseModel):
    """Request to generate judge feedback"""
    session_id: str = Field(..., description="Session ID to evaluate")
    judge_persona: str = Field("technical", description="Type of judge: technical, business, investor")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_neural_ninjas_001",
                "judge_persona": "investor",
                "focus_areas": ["market_opportunity", "team_capability", "scalability"]
            }
        }


# ============= Helper functions =============

def transform_mcp_to_rest_response(mcp_result: Dict[str, Any], response_model: type) -> Dict[str, Any]:
    """Transform MCP tool result to match REST API response model."""
    # Handle the common MCP response structure
    if not mcp_result.get("success", True):
        raise HTTPException(status_code=400, detail=mcp_result.get("error", "Unknown error"))
    
    # For scoring responses, map MCP structure to REST structure
    if "scores" in mcp_result and response_model == ScoringResponse:
        scores = mcp_result["scores"]
        return {
            "session_id": mcp_result.get("session_id"),
            "event_id": mcp_result.get("event_id"),
            "total_score": scores.get("overall", {}).get("total_score", 0),
            "category_scores": {
                "idea": scores.get("idea", {}).get("score", 0),
                "technical": scores.get("technical_implementation", {}).get("score", 0),
                "tools": scores.get("tool_use", {}).get("score", 0),
                "presentation": scores.get("presentation_delivery", {}).get("score", 0)
            },
            "ai_feedback": scores.get("overall", {}).get("judge_recommendation", ""),
            "strengths": [],  # Aggregate from all categories
            "improvements": [],  # Aggregate from all categories
            "recommendation": scores.get("overall", {}).get("ranking_tier", ""),
            "scored_at": datetime.fromisoformat(mcp_result.get("scoring_timestamp", datetime.utcnow().isoformat()))
        }
    
    # Default: return as-is for direct mapping
    return mcp_result


async def execute_analysis_tool(tool_name: str, args: Dict[str, Any]):
    """Execute scoring/analysis MCP tool."""
    try:
        # Check if it's an audio-integrated tool
        if "presentation_delivery" in tool_name or "audio" in tool_name:
            return await execute_audio_integrated_scoring_mcp_tool(tool_name, args)
        else:
            return await execute_scoring_mcp_tool(tool_name, args)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ============= Endpoints =============

@router.post("/score", response_model=ScoringResponse)
async def score_pitch(request: ScoringRequest):
    """Score a pitch session using MCP tool with structured REST response"""
    try:
        # Call MCP tool
        mcp_result = await execute_analysis_tool("analysis.score_pitch", {
            "session_id": request.session_id,
            "event_id": request.event_id,
            "scoring_context": request.scoring_criteria
        })
        
        # Transform MCP response to REST API structure
        rest_response = transform_mcp_to_rest_response(mcp_result, ScoringResponse)
        return ScoringResponse(**rest_response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/presentation-delivery", response_model=PresentationDeliveryResponse)
async def analyze_presentation_delivery(request: PresentationDeliveryRequest):
    """Analyze presentation delivery including audio metrics"""
    try:
        result = await execute_analysis_tool(
            "analysis.analyze_presentation_delivery", 
            request.dict()
        )
        return PresentationDeliveryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-score")
async def batch_score_pitches(request: BatchScoringRequest):
    """Score multiple pitch sessions in batch"""
    try:
        result = await execute_analysis_tool("analysis.batch_score", request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/judge-feedback")
async def generate_judge_feedback(request: JudgeFeedbackRequest):
    """Generate detailed judge feedback for a pitch"""
    try:
        result = await execute_analysis_tool("analysis.generate_judge_feedback", request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_scoring(session_id: str, event_id: str = Query(...)):
    """Get all scoring results for a session"""
    try:
        result = await execute_analysis_tool("analysis.get_scoring_results", {
            "session_id": session_id,
            "event_id": event_id
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/event/{event_id}/stats")
async def get_event_scoring_stats(event_id: str):
    """Get scoring statistics for an entire event"""
    try:
        result = await execute_analysis_tool("analysis.get_event_stats", {
            "event_id": event_id
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/compare")
async def compare_pitches(
    session_ids: List[str] = Body(..., description="List of session IDs to compare"),
    event_id: str = Body(..., description="Event ID for context")
):
    """Compare multiple pitches side by side"""
    try:
        result = await execute_analysis_tool("analysis.compare_pitches", {
            "session_ids": session_ids,
            "event_id": event_id
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/feedback/{session_id}/improve")
async def generate_improvement_suggestions(
    session_id: str,
    target_score: float = Query(90.0, description="Target score to achieve")
):
    """Generate specific improvement suggestions to reach target score"""
    try:
        result = await execute_analysis_tool("analysis.generate_improvements", {
            "session_id": session_id,
            "target_score": target_score
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
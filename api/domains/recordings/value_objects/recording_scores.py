#!/usr/bin/env python3
"""
Recording Scores Value Object

Represents the scoring data for a pitch recording, including individual category scores
and overall evaluation metrics.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class RecordingScores:
    """Value object representing scoring data for a pitch recording."""
    
    idea_score: float
    technical_score: float
    presentation_score: float
    tool_use_score: float
    total_score: float
    
    # Optional detailed scoring breakdown
    idea_details: Optional[Dict[str, Any]] = None
    technical_details: Optional[Dict[str, Any]] = None
    presentation_details: Optional[Dict[str, Any]] = None
    tool_use_details: Optional[Dict[str, Any]] = None
    overall_details: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate scoring data."""
        scores = [self.idea_score, self.technical_score, self.presentation_score, self.tool_use_score]
        
        for score in scores:
            if not isinstance(score, (int, float)):
                raise ValueError("All scores must be numeric")
            if score < 0:
                raise ValueError("Scores cannot be negative")
            if score > 25:
                raise ValueError("Individual category scores cannot exceed 25")
        
        if not isinstance(self.total_score, (int, float)):
            raise ValueError("Total score must be numeric")
        if self.total_score < 0:
            raise ValueError("Total score cannot be negative")
        if self.total_score > 100:
            raise ValueError("Total score cannot exceed 100")
        
        # Check if total score approximately matches sum of individual scores
        calculated_total = sum(scores)
        if abs(calculated_total - self.total_score) > 0.1:
            raise ValueError(f"Total score ({self.total_score}) does not match sum of category scores ({calculated_total})")
    
    @property
    def percentage(self) -> float:
        """Get total score as percentage."""
        return (self.total_score / 100.0) * 100
    
    @property
    def ranking_tier(self) -> str:
        """Get ranking tier based on total score."""
        if self.total_score >= 85:
            return "excellent"
        elif self.total_score >= 70:
            return "very_good"
        elif self.total_score >= 55:
            return "good"
        else:
            return "needs_improvement"
    
    def get_score(self, category: str) -> Optional[float]:
        """Get score for a specific category."""
        category_map = {
            "idea": self.idea_score,
            "technical": self.technical_score,
            "presentation": self.presentation_score,
            "tool_use": self.tool_use_score,
            "total": self.total_score
        }
        return category_map.get(category.lower())
    
    def get_category_details(self, category: str) -> Optional[Dict[str, Any]]:
        """Get detailed breakdown for a specific category."""
        details_map = {
            "idea": self.idea_details,
            "technical": self.technical_details,
            "presentation": self.presentation_details,
            "tool_use": self.tool_use_details,
            "overall": self.overall_details
        }
        return details_map.get(category.lower())
    
    def compare_with(self, other: 'RecordingScores') -> Dict[str, float]:
        """Compare scores with another RecordingScores instance."""
        return {
            "idea_change": self.idea_score - other.idea_score,
            "technical_change": self.technical_score - other.technical_score,
            "presentation_change": self.presentation_score - other.presentation_score,
            "tool_use_change": self.tool_use_score - other.tool_use_score,
            "total_change": self.total_score - other.total_score
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "idea_score": self.idea_score,
            "technical_score": self.technical_score,
            "presentation_score": self.presentation_score,
            "tool_use_score": self.tool_use_score,
            "total_score": self.total_score,
            "percentage": self.percentage,
            "ranking_tier": self.ranking_tier
        }
        
        # Add detailed breakdowns if available
        if self.idea_details:
            result["idea_details"] = self.idea_details
        if self.technical_details:
            result["technical_details"] = self.technical_details
        if self.presentation_details:
            result["presentation_details"] = self.presentation_details
        if self.tool_use_details:
            result["tool_use_details"] = self.tool_use_details
        if self.overall_details:
            result["overall_details"] = self.overall_details
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecordingScores':
        """Create from dictionary representation."""
        return cls(
            idea_score=data["idea_score"],
            technical_score=data["technical_score"],
            presentation_score=data["presentation_score"],
            tool_use_score=data["tool_use_score"],
            total_score=data["total_score"],
            idea_details=data.get("idea_details"),
            technical_details=data.get("technical_details"),
            presentation_details=data.get("presentation_details"),
            tool_use_details=data.get("tool_use_details"),
            overall_details=data.get("overall_details")
        )
    
    @classmethod
    def from_scoring_result(cls, scoring_data: Dict[str, Any]) -> 'RecordingScores':
        """Create from LLM scoring result format."""
        # Extract scores from the nested structure used by scoring system
        idea = scoring_data.get("idea", {})
        technical = scoring_data.get("technical_implementation", {})
        presentation = scoring_data.get("presentation_delivery", {})
        tool_use = scoring_data.get("tool_use", {})
        overall = scoring_data.get("overall", {})
        
        return cls(
            idea_score=float(idea.get("score", 0)),
            technical_score=float(technical.get("score", 0)),
            presentation_score=float(presentation.get("score", 0)),
            tool_use_score=float(tool_use.get("score", 0)),
            total_score=float(overall.get("total_score", 0)),
            idea_details=idea,
            technical_details=technical,
            presentation_details=presentation,
            tool_use_details=tool_use,
            overall_details=overall
        )
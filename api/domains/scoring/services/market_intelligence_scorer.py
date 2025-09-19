"""
Market Intelligence Scorer

Combines AI-powered pitch analysis with real-time market intelligence from BrightData
to provide enhanced scoring with market validation, competitive analysis, and industry trends.
"""
import asyncio
from typing import Dict, Any, List
from copy import deepcopy

from ...shared.infrastructure.logging import get_logger, log_with_context


class MarketIntelligenceScorer:
    """Scorer that combines AI analysis with real market intelligence data."""
    
    def __init__(self):
        self.logger = get_logger("market_intelligence_scorer")
    
    async def calculate_market_enhanced_score(
        self,
        base_ai_scores: Dict[str, Any],
        market_validation: Dict[str, Any],
        competitive_analysis: Dict[str, Any],
        industry_trends: Dict[str, Any],
        transcript_text: str
    ) -> Dict[str, Any]:
        """
        Calculate enhanced scores using market intelligence.
        
        Combines base AI analysis with real market data to provide
        more accurate and data-driven scoring.
        
        Args:
            base_ai_scores: Original AI-powered analysis scores
            market_validation: BrightData market size validation
            competitive_analysis: BrightData competitive landscape
            industry_trends: BrightData industry trend analysis
            transcript_text: Pitch transcript for context
            
        Returns:
            Enhanced scoring results with market intelligence integration
        """
        
        log_with_context(
            self.logger, "INFO", "Starting market intelligence score enhancement",
            operation="calculate_market_enhanced_score",
            has_market_validation=bool(market_validation.get("confidence")),
            has_competitive_analysis=bool(competitive_analysis.get("competitors")),
            has_industry_trends=bool(industry_trends.get("trending_keywords"))
        )
        
        # Start with base AI scores
        enhanced_scores = deepcopy(base_ai_scores)
        
        try:
            # 1. Enhance Idea Score with Market Validation
            idea_enhancement = await self._enhance_idea_score(
                base_idea_score=base_ai_scores.get("idea", {}).get("score", 0),
                market_validation=market_validation,
                industry_trends=industry_trends
            )
            
            enhanced_scores["idea"]["score"] = idea_enhancement["enhanced_score"]
            enhanced_scores["idea"]["market_validation"] = idea_enhancement["validation_details"]
            enhanced_scores["idea"]["market_timing"] = idea_enhancement["timing_analysis"]
            
            # 2. Add Market Intelligence Bonus Score (5%)
            market_bonus = await self._calculate_market_bonus(
                market_validation=market_validation,
                competitive_analysis=competitive_analysis,
                industry_trends=industry_trends
            )
            
            enhanced_scores["market_intelligence"] = {
                "score": market_bonus["score"],
                "analysis": market_bonus["analysis"],
                "data_quality": market_bonus["data_quality"],
                "confidence": market_bonus["confidence"]
            }
            
            # 3. Recalculate Total Score with Market Enhancement
            total_enhanced = (
                enhanced_scores["idea"]["score"] * 0.30 +  # 30% (was 25%)
                enhanced_scores["technical_implementation"]["score"] * 0.25 +
                enhanced_scores["tool_use"]["score"] * 0.20 +  # 20% (was 25%)
                enhanced_scores["presentation"]["score"] * 0.20 +  # 20% (was 25%) 
                enhanced_scores["market_intelligence"]["score"] * 0.05  # 5% bonus
            )
            
            original_total = base_ai_scores.get("overall", {}).get("total_score", 0)
            market_enhancement = round(total_enhanced - original_total, 1)
            
            enhanced_scores["overall"] = {
                "total_score": round(total_enhanced, 1),
                "base_ai_score": original_total,
                "market_enhancement": market_enhancement,
                "scoring_method": "market_enhanced_ai_analysis",
                "market_data_sources": len(market_validation.get("sources", [])),
                "competitive_data_points": len(competitive_analysis.get("competitors", [])),
                "analysis_confidence": min(
                    market_validation.get("confidence", 50),
                    self._get_competitive_confidence(competitive_analysis),
                    industry_trends.get("confidence", 50)
                )
            }
            
            log_with_context(
                self.logger, "INFO", "Market intelligence score enhancement completed",
                operation="calculate_market_enhanced_score",
                original_score=original_total,
                enhanced_score=round(total_enhanced, 1),
                market_enhancement=market_enhancement,
                enhancement_percentage=round((market_enhancement / original_total * 100), 1) if original_total > 0 else 0
            )
            
            return enhanced_scores
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", "Error in market intelligence score enhancement",
                operation="calculate_market_enhanced_score",
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Return base scores with error indication
            enhanced_scores = deepcopy(base_ai_scores)
            enhanced_scores["market_intelligence"] = {
                "score": 0,
                "analysis": f"Market intelligence enhancement failed: {str(e)}",
                "data_quality": "error",
                "confidence": 0
            }
            
            return enhanced_scores
    
    async def _enhance_idea_score(
        self,
        base_idea_score: float,
        market_validation: Dict[str, Any],
        industry_trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance idea score with market validation data."""
        
        log_with_context(
            self.logger, "DEBUG", "Enhancing idea score with market validation",
            operation="enhance_idea_score",
            base_score=base_idea_score,
            market_confidence=market_validation.get("confidence", 0)
        )
        
        enhancement_factors = []
        
        try:
            # Market Size Validation
            market_confidence = self._extract_market_confidence(market_validation)
            if market_confidence > 80:
                enhancement_factors.append(("strong_market_validation", 1.15))
            elif market_confidence > 60:
                enhancement_factors.append(("moderate_market_validation", 1.08))
            elif market_confidence < 30:
                enhancement_factors.append(("weak_market_validation", 0.92))
            
            # Industry Trend Alignment
            trend_alignment = self._calculate_trend_alignment(industry_trends)
            if trend_alignment > 80:
                enhancement_factors.append(("strong_trend_alignment", 1.12))
            elif trend_alignment > 60:
                enhancement_factors.append(("moderate_trend_alignment", 1.05))
            elif trend_alignment < 40:
                enhancement_factors.append(("poor_trend_alignment", 0.95))
            
            # Calculate enhanced score
            enhanced_score = base_idea_score
            validation_details = []
            
            for factor_name, multiplier in enhancement_factors:
                enhanced_score *= multiplier
                validation_details.append({
                    "factor": factor_name,
                    "multiplier": multiplier,
                    "impact": f"{((multiplier - 1) * 100):+.1f}%"
                })
            
            # Cap at 30 (max for 30% category)
            enhanced_score = min(30.0, enhanced_score)
            
            log_with_context(
                self.logger, "DEBUG", "Idea score enhancement completed",
                operation="enhance_idea_score",
                original_score=base_idea_score,
                enhanced_score=enhanced_score,
                enhancement_factors=len(enhancement_factors)
            )
            
            return {
                "enhanced_score": enhanced_score,
                "validation_details": validation_details,
                "timing_analysis": self._analyze_market_timing(industry_trends),
                "market_validation_confidence": market_confidence
            }
            
        except Exception as e:
            log_with_context(
                self.logger, "WARNING", "Error in idea score enhancement",
                operation="enhance_idea_score",
                error=str(e)
            )
            
            return {
                "enhanced_score": base_idea_score,
                "validation_details": [{"factor": "enhancement_error", "error": str(e)}],
                "timing_analysis": {},
                "market_validation_confidence": 0
            }
    
    async def _calculate_market_bonus(
        self,
        market_validation: Dict[str, Any],
        competitive_analysis: Dict[str, Any],
        industry_trends: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate bonus score for market intelligence quality."""
        
        log_with_context(
            self.logger, "DEBUG", "Calculating market intelligence bonus score",
            operation="calculate_market_bonus"
        )
        
        try:
            # Base bonus score calculation (0-5 points)
            bonus_score = 0.0
            analysis_components = []
            
            # Market validation quality (0-2 points)
            market_confidence = self._extract_market_confidence(market_validation)
            if market_confidence > 80:
                bonus_score += 2.0
                analysis_components.append("High confidence market validation")
            elif market_confidence > 60:
                bonus_score += 1.5
                analysis_components.append("Moderate confidence market validation")
            elif market_confidence > 30:
                bonus_score += 1.0
                analysis_components.append("Basic market validation available")
            
            # Competitive analysis depth (0-2 points)
            competitors_found = len(competitive_analysis.get("competitors", []))
            if competitors_found >= 10:
                bonus_score += 2.0
                analysis_components.append(f"Comprehensive competitive analysis ({competitors_found} competitors)")
            elif competitors_found >= 5:
                bonus_score += 1.5
                analysis_components.append(f"Good competitive analysis ({competitors_found} competitors)")
            elif competitors_found >= 2:
                bonus_score += 1.0
                analysis_components.append(f"Basic competitive analysis ({competitors_found} competitors)")
            
            # Industry trends relevance (0-1 point)
            trend_relevance = len(industry_trends.get("trending_keywords", []))
            if trend_relevance >= 5:
                bonus_score += 1.0
                analysis_components.append(f"Strong industry trend insights ({trend_relevance} trends)")
            elif trend_relevance >= 3:
                bonus_score += 0.5
                analysis_components.append(f"Moderate industry trend insights ({trend_relevance} trends)")
            
            # Data quality assessment
            data_quality = "excellent" if bonus_score >= 4.5 else \
                          "good" if bonus_score >= 3.0 else \
                          "moderate" if bonus_score >= 1.5 else "basic"
            
            confidence = min(95, max(20, (bonus_score / 5.0) * 100))
            
            log_with_context(
                self.logger, "DEBUG", "Market intelligence bonus calculated",
                operation="calculate_market_bonus",
                bonus_score=bonus_score,
                data_quality=data_quality,
                confidence=confidence
            )
            
            return {
                "score": bonus_score,
                "analysis": "; ".join(analysis_components) or "Limited market intelligence available",
                "data_quality": data_quality,
                "confidence": confidence,
                "components": {
                    "market_validation_points": min(2.0, market_confidence / 40),
                    "competitive_analysis_points": min(2.0, competitors_found / 5),
                    "industry_trends_points": min(1.0, trend_relevance / 5)
                }
            }
            
        except Exception as e:
            log_with_context(
                self.logger, "WARNING", "Error calculating market intelligence bonus",
                operation="calculate_market_bonus",
                error=str(e)
            )
            
            return {
                "score": 0.0,
                "analysis": f"Error calculating market bonus: {str(e)}",
                "data_quality": "error",
                "confidence": 0
            }
    
    def _extract_market_confidence(self, market_validation: Dict[str, Any]) -> float:
        """Extract market confidence score from validation data."""
        
        confidence = market_validation.get("confidence", 0)
        
        # Handle different confidence formats
        if isinstance(confidence, str):
            confidence_map = {
                "HIGH": 85,
                "MEDIUM": 65, 
                "LOW": 35,
                "UNKNOWN": 20
            }
            confidence = confidence_map.get(confidence.upper(), 20)
        elif isinstance(confidence, (int, float)):
            confidence = float(confidence)
        else:
            confidence = 20  # Default low confidence
        
        return max(0, min(100, confidence))
    
    def _get_competitive_confidence(self, competitive_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score based on competitive analysis quality."""
        
        competitors = competitive_analysis.get("competitors", [])
        if not competitors:
            return 20
        
        # Base confidence on number of competitors and data quality
        base_confidence = min(80, len(competitors) * 8)  # 8 points per competitor, max 80
        
        # Bonus for funding data
        funding_data_count = sum(1 for c in competitors if c.get("funding_amount"))
        if funding_data_count > 0:
            base_confidence += min(15, funding_data_count * 3)
        
        return min(95, base_confidence)
    
    def _calculate_trend_alignment(self, industry_trends: Dict[str, Any]) -> float:
        """Calculate how well the pitch aligns with industry trends."""
        
        trending_keywords = industry_trends.get("trending_keywords", [])
        recent_news = industry_trends.get("recent_news", [])
        
        if not trending_keywords and not recent_news:
            return 50  # Neutral when no trend data
        
        # Simple scoring based on available trend data
        trend_score = 40  # Base score
        
        if trending_keywords:
            trend_score += min(30, len(trending_keywords) * 6)  # 6 points per keyword, max 30
        
        if recent_news:
            trend_score += min(20, len(recent_news) * 4)  # 4 points per news item, max 20
        
        return min(90, trend_score)
    
    def _analyze_market_timing(self, industry_trends: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market timing based on industry trends."""
        
        trending_keywords = industry_trends.get("trending_keywords", [])
        recent_news = industry_trends.get("recent_news", [])
        
        if not trending_keywords and not recent_news:
            return {
                "timing_assessment": "neutral",
                "reasoning": "Insufficient trend data for timing analysis"
            }
        
        # Simple timing analysis
        positive_indicators = len(trending_keywords) + len(recent_news)
        
        if positive_indicators >= 8:
            return {
                "timing_assessment": "excellent",
                "reasoning": f"Strong market momentum with {positive_indicators} positive trend indicators"
            }
        elif positive_indicators >= 5:
            return {
                "timing_assessment": "good", 
                "reasoning": f"Positive market trends with {positive_indicators} supporting indicators"
            }
        elif positive_indicators >= 3:
            return {
                "timing_assessment": "moderate",
                "reasoning": f"Some market support with {positive_indicators} trend indicators"
            }
        else:
            return {
                "timing_assessment": "challenging",
                "reasoning": f"Limited market momentum with only {positive_indicators} trend indicators"
            }
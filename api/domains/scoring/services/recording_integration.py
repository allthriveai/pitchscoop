"""
Recording Integration for Background Market Intelligence

Integrates background market intelligence gathering with the existing
pitch recording workflow. Starts analysis as soon as recording begins.
"""
import asyncio
from typing import Dict, Any, Optional

from .background_market_intelligence import background_market_service
from ...recordings.entities.stt_session import STTSession
from ...shared.infrastructure.logging import get_logger, log_with_context


class RecordingMarketIntelligenceIntegrator:
    """Integrates market intelligence with pitch recording workflow."""
    
    def __init__(self):
        self.logger = get_logger("recording_market_integration")
    
    async def on_recording_started(
        self, 
        session: STTSession,
        team_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Triggered when a pitch recording starts.
        
        Immediately begins background market intelligence gathering
        so data is ready when judges need to score.
        """
        
        log_with_context(
            self.logger, "INFO", "Recording started - initiating background market intelligence",
            event_id=session.event_id,
            session_id=session.session_id,
            team_name=session.team_name,
            operation="on_recording_started"
        )
        
        # Gather team data from session or parameters
        if not team_data:
            team_data = {
                "team_name": session.team_name,
                "pitch_title": getattr(session, 'pitch_title', ''),
                "industry": getattr(session, 'industry', 'technology'),
                "company_description": getattr(session, 'company_description', '')
            }
        
        # Start background market intelligence analysis
        try:
            success = await background_market_service.start_predictive_analysis(
                session_id=session.session_id,
                event_id=session.event_id,
                team_data=team_data
            )
            
            if success:
                log_with_context(
                    self.logger, "INFO", "Background market intelligence initiated successfully",
                    event_id=session.event_id,
                    session_id=session.session_id,
                    team_name=session.team_name,
                    operation="market_intelligence_start"
                )
            else:
                log_with_context(
                    self.logger, "WARNING", "Failed to initiate background market intelligence",
                    event_id=session.event_id,
                    session_id=session.session_id,
                    team_name=session.team_name,
                    operation="market_intelligence_start"
                )
            
            return success
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", "Error initiating background market intelligence",
                event_id=session.event_id,
                session_id=session.session_id,
                team_name=session.team_name,
                operation="market_intelligence_start",
                error=str(e),
                error_type=type(e).__name__
            )
            return False
    
    async def on_recording_completed(
        self, 
        session: STTSession,
        transcript_available: bool = True
    ):
        """
        Triggered when a pitch recording completes.
        
        Checks if background market intelligence is ready and logs status.
        """
        
        log_with_context(
            self.logger, "INFO", "Recording completed - checking market intelligence status",
            event_id=session.event_id,
            session_id=session.session_id,
            team_name=session.team_name,
            operation="on_recording_completed",
            transcript_available=transcript_available
        )
        
        # Check status of background analysis
        try:
            status = await background_market_service.get_analysis_status(
                session_id=session.session_id,
                event_id=session.event_id
            )
            
            log_with_context(
                self.logger, "INFO", "Market intelligence status check complete",
                event_id=session.event_id,
                session_id=session.session_id,
                team_name=session.team_name,
                operation="market_intelligence_status",
                analysis_status=status.get("status"),
                has_cached_data=status.get("has_cached_data", False),
                estimated_completion=status.get("estimated_completion")
            )
            
            return status
            
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", "Error checking market intelligence status",
                event_id=session.event_id,
                session_id=session.session_id,
                team_name=session.team_name,
                operation="market_intelligence_status",
                error=str(e)
            )
            return {"status": "error", "error": str(e)}
    
    async def get_market_intelligence_for_scoring(
        self,
        session_id: str,
        event_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get market intelligence data for scoring.
        
        Returns cached data if available, None if still processing.
        """
        
        log_with_context(
            self.logger, "DEBUG", "Retrieving market intelligence for scoring",
            event_id=event_id,
            session_id=session_id,
            operation="get_market_intelligence_for_scoring"
        )
        
        try:
            # Try to get cached market intelligence
            market_data = await background_market_service.get_cached_market_intelligence(
                session_id=session_id,
                event_id=event_id
            )
            
            if market_data:
                log_with_context(
                    self.logger, "INFO", "Market intelligence data retrieved for scoring",
                    event_id=event_id,
                    session_id=session_id,
                    operation="get_market_intelligence_for_scoring",
                    has_market_validation=bool(market_data.get("market_validation")),
                    has_competitor_analysis=bool(market_data.get("competitor_analysis")),
                    has_industry_trends=bool(market_data.get("industry_trends"))
                )
                return market_data
            else:
                log_with_context(
                    self.logger, "DEBUG", "No market intelligence data available yet",
                    event_id=event_id,
                    session_id=session_id,
                    operation="get_market_intelligence_for_scoring"
                )
                return None
                
        except Exception as e:
            log_with_context(
                self.logger, "ERROR", "Error retrieving market intelligence for scoring",
                event_id=event_id,
                session_id=session_id,
                operation="get_market_intelligence_for_scoring",
                error=str(e)
            )
            return None


# Global integrator instance
recording_market_integrator = RecordingMarketIntelligenceIntegrator()
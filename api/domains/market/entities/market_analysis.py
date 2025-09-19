"""
Market Analysis Entities

Data classes for market intelligence results from Bright Data.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class CompetitorProfile:
    """Profile of a competitor found through market research."""
    name: str
    description: str
    website: Optional[str] = None
    funding_amount: Optional[str] = None
    funding_stage: Optional[str] = None
    employees: Optional[int] = None
    founded_year: Optional[int] = None
    similarity_score: Optional[float] = None


@dataclass
class MarketValidation:
    """Market size and growth validation results."""
    claimed_market_size: str
    validated_market_size: Optional[str] = None
    market_size_confidence: Optional[str] = None  # HIGH, MEDIUM, LOW
    growth_rate: Optional[str] = None
    market_trends: List[str] = None
    sources: List[str] = None
    
    def __post_init__(self):
        if self.market_trends is None:
            self.market_trends = []
        if self.sources is None:
            self.sources = []


@dataclass
class MarketAnalysis:
    """Complete market intelligence analysis for a pitch/team."""
    event_id: str
    team_name: str
    session_id: Optional[str] = None
    
    # Market validation
    market_validation: Optional[MarketValidation] = None
    
    # Competitive analysis
    competitors: List[CompetitorProfile] = None
    competitive_density: Optional[str] = None  # HIGH, MEDIUM, LOW
    
    # Industry trends
    industry: Optional[str] = None
    trending_keywords: List[str] = None
    recent_news: List[Dict[str, Any]] = None
    
    # Metadata
    analyzed_at: Optional[datetime] = None
    cached_until: Optional[datetime] = None
    bright_data_cost: Optional[float] = None
    
    def __post_init__(self):
        if self.competitors is None:
            self.competitors = []
        if self.trending_keywords is None:
            self.trending_keywords = []
        if self.recent_news is None:
            self.recent_news = []
        if self.analyzed_at is None:
            self.analyzed_at = datetime.utcnow()
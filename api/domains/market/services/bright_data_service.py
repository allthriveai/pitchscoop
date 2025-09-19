"""
Bright Data Service

Wrapper for Bright Data API calls with error handling, rate limiting, and response processing.
"""
import os
import aiohttp
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

from ..entities.market_analysis import CompetitorProfile, MarketValidation, MarketAnalysis
from ...shared.infrastructure.logging import get_logger, log_with_context


class BrightDataService:
    """Service for interacting with Bright Data APIs."""
    
    def __init__(self):
        self.api_key = os.getenv("BRIGHT_DATA_API_KEY")
        self.base_url = os.getenv("BRIGHT_DATA_BASE_URL", "https://api.brightdata.com")
        self.rate_limit = int(os.getenv("BRIGHT_DATA_RATE_LIMIT", "100"))
        self.logger = get_logger("market.bright_data")
        
        # Rate limiting
        self._last_request_time = 0
        self._request_count = 0
        self._rate_limit_window = 60  # 1 minute
        
        if not self.api_key:
            self.logger.warning("BRIGHT_DATA_API_KEY not set - using mock mode")
    
    async def _rate_limit_check(self):
        """Implement simple rate limiting."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self._last_request_time > self._rate_limit_window:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Check if we're over the rate limit
        if self._request_count >= self.rate_limit:
            sleep_time = self._rate_limit_window - (current_time - self._last_request_time)
            if sleep_time > 0:
                self.logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()
        
        self._request_count += 1
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Bright Data API."""
        if not self.api_key:
            return await self._mock_response(endpoint, params)
        
        await self._rate_limit_check()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params, headers=headers) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return response_data
                    else:
                        self.logger.error(f"Bright Data API error: {response.status} - {response_data}")
                        return {"error": f"API error: {response.status}", "details": response_data}
        
        except Exception as e:
            self.logger.error(f"Request to Bright Data failed: {str(e)}")
            return {"error": f"Request failed: {str(e)}"}
    
    async def _mock_response(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate mock responses for testing without API key."""
        await asyncio.sleep(0.1)  # Simulate API latency
        
        if "competitor" in endpoint:
            return {
                "competitors": [
                    {
                        "name": "Example Competitor 1",
                        "description": "A similar company in the same space",
                        "website": "https://competitor1.com",
                        "funding_amount": "$5.2M",
                        "funding_stage": "Series A",
                        "employees": 25,
                        "founded_year": 2020,
                        "similarity_score": 0.85
                    },
                    {
                        "name": "Example Competitor 2", 
                        "description": "Another competitor with similar offerings",
                        "website": "https://competitor2.com",
                        "funding_amount": "$12.1M",
                        "funding_stage": "Series B",
                        "employees": 67,
                        "founded_year": 2018,
                        "similarity_score": 0.72
                    }
                ],
                "total_found": 15,
                "competitive_density": "HIGH"
            }
        
        elif "market" in endpoint:
            return {
                "market_size": "$12.3B",
                "growth_rate": "15.2% CAGR",
                "confidence": "HIGH",
                "trends": [
                    "Increased demand for fintech solutions",
                    "Regulatory support for digital lending",
                    "AI adoption in financial services"
                ],
                "sources": [
                    "Grand View Research Market Report 2024",
                    "McKinsey Digital Banking Survey",
                    "CB Insights Fintech Trends"
                ]
            }
        
        elif "industry" in endpoint:
            return {
                "industry": "Financial Technology",
                "trending_keywords": ["AI lending", "micro-finance", "digital banking"],
                "recent_news": [
                    {
                        "title": "Fintech funding reaches new heights in Q3 2024",
                        "source": "TechCrunch",
                        "date": "2024-09-15",
                        "relevance": 0.9
                    }
                ]
            }
        
        return {"error": "Unknown endpoint", "mock": True}
    
    async def analyze_competitors(self, company_description: str, industry: str, event_id: str) -> Dict[str, Any]:
        """Find and analyze competitors using Bright Data web scraping."""
        log_with_context(
            self.logger, "INFO", "Starting competitor analysis",
            event_id=event_id,
            operation="analyze_competitors",
            industry=industry
        )
        
        params = {
            "query": company_description,
            "industry": industry,
            "limit": 10,
            "include_funding": True,
            "include_employee_count": True
        }
        
        start_time = time.time()
        result = await self._make_request("/competitor-analysis", params)
        duration_ms = (time.time() - start_time) * 1000
        
        log_with_context(
            self.logger, "INFO", "Competitor analysis completed",
            event_id=event_id,
            operation="analyze_competitors",
            duration_ms=duration_ms,
            success="error" not in result,
            competitors_found=len(result.get("competitors", []))
        )
        
        return result
    
    async def validate_market_size(self, market_claims: str, industry: str, event_id: str) -> Dict[str, Any]:
        """Validate market size claims using industry data scraping."""
        log_with_context(
            self.logger, "INFO", "Starting market validation",
            event_id=event_id,
            operation="validate_market_size",
            industry=industry
        )
        
        params = {
            "claimed_market": market_claims,
            "industry": industry,
            "include_growth_rates": True,
            "include_sources": True
        }
        
        start_time = time.time()
        result = await self._make_request("/market-validation", params)
        duration_ms = (time.time() - start_time) * 1000
        
        log_with_context(
            self.logger, "INFO", "Market validation completed",
            event_id=event_id,
            operation="validate_market_size",
            duration_ms=duration_ms,
            success="error" not in result,
            confidence=result.get("confidence", "UNKNOWN")
        )
        
        return result
    
    async def get_industry_trends(self, industry: str, keywords: List[str], event_id: str) -> Dict[str, Any]:
        """Get current industry trends and recent news."""
        log_with_context(
            self.logger, "INFO", "Fetching industry trends",
            event_id=event_id,
            operation="get_industry_trends",
            industry=industry,
            keyword_count=len(keywords)
        )
        
        params = {
            "industry": industry,
            "keywords": keywords,
            "timeframe": "3months",
            "include_news": True,
            "news_limit": 5
        }
        
        start_time = time.time()
        result = await self._make_request("/industry-trends", params)
        duration_ms = (time.time() - start_time) * 1000
        
        log_with_context(
            self.logger, "INFO", "Industry trends completed",
            event_id=event_id,
            operation="get_industry_trends",
            duration_ms=duration_ms,
            success="error" not in result,
            trends_found=len(result.get("trending_keywords", []))
        )
        
        return result


# Global service instance
bright_data_service = BrightDataService()
"""
Hume AI API Repository for Video Emotion Analysis.

This repository handles interactions with Hume AI's expression measurement API
for analyzing emotional expressions in video recordings of pitch presentations.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
import aiohttp
import base64
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class HumeAPIRepository:
    """Repository for Hume AI expression measurement API integration."""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """
        Initialize Hume API client.
        
        Args:
            api_key: Hume API key (optional, will use environment if not provided)
            secret_key: Hume secret key (optional, will use environment if not provided)
        """
        self.api_key = api_key or os.getenv('HUME_API_KEY')
        self.secret_key = secret_key or os.getenv('HUME_SECRET_KEY')
        self.base_url = "https://api.hume.ai/v0"
        
        # Validate credentials
        if not self.api_key or not self.secret_key:
            logger.warning("Hume API credentials not configured")
        
        # Session for connection pooling
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    'X-Hume-Api-Key': self.api_key,
                    'Content-Type': 'application/json'
                },
                timeout=aiohttp.ClientTimeout(total=300)  # 5 minutes for video processing
            )
        return self._session
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Hume API is accessible and credentials are valid.
        
        Returns:
            Dictionary with health status and configuration info
        """
        if not self.api_key or not self.secret_key:
            return {
                "status": "error",
                "error": "Hume API credentials not configured",
                "has_api_key": bool(self.api_key),
                "has_secret_key": bool(self.secret_key)
            }
        
        # Try different potential endpoints to find the correct API structure
        test_endpoints = [
            "/batch/jobs",            # Batch processing (known working)
            "/stream/models",         # Check for streaming endpoints
            "/streaming/models",      # Alternative streaming endpoint
            "/expression/stream",     # Expression streaming
            "/websocket",             # WebSocket endpoint
            "/stream",                # Generic streaming
            "/expression/batch/jobs", # Batch jobs endpoint
            "/expression/models",     # Original attempt
            "/models",                # Simpler models endpoint
            "/",                      # Root endpoint
        ]
        
        try:
            session = await self._get_session()
            
            for endpoint in test_endpoints:
                try:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        logger.info(f"Trying endpoint {endpoint}: status {response.status}")
                        
                        if response.status == 200:
                            try:
                                result = await response.json()
                                return {
                                    "status": "healthy",
                                    "api_accessible": True,
                                    "working_endpoint": endpoint,
                                    "response": result,
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                }
                            except:
                                # Even if JSON parsing fails, 200 means API is accessible
                                return {
                                    "status": "healthy",
                                    "api_accessible": True,
                                    "working_endpoint": endpoint,
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                }
                        
                        elif response.status == 401:
                            error_text = await response.text()
                            return {
                                "status": "error",
                                "error": f"Authentication failed: {error_text}",
                                "api_accessible": True,  # API is reachable, but auth failed
                                "credentials_valid": False
                            }
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed: {e}")
                    continue
            
            # If all endpoints failed
            return {
                "status": "error",
                "error": "All test endpoints failed",
                "api_accessible": False,
                "endpoints_tried": test_endpoints
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": f"Connection failed: {str(e)}",
                "api_accessible": False
            }
    
    async def upload_video_for_analysis(self, video_data: bytes, filename: str = "video.mp4") -> Dict[str, Any]:
        """
        Upload video file to Hume for expression analysis.
        
        Args:
            video_data: Raw video file bytes
            filename: Name of the video file
            
        Returns:
            Upload response with job ID or error details
        """
        try:
            session = await self._get_session()
            
            # Hume API expects different format - let's try with base64 encoded data first
            import base64
            
            # Encode video data as base64
            video_b64 = base64.b64encode(video_data).decode('utf-8')
            
            # Create JSON payload - simplified format
            payload = {
                "models": {
                    "face": {
                        "facs": {},
                        "descriptions": {}
                    }
                },
                "files": [
                    {
                        "filename": filename,
                        "data": video_b64
                    }
                ]
            }
            
            # Use JSON content type
            headers = {
                'X-Hume-Api-Key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            async with session.post(
                f"{self.base_url}/batch/jobs",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status in [200, 201, 202]:
                    result = await response.json()
                    logger.info(f"Video upload successful: {result.get('job_id', 'No job ID')}")
                    return {
                        "success": True,
                        "job_id": result.get("job_id"),
                        "status": result.get("status", "submitted"),
                        "message": "Video uploaded for expression analysis",
                        "response": result
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Video upload failed: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Upload failed: {response.status}",
                        "details": error_text
                    }
                    
        except Exception as e:
            logger.error(f"Exception during video upload: {str(e)}")
            return {
                "success": False,
                "error": f"Upload exception: {str(e)}"
            }
    
    async def get_analysis_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a video analysis job.
        
        Args:
            job_id: The job ID returned from upload_video_for_analysis
            
        Returns:
            Job status and results if completed
        """
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/batch/jobs/{job_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "job_id": job_id,
                        "status": result.get("status"),
                        "progress": result.get("progress"),
                        "results": result.get("results"),
                        "response": result
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Status check failed: {response.status}",
                        "details": error_text
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Status check exception: {str(e)}"
            }
    
    async def wait_for_analysis_completion(self, job_id: str, max_wait_seconds: int = 300, 
                                          poll_interval: int = 10) -> Dict[str, Any]:
        """
        Wait for video analysis to complete, polling periodically.
        
        Args:
            job_id: The job ID to monitor
            max_wait_seconds: Maximum time to wait (default: 5 minutes)
            poll_interval: Seconds between status checks (default: 10)
            
        Returns:
            Final analysis results or timeout error
        """
        start_time = datetime.now()
        max_wait_time = max_wait_seconds
        
        logger.info(f"Waiting for analysis completion: {job_id}")
        
        while True:
            # Check current status
            status_result = await self.get_analysis_status(job_id)
            
            if not status_result.get("success"):
                return status_result
            
            status = status_result.get("status", "unknown")
            
            if status == "completed":
                logger.info(f"Analysis completed: {job_id}")
                return status_result
            
            elif status == "failed":
                logger.error(f"Analysis failed: {job_id}")
                return {
                    "success": False,
                    "error": "Analysis failed",
                    "job_id": job_id,
                    "status": status
                }
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= max_wait_time:
                logger.warning(f"Analysis timeout: {job_id} after {elapsed:.1f}s")
                return {
                    "success": False,
                    "error": "Analysis timeout",
                    "job_id": job_id,
                    "elapsed_seconds": elapsed,
                    "last_status": status
                }
            
            # Wait before next poll
            logger.debug(f"Analysis status: {status}, waiting {poll_interval}s...")
            await asyncio.sleep(poll_interval)
    
    async def analyze_video_complete(self, video_data: bytes, filename: str = "pitch_video.mp4",
                                   max_wait_seconds: int = 300) -> Dict[str, Any]:
        """
        Complete workflow: upload video, wait for analysis, return results.
        
        Args:
            video_data: Raw video file bytes
            filename: Video filename
            max_wait_seconds: Maximum wait time for processing
            
        Returns:
            Complete analysis results including expression data
        """
        logger.info(f"Starting complete video analysis workflow: {filename}")
        
        # Step 1: Upload video
        upload_result = await self.upload_video_for_analysis(video_data, filename)
        
        if not upload_result.get("success"):
            return upload_result
        
        job_id = upload_result.get("job_id")
        if not job_id:
            return {
                "success": False,
                "error": "No job ID returned from upload"
            }
        
        # Step 2: Wait for completion
        completion_result = await self.wait_for_analysis_completion(job_id, max_wait_seconds)
        
        if completion_result.get("success") and completion_result.get("status") == "completed":
            logger.info(f"Video analysis workflow complete: {filename}")
            return {
                "success": True,
                "job_id": job_id,
                "analysis_results": completion_result.get("results"),
                "filename": filename,
                "processing_time": completion_result.get("processing_time"),
                "workflow_complete": True
            }
        else:
            logger.error(f"Video analysis workflow failed: {filename}")
            return completion_result


class MockHumeAPIRepository(HumeAPIRepository):
    """Mock repository for testing without actual API calls."""
    
    def __init__(self):
        # Initialize without real credentials
        super().__init__(api_key="mock_key", secret_key="mock_secret")
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        return {
            "status": "healthy",
            "api_accessible": True,
            "mock": True,
            "available_models": ["expression"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def upload_video_for_analysis(self, video_data: bytes, filename: str = "video.mp4") -> Dict[str, Any]:
        """Mock video upload."""
        mock_job_id = f"mock_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {
            "success": True,
            "job_id": mock_job_id,
            "status": "submitted",
            "message": "Mock video upload successful",
            "mock": True
        }
    
    async def get_analysis_status(self, job_id: str) -> Dict[str, Any]:
        """Mock analysis status - always returns completed."""
        return {
            "success": True,
            "job_id": job_id,
            "status": "completed",
            "progress": 100,
            "results": {
                "expressions": [
                    {
                        "time": 0.5,
                        "confidence": 0.85,
                        "joy": 0.7,
                        "surprise": 0.3,
                        "fear": 0.1,
                        "anger": 0.05,
                        "sadness": 0.1,
                        "disgust": 0.05,
                        "contempt": 0.02
                    }
                ]
            },
            "mock": True
        }
    
    async def analyze_video_complete(self, video_data: bytes, filename: str = "pitch_video.mp4",
                                   max_wait_seconds: int = 300) -> Dict[str, Any]:
        """Mock complete analysis."""
        return {
            "success": True,
            "job_id": f"mock_job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "analysis_results": {
                "expressions": [
                    {
                        "time": 1.0,
                        "confidence": 0.88,
                        "joy": 0.75,
                        "surprise": 0.25,
                        "fear": 0.08,
                        "anger": 0.03,
                        "sadness": 0.12,
                        "disgust": 0.04,
                        "contempt": 0.02
                    },
                    {
                        "time": 2.0,
                        "confidence": 0.82,
                        "joy": 0.68,
                        "surprise": 0.35,
                        "fear": 0.12,
                        "anger": 0.05,
                        "sadness": 0.15,
                        "disgust": 0.06,
                        "contempt": 0.03
                    }
                ]
            },
            "filename": filename,
            "processing_time": 2.5,
            "workflow_complete": True,
            "mock": True
        }


def get_hume_client() -> HumeAPIRepository:
    """
    Factory function to get configured Hume API client.
    
    Returns:
        Real or mock Hume API repository based on configuration
    """
    api_key = os.getenv('HUME_API_KEY')
    secret_key = os.getenv('HUME_SECRET_KEY')
    
    if not api_key or not secret_key or api_key == 'your_hume_api_key_here':
        logger.info("Using mock Hume API repository (no valid credentials)")
        return MockHumeAPIRepository()
    else:
        logger.info("Using real Hume API repository")
        return HumeAPIRepository(api_key, secret_key)
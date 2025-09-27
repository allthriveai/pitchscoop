"""
Shared models used across multiple domains
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ============= Error Models =============

class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str
    message: str
    field: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    details: Optional[str] = None
    code: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Resource not found",
                "details": "Event with ID 'xyz' does not exist",
                "code": "EVENT_NOT_FOUND"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    error: str = "Validation error"
    details: List[ErrorDetail]
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Validation error",
                "details": [
                    {
                        "code": "REQUIRED_FIELD",
                        "message": "Field is required",
                        "field": "event_name"
                    }
                ]
            }
        }


# ============= Base Response Models =============

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response"""
    ok: bool
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    services: Optional[Dict[str, str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "timestamp": "2024-01-15T10:30:00Z",
                "services": {"redis": "healthy"}
            }
        }


# ============= Common Domain Models =============

class PaginationParams(BaseModel):
    """Common pagination parameters"""
    offset: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum items to return")


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow()


class AuditMixin(BaseModel):
    """Mixin for models with audit fields"""
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    version: int = Field(1, ge=1)
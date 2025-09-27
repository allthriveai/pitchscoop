"""
Users/Auth domain REST API router  
"""
from typing import Dict, Any, Optional, List, Literal
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import json
import redis.asyncio as redis
import os
from dotenv import load_dotenv

# Import MCP handlers
from .mcp.users_mcp_tools import USERS_TOOLS, handle_users_tool_call

load_dotenv()
router = APIRouter(prefix="/api", tags=["users", "auth"])


# ============= Models =============

class SetRoleRequest(BaseModel):
    """Request to set user role"""
    user_id: str = Field(..., description="User identifier")
    role: Literal["organizer", "individual", "judge", "participant", "admin"]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "role": "organizer"
            }
        }


class SetRoleResponse(BaseModel):
    """Response for role setting"""
    ok: bool
    user_id: str
    role: str
    message: str = "Role updated successfully"


class UserProfile(BaseModel):
    """User profile information"""
    user_id: str
    email: Optional[EmailStr]
    display_name: Optional[str]
    role: str
    created_at: datetime
    last_active: Optional[datetime]
    metadata: Dict[str, Any] = {}


class CreateUserRequest(BaseModel):
    """Request to create a new user"""
    email: EmailStr
    display_name: str
    role: Literal["organizer", "individual", "judge", "participant"] = "participant"
    password: Optional[str] = Field(None, description="Optional password for auth")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "display_name": "John Doe",
                "role": "participant"
            }
        }


class UserResponse(BaseModel):
    """User creation/update response"""
    user_id: str
    email: str
    display_name: str
    role: str
    created_at: datetime


class AuthRequest(BaseModel):
    """Authentication request"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "securepassword123"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user_id: str
    role: str


class UserListResponse(BaseModel):
    """Response for user listing"""
    users: List[UserProfile]
    total_count: int
    filters_applied: Dict[str, Any] = {}


# ============= Dependencies =============

async def get_redis() -> redis.Redis:
    """Get Redis connection"""
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return await redis.from_url(REDIS_URL, decode_responses=True)


# ============= Helper functions =============

async def execute_users_tool(tool_name: str, args: Dict[str, Any]):
    """Execute users MCP tool."""
    try:
        return await handle_users_tool_call(tool_name, args)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# ============= Endpoints =============

# Legacy endpoint for backward compatibility
@router.post("/auth.set_role", response_model=SetRoleResponse)
async def set_role_legacy(request: SetRoleRequest):
    """Legacy endpoint: Set user role"""
    r = await get_redis()
    try:
        user_key = f"user:{request.user_id}"
        await r.hset(user_key, "role", request.role)
        
        return SetRoleResponse(
            ok=True,
            user_id=request.user_id,
            role=request.role
        )
    finally:
        await r.close()


@router.post("/users/create", response_model=UserResponse)
async def create_user(request: CreateUserRequest):
    """Create a new user"""
    try:
        result = await execute_users_tool("users.create_user", request.dict())
        return UserResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/role", response_model=SetRoleResponse)
async def set_user_role(user_id: str, role: str = Body(...)):
    """Set or update user role"""
    r = await get_redis()
    try:
        user_key = f"user:{user_id}"
        
        # Check if user exists
        exists = await r.exists(user_key)
        if not exists:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        await r.hset(user_key, "role", role)
        
        return SetRoleResponse(
            ok=True,
            user_id=user_id,
            role=role
        )
    finally:
        await r.close()


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user(user_id: str):
    """Get user profile information"""
    try:
        result = await execute_users_tool("users.get_user", {
            "user_id": user_id
        })
        return UserProfile(**result)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users", response_model=UserListResponse)
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    active_since: Optional[str] = Query(None, description="Filter by last active date"),
    limit: int = Query(100, le=500, description="Maximum results to return")
):
    """List all users with optional filters"""
    try:
        result = await execute_users_tool("users.list_users", {
            "role": role,
            "active_since": active_since,
            "limit": limit
        })
        
        return UserListResponse(
            users=[UserProfile(**u) for u in result.get("users", [])],
            total_count=result.get("total_count", 0),
            filters_applied={
                "role": role,
                "active_since": active_since
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/login", response_model=AuthResponse)
async def login(request: AuthRequest):
    """Authenticate user and get access token"""
    try:
        result = await execute_users_tool("users.authenticate", request.dict())
        return AuthResponse(**result)
    except Exception as e:
        if "invalid" in str(e).lower():
            raise HTTPException(status_code=401, detail="Invalid credentials")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/auth/logout")
async def logout(user_id: str = Body(...)):
    """Logout user and invalidate token"""
    try:
        result = await execute_users_tool("users.logout", {
            "user_id": user_id
        })
        return {"message": "Logged out successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user account"""
    try:
        result = await execute_users_tool("users.delete_user", {
            "user_id": user_id
        })
        return {"message": f"User {user_id} deleted successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    """Get all pitch sessions for a user"""
    try:
        result = await execute_users_tool("users.get_user_sessions", {
            "user_id": user_id
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/users/{user_id}/events")
async def get_user_events(user_id: str):
    """Get all events a user is participating in"""
    try:
        result = await execute_users_tool("users.get_user_events", {
            "user_id": user_id
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/users/{user_id}")
async def update_user_profile(
    user_id: str,
    display_name: Optional[str] = Body(None),
    email: Optional[EmailStr] = Body(None),
    metadata: Optional[Dict[str, Any]] = Body(None)
):
    """Update user profile information"""
    try:
        update_data = {}
        if display_name:
            update_data["display_name"] = display_name
        if email:
            update_data["email"] = email
        if metadata:
            update_data["metadata"] = metadata
            
        result = await execute_users_tool("users.update_profile", {
            "user_id": user_id,
            **update_data
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
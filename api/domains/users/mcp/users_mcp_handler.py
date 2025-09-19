"""
Users MCP Handler - Business logic for user management

This handler manages users (participants, organizers, judges) using Redis for persistence.

Users are stored with the following structure:
- user:{user_id} - Main user data
- user:email:{email} - Email to user_id mapping for lookups
- user:{user_id}:recordings - Set of recording IDs for this user
- user:{user_id}:events - Set of event IDs for this user
"""
import json
import uuid
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

import redis.asyncio as redis
from dotenv import load_dotenv

from ..entities.user import User, UserRole, UserStatus, UserProfile

# Load environment variables
load_dotenv()


class UsersMCPHandler:
    """MCP handler for Users domain operations."""
    
    def __init__(self):
        """Initialize the Users MCP handler."""
        self.redis_client: Optional[redis.Redis] = None
        
    async def get_redis(self) -> redis.Redis:
        """Get Redis client connection."""
        if self.redis_client is None:
            # Use environment variable, fallback to Docker internal network
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
        return self.redis_client
    
    async def create_user(
        self,
        name: str,
        email: str,
        role: str = "participant",
        profile_data: Optional[Dict[str, Any]] = None,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            name: User's full name
            email: User's email address (must be unique)
            role: User role (participant, organizer, judge, admin)
            profile_data: Optional profile information
            org_id: Organization ID for multi-tenant isolation
            
        Returns:
            Created user information
        """
        try:
            redis_client = await self.get_redis()
            
            # Build Redis key prefix for multi-tenant support
            key_prefix = f"{org_id}:" if org_id else ""
            
            # Check if email already exists
            existing_user_id = await redis_client.get(f"{key_prefix}user:email:{email}")
            if existing_user_id:
                return {
                    "error": "Email already registered",
                    "email": email
                }
            
            # Create user profile
            profile = UserProfile()
            if profile_data:
                for key, value in profile_data.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
            
            # Create user entity
            user = User.create_new(
                name=name,
                email=email,
                role=UserRole(role),
                profile=profile
            )
            
            # Store user data in Redis
            user_key = f"{key_prefix}user:{user.user_id}"
            await redis_client.setex(
                user_key,
                86400 * 365,  # 1 year TTL
                json.dumps(user.to_dict())
            )
            
            # Create email lookup
            await redis_client.setex(
                f"{key_prefix}user:email:{email}",
                86400 * 365,
                user.user_id
            )
            
            # Initialize empty relationships
            await redis_client.setex(
                f"{key_prefix}user:{user.user_id}:recordings",
                86400 * 365,
                json.dumps([])
            )
            
            await redis_client.setex(
                f"{key_prefix}user:{user.user_id}:events",
                86400 * 365,
                json.dumps([])
            )
            
            return {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "status": user.status.value,
                "created_at": user.created_at.isoformat(),
                "profile": user.profile.to_dict(),
                "instructions": {
                    "next_step": "User created successfully. Can now join events or create recordings.",
                    "join_event": "Use events.join_event to participate in events",
                    "create_recording": "Use recordings.start_session to create pitch recordings"
                }
            }
            
        except ValueError as e:
            return {"error": f"Invalid user data: {str(e)}"}
        except Exception as e:
            return {"error": f"Failed to create user: {str(e)}"}
    
    async def get_user_by_id(
        self,
        user_id: str,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user by ID.
        
        Args:
            user_id: User identifier
            org_id: Organization ID for multi-tenant isolation
            
        Returns:
            User information with relationships
        """
        try:
            redis_client = await self.get_redis()
            key_prefix = f"{org_id}:" if org_id else ""
            
            # Get user data
            user_json = await redis_client.get(f"{key_prefix}user:{user_id}")
            if not user_json:
                return {"error": "User not found", "user_id": user_id}
            
            user_data = json.loads(user_json)
            
            # Get user's recordings
            recordings_json = await redis_client.get(f"{key_prefix}user:{user_id}:recordings")
            recordings = json.loads(recordings_json) if recordings_json else []
            
            # Get user's events
            events_json = await redis_client.get(f"{key_prefix}user:{user_id}:events")
            events = json.loads(events_json) if events_json else []
            
            # Add relationship data
            user_data["recordings"] = recordings
            user_data["events"] = events
            user_data["recording_count"] = len(recordings)
            user_data["event_count"] = len(events)
            
            return user_data
            
        except Exception as e:
            return {"error": f"Failed to get user: {str(e)}", "user_id": user_id}
    
    async def get_user_by_email(
        self,
        email: str,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user by email address.
        
        Args:
            email: User's email address
            org_id: Organization ID for multi-tenant isolation
            
        Returns:
            User information
        """
        try:
            redis_client = await self.get_redis()
            key_prefix = f"{org_id}:" if org_id else ""
            
            # Get user ID from email lookup
            user_id = await redis_client.get(f"{key_prefix}user:email:{email}")
            if not user_id:
                return {"error": "User not found", "email": email}
            
            # Get user by ID
            return await self.get_user_by_id(user_id, org_id)
            
        except Exception as e:
            return {"error": f"Failed to get user by email: {str(e)}", "email": email}
    
    async def update_user(
        self,
        user_id: str,
        updates: Dict[str, Any],
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update user information.
        
        Args:
            user_id: User identifier
            updates: Fields to update
            org_id: Organization ID for multi-tenant isolation
            
        Returns:
            Updated user information
        """
        try:
            redis_client = await self.get_redis()
            key_prefix = f"{org_id}:" if org_id else ""
            
            # Get existing user
            user_json = await redis_client.get(f"{key_prefix}user:{user_id}")
            if not user_json:
                return {"error": "User not found", "user_id": user_id}
            
            # Recreate user entity from stored data
            user_data = json.loads(user_json)
            user = User.from_dict(user_data)
            
            # Apply updates
            if "name" in updates:
                user.name = updates["name"]
            
            if "role" in updates:
                user.update_role(UserRole(updates["role"]))
            
            if "status" in updates:
                user.update_status(UserStatus(updates["status"]))
            
            if "profile" in updates:
                user.update_profile(**updates["profile"])
            
            # Handle email change (more complex due to lookup)
            if "email" in updates and updates["email"] != user.email:
                new_email = updates["email"]
                
                # Check if new email is already taken
                existing_user_id = await redis_client.get(f"{key_prefix}user:email:{new_email}")
                if existing_user_id and existing_user_id != user_id:
                    return {"error": "Email already in use", "email": new_email}
                
                # Remove old email lookup
                await redis_client.delete(f"{key_prefix}user:email:{user.email}")
                
                # Update user email
                user.email = new_email
                
                # Create new email lookup
                await redis_client.setex(
                    f"{key_prefix}user:email:{new_email}",
                    86400 * 365,
                    user_id
                )
            
            # Save updated user
            await redis_client.setex(
                f"{key_prefix}user:{user_id}",
                86400 * 365,
                json.dumps(user.to_dict())
            )
            
            return {
                "user_id": user.user_id,
                "name": user.name,
                "email": user.email,
                "role": user.role.value,
                "status": user.status.value,
                "updated_at": user.updated_at.isoformat(),
                "message": "User updated successfully"
            }
            
        except ValueError as e:
            return {"error": f"Invalid update data: {str(e)}", "user_id": user_id}
        except Exception as e:
            return {"error": f"Failed to update user: {str(e)}", "user_id": user_id}
    
    async def list_users(
        self,
        role: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List users with optional filtering.
        
        Args:
            role: Filter by user role
            status: Filter by user status
            limit: Maximum number of results
            org_id: Organization ID for multi-tenant isolation
            
        Returns:
            List of user summaries
        """
        try:
            redis_client = await self.get_redis()
            key_prefix = f"{org_id}:" if org_id else ""
            
            # Get all user keys
            user_keys = []
            search_pattern = f"{key_prefix}user:*" if key_prefix else "user:*"
            async for key in redis_client.scan_iter(match=search_pattern):
                # Skip email lookup and relationship keys
                if (":email:" not in key and 
                    ":recordings" not in key and 
                    ":events" not in key and
                    key.count(":") == 1):  # Only user:{user_id} keys
                    user_keys.append(key)
            
            users = []
            for key in user_keys[:limit * 2]:  # Get extra in case some are filtered out
                try:
                    user_json = await redis_client.get(key)
                    if user_json:
                        user_data = json.loads(user_json)
                        
                        # Apply filters
                        if role and user_data.get("role") != role:
                            continue
                        if status and user_data.get("status") != status:
                            continue
                        
                        # Create user summary
                        user_summary = {
                            "user_id": user_data["user_id"],
                            "name": user_data["name"],
                            "email": user_data["email"],
                            "role": user_data["role"],
                            "status": user_data["status"],
                            "created_at": user_data["created_at"],
                            "last_login_at": user_data.get("last_login_at"),
                            "recording_count": len(user_data.get("recording_ids", [])),
                            "event_count": len(user_data.get("event_ids", []))
                        }
                        
                        # Add profile highlights
                        profile = user_data.get("profile", {})
                        if profile.get("company"):
                            user_summary["company"] = profile["company"]
                        if profile.get("position"):
                            user_summary["position"] = profile["position"]
                        
                        users.append(user_summary)
                        
                        if len(users) >= limit:
                            break
                            
                except Exception as e:
                    # Skip invalid users
                    continue
            
            # Sort by creation time (newest first)
            users.sort(key=lambda x: x["created_at"], reverse=True)
            
            return {
                "users": users,
                "total_count": len(users),
                "filters_applied": {
                    "role": role,
                    "status": status,
                    "limit": limit
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to list users: {str(e)}", "users": []}
    
    async def add_user_recording(
        self,
        user_id: str,
        recording_id: str,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a recording to user's collection.
        
        Args:
            user_id: User identifier
            recording_id: Recording identifier
            org_id: Organization ID for multi-tenant isolation
            
        Returns:
            Success confirmation
        """
        try:
            redis_client = await self.get_redis()
            key_prefix = f"{org_id}:" if org_id else ""
            
            # Get user's current recordings
            recordings_json = await redis_client.get(f"{key_prefix}user:{user_id}:recordings")
            recordings = json.loads(recordings_json) if recordings_json else []
            
            # Add recording if not already present
            if recording_id not in recordings:
                recordings.append(recording_id)
                
                # Update recordings list
                await redis_client.setex(
                    f"{key_prefix}user:{user_id}:recordings",
                    86400 * 365,
                    json.dumps(recordings)
                )
                
                # Update user entity's recording_ids
                user_json = await redis_client.get(f"{key_prefix}user:{user_id}")
                if user_json:
                    user_data = json.loads(user_json)
                    user = User.from_dict(user_data)
                    user.add_recording(recording_id)
                    
                    await redis_client.setex(
                        f"{key_prefix}user:{user_id}",
                        86400 * 365,
                        json.dumps(user.to_dict())
                    )
            
            return {
                "user_id": user_id,
                "recording_id": recording_id,
                "total_recordings": len(recordings),
                "message": "Recording added to user"
            }
            
        except Exception as e:
            return {"error": f"Failed to add recording to user: {str(e)}"}
    
    async def add_user_event(
        self,
        user_id: str,
        event_id: str,
        org_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add an event to user's collection.
        
        Args:
            user_id: User identifier
            event_id: Event identifier
            org_id: Organization ID for multi-tenant isolation
            
        Returns:
            Success confirmation
        """
        try:
            redis_client = await self.get_redis()
            key_prefix = f"{org_id}:" if org_id else ""
            
            # Get user's current events
            events_json = await redis_client.get(f"{key_prefix}user:{user_id}:events")
            events = json.loads(events_json) if events_json else []
            
            # Add event if not already present
            if event_id not in events:
                events.append(event_id)
                
                # Update events list
                await redis_client.setex(
                    f"{key_prefix}user:{user_id}:events",
                    86400 * 365,
                    json.dumps(events)
                )
                
                # Update user entity's event_ids
                user_json = await redis_client.get(f"{key_prefix}user:{user_id}")
                if user_json:
                    user_data = json.loads(user_json)
                    user = User.from_dict(user_data)
                    user.add_event(event_id)
                    
                    await redis_client.setex(
                        f"{key_prefix}user:{user_id}",
                        86400 * 365,
                        json.dumps(user.to_dict())
                    )
            
            return {
                "user_id": user_id,
                "event_id": event_id,
                "total_events": len(events),
                "message": "Event added to user"
            }
            
        except Exception as e:
            return {"error": f"Failed to add event to user: {str(e)}"}
    
    async def delete_user(
        self,
        user_id: str,
        org_id: Optional[str] = None,
        hard_delete: bool = False
    ) -> Dict[str, Any]:
        """
        Delete or deactivate a user.
        
        Args:
            user_id: User identifier
            org_id: Organization ID for multi-tenant isolation
            hard_delete: If True, permanently delete; if False, just deactivate
            
        Returns:
            Deletion confirmation
        """
        try:
            redis_client = await self.get_redis()
            key_prefix = f"{org_id}:" if org_id else ""
            
            # Get user data
            user_json = await redis_client.get(f"{key_prefix}user:{user_id}")
            if not user_json:
                return {"error": "User not found", "user_id": user_id}
            
            if hard_delete:
                # Get user data to remove email lookup
                user_data = json.loads(user_json)
                email = user_data.get("email")
                
                # Delete all user data
                await redis_client.delete(f"{key_prefix}user:{user_id}")
                await redis_client.delete(f"{key_prefix}user:{user_id}:recordings")
                await redis_client.delete(f"{key_prefix}user:{user_id}:events")
                
                if email:
                    await redis_client.delete(f"{key_prefix}user:email:{email}")
                
                return {
                    "user_id": user_id,
                    "message": "User permanently deleted",
                    "hard_delete": True
                }
            else:
                # Soft delete - just change status
                user_data = json.loads(user_json)
                user = User.from_dict(user_data)
                user.update_status(UserStatus.DELETED)
                
                await redis_client.setex(
                    f"{key_prefix}user:{user_id}",
                    86400 * 365,
                    json.dumps(user.to_dict())
                )
                
                return {
                    "user_id": user_id,
                    "message": "User deactivated (soft delete)",
                    "hard_delete": False,
                    "status": "deleted"
                }
            
        except Exception as e:
            return {"error": f"Failed to delete user: {str(e)}", "user_id": user_id}
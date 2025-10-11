"""
Onboarding Repository

Handles database operations for onboarding domain.
Provides CRUD operations for sessions, profiles, and event customizations.
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from ..entities.onboarding_session import OnboardingSession, OnboardingStatus, OnboardingRole
from ..entities.user_profile import UserProfile
from ..entities.event_customization import EventCustomization


class OnboardingRepository:
    """Repository for onboarding database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # === Onboarding Session Operations ===
    
    async def create_session(self, session: OnboardingSession) -> OnboardingSession:
        """Create a new onboarding session"""
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def get_session(self, session_id: str) -> Optional[OnboardingSession]:
        """Get onboarding session by ID"""
        result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_active_session(self, user_id: str) -> Optional[OnboardingSession]:
        """Get user's active (in-progress) onboarding session"""
        result = await self.db.execute(
            select(OnboardingSession).where(
                OnboardingSession.user_id == user_id,
                OnboardingSession.status == OnboardingStatus.IN_PROGRESS
            ).order_by(OnboardingSession.started_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def update_session(self, session: OnboardingSession) -> OnboardingSession:
        """Update onboarding session"""
        session.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(session)
        return session
    
    async def complete_session(self, session_id: str) -> OnboardingSession:
        """Mark session as completed"""
        session = await self.get_session(session_id)
        if session:
            session.status = OnboardingStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            await self.db.flush()
            await self.db.refresh(session)
        return session
    
    # === User Profile Operations ===
    
    async def create_profile(self, profile: UserProfile) -> UserProfile:
        """Create a new user profile"""
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile
    
    async def get_profile_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user ID"""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_profile(self, profile: UserProfile) -> UserProfile:
        """Update user profile"""
        profile.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(profile)
        return profile
    
    # === Event Customization Operations ===
    
    async def create_event_customization(self, customization: EventCustomization) -> EventCustomization:
        """Create event customization"""
        self.db.add(customization)
        await self.db.flush()
        await self.db.refresh(customization)
        return customization
    
    async def get_event_customization(self, event_id: str) -> Optional[EventCustomization]:
        """Get event customization by event ID"""
        result = await self.db.execute(
            select(EventCustomization).where(EventCustomization.event_id == event_id)
        )
        return result.scalar_one_or_none()
    
    async def update_event_customization(self, customization: EventCustomization) -> EventCustomization:
        """Update event customization"""
        customization.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(customization)
        return customization
    
    async def list_user_event_customizations(self, user_id: str) -> List[EventCustomization]:
        """List all event customizations created by a user"""
        result = await self.db.execute(
            select(EventCustomization).where(
                EventCustomization.created_by == user_id
            ).order_by(EventCustomization.created_at.desc())
        )
        return list(result.scalars().all())

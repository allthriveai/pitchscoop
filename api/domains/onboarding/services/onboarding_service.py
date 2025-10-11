"""
Onboarding Service

Implements the onboarding flow from docs/ONBOARDING_FLOW.md
Works for both MCP (Claude Desktop) and Web UI.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..entities.onboarding_session import OnboardingSession, OnboardingRole, OnboardingStatus
from ..entities.user_profile import UserProfile
from ..entities.event_customization import EventCustomization
from ..repositories.onboarding_repository import OnboardingRepository
from ..config.default_judging_criteria import (
    get_default_judging_categories,
    normalize_judging_weights,
    DEFAULT_REQUIRED_FIELDS,
    DEFAULT_HELP_TEXT
)


class OnboardingService:
    """Onboarding business logic - shared by MCP and Web"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OnboardingRepository(db)
    
    async def start_onboarding(self, user_id: str, role: str, event_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start onboarding flow.
        
        Initial User Decision Point from ONBOARDING_FLOW.md:
        Question: "What would you like to do?"
        - Path A: Create an Event (role="organizer")
        - Path B: Join an Event (role="participant")
        
        Args:
            user_id: User identifier
            role: "organizer" or "participant"
            event_id: Optional event ID if joining existing event
            
        Returns:
            Session info and welcome message
        """
        # Check for existing active session
        existing_session = await self.repo.get_user_active_session(user_id)
        if existing_session:
            return {
                "session_id": existing_session.id,
                "resuming": True,
                "message": "Welcome back! Continue where you left off.",
                "current_step": await self._get_step_details(existing_session)
            }
        
        # Create new session
        onboarding_role = OnboardingRole.ORGANIZER if role == "organizer" else OnboardingRole.PARTICIPANT
        
        session = OnboardingSession(
            user_id=user_id,
            role=onboarding_role,
            current_flow="event_creation_flow" if role == "organizer" else "participant_flow",
            current_step="event_link_check" if role == "organizer" else "create_profile",
            completed_steps=[],
            session_data={},
            total_steps=3 if role == "organizer" else 2,  # link_check + event_details + judging OR profile + options
            event_id=event_id
        )
        
        session = await self.repo.create_session(session)
        await self.db.commit()
        
        # Welcome message from ONBOARDING_FLOW.md
        if role == "organizer":
            welcome = "Ready to create an amazing competition?"
            help_text = "You can be an event organizer or set up a one-off practice. Events can be practice, a hackathon, investor pitch, or job interview."
        else:
            welcome = "Find the perfect event to showcase your skills!"
            help_text = "Join an event as practice or submit to the event to be part of the leaderboard."
        
        return {
            "session_id": session.id,
            "resuming": False,
            "role": role,
            "welcome_message": welcome,
            "help_text": help_text,
            "current_step": await self._get_step_details(session)
        }
    
    async def process_step(self, session_id: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data for current step and move to next step.
        
        Args:
            session_id: Onboarding session ID
            step_data: Data submitted for current step
            
        Returns:
            Result with next step or completion status
        """
        session = await self.repo.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        # Validate step data
        validation_result = await self._validate_step_data(session, step_data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "errors": validation_result["errors"],
                "current_step": await self._get_step_details(session)
            }
        
        # Save step data
        session.session_data.update(step_data)
        session.completed_steps.append(session.current_step)
        
        # Move to next step based on flow
        next_step_result = await self._move_to_next_step(session)
        
        await self.repo.update_session(session)
        await self.db.commit()
        
        return next_step_result
    
    async def _move_to_next_step(self, session: OnboardingSession) -> Dict[str, Any]:
        """Determine and move to next step based on current flow"""
        
        if session.role == OnboardingRole.ORGANIZER:
            # Event Creation Flow from ONBOARDING_FLOW.md
            if session.current_step == "event_link_check":
                # Check if user provided a link
                if session.session_data.get("event_link"):
                    # TODO: Scrape event details from link
                    session.current_step = "event_details"
                    return {
                        "success": True,
                        "completed": False,
                        "message": "Great! I'll try to scrape details from that link. Please review and fill in any missing information.",
                        "next_step": await self._get_step_details(session),
                        "progress": {
                            "completed": len(session.completed_steps),
                            "total": session.total_steps,
                            "percentage": int((len(session.completed_steps) / session.total_steps) * 100)
                        }
                    }
                else:
                    # No link provided, go to manual entry
                    session.current_step = "event_details"
                    return {
                        "success": True,
                        "completed": False,
                        "message": "No problem! Let's create your event manually.",
                        "next_step": await self._get_step_details(session),
                        "progress": {
                            "completed": len(session.completed_steps),
                            "total": session.total_steps,
                            "percentage": int((len(session.completed_steps) / session.total_steps) * 100)
                        }
                    }
            
            elif session.current_step == "event_details":
                # Move to judging criteria setup
                session.current_step = "judging_criteria"
                return {
                    "success": True,
                    "completed": False,
                    "message": "Event details saved!",
                    "next_step": await self._get_step_details(session),
                    "progress": {
                        "completed": len(session.completed_steps),
                        "total": session.total_steps,
                        "percentage": int((len(session.completed_steps) / session.total_steps) * 100)
                    }
                }
            
            elif session.current_step == "judging_criteria":
                # Complete onboarding - create event customization
                await self._create_event_customization(session)
                session.status = OnboardingStatus.COMPLETED
                session.completed_at = datetime.utcnow()
                
                return {
                    "success": True,
                    "completed": True,
                    "message": "🎉 Your event is ready!",
                    "event_id": session.session_data.get("event_id"),
                    "summary": await self._get_organizer_summary(session),
                    "next_actions": [
                        "Manage event settings",
                        "Adjust judging criteria weights",
                        "View participant submissions"
                    ]
                }
        
        else:  # PARTICIPANT
            # Participant Onboarding Flow from ONBOARDING_FLOW.md
            if session.current_step == "create_profile":
                # Create user profile
                await self._create_user_profile(session)
                
                # Move to participation options
                session.current_step = "participation_options"
                return {
                    "success": True,
                    "completed": False,
                    "message": "Profile created!",
                    "next_step": await self._get_step_details(session),
                    "progress": {
                        "completed": len(session.completed_steps),
                        "total": session.total_steps,
                        "percentage": int((len(session.completed_steps) / session.total_steps) * 100)
                    }
                }
            
            elif session.current_step == "participation_options":
                # Complete onboarding
                session.status = OnboardingStatus.COMPLETED
                session.completed_at = datetime.utcnow()
                
                return {
                    "success": True,
                    "completed": True,
                    "message": "✅ You're all set!",
                    "summary": await self._get_participant_summary(session),
                    "next_actions": [
                        "Join an existing event",
                        "Upload video or take a video",
                        "See past events",
                        "Record and practice"
                    ]
                }
        
        return {"success": False, "error": "Unknown step"}
    
    async def _get_step_details(self, session: OnboardingSession) -> Dict[str, Any]:
        """Get detailed information about current step"""
        
        if session.role == OnboardingRole.ORGANIZER:
            if session.current_step == "event_link_check":
                # Initial Link Check step
                return {
                    "step_id": "event_link_check",
                    "title": "Quick Start",
                    "description": "Do you have a public event page I can automatically scrape details from to save you time?",
                    "fields": [
                        {
                            "id": "event_link",
                            "label": "Event page URL (optional)",
                            "type": "url",
                            "required": False,
                            "placeholder": "https://devpost.com/your-hackathon or https://lu.ma/your-event",
                            "help_text": "I can auto-fill details from Devpost, Luma, Eventbrite, and other event platforms. Leave blank to enter manually."
                        }
                    ]
                }
            
            elif session.current_step == "event_details":
                # Event Details step from ONBOARDING_FLOW.md
                return {
                    "step_id": "event_details",
                    "title": "Event Details",
                    "description": "Tell us about your event" if not session.session_data.get("event_link") else "Review and complete the event details",
                    "fields": [
                        {
                            "id": "event_name",
                            "label": "Name of event",
                            "type": "text",
                            "required": True
                        },
                        {
                            "id": "event_type",
                            "label": "Event Type",
                            "type": "select",
                            "required": True,
                            "options": ["Hackathon", "VC Pitch", "Interview", "Practice", "Other"],
                            "help_text": DEFAULT_HELP_TEXT["event_types"]
                        },
                        {
                            "id": "event_date",
                            "label": "Date of event",
                            "type": "date",
                            "required": True
                        },
                        {
                            "id": "judging_rules",
                            "label": "Rules for judging",
                            "type": "textarea",
                            "required": True
                        }
                    ]
                }
            
            elif session.current_step == "judging_criteria":
                # Judging Criteria Setup from ONBOARDING_FLOW.md
                default_categories = get_default_judging_categories()
                
                return {
                    "step_id": "judging_criteria",
                    "title": "Judging Criteria Setup",
                    "description": "Set up how participants will be evaluated",
                    "default_categories": default_categories,
                    "help_text": {
                        "weights": DEFAULT_HELP_TEXT["judging_weights"],
                        "custom": DEFAULT_HELP_TEXT["custom_categories"]
                    },
                    "fields": [
                        {
                            "id": "judging_categories",
                            "label": "Judging Categories",
                            "type": "category_list",
                            "default": default_categories,
                            "adjustable_weights": True
                        },
                        {
                            "id": "custom_category_name",
                            "label": "Custom category name (Optional)",
                            "type": "text",
                            "required": False,
                            "placeholder": "e.g., Sustainability Impact, User Experience"
                        },
                        {
                            "id": "custom_category_description",
                            "label": "Custom criteria description",
                            "type": "textarea",
                            "required": False,
                            "placeholder": "Describe what this category measures"
                        },
                        {
                            "id": "custom_category_weight",
                            "label": "Custom category weight",
                            "type": "number",
                            "required": False,
                            "min": 0,
                            "max": 1,
                            "step": 0.05
                        }
                    ]
                }
        
        else:  # PARTICIPANT
            if session.current_step == "create_profile":
                # Create Profile from ONBOARDING_FLOW.md
                return {
                    "step_id": "create_profile",
                    "title": "Create Profile",
                    "description": "Tell us about you and your project",
                    "fields": [
                        {
                            "id": "user_name",
                            "label": "User name",
                            "type": "text",
                            "required": True
                        },
                        {
                            "id": "team_name",
                            "label": "Team name",
                            "type": "text",
                            "required": True
                        },
                        {
                            "id": "project_name",
                            "label": "Project name",
                            "type": "text",
                            "required": True
                        },
                        {
                            "id": "project_description",
                            "label": "Project description",
                            "type": "textarea",
                            "required": True,
                            "help_text": DEFAULT_HELP_TEXT["project_description"]
                        },
                        {
                            "id": "github_repo",
                            "label": "GitHub repo",
                            "type": "url",
                            "required": False
                        }
                    ]
                }
            
            elif session.current_step == "participation_options":
                # Event Participation Options from ONBOARDING_FLOW.md
                return {
                    "step_id": "participation_options",
                    "title": "Event Participation Options",
                    "description": "Choose how you want to participate",
                    "options": [
                        {"id": "join_existing", "label": "Join an existing event"},
                        {"id": "upload_video", "label": "Upload video or take a video"},
                        {"id": "see_past_events", "label": "See past events"},
                        {"id": "record_practice", "label": "Record and practice"}
                    ]
                }
        
        return {}
    
    async def _validate_step_data(self, session: OnboardingSession, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate step data based on step requirements"""
        errors = []
        
        step_details = await self._get_step_details(session)
        fields = step_details.get("fields", [])
        
        # Check required fields
        for field in fields:
            if field.get("required") and not step_data.get(field["id"]):
                errors.append(f"{field['label']} is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def _create_user_profile(self, session: OnboardingSession):
        """Create user profile from session data"""
        profile_data = session.session_data
        
        profile = UserProfile(
            user_id=session.user_id,
            user_name=profile_data.get("user_name"),
            team_name=profile_data.get("team_name"),
            project_name=profile_data.get("project_name"),
            project_description=profile_data.get("project_description"),
            github_repo=profile_data.get("github_repo")
        )
        
        await self.repo.create_profile(profile)
    
    async def _create_event_customization(self, session: OnboardingSession):
        """Create event customization from session data"""
        event_data = session.session_data
        
        # Get judging categories
        categories = event_data.get("judging_categories", get_default_judging_categories())
        
        # Add custom category if provided
        if event_data.get("custom_category_name"):
            categories.append({
                "id": "custom",
                "name": event_data.get("custom_category_name"),
                "weight": event_data.get("custom_category_weight", 0.15),
                "adjustable": True,
                "description": event_data.get("custom_category_description")
            })
            
            # Normalize weights to sum to 1.0
            categories = normalize_judging_weights(categories)
        
        # Generate event ID (in real implementation, this would come from events domain)
        event_id = event_data.get("event_id") or f"{event_data.get('event_name', 'event').lower().replace(' ', '-')}-{datetime.utcnow().strftime('%Y%m%d')}"
        
        customization = EventCustomization(
            event_id=event_id,
            event_name=event_data.get("event_name"),
            welcome_message=f"Welcome to {event_data.get('event_name')}!",
            required_fields=DEFAULT_REQUIRED_FIELDS,
            judging_categories=categories,
            custom_category_name=event_data.get("custom_category_name"),
            custom_category_description=event_data.get("custom_category_description"),
            custom_category_weight=event_data.get("custom_category_weight"),
            created_by=session.user_id
        )
        
        await self.repo.create_event_customization(customization)
        
        # Store event_id in session for reference
        session.session_data["event_id"] = event_id
    
    async def _get_organizer_summary(self, session: OnboardingSession) -> Dict[str, Any]:
        """Get summary for completed organizer onboarding"""
        event_data = session.session_data
        
        return {
            "event_name": event_data.get("event_name"),
            "event_type": event_data.get("event_type"),
            "event_date": event_data.get("event_date"),
            "event_id": event_data.get("event_id"),
            "judging_categories": event_data.get("judging_categories", [])
        }
    
    async def _get_participant_summary(self, session: OnboardingSession) -> Dict[str, Any]:
        """Get summary for completed participant onboarding"""
        profile_data = session.session_data
        
        return {
            "user_name": profile_data.get("user_name"),
            "team_name": profile_data.get("team_name"),
            "project_name": profile_data.get("project_name"),
            "github_repo": profile_data.get("github_repo")
        }
    
    async def get_help(self, topic: str) -> Dict[str, Any]:
        """Get help text for specific topic"""
        if topic in DEFAULT_HELP_TEXT:
            return {
                "topic": topic,
                "help_text": DEFAULT_HELP_TEXT[topic]
            }
        
        return {
            "topic": topic,
            "help_text": "No help available for this topic"
        }
